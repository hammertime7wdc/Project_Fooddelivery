import flet as ft
from datetime import datetime

from core.auth import disable_user, enable_user
from core.database import get_audit_logs
from utils import (
    ACCENT_DARK,
    ACCENT_PRIMARY,
    CREAM,
    FIELD_BG,
    FIELD_BORDER,
    TEXT_DARK,
    show_snackbar,
)
from .fraud_risk_data import RULES, _compute_risk_data, _normalize_text, _time_ago


def _build_kpi_card(title: str, value_ref: ft.Text, tone: str = "default"):
    tone_map = {
        "default": {"bar": ACCENT_PRIMARY, "bg": CREAM},
        "high": {"bar": "#B71C1C", "bg": CREAM},
        "medium": {"bar": "#E65100", "bg": CREAM},
        "low": {"bar": "#33691E", "bg": CREAM},
    }
    colors = tone_map.get(tone, tone_map["default"])
    sparkline = ft.Row(spacing=3, alignment=ft.MainAxisAlignment.START)

    return ft.Container(
        content=ft.Column(
            [
                ft.Text(title, size=11, color="#666666", weight=ft.FontWeight.W_500),
                value_ref,
                sparkline,
                ft.Container(height=3, bgcolor=colors["bar"], border_radius=8, width=54),
            ],
            spacing=6,
        ),
        bgcolor=colors["bg"],
        border=ft.border.all(1, FIELD_BORDER),
        border_radius=10,
        padding=12,
        width=180,
        data={"sparkline": sparkline, "bar_color": colors["bar"]},
    )


def _set_sparkline(card: ft.Container, values):
    sparkline = card.data.get("sparkline") if isinstance(card.data, dict) else None
    bar_color = card.data.get("bar_color") if isinstance(card.data, dict) else ACCENT_PRIMARY
    if sparkline is None:
        return

    max_value = max(values, default=0)
    max_value = max(max_value, 1)
    sparkline.controls = [
        ft.Container(
            width=8,
            height=max(4, int((value / max_value) * 18)),
            bgcolor=bar_color,
            border_radius=3,
        )
        for value in values
    ]


