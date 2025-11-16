package org.example.controller

import org.example.dto.CreateClaimRequest
import org.example.dto.PickShortageEventRequest
import org.example.dto.PickShortageEventResponse
import org.example.dto.ShortageProactiveRequest
import org.example.dto.ShortageProactiveResponse
import org.example.dto.StubDescriptionResponse
import org.example.services.ShortageWorkflowService
import org.springframework.http.HttpStatus
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestBody
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RestController

@RestController
@RequestMapping("/api/orders")
class OrderEventsController(
    private val shortageWorkflowService: ShortageWorkflowService
) {

    /**
     * Triggered when a picker detects a shortage during picking.
     * Flags the order line, proposes replacements and notifies downstream services.
     */
    @PostMapping("/events/pick-shortage")
    fun registerPickShortageEvent(
        @RequestBody payload: PickShortageEventRequest
    ): ResponseEntity<PickShortageEventResponse> {
        val response = shortageWorkflowService.handlePickerShortage(payload)
        return ResponseEntity.ok(response)
    }

    /**
     * Local implementation of the shortage decision API that would normally be provided
     * by an external service. Produces KEEP / REPLACE / DELETE recommendations.
     */
    @PostMapping("/shortage/proactive-call")
    fun proactiveShortageDecisions(
        @RequestBody request: ShortageProactiveRequest
    ): ResponseEntity<ShortageProactiveResponse> {
        val response = shortageWorkflowService.decideShortages(request)
        return ResponseEntity.ok(response)
    }

    /**
     * Claim creation after delivery (invoked by Communication Orchestrator or NLU).
     * Still returns a stub payload describing the work to be implemented.
     */
    @PostMapping("/claims/create")
    fun createClaim(
        @RequestBody payload: CreateClaimRequest
    ): ResponseEntity<StubDescriptionResponse> {
        val description = listOf(
            "Persist the complaint context for order ${payload.orderId} submitted via ${payload.channel}.",
            "Request Multimodal Evidence Service to validate provided attachmentIds.",
            "Based on the evaluation, call Compensation and orchestrate follow-up back-office actions."
        )

        return ResponseEntity
            .status(HttpStatus.NOT_IMPLEMENTED)
            .body(
                StubDescriptionResponse(
                    endpoint = "/api/orders/claims/create",
                    description = description
                )
            )
    }
}
