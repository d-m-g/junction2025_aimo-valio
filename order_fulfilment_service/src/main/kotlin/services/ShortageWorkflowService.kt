package org.example.services

import org.example.dto.PickShortageEventRequest
import org.example.dto.PickShortageEventResponse
import org.example.dto.ReplacementCandidateDto
import org.example.dto.ShortageAction
import org.example.dto.ShortageDecision
import org.example.dto.ShortageProactiveRequest
import org.example.dto.ShortageProactiveResponse
import org.example.dto.SubstitutionResponse
import org.example.dto.WarehouseItem
import org.example.repositories.OrderRepository
import org.example.repositories.WarehouseItemRepository
import org.slf4j.LoggerFactory
import org.springframework.http.HttpStatus
import org.springframework.stereotype.Service
import org.springframework.transaction.annotation.Transactional
import org.springframework.web.server.ResponseStatusException
import kotlin.math.min

@Service
class ShortageWorkflowService(
    private val orderRepository: OrderRepository,
    private val warehouseItemRepository: WarehouseItemRepository,
    private val externalServicesClient: ExternalOrderServicesClient
) {
    private val logger = LoggerFactory.getLogger(ShortageWorkflowService::class.java)

    @Transactional
    fun handlePickerShortage(event: PickShortageEventRequest): PickShortageEventResponse {
        val order = orderRepository.findById(event.orderId)
            .orElseThrow {
                ResponseStatusException(
                    HttpStatus.NOT_FOUND,
                    "Order ${event.orderId} not found"
                )
            }

        val orderItem = order.items.firstOrNull { it.lineId == event.lineId }
            ?: throw ResponseStatusException(
                HttpStatus.NOT_FOUND,
                "Order ${event.orderId} does not contain line ${event.lineId}"
            )

        val shortageQty = (event.expectedQty - event.pickedQty).coerceAtLeast(0.0)

        if (!orderItem.shortPick) {
            orderItem.shortPick = true
        }

        val substitutionResponse = if (shortageQty > 0.0) {
            externalServicesClient.getSubstitutionsForItem(
                lineId = event.lineId,
                productCode = event.productCode,
                qty = shortageQty,
                name = null
            )
        } else {
            SubstitutionResponse(event.lineId, emptyList())
        }

        val replacements = loadReplacementOptions(substitutionResponse.suggestedLineIds)
        val action = when {
            shortageQty <= 0.0 -> ShortageAction.KEEP
            replacements.isNotEmpty() -> ShortageAction.REPLACE
            else -> ShortageAction.DELETE
        }

        val notifications = buildNotifications(event, shortageQty, action, replacements)

        logger.info(
            "Shortage registered for order {} line {} (action={}, replacements={})",
            event.orderId,
            event.lineId,
            action,
            replacements.size
        )

        return PickShortageEventResponse(
            orderId = event.orderId,
            lineId = event.lineId,
            shortageQty = shortageQty,
            action = action,
            replacements = replacements,
            notifications = notifications
        )
    }

    fun decideShortages(request: ShortageProactiveRequest): ShortageProactiveResponse {
        val decisions = request.items.map { item ->
            val replacementItem = item.to?.lineId?.let { findWarehouseItem(it) }
            val requestedQty = item.to?.qty ?: item.from.qty

            when {
                replacementItem != null -> {
                    val available = replacementItem.qty.toDouble()
                    val replacementQty = min(available, requestedQty).coerceAtLeast(0.0)
                    ShortageDecision(
                        lineId = item.from.lineId,
                        action = ShortageAction.REPLACE,
                        replacementQty = replacementQty
                    )
                }

                item.from.qty <= 1.0 -> {
                    ShortageDecision(item.from.lineId, ShortageAction.KEEP)
                }

                else -> {
                    ShortageDecision(item.from.lineId, ShortageAction.DELETE)
                }
            }
        }

        logger.info("Calculated {} shortage decision(s)", decisions.size)
        return ShortageProactiveResponse(decisions)
    }

    private fun loadReplacementOptions(ids: List<Int>): List<ReplacementCandidateDto> {
        if (ids.isEmpty()) {
            return emptyList()
        }

        val replacementsById = warehouseItemRepository.findAllById(ids)
            .associateBy { it.lineId }

        return ids.distinct().mapNotNull { replacementsById[it] }.map { toReplacementDto(it) }
    }

    private fun findWarehouseItem(lineId: Int): WarehouseItem? =
        warehouseItemRepository.findById(lineId).orElse(null)

    private fun toReplacementDto(item: WarehouseItem): ReplacementCandidateDto =
        ReplacementCandidateDto(
            lineId = item.lineId,
            productCode = item.productCode,
            name = item.name,
            availableQty = item.qty.toDouble(),
            unit = item.unit
        )

    private fun buildNotifications(
        event: PickShortageEventRequest,
        shortageQty: Double,
        action: ShortageAction,
        replacements: List<ReplacementCandidateDto>
    ): List<String> {
        val humanReadableQty = String.format("%.2f", shortageQty)
        val messages = mutableListOf(
            "Order ${event.orderId} line ${event.lineId} flagged as short_pick (shortage $humanReadableQty units)."
        )

        event.comment?.takeIf { it.isNotBlank() }?.let { comment ->
            messages += "Picker note: $comment"
        }

        when (action) {
            ShortageAction.REPLACE ->
                messages += "Prepared ${replacements.size} replacement option(s) for Communication Orchestrator."

            ShortageAction.DELETE ->
                messages += "No replacements available; customer approval required to remove the item."

            ShortageAction.KEEP ->
                messages += "Shortage resolved during picking; no customer action required."
        }
        return messages
    }
}

