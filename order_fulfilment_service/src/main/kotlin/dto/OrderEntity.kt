package org.example.dto

import jakarta.persistence.CascadeType
import jakarta.persistence.Column
import jakarta.persistence.Entity
import jakarta.persistence.FetchType
import jakarta.persistence.GeneratedValue
import jakarta.persistence.GenerationType
import jakarta.persistence.Id
import jakarta.persistence.JoinColumn
import jakarta.persistence.ManyToOne
import jakarta.persistence.OneToMany
import jakarta.persistence.Table
import java.math.BigDecimal
import java.time.LocalDate
import java.time.OffsetDateTime

@Entity
@Table(name = "orders")
class OrderEntity(

    @Id
    @Column(name = "order_id")
    var orderId: String = "",

    @Column(name = "customer_id", nullable = false)
    var customerId: String = "",

    @Column(name = "created_at", nullable = false)
    var createdAt: OffsetDateTime = OffsetDateTime.now(),

    @Column(name = "delivery_date", nullable = false)
    var deliveryDate: LocalDate = LocalDate.now(),

    @Column(name = "phone")
    var phone: String? = null,

    @Column(name = "email")
    var email: String? = null,

    @Column(name = "language")
    var language: String? = null,

    @OneToMany(
        mappedBy = "order",
        cascade = [CascadeType.ALL],
        orphanRemoval = true,
        fetch = FetchType.LAZY
    )
    var items: MutableList<OrderItemEntity> = mutableListOf()
)

@Entity
@Table(name = "order_items")
class OrderItemEntity(

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    var id: Long? = null,

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "order_id", nullable = false)
    var order: OrderEntity? = null,

    @Column(name = "line_id", nullable = false)
    var lineId: Int = 0,

    @Column(name = "product_code", nullable = false)
    var productCode: String = "",

    @Column(name = "name", nullable = false)
    var name: String = "",

    @Column(name = "qty", nullable = false)
    var qty: BigDecimal = BigDecimal.ZERO,

    @Column(name = "unit", nullable = false)
    var unit: String = "",

    @Column(name = "short_pick", nullable = false)
    var shortPick: Boolean = false
)
