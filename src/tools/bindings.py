"""Pipecat function-call wrappers. Import only from the voice pipeline."""

from __future__ import annotations

from src.tools.capacity import check_capacity
from src.tools.negotiation import end_party_call, update_negotiation_state
from src.tools.rate_card import get_rate_card
from src.tools.status import get_shipment_status


def make_voice_tools(session_id: str):
    """Build tool callables closed over this call's session_id."""
    from pipecat.services.llm_service import FunctionCallParams

    async def get_rate_card_tool(
        params: FunctionCallParams,
        origin: str,
        destination: str,
        vehicle_type: str,
    ):
        """Look up the rate card for a lane and vehicle.

        Args:
            origin: Origin city or code.
            destination: Destination city or code.
            vehicle_type: Vehicle type such as 14ft or 19ft.
        """
        await params.result_callback(get_rate_card(origin, destination, vehicle_type))

    async def check_capacity_tool(params: FunctionCallParams, location: str, date: str):
        """Check warehouse loading capacity for a location and date.

        Args:
            location: Warehouse city or code.
            date: Date as YYYY-MM-DD, today, or tomorrow.
        """
        await params.result_callback(check_capacity(location, date))

    async def get_shipment_status_tool(params: FunctionCallParams, shipment_id: str):
        """Get shipment status by id.

        Args:
            shipment_id: Shipment id such as MM-1001.
        """
        await params.result_callback(get_shipment_status(shipment_id))

    async def update_negotiation_state_tool(
        params: FunctionCallParams,
        origin: str | None = None,
        destination: str | None = None,
        vehicle_type: str | None = None,
        pickup_date: str | None = None,
        offered_rate: float | None = None,
        accepted_rate: float | None = None,
        shipment_id: str | None = None,
        blocker: str | None = None,
        escalate: bool | None = None,
    ):
        """Update shared negotiation state.

        Args:
            origin: Pickup city if newly known.
            destination: Drop city if newly known.
            vehicle_type: Vehicle if newly known.
            pickup_date: ISO date if newly known.
            offered_rate: Rate currently discussed.
            accepted_rate: Rate a party agreed.
            shipment_id: Shipment id if newly known.
            blocker: Optional blocker text.
            escalate: True to request a human.
        """
        await params.result_callback(
            update_negotiation_state(
                session_id,
                origin=origin,
                destination=destination,
                vehicle_type=vehicle_type,
                pickup_date=pickup_date,
                offered_rate=offered_rate,
                accepted_rate=accepted_rate,
                shipment_id=shipment_id,
                blocker=blocker,
                escalate=escalate,
            )
        )

    async def end_party_call_tool(
        params: FunctionCallParams,
        outcome: str,
        summary: str,
        rate: float | None = None,
        blocker: str | None = None,
    ):
        """Finish with the current party so the coordinator can call the next one.

        Args:
            outcome: accepted, rejected, blocked, or no_answer.
            summary: One sentence of what happened.
            rate: Rate discussed, if any.
            blocker: Why it failed, if it failed.
        """
        await params.result_callback(
            end_party_call(
                session_id,
                outcome=outcome,
                summary=summary,
                rate=rate,
                blocker=blocker,
            )
        )

    return [
        get_rate_card_tool,
        check_capacity_tool,
        get_shipment_status_tool,
        update_negotiation_state_tool,
        end_party_call_tool,
    ]
