package org.example

import org.springframework.boot.autoconfigure.SpringBootApplication
import org.springframework.boot.runApplication

@SpringBootApplication
class OrderFulfilmentServiceApplication

fun main(args: Array<String>) {
    runApplication<OrderFulfilmentServiceApplication>(*args)
}