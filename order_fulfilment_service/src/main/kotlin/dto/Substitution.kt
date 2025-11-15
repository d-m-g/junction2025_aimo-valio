package org.example.dto

data class SubstitutionRequest(
    val lineId: Int,
    val productCode: String,
    val qty: Double
)

data class SubstitutionResponse(
    val lineId: Int,
    val suggestedLineIds: List<Int>  // только id товаров-замен
)
