package org.example.dto

data class ProcessedOrderItem(
    val lineId: Int,
    val productCode: String,
    val name: String,
    val qty: Double,
    val unit: String
)

data class ReplacementDescriptor(
    val productCode: String,
    val name: String,
    val unit: String,
    val image: String? = null
)

data class ShortageDecisionResponse(
    val lineId: Int,
    val action: ShortageAction,
    val replacements: List<ReplacementDescriptor> = emptyList()
)

data class OrderProcessingResponse(
    val orderId: String,
    val items: List<ProcessedOrderItem>,
    val shortages: List<ShortageDecisionResponse>
)

