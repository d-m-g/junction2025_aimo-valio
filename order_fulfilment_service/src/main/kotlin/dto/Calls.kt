package org.example.dto

data class ShortageProactiveRequest(
    val items: List<ShortageItemRequest>
)

data class ShortageItemRequest(
    val from: ShortageLine,
    val to: ShortageLine? = null
)

data class ShortageLine(
    val lineId: Int,
    val qty: Double
)

data class ShortageProactiveResponse(
    val decisions: List<ShortageDecision>
)

data class ShortageDecision(
    val lineId: Int,
    val action: ShortageAction,
    val replacementQty: Double? = null   // количество товара замены (если REPLACE)
)

enum class ShortageAction {
    KEEP,
    REPLACE,
    DELETE
}
