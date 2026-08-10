"""Shared telecom tools available via import_tools."""

from __future__ import annotations

import random
from datetime import datetime
from typing import Optional

from rasa.calm_v2.tools.decorator import ToolContext, tool
from rasa.calm_v2.tools.result import ToolResult

from lib.database import (
    DEMO_CUSTOMER_ID,
    SPEED_THRESHOLD_MBPS,
    Database,
    get_customer_by_id,
    get_customer_by_name,
    month_to_billing_date,
    normalize_month,
    resolve_customer_id,
    resolve_username,
)


def _username(context: Optional[ToolContext]) -> str:
    if context is None:
        return resolve_username()
    return resolve_username(context.memory.get("username"))


def _customer_id(context: Optional[ToolContext]) -> str:
    if context is None:
        return resolve_customer_id()
    return resolve_customer_id(context.memory.get("customer_id"))


@tool(description="Load the demo customer profile into project memory.")
async def load_customer_profile(context: ToolContext = None) -> ToolResult:
    """Ensure username / customer_id / plan details are available."""
    username = _username(context)
    customer_id = _customer_id(context)
    db = Database()

    row = get_customer_by_name(db, username)
    if not row:
        row = get_customer_by_id(db, customer_id)
    if not row:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "customer_not_found",
                "username": username,
                "customer_id": customer_id,
            }
        )

    cid, first_name, last_name, name, email, address, plan_name = row
    if context is not None:
        context.memory.set("username", name)
        context.memory.set("customer_id", str(cid))
        context.memory.set("plan_name", plan_name)
        context.memory.set("email_address", email)
        context.memory.set("physical_address", address)

    return ToolResult(
        llm_response={
            "ok": True,
            "username": name,
            "first_name": first_name,
            "last_name": last_name,
            "customer_id": str(cid),
            "plan_name": plan_name,
            "email_address": email,
            "physical_address": address,
        }
    )


@tool(description="Summarize a customer's bill for a given month and compare to their average.")
async def get_bill_summary(bill_month: str, context: ToolContext = None) -> ToolResult:
    """Look up bill amount for a month and compare to the customer's average.

    Args:
        bill_month: Month name such as February or Feb.
    """
    customer_id = _customer_id(context)
    month = normalize_month(bill_month)
    bill_date = month_to_billing_date(bill_month)
    if not month or not bill_date:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "invalid_month",
                "hint": "Ask for a calendar month such as January or February.",
            }
        )

    db = Database()
    rows = db.run_query(
        "SELECT date, amount, source FROM billing WHERE customer_id = ? ORDER BY date",
        (customer_id,),
        one_record=False,
    )
    if not rows:
        return ToolResult(
            llm_response={"ok": False, "error": "no_bills", "customer_id": customer_id}
        )

    specific = [row for row in rows if row[0] == bill_date]
    if not specific:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "bill_not_found",
                "bill_month": month,
                "bill_date": bill_date,
            }
        )

    bill_amount = float(specific[0][1])
    source = specific[0][2]
    amounts = [float(row[1]) for row in rows]
    average_bill = sum(amounts) / len(amounts)
    difference = bill_amount - average_bill
    comparison = "higher" if difference > 0 else "lower" if difference < 0 else "equal"

    if context is not None:
        context.memory.set("bill_month", month)
        context.memory.set("bill_amount", bill_amount)
        context.memory.set("average_bill", round(average_bill, 2))
        context.memory.set("difference", round(abs(difference), 2))

    return ToolResult(
        llm_response={
            "ok": True,
            "bill_month": month,
            "bill_year": 2026,
            "bill_amount": bill_amount,
            "average_bill": round(average_bill, 2),
            "difference": round(abs(difference), 2),
            "comparison": comparison,
            "source": source,
            "currency": "USD",
        }
    )


@tool(description="List all billing line items for the current customer.")
async def list_bill_charges(context: ToolContext = None) -> ToolResult:
    """Return every billing row for the active customer."""
    customer_id = _customer_id(context)
    db = Database()
    rows = db.run_query(
        "SELECT date, amount, source FROM billing WHERE customer_id = ? ORDER BY date",
        (customer_id,),
        one_record=False,
    )
    charges = [
        {"date": date, "amount": float(amount), "source": source}
        for date, amount, source in rows or []
    ]
    return ToolResult(
        llm_response={
            "ok": True,
            "charges": charges,
            "charge_count": len(charges),
            "currency": "USD",
        }
    )


