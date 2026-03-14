import json
import csv
import os
from datetime import datetime, timedelta
import flet as ft

from core.database import get_all_orders, get_all_menu_items
from utils import CREAM, TEXT_DARK, FIELD_BG, FIELD_BORDER, ACCENT_PRIMARY, ACCENT_DARK, show_snackbar


def _to_int(value, default=0):
    try:
        if value is None:
            return default
        if isinstance(value, bool):
            return int(value)
        return int(float(str(value).strip()))
    except Exception:
        return default


def _to_float(value, default=0.0):
    try:
        if value is None:
            return default
        if isinstance(value, (int, float)):
            return float(value)
        cleaned = str(value).replace("₱", "").replace(",", "").strip()
        return float(cleaned)
    except Exception:
        return default


def _parse_order_datetime(order):
    date_str = order.get("created_at") or order.get("placed_at")
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str)
    except Exception:
        return None


def _pct_change(current, previous):
    if previous <= 0:
        if current > 0:
            return 100.0
        return 0.0
    return ((current - previous) / previous) * 100.0


def _compute_sales_stats(period_days=30, low_stock_threshold=10):
    orders = get_all_orders()
    menu_items = get_all_menu_items()

    today = datetime.now().date()
    seven_days_ago = today - timedelta(days=6)
    thirty_days_ago = today - timedelta(days=29)
    period_start = today - timedelta(days=max(0, period_days - 1))
    previous_period_end = period_start - timedelta(days=1)
    previous_period_start = previous_period_end - timedelta(days=max(0, period_days - 1))

    daily_revenue = 0.0
    weekly_revenue = 0.0
    monthly_revenue = 0.0
    total_revenue = 0.0
    previous_period_revenue = 0.0

    total_orders = 0
    delivered_orders = 0
    cancelled_orders = 0
    previous_period_orders = 0

    chart_days = 7 if period_days <= 7 else 14
    trend_revenue_by_day = {
        (today - timedelta(days=index)): 0.0
        for index in range(chart_days)
    }
    trend_orders_by_day = {
        (today - timedelta(days=index)): 0
        for index in range(chart_days)
    }
    trend_delivered_orders_by_day = {
        (today - timedelta(days=index)): 0
        for index in range(chart_days)
    }

    item_stats = {}
    category_by_item_id = {
        item.get("id"): item.get("category", "Other")
        for item in menu_items
        if isinstance(item, dict)
    }

    for order in orders:
        order_dt = _parse_order_datetime(order)
        if not order_dt:
            continue

        order_date = order_dt.date()
        status = (order.get("status") or "").strip().lower()
        amount = _to_float(order.get("total_amount"), 0.0)

        if previous_period_start <= order_date <= previous_period_end:
            if status != "cancelled":
                previous_period_revenue += amount
                previous_period_orders += 1

        if order_date < period_start or order_date > today:
            continue

        total_orders += 1

        if status == "cancelled":
            cancelled_orders += 1
            continue

        total_revenue += amount

        if status == "delivered":
            delivered_orders += 1

        if order_date == today and status == "delivered":
            daily_revenue += amount

        if seven_days_ago <= order_date <= today:
            weekly_revenue += amount

        if thirty_days_ago <= order_date <= today:
            monthly_revenue += amount

        if order_date in trend_revenue_by_day:
            trend_revenue_by_day[order_date] += amount
            trend_orders_by_day[order_date] += 1
            if status == "delivered":
                trend_delivered_orders_by_day[order_date] += 1

        items = order.get("items", [])
        if isinstance(items, str):
            try:
                items = json.loads(items)
            except Exception:
                items = []

        for item in items:
            if not isinstance(item, dict):
                continue

            item_id = item.get("id")
            if not item_id:
                continue

            qty = _to_int(item.get("quantity"), 0)
            price = _to_float(item.get("price"), 0.0)
            name = item.get("name") or f"Item #{item_id}"

            if item_id not in item_stats:
                item_stats[item_id] = {
                    "name": name,
                    "quantity_sold": 0,
                    "revenue": 0.0,
                    "category": category_by_item_id.get(item_id, "Other"),
                }

            item_stats[item_id]["quantity_sold"] += qty
            item_stats[item_id]["revenue"] += qty * price

    top_selling_by_qty = sorted(
        item_stats.values(),
        key=lambda entry: (entry["quantity_sold"], entry["revenue"]),
        reverse=True,
    )[:5]

    top_selling_by_revenue = sorted(
        item_stats.values(),
        key=lambda entry: (entry["revenue"], entry["quantity_sold"]),
        reverse=True,
    )[:5]

    low_stock_items = sorted(
        [
            item for item in menu_items
            if isinstance(item, dict) and _to_int(item.get("stock"), 0) <= low_stock_threshold
        ],
        key=lambda item: _to_int(item.get("stock"), 0),
    )

    avg_order_value = (total_revenue / (total_orders - cancelled_orders)) if (total_orders - cancelled_orders) > 0 else 0.0
    delivery_rate = (delivered_orders / total_orders * 100.0) if total_orders > 0 else 0.0
    previous_avg_order_value = (previous_period_revenue / previous_period_orders) if previous_period_orders > 0 else 0.0

    trend_points = []
    for day in sorted(trend_revenue_by_day.keys()):
        orders_count = trend_orders_by_day[day]
        day_revenue = trend_revenue_by_day[day]
        trend_points.append({
            "label": day.strftime("%a"),
            "date_label": day.strftime("%b %d"),
            "revenue": day_revenue,
            "orders": orders_count,
            "delivered_orders": trend_delivered_orders_by_day[day],
            "average_ticket": (day_revenue / orders_count) if orders_count > 0 else 0.0,
        })

    return {
        "daily_revenue": daily_revenue,
        "weekly_revenue": weekly_revenue,
        "monthly_revenue": monthly_revenue,
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "delivered_orders": delivered_orders,
        "cancelled_orders": cancelled_orders,
        "avg_order_value": avg_order_value,
        "previous_period_revenue": previous_period_revenue,
        "previous_period_orders": previous_period_orders,
        "previous_avg_order_value": previous_avg_order_value,
        "revenue_change_pct": _pct_change(total_revenue, previous_period_revenue),
        "orders_change_pct": _pct_change(total_orders - cancelled_orders, previous_period_orders),
        "avg_order_change_pct": _pct_change(avg_order_value, previous_avg_order_value),
        "delivery_rate": delivery_rate,
        "top_selling_by_qty": top_selling_by_qty,
        "top_selling_by_revenue": top_selling_by_revenue,
        "low_stock": low_stock_items,
        "daily_trend": trend_points,
    }