def create_fraud_risk_tab(page: ft.Page, current_user: dict, on_user_change=None):
    threshold_options = {
        "Low (30+)": 30,
        "Medium (50+)": 50,
        "High (80+)": 80,
    }
    threshold_state = {"label": "Medium (50+)"}
    rules_state = {"visible": False}

    summary_text = ft.Text(size=12, color="#555555")
    guide_text = ft.Text(size=12, color="#666666")

    total_risk_text = ft.Text("0", size=28, color=TEXT_DARK, weight=ft.FontWeight.BOLD)
    high_risk_text = ft.Text("0", size=28, color="#B71C1C", weight=ft.FontWeight.BOLD)
    medium_risk_text = ft.Text("0", size=28, color="#E65100", weight=ft.FontWeight.BOLD)
    low_risk_text = ft.Text("0", size=28, color="#33691E", weight=ft.FontWeight.BOLD)
    cancel_rate_text = ft.Text("0.00%", size=28, color=ACCENT_DARK, weight=ft.FontWeight.BOLD)

    approved_volume_chart = ft.Row(spacing=7, alignment=ft.MainAxisAlignment.SPACE_AROUND)
    cancelled_volume_chart = ft.Row(spacing=7, alignment=ft.MainAxisAlignment.SPACE_AROUND)

    processed_ring = ft.ProgressRing(width=160, height=160, value=0.0, color=ACCENT_DARK, stroke_width=16, bgcolor="#DAD0C0")
    processed_rate_text = ft.Text("0.0%", size=24, color=TEXT_DARK, weight=ft.FontWeight.BOLD)
    completed_text = ft.Text("Completed: 0", size=12, color="#666666")
    progress_text = ft.Text("In Progress: 0", size=12, color="#666666")

    suspicious_list = ft.ListView(spacing=8, padding=0, auto_scroll=False, expand=True)
    live_alerts_list = ft.ListView(spacing=8, padding=0, auto_scroll=False, expand=True)

    total_kpi = _build_kpi_card("Total Flagged", total_risk_text)
    high_kpi = _build_kpi_card("High Risk", high_risk_text, tone="high")
    medium_kpi = _build_kpi_card("Medium Risk", medium_risk_text, tone="medium")
    low_kpi = _build_kpi_card("Low Risk", low_risk_text, tone="low")

    def _metric_pill(value_ref: ft.Text, label: str):
        return ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        content=value_ref,
                        bgcolor=CREAM,
                        border=ft.border.all(1, FIELD_BORDER),
                        border_radius=8,
                        padding=ft.padding.symmetric(horizontal=12, vertical=8),
                        width=120,
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(
                        content=ft.Text(label, size=12, color=TEXT_DARK, weight=ft.FontWeight.W_500),
                        bgcolor=CREAM,
                        border_radius=16,
                        border=ft.border.all(1, FIELD_BORDER),
                        padding=ft.padding.symmetric(horizontal=14, vertical=10),
                        expand=True,
                    ),
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=6,
            border=ft.border.all(1, FIELD_BORDER),
            border_radius=12,
            bgcolor="#FFFFFF",
        )

    def _build_bar_chart(row_control: ft.Row, values, labels, color):
        max_value = max(values, default=0)
        max_value = max(max_value, 1)
        row_control.controls = [
            ft.Column(
                [
                    ft.Text(str(value), size=10, color="#666666", text_align=ft.TextAlign.CENTER),
                    ft.Container(
                        width=22,
                        height=max(8, int((value / max_value) * 130)),
                        bgcolor=color,
                        border_radius=ft.border_radius.only(top_left=6, top_right=6, bottom_left=3, bottom_right=3),
                    ),
                    ft.Text(label, size=10, color=TEXT_DARK, text_align=ft.TextAlign.CENTER),
                ],
                spacing=4,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.END,
            )
            for value, label in zip(values, labels)
        ]

    threshold_dropdown = ft.Dropdown(
        width=170,
        value=threshold_state["label"],
        options=[
            ft.dropdown.Option(
                key=label,
                text=label,
                content=ft.Text(label, color="#000000", size=13, weight=ft.FontWeight.W_500),
            )
            for label in threshold_options.keys()
        ],
        bgcolor=FIELD_BG,
        fill_color=FIELD_BG,
        filled=True,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        border_radius=8,
        text_style=ft.TextStyle(color=TEXT_DARK, size=12, weight=ft.FontWeight.W_500),
    )

    def _block_user(user_id):
        disable_user(user_id, current_user["user"]["id"])
        show_snackbar(page, f"User #{user_id} blocked.")
        refresh_data()
        if on_user_change:
            on_user_change()

    def _unblock_user(user_id):
        enable_user(user_id, current_user["user"]["id"])
        show_snackbar(page, f"User #{user_id} unblocked.")
        refresh_data()
        if on_user_change:
            on_user_change()

    def render():
        risk_payload = _compute_risk_data()
        risk_entries = risk_payload["entries"]
        daily_series = risk_payload["daily_series"]
        all_orders = risk_payload["all_orders"]
        threshold_value = threshold_options[threshold_state["label"]]
        filtered = [entry for entry in risk_entries if entry["score"] >= threshold_value]

        high_count = sum(1 for entry in risk_entries if entry["level"] == "HIGH")
        medium_count = sum(1 for entry in risk_entries if entry["level"] == "MEDIUM")
        low_count = sum(1 for entry in risk_entries if entry["level"] == "LOW")
        total_risk_text.value = str(len(risk_entries))
        high_risk_text.value = str(high_count)
        medium_risk_text.value = str(medium_count)
        low_risk_text.value = str(low_count)

        # Use ALL orders for system-wide stats (not just flagged accounts)
        all_cancelled = sum(1 for o in all_orders if _normalize_text(o.get("status")) == "cancelled")
        all_delivered = sum(1 for o in all_orders if _normalize_text(o.get("status")) == "delivered")
        all_in_progress = sum(1 for o in all_orders if _normalize_text(o.get("status")) in {"placed", "preparing", "out for delivery"})
        total_all = len(all_orders)
        cancel_rate = (all_cancelled / total_all * 100.0) if total_all > 0 else 0.0
        cancel_rate_text.value = f"{cancel_rate:.2f}%"

        _set_sparkline(total_kpi, [day["total"] for day in daily_series])
        _set_sparkline(high_kpi, [day["high"] for day in daily_series])
        _set_sparkline(medium_kpi, [day["medium"] for day in daily_series])
        _set_sparkline(low_kpi, [day["low"] for day in daily_series])

        labels = [day["label"] for day in daily_series]
        _build_bar_chart(approved_volume_chart, [day["delivered"] for day in daily_series], labels, ACCENT_DARK)
        _build_bar_chart(cancelled_volume_chart, [day["cancelled"] for day in daily_series], labels, ACCENT_PRIMARY)

        delivered_ratio = (all_delivered / total_all) if total_all > 0 else 0.0
        processed_ring.value = delivered_ratio
        processed_rate_text.value = f"{delivered_ratio * 100:.1f}%"
        completed_text.value = f"Delivered: {all_delivered} of {total_all}"
        progress_text.value = f"In Progress: {all_in_progress} | Cancelled: {all_cancelled}"

        summary_text.value = (
            f"Detected: {len(risk_entries)} risk account(s) • "
            f"Showing: {len(filtered)} account(s) for {threshold_state['label']}"
        )
        guide_text.value = (
            "Guide — Customer: account identity • Severity: risk level + score • "
            "Action: block/unblock account based on review"
        )

        suspicious_list.controls.clear()
        if not filtered:
            suspicious_list.controls.append(ft.Text("No risky accounts for this threshold.", size=12, color="#666666"))
        else:
            for entry in filtered[:12]:
                cancellation_rate = (entry["cancelled"] / entry["orders"] * 100.0) if entry["orders"] > 0 else 0.0
                action_btn = (
                    ft.OutlinedButton(
                        "Block",
                        icon=ft.Icons.BLOCK,
                        style=ft.ButtonStyle(color="#B71C1C", side=ft.BorderSide(1, "#B71C1C")),
                        on_click=lambda e, uid=entry["customer_id"]: _block_user(uid),
                    )
                    if entry["is_active"]
                    else ft.ElevatedButton(
                        "Unblock",
                        icon=ft.Icons.LOCK_OPEN,
                        bgcolor=ACCENT_DARK,
                        color=CREAM,
                        on_click=lambda e, uid=entry["customer_id"]: _unblock_user(uid),
                    )
                )

                suspicious_list.controls.append(
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text(entry["name"], size=13, color=TEXT_DARK, weight=ft.FontWeight.BOLD),
                                        ft.Text(entry["email"], size=11, color="#666666"),
                                        ft.Text(
                                            f"Cancelled: {entry['cancelled']} of {entry['orders']} ({cancellation_rate:.1f}%)",
                                            size=11,
                                            color="#666666",
                                        ),
                                            ft.Text(
                                                f"Last order: {entry['latest_order']}",
                                            size=10,
                                            color="#AAAAAA",
                                        ),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                                ft.Container(
                                    content=ft.Text(f"{entry['level']} • {entry['score']}", size=10, color=entry["level_color"], weight=ft.FontWeight.BOLD),
                                    bgcolor=entry["badge_bg"],
                                    border_radius=12,
                                    padding=ft.padding.symmetric(horizontal=8, vertical=6),
                                ),
                                action_btn,
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        bgcolor="#FFFFFF",
                        border=ft.border.all(1, FIELD_BORDER),
                        border_radius=8,
                        padding=10,
                    )
                )

        live_alerts_list.controls.clear()
        logs = get_audit_logs(limit=20)
        relevant_logs = [
            log for log in logs
            if str(log.get("action", "")).upper() in {"ACCOUNT_LOCKED", "USER_DISABLED", "USER_ENABLED", "ORDER_STATUS_UPDATED"}
        ]
        if not relevant_logs:
            live_alerts_list.controls.append(ft.Text("No live alerts available.", size=12, color="#666666"))
        else:
            for log in relevant_logs[:8]:
                action = log.get("action", "N/A")
                details = log.get("details", "")
                raw_ts = log.get("timestamp", "")
                try:
                    ts_dt = datetime.fromisoformat(raw_ts) if raw_ts else None
                    ts_display = ts_dt.strftime("%b %d, %Y  %I:%M %p") if ts_dt else "Unknown time"
                    ts_ago = _time_ago(ts_dt) if ts_dt else ""
                except Exception:
                    ts_display = raw_ts
                    ts_ago = ""
                live_alerts_list.controls.append(
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Text(action.replace("_", " ").title(), size=12, color=TEXT_DARK, weight=ft.FontWeight.BOLD, expand=True),
                                        ft.Text(ts_ago, size=10, color="#888888"),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                                ft.Text(details, size=11, color="#666666"),
                                ft.Text(ts_display, size=10, color="#AAAAAA"),
                            ],
                            spacing=2,
                        ),
                        bgcolor="#FFFFFF",
                        border=ft.border.all(1, FIELD_BORDER),
                        border_radius=8,
                        padding=10,
                    )
                )

    def refresh_data(e=None):
        render()
        page.update()

    def on_threshold_change(e):
        threshold_state["label"] = e.control.value or "Medium (50+)"
        refresh_data()

    def toggle_rules(e):
        rules_state["visible"] = not rules_state["visible"]
        rules_section.visible = rules_state["visible"]
        help_button.icon = ft.Icons.QUESTION_MARK if rules_state["visible"] else ft.Icons.HELP_OUTLINE_ROUNDED
        page.update()

    threshold_dropdown.on_change = on_threshold_change

    refresh_button = ft.ElevatedButton(
        "Refresh",
        icon=ft.Icons.REFRESH,
        bgcolor=ACCENT_PRIMARY,
        color=CREAM,
        on_click=refresh_data,
    )

    help_button = ft.IconButton(
        icon=ft.Icons.HELP_OUTLINE_ROUNDED,
        icon_color=ACCENT_DARK,
        tooltip="Show / hide flag rules",
        on_click=toggle_rules,
    )

    rules_section = ft.Container(
        content=ft.Column(
            [
                ft.Text("Flag Rules", size=15, color=TEXT_DARK, weight=ft.FontWeight.BOLD),
                *[ft.Text(f"• {rule}", size=12, color="#555555") for rule in RULES],
            ],
            spacing=6,
        ),
        bgcolor=CREAM,
        border=ft.border.all(1, FIELD_BORDER),
        border_radius=10,
        padding=12,
        visible=rules_state["visible"],
    )

    refresh_data()

    _fraud_content = ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.SECURITY, color=CREAM, size=22),
                            ft.Column(
                                [
                                    ft.Text("Fraud Risk Monitoring", size=18, weight=ft.FontWeight.BOLD, color=CREAM),
                                    ft.Text("Monitor suspicious activity and enforce account actions.", size=11, color="#F4EEE2"),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            threshold_dropdown,
                            refresh_button,
                            help_button,
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    bgcolor=ACCENT_PRIMARY,
                    padding=12,
                    border_radius=10,
                ),
                summary_text,
                ft.Container(
                    content=guide_text,
                    bgcolor=FIELD_BG,
                    border=ft.border.all(1, FIELD_BORDER),
                    border_radius=8,
                    padding=10,
                ),
                ft.ResponsiveRow(
                    [
                        ft.Container(
                            content=ft.Column(
                                [
                                    _metric_pill(total_risk_text, "Total Flagged"),
                                    _metric_pill(high_risk_text, "High Risk Accounts"),
                                    _metric_pill(medium_risk_text, "Medium Risk Accounts"),
                                    _metric_pill(low_risk_text, "Low Risk Accounts"),
                                    ft.Container(
                                        content=ft.Column(
                                            [
                                                cancel_rate_text,
                                                ft.Text("Chargebacks / Cancellation Rate", size=12, color="#666666"),
                                                total_kpi,
                                            ],
                                            spacing=8,
                                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                        ),
                                        bgcolor="#FFFFFF",
                                        border=ft.border.all(1, FIELD_BORDER),
                                        border_radius=12,
                                        padding=12,
                                    ),
                                    rules_section,
                                ],
                                spacing=10,
                            ),
                            col={"xs": 12, "md": 3},
                        ),
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.ResponsiveRow(
                                        [
                                            ft.Container(
                                                content=ft.Column(
                                                    [
                                                        ft.Text("Delivered Orders", size=16, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                                                        ft.Text("Daily count of successfully delivered orders (all customers).", size=11, color="#666666"),
                                                        ft.Container(
                                                            content=approved_volume_chart,
                                                            bgcolor=CREAM,
                                                            border=ft.border.all(1, FIELD_BORDER),
                                                            border_radius=10,
                                                            padding=12,
                                                            height=210,
                                                            alignment=ft.alignment.bottom_center,
                                                        ),
                                                    ],
                                                    spacing=8,
                                                ),
                                                col={"xs": 12, "md": 6},
                                            ),
                                            ft.Container(
                                                content=ft.Column(
                                                    [
                                                        ft.Text("Cancellations", size=16, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                                                        ft.Text("Daily cancelled orders across all customers.", size=11, color="#666666"),
                                                        ft.Container(
                                                            content=cancelled_volume_chart,
                                                            bgcolor=CREAM,
                                                            border=ft.border.all(1, FIELD_BORDER),
                                                            border_radius=10,
                                                            padding=12,
                                                            height=210,
                                                            alignment=ft.alignment.bottom_center,
                                                        ),
                                                    ],
                                                    spacing=8,
                                                ),
                                                col={"xs": 12, "md": 6},
                                            ),
                                        ],
                                        spacing=10,
                                    ),
                                    ft.ResponsiveRow(
                                        [
                                            ft.Container(
                                                content=ft.Column(
                                                    [
                                                        ft.Text("Processed", size=16, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                                                        ft.Text("Delivered orders ÷ all orders placed (system-wide).", size=11, color="#666666"),
                                                        ft.Container(
                                                            content=ft.Column(
                                                                [
                                                                    processed_ring,
                                                                    processed_rate_text,
                                                                    completed_text,
                                                                    progress_text,
                                                                ],
                                                                spacing=6,
                                                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                            ),
                                                            bgcolor=CREAM,
                                                            border=ft.border.all(1, FIELD_BORDER),
                                                            border_radius=10,
                                                            padding=12,
                                                            height=260,
                                                            alignment=ft.alignment.center,
                                                        ),
                                                    ],
                                                    spacing=8,
                                                ),
                                                col={"xs": 12, "md": 4},
                                            ),
                                            ft.Container(
                                                content=ft.Column(
                                                    [
                                                        ft.Text("Latest Suspicious Accounts", size=16, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                                                        ft.Text("Customer | Severity | Action", size=11, color="#666666"),
                                                        ft.Container(
                                                            content=suspicious_list,
                                                            bgcolor=CREAM,
                                                            border=ft.border.all(1, FIELD_BORDER),
                                                            border_radius=10,
                                                            padding=10,
                                                            height=260,
                                                        ),
                                                    ],
                                                    spacing=8,
                                                ),
                                                col={"xs": 12, "md": 8},
                                            ),
                                        ],
                                        spacing=10,
                                    ),
                                    ft.Text("Live Alerts", size=14, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                                    ft.Text("Recent security-related audit events.", size=11, color="#666666"),
                                    ft.Container(
                                        content=live_alerts_list,
                                        border=ft.border.all(1.5, FIELD_BORDER),
                                        border_radius=10,
                                        bgcolor=CREAM,
                                        padding=10,
                                        height=220,
                                    ),
                                ],
                                spacing=10,
                            ),
                            col={"xs": 12, "md": 9},
                        ),
                    ],
                    spacing=12,
                ),
            ],
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
        ),
        padding=10,
        bgcolor="#FFFFFF",
        expand=True,
    )
    return _fraud_content, refresh_data
