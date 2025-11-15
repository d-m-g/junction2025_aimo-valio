package org.example.dto

import jakarta.persistence.*
import java.math.BigDecimal

@Entity
@Table(name = "warehouse_items")
data class WarehouseItem(
    @Id
    @Column(name = "line_id")
    val lineId: Int,

    @Column(name = "product_code", nullable = false)
    val productCode: String,

    @Column(name = "name", nullable = false)
    val name: String,

    @Column(name = "qty", nullable = false)
    val qty: BigDecimal,

    @Column(name = "unit", nullable = false)
    val unit: String
)
