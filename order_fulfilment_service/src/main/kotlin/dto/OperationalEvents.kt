package org.example.dto

/**
 * Request sent by warehouse pickers when a shortage is detected during picking.
 */
data class PickShortageEventRequest(
    val orderId: String,
    val lineId: Int,
    val productCode: String,
    val expectedQty: Double,
    val pickedQty: Double,
    val pickerId: String? = null,
    val comment: String? = null
)

/**
 * Request initiated by Communication Orchestrator or NLU to create a claim after delivery.
 */
data class CreateClaimRequest(
    val orderId: String,
    val customerId: String,
    val channel: String,
    val description: String,
    val attachmentIds: List<String> = emptyList()
)

/**
 * Generic stub response that explains what the endpoint will eventually perform.
 */
data class StubDescriptionResponse(
    val endpoint: String,
    val status: String = "NOT_IMPLEMENTED",
    val description: List<String>
)

data class PickShortageEventResponse(
    val orderId: String,
    val lineId: Int,
    val shortageQty: Double,
    val action: ShortageAction,
    val replacements: List<ReplacementCandidateDto>,
    val notifications: List<String> = emptyList()
)

data class ReplacementCandidateDto(
    val lineId: Int,
    val productCode: String,
    val name: String,
    val availableQty: Double,
    val unit: String
)
