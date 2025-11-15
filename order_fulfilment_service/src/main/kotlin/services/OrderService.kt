package org.example.services

import org.example.dto.OrderEntity
import org.example.dto.OrderItemDto
import org.example.dto.OrderItemEntity
import org.example.dto.ProductDto
import org.example.dto.ShortageAction
import org.example.dto.ShortageDecision
import org.example.dto.ShortageItemRequest
import org.example.dto.ShortageLine
import org.example.dto.ShortageProactiveRequest
import org.example.dto.WarehouseItem
import org.example.repositories.OrderRepository
import org.example.repositories.WarehouseItemRepository
import org.springframework.stereotype.Service
import org.springframework.transaction.annotation.Transactional

@Service
class OrderService(
    private val externalClient: ExternalOrderServicesClient,
    private val warehouseItemRepository: WarehouseItemRepository,
    private val orderRepository: OrderRepository
) {

    @Transactional
    fun saveOrder(order: ProductDto) {
        // 1. /predict/order — id позиций, которые стоит рассмотреть на замену
        val predictResponse = externalClient.getItemsToReplace(order)
        val lineIdsToReplace: Set<Int> = predictResponse.lineIds.toSet()

        // 2. Для каждого такого id берём список id-замен из /substitution/suggest
        val substitutionsMap: MutableMap<Int, List<Int>> = mutableMapOf()
        for (lineId in lineIdsToReplace) {
            val item = order.items.firstOrNull { it.lineId == lineId } ?: continue

            val substitutionResponse = externalClient.getSubstitutionsForItem(
                lineId = item.lineId,
                productCode = item.productCode,
                qty = item.qty
            )

            substitutionsMap[lineId] = substitutionResponse.suggestedLineIds
        }

        val warehouseItemsById = loadReplacementItems(substitutionsMap)

        val shortageRequestItems = buildShortageRequestItems(order, substitutionsMap)

        // 3. /shortage/proactive-call — решение по каждому товару
        val shortageResponse = externalClient.getShortageDecisions(
            ShortageProactiveRequest(shortageRequestItems)
        )
        val decisionsByLineId: Map<Int, ShortageDecision> =
            shortageResponse.decisions.associateBy { it.lineId }

        // 4. Собираем финальный список items, подтягивая замену из склада по id
        val finalItems: List<OrderItemDto> = order.items.mapNotNull { item ->
            val decision = decisionsByLineId[item.lineId]

            when (decision?.action) {
                null, ShortageAction.KEEP -> item

                ShortageAction.DELETE -> null

                ShortageAction.REPLACE -> {
                    val replacementIds = substitutionsMap[item.lineId]
                    val replacementId = replacementIds?.firstOrNull()

                    if (replacementId != null) {
                        val replacement = warehouseItemsById[replacementId]
                            ?: warehouseItemRepository.findById(replacementId).orElse(null)?.also {
                                warehouseItemsById[replacementId] = it
                            }

                        if (replacement != null) {
                            val newQty = decision.replacementQty ?: item.qty

                            item.copy(
                                productCode = replacement.productCode,
                                name = replacement.name,
                                unit = replacement.unit,
                                qty = newQty
                            )
                        } else {
                            item
                        }
                    } else {
                        item
                    }
                }
            }
        }

        val finalOrder = order.copy(items = finalItems)

        // 5. Маппим в сущности и сохраняем только в БД
        val entity = mapToEntity(finalOrder, finalItems)
        orderRepository.save(entity)
    }

    private fun mapToEntity(order: ProductDto, finalItems: List<OrderItemDto>): OrderEntity {
        val orderEntity = OrderEntity(
            orderId = order.orderId,
            customerId = order.customerId,
            createdAt = order.createdAt,
            deliveryDate = order.deliveryDate,
            phone = order.customerContact.phone,
            email = order.customerContact.email,
            language = order.customerContact.language
        )

        val itemEntities = finalItems.map { itemDto ->
            OrderItemEntity(
                order = orderEntity,
                lineId = itemDto.lineId,
                productCode = itemDto.productCode,
                name = itemDto.name,
                qty = itemDto.qty.toBigDecimal(),
                unit = itemDto.unit
            )
        }

        orderEntity.items.addAll(itemEntities)
        return orderEntity
    }

    private fun buildShortageRequestItems(
        order: ProductDto,
        substitutionsMap: Map<Int, List<Int>>
    ): List<ShortageItemRequest> {
        return order.items.map { item ->
            val replacementId = substitutionsMap[item.lineId]?.firstOrNull()
            val replacementLine = replacementId?.let { id ->
                ShortageLine(
                    lineId = id,
                    qty = item.qty
                )
            }

            ShortageItemRequest(
                from = ShortageLine(
                    lineId = item.lineId,
                    qty = item.qty
                ),
                to = replacementLine
            )
        }
    }

    private fun loadReplacementItems(
        substitutionsMap: Map<Int, List<Int>>
    ): MutableMap<Int, WarehouseItem> {
        val replacementIds = substitutionsMap.values.flatten().distinct()
        if (replacementIds.isEmpty()) {
            return mutableMapOf()
        }

        val replacements = warehouseItemRepository.findAllById(replacementIds)
        val result = mutableMapOf<Int, WarehouseItem>()
        replacements.forEach { item -> result[item.lineId] = item }
        return result
    }
}
