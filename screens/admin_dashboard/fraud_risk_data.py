import re
from datetime import datetime, timedelta

from core.auth import get_all_users
from core.database import get_all_orders, get_audit_logs


RULES = [
    "3+ cancellations in the last 7 days (+40)",
    "Cancellation rate >= 60% (+30)",
    "2+ cancelled orders in the last 24 hours (+20)",
    "3+ active orders with same contact number (+15)",
    "3+ active orders with same delivery address (+15)",
]


def _parse_dt(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


def _normalize_text(value):
    return (value or "").strip().lower()


def _time_ago(dt: datetime) -> str:
    delta = datetime.now() - dt
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return f"{seconds}s ago"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    return f"{days}d ago"


def _compute_daily_risk_series(orders, days=7):
    today = datetime.now().date()
    series = []

    for idx in range(days - 1, -1, -1):
        day = today - timedelta(days=idx)
        day_orders = []
        for order in orders:
            order_dt = _parse_dt(order.get("created_at") or order.get("placed_at"))
            if order_dt and order_dt.date() == day:
                day_orders.append(order)

        by_customer = {}
        for order in day_orders:
            customer_id = order.get("customer_id")
            status = _normalize_text(order.get("status"))
            if customer_id not in by_customer:
                by_customer[customer_id] = {"orders": 0, "cancelled": 0}
            by_customer[customer_id]["orders"] += 1
            if status == "cancelled":
                by_customer[customer_id]["cancelled"] += 1

        high = 0
        medium = 0
        low = 0
        cancelled_total = sum(1 for o in day_orders if _normalize_text(o.get("status")) == "cancelled")
        delivered_total = sum(1 for o in day_orders if _normalize_text(o.get("status")) == "delivered")

        for stats in by_customer.values():
            score = 0
            cancellation_rate = (stats["cancelled"] / stats["orders"] * 100.0) if stats["orders"] > 0 else 0.0
            if stats["cancelled"] >= 2:
                score += 40
            if stats["cancelled"] >= 2 and cancellation_rate >= 60:
                score += 30

            if score >= 80:
                high += 1
            elif score >= 50:
                medium += 1
            elif score >= 30:
                low += 1

        series.append(
            {
                "label": day.strftime("%a"),
                "high": high,
                "medium": medium,
                "low": low,
                "total": high + medium + low,
                "cancelled": cancelled_total,
                "delivered": delivered_total,
            }
        )

    return series


def _compute_risk_data():
    orders = get_all_orders()
    users = get_all_users()
    audit_logs = get_audit_logs(limit=5000)

    now = datetime.now()
    users_by_id = {u.get("id"): u for u in users if isinstance(u, dict)}

    admin_cancelled_order_ids = set()
    for log in audit_logs:
        if log.get("action") != "ORDER_STATUS_UPDATED":
            continue
        details = log.get("details", "")
        if "\u2192 cancelled" not in details and "-> cancelled" not in details.lower():
            continue
        match = re.search(r"Order #(\d+)", details)
        if not match:
            continue
        order_id = int(match.group(1))
        cancelling_uid = log.get("user_id")
        if cancelling_uid is None:
            continue
        cancelling_user = users_by_id.get(cancelling_uid, {})
        if cancelling_user.get("role", "customer") in {"admin", "owner"}:
            admin_cancelled_order_ids.add(order_id)

    by_customer = {}
    active_by_contact = {}
    active_by_address = {}

    for order in orders:
        if not isinstance(order, dict):
            continue

        customer_id = order.get("customer_id")
        status = _normalize_text(order.get("status"))
        order_dt = _parse_dt(order.get("created_at") or order.get("placed_at"))

        if customer_id not in by_customer:
            by_customer[customer_id] = {
                "orders": 0,
                "cancelled": 0,
                "cancelled_7d": 0,
                "cancelled_24h": 0,
                "active": 0,
                "latest_order": None,
            }

        bucket = by_customer[customer_id]
        bucket["orders"] += 1

        if order_dt and (bucket["latest_order"] is None or order_dt > bucket["latest_order"]):
            bucket["latest_order"] = order_dt

        is_cancelled = status == "cancelled"
        is_active_order = status in {"placed", "preparing", "out for delivery"}

        if is_cancelled and order.get("id") not in admin_cancelled_order_ids:
            bucket["cancelled"] += 1
            if order_dt and order_dt >= now - timedelta(days=7):
                bucket["cancelled_7d"] += 1
            if order_dt and order_dt >= now - timedelta(hours=24):
                bucket["cancelled_24h"] += 1

        if is_active_order:
            bucket["active"] += 1
            contact_key = _normalize_text(order.get("contact_number"))
            address_key = _normalize_text(order.get("delivery_address"))
            if contact_key:
                active_by_contact[contact_key] = active_by_contact.get(contact_key, 0) + 1
            if address_key:
                active_by_address[address_key] = active_by_address.get(address_key, 0) + 1

    entries = []
    for customer_id, stats in by_customer.items():
        if not customer_id:
            continue

        user = users_by_id.get(customer_id, {})
        score = 0
        reasons = []

        cancelled = stats["cancelled"]
        total_orders = stats["orders"]
        cancellation_rate = (cancelled / total_orders * 100.0) if total_orders > 0 else 0.0

        if stats["cancelled_7d"] >= 3:
            score += 40
            reasons.append(f"{stats['cancelled_7d']} cancellations in 7 days")

        if cancellation_rate >= 60 and cancelled >= 3:
            score += 30
            reasons.append(f"High cancellation rate ({cancellation_rate:.0f}%)")

        if stats["cancelled_24h"] >= 2:
            score += 20
            reasons.append(f"{stats['cancelled_24h']} cancellations in 24h")

        sample_contact = None
        sample_address = None
        for order in orders:
            if order.get("customer_id") == customer_id:
                contact_key = _normalize_text(order.get("contact_number"))
                address_key = _normalize_text(order.get("delivery_address"))
                if not sample_contact and contact_key:
                    sample_contact = contact_key
                if not sample_address and address_key:
                    sample_address = address_key
                if sample_contact and sample_address:
                    break

        if sample_contact and active_by_contact.get(sample_contact, 0) >= 3:
            score += 15
            reasons.append("Shared contact across multiple active orders")

        if sample_address and active_by_address.get(sample_address, 0) >= 3:
            score += 15
            reasons.append("Shared address across multiple active orders")

        if score <= 0:
            continue

        if score >= 80:
            level = "HIGH"
            level_color = "#B71C1C"
            badge_bg = "#FFEBEE"
        elif score >= 50:
            level = "MEDIUM"
            level_color = "#E65100"
            badge_bg = "#FFF3E0"
        else:
            level = "LOW"
            level_color = "#33691E"
            badge_bg = "#F1F8E9"

        entries.append(
            {
                "customer_id": customer_id,
                "name": user.get("full_name", f"User #{customer_id}"),
                "email": user.get("email", "N/A"),
                "is_active": bool(user.get("is_active", 0)),
                "score": score,
                "level": level,
                "level_color": level_color,
                "badge_bg": badge_bg,
                "reasons": reasons,
                "orders": total_orders,
                "cancelled": cancelled,
                "latest_order": stats["latest_order"].strftime("%b %d, %Y %I:%M %p") if stats["latest_order"] else "N/A",
            }
        )

    entries.sort(key=lambda entry: entry["score"], reverse=True)
    daily_series = _compute_daily_risk_series(orders, days=7)
    return {
        "entries": entries,
        "daily_series": daily_series,
        "all_orders": orders,
    }
