"""Pipecat function-call wrappers. Import only from the voice pipeline."""

from __future__ import annotations

from pipecat.services.llm_service import FunctionCallParams

from src.agent.state import get_store
from src.tools.capacity import check_availability
from src.tools.negotiation import end_party_call, update_negotiation_state
from src.tools.rate_card import lookup_price
from src.tools.status import get_record_status


def trace_tool(session_id: str, name: str) -> None:
    store = get_store()
    session = store.get(session_id)
    if session is None:
        return
    calls = list(session.extra.get("tool_calls") or [])
    calls.append(name)
    session.extra["tool_calls"] = calls
    store.put(session)


def make_voice_tools(session_id: str):
    """Build tool callables closed over this call's session_id."""

    async def lookup_price_tool(
        params: FunctionCallParams,
        origin: str,
        destination: str,
        item_type: str,
    ):
        """Look up min/typical/max price for a from/to pair and item.

        Args:
            origin: Origin place.
            destination: Destination place.
            item_type: half-day, full-day, or hourly.
        """
        trace_tool(session_id, "lookup_price")
        await params.result_callback(lookup_price(origin, destination, item_type))

    async def check_availability_tool(params: FunctionCallParams, location: str, date: str):
        """Check remaining slots at a location for a date.

        Args:
            location: Place name.
            date: Date as YYYY-MM-DD, today, or tomorrow.
        """
        trace_tool(session_id, "check_availability")
        await params.result_callback(check_availability(location, date))

    async def get_record_status_tool(params: FunctionCallParams, record_id: str):
        """Get a sample booking by id.

        Args:
            record_id: Booking id such as BK-1001.
        """
        trace_tool(session_id, "get_record_status")
        await params.result_callback(get_record_status(record_id))

    async def update_negotiation_state_tool(
        params: FunctionCallParams,
        origin: str | None = None,
        destination: str | None = None,
        item_type: str | None = None,
        slot_date: str | None = None,
        offered_rate: float | None = None,
        accepted_rate: float | None = None,
        record_id: str | None = None,
        blocker: str | None = None,
        escalate: bool | None = None,
    ):
        """Update shared negotiation state."""
        trace_tool(session_id, "update_negotiation_state")
        await params.result_callback(
            update_negotiation_state(
                session_id,
                origin=origin,
                destination=destination,
                item_type=item_type,
                slot_date=slot_date,
                offered_rate=offered_rate,
                accepted_rate=accepted_rate,
                record_id=record_id,
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
        trace_tool(session_id, "end_party_call")
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
        lookup_price_tool,
        check_availability_tool,
        get_record_status_tool,
        update_negotiation_state_tool,
        end_party_call_tool,
    ]