@tool(description="List routers registered to the current customer.")
async def list_routers(context: ToolContext = None) -> ToolResult:
    """List the customer's routers with model and status."""
    customer_id = _customer_id(context)
    db = Database()
    rows = db.run_query(
        """
        SELECT device_id, model, status, wifi_name
        FROM routers WHERE customer_id = ?
        """,
        (customer_id,),
        one_record=False,
    )
    routers = [
        {
            "device_id": device_id,
            "model": model,
            "status": status,
            "wifi_name": wifi_name,
        }
        for device_id, model, status, wifi_name in rows or []
    ]
    if context is not None:
        context.memory.set("routers_loaded", True)
    return ToolResult(
        llm_response={"ok": True, "routers": routers, "router_count": len(routers)}
    )


@tool(description="Run a network speed test and return download speed in Mbps.")
async def run_speed_test(context: ToolContext = None) -> ToolResult:
    """Simulate a download speed test for the active customer line."""
    override = None
    if context is not None:
        override = context.memory.get("network_speed_override")

    if override is not None:
        try:
            speed = float(override)
        except (TypeError, ValueError):
            speed = float(random.randint(10, 140))
    else:
        speed = float(random.randint(10, 140))

    speed = round(speed, 1)
    is_slow = speed < SPEED_THRESHOLD_MBPS

    if context is not None:
        context.memory.set("network_speed", speed)
        context.memory.set("speed_is_slow", is_slow)

    return ToolResult(
        llm_response={
            "ok": True,
            "download_mbps": speed,
            "threshold_mbps": SPEED_THRESHOLD_MBPS,
            "is_slow": is_slow,
            "message": (
                f"Your network download speed is {speed} Mbps."
                if is_slow
                else f"{speed} Mbps — that looks healthy."
            ),
        }
    )


@tool(description="Remotely factory-reset a customer router. This wipes Wi-Fi settings.")
async def reset_router(device_id: str, context: ToolContext = None) -> ToolResult:
    """Factory-reset a router by device id.

    Args:
        device_id: Router device id such as RTR-123-01.
    """
    customer_id = _customer_id(context)
    db = Database()
    row = db.run_query(
        """
        SELECT device_id, model, wifi_name
        FROM routers WHERE customer_id = ? AND device_id = ?
        """,
        (customer_id, device_id),
        one_record=True,
    )
    if not row:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "router_not_found",
                "device_id": device_id,
                "hint": "Ask the customer which router to reset from their registered devices.",
            }
        )

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    db.cursor.execute(
        """
        UPDATE routers
        SET status = 'resetting', last_reset_at = ?, wifi_name = NULL
        WHERE device_id = ? AND customer_id = ?
        """,
        (now, device_id, customer_id),
    )
    # Simulate completion of the remote reset
    db.cursor.execute(
        """
        UPDATE routers
        SET status = 'online', wifi_name = 'TelecomOfRasa-Setup'
        WHERE device_id = ? AND customer_id = ?
        """,
        (device_id, customer_id),
    )
    db.commit()

    device_id_val, model, _old_wifi = row
    if context is not None:
        context.memory.set("router_reset", True)
        context.memory.set("selected_device_id", device_id_val)
        context.memory.set("selected_device_label", model)

    return ToolResult(
        llm_response={
            "ok": True,
            "device_id": device_id_val,
            "model": model,
            "status": "online",
            "wifi_name": "TelecomOfRasa-Setup",
            "message": (
                "Factory reset complete. The Wi-Fi name was restored to "
                "TelecomOfRasa-Setup. The customer may need to reconnect devices."
            ),
        }
    )


@tool(description="Create a human handoff ticket for a live support agent.")
async def create_support_ticket(reason: str, context: ToolContext = None) -> ToolResult:
    """Create a handoff ticket.

    Args:
        reason: Why the customer wants a human agent.
    """
    ticket_id = f"TEL-{datetime.utcnow().strftime('%H%M%S')}"
    if context is not None:
        context.memory.set("handoff_created", True)
        context.memory.set("handoff_ticket_id", ticket_id)
    return ToolResult(
        llm_response={
            "ok": True,
            "ticket_id": ticket_id,
            "reason": reason,
            "eta_minutes": 5,
            "customer_id": _customer_id(context) or DEMO_CUSTOMER_ID,
        }
    )
