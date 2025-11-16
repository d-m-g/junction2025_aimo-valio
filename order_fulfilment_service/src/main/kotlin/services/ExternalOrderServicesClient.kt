package org.example.services

import org.example.config.ExternalServicesProperties
import org.example.dto.PredictOrderResponse
import org.example.dto.ProductDto
import org.example.dto.ShortageAction
import org.example.dto.ShortageDecision
import org.example.dto.ShortageProactiveRequest
import org.example.dto.ShortageProactiveResponse
import org.example.dto.SubstitutionRequest
import org.example.dto.SubstitutionResponse
import org.slf4j.LoggerFactory
import org.springframework.stereotype.Component
import org.springframework.web.client.RestClientException
import org.springframework.web.client.RestTemplate

@Component
class ExternalOrderServicesClient(
    private val restTemplate: RestTemplate,
    private val externalServicesProperties: ExternalServicesProperties
) {
    private val logger = LoggerFactory.getLogger(ExternalOrderServicesClient::class.java)

    fun getItemsToReplace(order: ProductDto): PredictOrderResponse {
        return try {
            restTemplate.postForObject(
                externalServicesProperties.predictOrderUrl,
                order,
                PredictOrderResponse::class.java
            ) ?: PredictOrderResponse(emptyList())
        } catch (ex: RestClientException) {
            logger.warn(
                "Predict service unavailable ({}). Defaulting to empty replacements.",
                ex.message
            )
            PredictOrderResponse(emptyList())
        }
    }

    fun getSubstitutionsForItem(
        lineId: Int,
        productCode: String,
        qty: Double,
        name: String?
    ): SubstitutionResponse {
        val request = SubstitutionRequest(lineId, productCode, qty, name)

        return try {
            restTemplate.postForObject(
                externalServicesProperties.substitutionSuggestUrl,
                request,
                SubstitutionResponse::class.java
            ) ?: SubstitutionResponse(lineId, emptyList())
        } catch (ex: RestClientException) {
            logger.warn(
                "Substitution service unavailable ({}). Defaulting to empty suggestions for line {}.",
                ex.message,
                lineId
            )
            SubstitutionResponse(lineId, emptyList())
        }
    }

    fun getShortageDecisions(request: ShortageProactiveRequest): ShortageProactiveResponse {
        return try {
            restTemplate.postForObject(
                externalServicesProperties.shortageUrl,
                request,
                ShortageProactiveResponse::class.java
            ) ?: ShortageProactiveResponse(emptyList())
        } catch (ex: RestClientException) {
            logger.warn(
                "Shortage service unavailable ({}). Defaulting to KEEP decisions for {} items.",
                ex.message,
                request.items.size
            )
            val fallback = request.items.map { item ->
                ShortageDecision(lineId = item.from.lineId, action = ShortageAction.KEEP)
            }
            ShortageProactiveResponse(fallback)
        }
    }
}
