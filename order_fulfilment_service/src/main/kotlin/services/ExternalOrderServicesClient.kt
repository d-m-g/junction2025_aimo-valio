package org.example.services

import org.example.dto.PredictOrderResponse
import org.example.dto.ProductDto
import org.example.dto.ShortageProactiveRequest
import org.example.dto.ShortageProactiveResponse
import org.example.dto.SubstitutionRequest
import org.example.dto.SubstitutionResponse
import org.springframework.stereotype.Component
import org.springframework.web.client.RestTemplate

@Component
class ExternalOrderServicesClient(
    private val restTemplate: RestTemplate
) {
    private val predictOrderUrl = "http://localhost:8081/predict/order"
    private val substitutionSuggestUrl = "http://localhost:8082/substitution/suggest"
    private val shortageUrl = "http://localhost:8083/shortage/proactive-call"

    fun getItemsToReplace(order: ProductDto): PredictOrderResponse {
        return restTemplate.postForObject(
            predictOrderUrl,
            order,
            PredictOrderResponse::class.java
        ) ?: PredictOrderResponse(emptyList())
    }

    fun getSubstitutionsForItem(
        lineId: Int,
        productCode: String,
        qty: Double
    ): SubstitutionResponse {
        val request = SubstitutionRequest(lineId, productCode, qty)

        return restTemplate.postForObject(
            substitutionSuggestUrl,
            request,
            SubstitutionResponse::class.java
        ) ?: SubstitutionResponse(lineId, emptyList())
    }

    fun getShortageDecisions(request: ShortageProactiveRequest): ShortageProactiveResponse {
        return restTemplate.postForObject(
            shortageUrl,
            request,
            ShortageProactiveResponse::class.java
        ) ?: ShortageProactiveResponse(emptyList())
    }
}