def _build_kpi_card(title, value, subtext, accent_color):
    return ft.Container(
        content=ft.Column(
            [
                ft.Text(title, size=11, color="#666666", weight=ft.FontWeight.W_500),
                ft.Text(value, size=28, color=TEXT_DARK, weight=ft.FontWeight.BOLD),
                ft.Text(subtext, size=11, color=accent_color, weight=ft.FontWeight.BOLD),
                ft.Container(height=3, bgcolor=accent_color, border_radius=8, width=80),
            ],
            spacing=4,
        ),
        bgcolor="#FFFFFF",
        border=ft.border.all(1, "#D5CCBD"),
        border_radius=12,
        padding=14,
    )


def _build_section(title, content):
    return ft.Container(
        content=ft.Column(
            [
                ft.Text(title, size=16, color=TEXT_DARK, weight=ft.FontWeight.BOLD),
                content,
            ],
            spacing=10,
        ),
        bgcolor="#FFFFFF",
        border=ft.border.all(1, "#D5CCBD"),
        border_radius=12,
        padding=14,
    )


def _build_revenue_chart(points, metric_key="revenue"):
    metric_specs = {
        "revenue": {"prefix": "₱", "precision": 0},
        "orders": {"prefix": "", "precision": 0},
        "delivered_orders": {"prefix": "", "precision": 0},
        "average_ticket": {"prefix": "₱", "precision": 0},
    }
    spec = metric_specs.get(metric_key, metric_specs["revenue"])

    values = [_to_float(point.get(metric_key), 0.0) for point in points]
    max_value = max(values, default=0.0)
    max_value = max(max_value, 1.0)
    active_count = sum(1 for value in values if value > 0)
    sparse_mode = active_count <= max(1, len(points) // 3)

    chart_controls = []
    for point in points:
        value = _to_float(point.get(metric_key), 0.0)
        ratio = value / max_value
        label_value = f"{spec['prefix']}{value:.{spec['precision']}f}"

        if sparse_mode:
            stem_height = max(8, int(90 * ratio)) if value > 0 else 8
            marker_color = ACCENT_PRIMARY if value > 0 else "#B6AD9E"
            chart_controls.append(
                ft.Column(
                    [
                        ft.Text(label_value if value > 0 else "", size=10, color="#666666", height=12),
                        ft.Container(width=2, height=stem_height, bgcolor="#CFC5B6", border_radius=2),
                        ft.Container(width=12, height=12, bgcolor=marker_color, border_radius=12),
                        ft.Text(point.get("date_label", point.get("label", "")), size=11, color=TEXT_DARK, weight=ft.FontWeight.W_500),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=4,
                    alignment=ft.MainAxisAlignment.END,
                )
            )
        else:
            bar_height = max(12, int(120 * ratio)) if value > 0 else 8
            chart_controls.append(
                ft.Column(
                    [
                        ft.Text(label_value if value > 0 else "", size=10, color="#666666", height=12),
                        ft.Container(
                            width=30,
                            height=bar_height,
                            bgcolor=ACCENT_PRIMARY if value > 0 else "#B6AD9E",
                            border_radius=ft.border_radius.only(top_left=7, top_right=7, bottom_left=3, bottom_right=3),
                        ),
                        ft.Text(point.get("date_label", point.get("label", "")), size=11, color=TEXT_DARK, weight=ft.FontWeight.W_500),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=4,
                    alignment=ft.MainAxisAlignment.END,
                )
            )

    if not chart_controls:
        chart_controls.append(ft.Text("No trend data available.", size=12, color="#666666"))

    return ft.Container(
        content=ft.Row(
            chart_controls,
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
            vertical_alignment=ft.CrossAxisAlignment.END,
        ),
        height=188,
        bgcolor=FIELD_BG,
        border=ft.border.all(1, FIELD_BORDER),
        border_radius=10,
        padding=8,
    )


def _build_delivery_panel(delivery_rate, delivered_orders, total_orders):
    return ft.Container(
        content=ft.Column(
            [
                ft.Text("Delivery Performance", size=16, color=TEXT_DARK, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.ProgressRing(
                                value=min(1.0, max(0.0, delivery_rate / 100.0)),
                                width=140,
                                height=140,
                                color=ACCENT_DARK,
                                stroke_width=10,
                                bgcolor="#D8D0C2",
                            ),
                            ft.Text(f"{delivery_rate:.1f}%", size=26, color=ACCENT_DARK, weight=ft.FontWeight.BOLD),
                            ft.Text("Delivered Rate", size=12, color="#666666"),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    alignment=ft.alignment.center,
                ),
                ft.Text(f"Delivered: {delivered_orders}", size=12, color=TEXT_DARK, weight=ft.FontWeight.W_500),
                ft.Text(f"Total Orders: {total_orders}", size=12, color=TEXT_DARK, weight=ft.FontWeight.W_500),
            ],
            spacing=10,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor="#FFFFFF",
        border=ft.border.all(1, "#D5CCBD"),
        border_radius=12,
        padding=14,
        width=320,
    )


def _build_small_stat(title, value, hint):
    return ft.Container(
        content=ft.Column(
            [
                ft.Text(title, size=11, color="#666666"),
                ft.Text(value, size=42, color=TEXT_DARK, weight=ft.FontWeight.BOLD),
                ft.Text(hint, size=11, color=ACCENT_DARK, weight=ft.FontWeight.W_500),
            ],
            spacing=8,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor="#FFFFFF",
        border=ft.border.all(1, "#CEC3B1"),
        border_radius=14,
        padding=16,
        height=160,
        width=380,
    )


def _build_comparison_card(title, value, delta_pct, baseline_text):
    is_up = delta_pct >= 0
    arrow = "▲" if is_up else "▼"
    delta_color = ACCENT_DARK if is_up else "#C62828"
    delta_bg = "#DDF0E1" if is_up else "#FDE7E7"
    return ft.Container(
        content=ft.Column(
            [
                ft.Text(title, size=11, color="#666666"),
                ft.Text(value, size=28, color=TEXT_DARK, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Text(
                        f"{arrow} {abs(delta_pct):.1f}% vs previous",
                        size=11,
                        color=delta_color,
                        weight=ft.FontWeight.BOLD,
                    ),
                    bgcolor=delta_bg,
                    border_radius=12,
                    padding=ft.padding.symmetric(horizontal=10, vertical=5),
                ),
                ft.Text(baseline_text, size=11, color="#666666"),
            ],
            spacing=8,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor="#FFFFFF",
        border=ft.border.all(1, "#CEC3B1"),
        border_radius=14,
        padding=16,
        height=160,
        width=245,
    )


def _build_top_item_card(index, item):
    return ft.Container(
        content=ft.Row(
            [
                ft.Text(f"#{index}", size=14, color=ACCENT_DARK, weight=ft.FontWeight.BOLD, width=30),
                ft.Column(
                    [
                        ft.Text(item["name"], size=14, color=TEXT_DARK, weight=ft.FontWeight.BOLD),
                        ft.Text(f"{item.get('category', 'Other')}", size=11, color="#666666"),
                    ],
                    spacing=2,
                    expand=True,
                ),
                ft.Container(
                    content=ft.Text(f"{item['quantity_sold']} sold", size=11, color=ACCENT_DARK, weight=ft.FontWeight.BOLD),
                    bgcolor="#CFE7D3",
                    border_radius=12,
                    padding=ft.padding.symmetric(horizontal=10, vertical=5),
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        bgcolor="#D7CEBE",
        border=ft.border.all(1, "#C8BAA2"),
        border_radius=10,
        padding=10,
    )


def _build_top_revenue_card(index, item):
    return ft.Container(
        content=ft.Row(
            [
                ft.Text(f"#{index}", size=14, color=ACCENT_PRIMARY, weight=ft.FontWeight.BOLD, width=30),
                ft.Column(
                    [
                        ft.Text(item["name"], size=14, color=TEXT_DARK, weight=ft.FontWeight.BOLD),
                        ft.Text(f"{item.get('category', 'Other')} • {item['quantity_sold']} sold", size=11, color="#666666"),
                    ],
                    spacing=2,
                    expand=True,
                ),
                ft.Container(
                    content=ft.Text(f"₱{item['revenue']:.2f}", size=11, color="#FFFFFF", weight=ft.FontWeight.BOLD),
                    bgcolor=ACCENT_PRIMARY,
                    border_radius=12,
                    padding=ft.padding.symmetric(horizontal=10, vertical=5),
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        bgcolor="#D7CEBE",
        border=ft.border.all(1, "#C8BAA2"),
        border_radius=10,
        padding=10,
    )


def _build_low_stock_card(item):
    stock_value = _to_int(item.get("stock"), 0)
    critical = stock_value <= 3
    badge_color = "#C62828" if critical else "#EF6C00"
    badge_bg = "#FFEBEE" if critical else "#FFF3E0"
    badge_text = "CRITICAL" if critical else "LOW"

    return ft.Container(
        content=ft.Row(
            [
                ft.Column(
                    [
                        ft.Text(item.get("name", "Unnamed"), size=14, color=TEXT_DARK, weight=ft.FontWeight.BOLD),
                        ft.Text(f"Stock: {stock_value}", size=12, color="#666666"),
                    ],
                    spacing=2,
                    expand=True,
                ),
                ft.Container(
                    content=ft.Text(badge_text, size=11, color=badge_color, weight=ft.FontWeight.BOLD),
                    bgcolor=badge_bg,
                    border_radius=12,
                    padding=ft.padding.symmetric(horizontal=10, vertical=5),
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        bgcolor="#D7CEBE",
        border=ft.border.all(1, "#C8BAA2"),
        border_radius=10,
        padding=10,
    )


def create_sales_dashboard(page: ft.Page):
    period_options = {
        "Today": 1,
        "7D": 7,
        "30D": 30,
        "90D": 90,
    }
    chart_metric_options = {
        "Revenue": "revenue",
        "Orders": "orders",
        "Delivered orders": "delivered_orders",
        "Average Order Value": "average_ticket",
    }
    period_state = {"label": "30D"}
    chart_metric_state = {"label": "Revenue"}

    try:
        stats = _compute_sales_stats(period_days=period_options[period_state["label"]])
    except Exception:
        stats = {
            "daily_revenue": 0.0,
            "weekly_revenue": 0.0,
            "monthly_revenue": 0.0,
            "total_revenue": 0.0,
            "total_orders": 0,
            "delivered_orders": 0,
            "cancelled_orders": 0,
            "avg_order_value": 0.0,
            "previous_period_revenue": 0.0,
            "previous_period_orders": 0,
            "previous_avg_order_value": 0.0,
            "revenue_change_pct": 0.0,
            "orders_change_pct": 0.0,
            "avg_order_change_pct": 0.0,
            "delivery_rate": 0.0,
            "top_selling_by_qty": [],
            "top_selling_by_revenue": [],
            "low_stock": [],
            "daily_trend": [],
        }
    stats_state = {"data": stats}

    kpi_grid = ft.Row(
        spacing=12,
        wrap=True,
    )

    top_items_column = ft.Column(spacing=8)
    top_revenue_column = ft.Column(spacing=8)
    low_stock_column = ft.Column(spacing=8)
    summary_row = ft.Row(spacing=12, wrap=True)

    delivery_panel_container = ft.Container()
    chart_panel_container = ft.Container()

    status_summary = ft.Text(size=13, color=TEXT_DARK, weight=ft.FontWeight.W_500)

    period_dropdown = ft.Dropdown(
        width=120,
        value=period_state["label"],
        options=[
            ft.dropdown.Option(
                key=label,
                text=label,
                content=ft.Text(label, color="#000000", size=14, weight=ft.FontWeight.W_500),
            )
            for label in period_options.keys()
        ],
        bgcolor="#FFFFFF",
        fill_color="#FFFFFF",
        filled=True,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        border_radius=8,
        text_style=ft.TextStyle(color=TEXT_DARK, size=12, weight=ft.FontWeight.W_500),
    )

    chart_metric_dropdown = ft.Dropdown(
        width=180,
        value=chart_metric_state["label"],
        options=[
            ft.dropdown.Option(
                key=label,
                text=label,
                content=ft.Text(label, color="#000000", size=14, weight=ft.FontWeight.W_500),
            )
            for label in chart_metric_options.keys()
        ],
        bgcolor="#FFFFFF",
        fill_color="#FFFFFF",
        filled=True,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        border_radius=8,
        text_style=ft.TextStyle(color=TEXT_DARK, size=12, weight=ft.FontWeight.W_500),
    )

    export_csv_button = ft.ElevatedButton(
        "Export CSV",
        icon=ft.Icons.DOWNLOAD,
        bgcolor=ACCENT_DARK,
        color="#FFFFFF",
    )

    export_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "exports")

    def export_csv(e):
        export_csv_button.text = "Exporting..."
        export_csv_button.icon = ft.Icons.HOURGLASS_TOP
        export_csv_button.bgcolor = ACCENT_PRIMARY
        export_csv_button.disabled = True
        page.update()
        try:
            os.makedirs(export_dir, exist_ok=True)
            period_label = period_state["label"].lower().replace(" ", "")
            days = period_options[period_state["label"]]
            now = datetime.now()
            cutoff_date = now.date() - timedelta(days=max(0, days - 1))

            file_name = f"sales_{period_label}_{now.strftime('%Y%m%d_%H%M%S')}.csv"
            file_path = os.path.join(export_dir, file_name)

            orders = get_all_orders()
            rows = []
            revenue = 0.0

            for order in orders:
                order_dt = _parse_order_datetime(order)
                if not order_dt:
                    continue
                if order_dt.date() < cutoff_date:
                    continue

                status = (order.get("status") or "").lower().strip()
                amount = _to_float(order.get("total_amount"), 0.0)
                if status != "cancelled":
                    revenue += amount

                rows.append({
                    "order_id": order.get("id"),
                    "date": order_dt.strftime("%Y-%m-%d %H:%M"),
                    "customer": order.get("customer_name", ""),
                    "status": status,
                    "amount": f"{amount:.2f}",
                })

            with open(file_path, "w", newline="", encoding="utf-8") as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=["order_id", "date", "customer", "status", "amount"])
                writer.writeheader()
                writer.writerows(rows)
                writer.writerow({})
                writer.writerow({"order_id": "SUMMARY"})
                writer.writerow({"order_id": "period", "date": period_state["label"]})
                writer.writerow({"order_id": "orders_count", "date": str(len(rows))})
                writer.writerow({"order_id": "non_cancelled_revenue", "date": f"{revenue:.2f}"})

            show_snackbar(page, f"CSV exported: {file_path}", success=True)
        except Exception as ex:
            show_snackbar(page, f"CSV export failed: {str(ex)}", error=True)
        finally:
            export_csv_button.text = "Export CSV"
            export_csv_button.icon = ft.Icons.DOWNLOAD
            export_csv_button.bgcolor = ACCENT_DARK
            export_csv_button.disabled = False
            page.update()

    def render(new_stats):
        status_summary.value = (
            f"Total orders: {new_stats['total_orders']}   •   "
            f"Delivered: {new_stats['delivered_orders']}   •   "
            f"Cancelled: {new_stats['cancelled_orders']}"
        )

        kpi_grid.controls = [
            _build_kpi_card("Daily Revenue", f"₱{new_stats['daily_revenue']:.2f}", "Delivered today", ACCENT_DARK),
            _build_kpi_card(f"Revenue ({period_state['label']})", f"₱{new_stats['total_revenue']:.2f}", f"Selected period {period_state['label']}", ACCENT_PRIMARY),
            _build_kpi_card("Weekly Revenue", f"₱{new_stats['weekly_revenue']:.2f}", "Last 7 days", ACCENT_DARK),
            _build_kpi_card("Total Revenue", f"₱{new_stats['total_revenue']:.2f}", "All non-cancelled", ACCENT_PRIMARY),
        ]

        selected_metric_key = chart_metric_options[chart_metric_state["label"]]
        chart_panel_container.content = _build_section(
            f"{chart_metric_state['label']} Trend",
            _build_revenue_chart(new_stats.get("daily_trend", []), selected_metric_key),
        )
        delivery_panel_container.content = _build_delivery_panel(
            new_stats["delivery_rate"],
            new_stats["delivered_orders"],
            new_stats["total_orders"],
        )

        summary_row.controls = [
            _build_comparison_card(
                "Period Revenue",
                f"₱{new_stats['total_revenue']:.2f}",
                new_stats["revenue_change_pct"],
                f"Prev: ₱{new_stats['previous_period_revenue']:.2f}",
            ),
            _build_comparison_card(
                "Completed Orders",
                str(new_stats['total_orders'] - new_stats['cancelled_orders']),
                new_stats["orders_change_pct"],
                f"Prev: {new_stats['previous_period_orders']}",
            ),
            _build_comparison_card(
                "Avg Order Value",
                f"₱{new_stats['avg_order_value']:.2f}",
                new_stats["avg_order_change_pct"],
                f"Prev: ₱{new_stats['previous_avg_order_value']:.2f}",
            ),
        ]

        top_items_column.controls.clear()
        if new_stats["top_selling_by_qty"]:
            for index, item in enumerate(new_stats["top_selling_by_qty"], start=1):
                top_items_column.controls.append(_build_top_item_card(index, item))
        else:
            top_items_column.controls.append(ft.Text("No sales data yet.", size=12, color="#666666"))

        top_revenue_column.controls.clear()
        if new_stats["top_selling_by_revenue"]:
            for index, item in enumerate(new_stats["top_selling_by_revenue"], start=1):
                top_revenue_column.controls.append(_build_top_revenue_card(index, item))
        else:
            top_revenue_column.controls.append(ft.Text("No revenue data yet.", size=12, color="#666666"))

        low_stock_column.controls.clear()
        if new_stats["low_stock"]:
            for item in new_stats["low_stock"][:8]:
                low_stock_column.controls.append(_build_low_stock_card(item))
        else:
            low_stock_column.controls.append(ft.Text("No low-stock alerts.", size=12, color="#666666"))

    def refresh_dashboard(e):
        try:
            new_stats = _compute_sales_stats(period_days=period_options[period_state["label"]])
        except Exception:
            new_stats = stats_state["data"]
        stats_state["data"] = new_stats
        render(new_stats)
        page.update()

    def on_period_change(e):
        chosen = e.control.value or "30D"
        period_state["label"] = chosen
        try:
            new_stats = _compute_sales_stats(period_days=period_options[period_state["label"]])
        except Exception:
            new_stats = stats_state["data"]
        stats_state["data"] = new_stats
        render(new_stats)
        page.update()

    def on_chart_metric_change(e):
        chart_metric_state["label"] = e.control.value or "Revenue"
        render(stats_state["data"])
        page.update()

    period_dropdown.on_change = on_period_change
    chart_metric_dropdown.on_change = on_chart_metric_change

    refresh_button = ft.ElevatedButton(
        "Refresh",
        icon=ft.Icons.REFRESH,
        bgcolor=ACCENT_PRIMARY,
        color="#FFFFFF",
        on_click=refresh_dashboard,
    )

    export_csv_button.on_click = export_csv

    render(stats)

    return ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Sales Dashboard", size=18, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                        ft.Row([period_dropdown, chart_metric_dropdown, refresh_button, export_csv_button], spacing=8, wrap=True),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(
                    content=ft.Text(
                        "Daily revenue resets at 12:00 AM based on server local time.",
                        size=12,
                        color=TEXT_DARK,
                    ),
                    bgcolor="#F4E4CC",
                    border=ft.border.all(1, "#E1C999"),
                    border_radius=8,
                    padding=10,
                ),
                status_summary,
                kpi_grid,
                ft.Row(
                    [
                        ft.Container(content=chart_panel_container, expand=True),
                        delivery_panel_container,
                    ],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
                summary_row,
                ft.Row(
                    [
                        ft.Container(content=_build_section("Top-Selling Items", top_items_column), expand=True),
                        ft.Container(content=_build_section("Top Items by Revenue", top_revenue_column), expand=True),
                    ],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
                _build_section("Low-Stock Alerts", low_stock_column),
            ],
            spacing=14,
            scroll=ft.ScrollMode.AUTO,
        ),
        expand=True,
        padding=10,
        bgcolor=CREAM,
    )
