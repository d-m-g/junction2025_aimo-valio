package org.example.controller

import org.example.dto.ProductDto
import org.example.dto.OrderProcessingResponse
import org.example.services.OrderService
import org.slf4j.LoggerFactory
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestBody
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RequestMethod
import org.springframework.web.bind.annotation.RestController

import org.springframework.web.bind.annotation.CrossOrigin

@RestController
@RequestMapping("/api/orders")
@CrossOrigin(
    origins = ["http://localhost:1234", "http://127.0.0.1:1234"],
    maxAge = 3600,
    allowedHeaders = ["*"],
    methods = [RequestMethod.GET, RequestMethod.POST, RequestMethod.PUT, RequestMethod.PATCH, RequestMethod.DELETE, RequestMethod.OPTIONS]
)
class CreateOrderController(
    private val orderService: OrderService
) {
    private val logger = LoggerFactory.getLogger(CreateOrderController::class.java)

    @PostMapping
    fun createOrder(@RequestBody payload: ProductDto): ResponseEntity<OrderProcessingResponse> {
        logger.info(
            "Received create order request: orderId={}, customerId={}, items={}",
            payload.orderId,
            payload.customerId,
            payload.items.size
        )
        val response = orderService.saveOrder(payload)
        logger.info("Order {} processed successfully", payload.orderId)
        return ResponseEntity.ok(response)
    }
}
