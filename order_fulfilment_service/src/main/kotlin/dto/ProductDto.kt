package org.example.dto

import com.fasterxml.jackson.annotation.JsonProperty
import java.time.LocalDate
import java.time.OffsetDateTime

data class ProductDto(
    @JsonProperty("order_id")
    val orderId: String,

    @JsonProperty("customer_id")
    val customerId: String,

    @JsonProperty("created_at")
    val createdAt: OffsetDateTime,

    @JsonProperty("delivery_date")
    val deliveryDate: LocalDate,

    @JsonProperty("customer_contact")
    val customerContact: CustomerContactDto,

    @JsonProperty("items")
    val items: List<OrderItemDto>
)

data class CustomerContactDto(
    val phone: String? = null,
    val email: String? = null,
    val language: String? = null
)

data class OrderItemDto(
    @JsonProperty("line_id")
    val lineId: Int,

    @JsonProperty("product_code")
    val productCode: String,

    val name: String,

    val qty: Double,

    val unit: String
)
