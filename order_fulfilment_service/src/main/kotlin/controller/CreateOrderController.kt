package org.example.controller

import org.example.dto.ProductDto
import org.example.services.OrderService
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestBody
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RestController

@RestController
@RequestMapping("/api/orders")
class CreateOrderController(
    private val orderService: OrderService
) {

    @PostMapping
    fun createOrder(@RequestBody payload: ProductDto): ResponseEntity<Void> {
        orderService.saveOrder(payload)
        return ResponseEntity.accepted().build()
    }
}
