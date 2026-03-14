import flet as ft
import os
import imghdr
import uuid
from core.database import (
	get_all_menu_items,
	create_menu_item,
	update_menu_item,
	delete_menu_item,
)
from core.cloudinary_storage import upload_menu_image
from utils import (
	show_snackbar,
	create_image_widget,
	TEXT_DARK,
	ACCENT_PRIMARY,
	FIELD_BG,
	FIELD_BORDER,
	ACCENT_DARK,
)


UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads")


def create_menu_handlers(page, current_user, menu_list, form_container, fields, uploaded_image, menu_filter_buttons, file_picker=None, search_field=None):
	"""Create all menu-related handlers"""

	current_menu_filter = {"value": "All"}
	current_search = {"value": ""}
	edit_mode = {"active": False, "item_id": None}
	pending_uploads = {}
	upload_state = {"in_progress": False}

	def _resolve_pending_upload_path(file_name):
		file_path = pending_uploads.pop(file_name, None)
		if file_path:
			return file_path

		# Fallback: sometimes event key differs from original selected file name.
		if len(pending_uploads) == 1:
			_, only_path = pending_uploads.popitem()
			return only_path

		fallback_path = os.path.join(UPLOAD_DIR, file_name.replace("/", os.sep))
		if os.path.exists(fallback_path):
			return fallback_path

		return None

	def finalize_cloudinary_upload(file_path):
		detected_type = imghdr.what(file_path)
		if detected_type not in ("jpeg", "png", "gif"):
			upload_state["in_progress"] = False
			show_snackbar(page, "Invalid image file")
			return

		success, image_url, error_message = upload_menu_image(file_path)
		if not success:
			upload_state["in_progress"] = False
			print(error_message)
			show_snackbar(page, f"Cloud upload failed: {error_message}")
			return

		uploaded_image["data"] = image_url
		uploaded_image["type"] = "url"
		upload_state["in_progress"] = False
		fields["image_preview"].content = ft.Image(
			src=image_url,
			width=150,
			height=150,
			fit=ft.ImageFit.COVER,
			border_radius=10,
		)
		show_snackbar(page, "Image uploaded!", success=True)
		page.update()

	def handle_upload_progress(e: ft.FilePickerUploadEvent):
		if e.error:
			file_path = _resolve_pending_upload_path(e.file_name)
			upload_state["in_progress"] = False
			if file_path and os.path.exists(file_path):
				try:
					os.remove(file_path)
				except OSError:
					pass
			show_snackbar(page, f"Upload failed: {e.error}")
			return

		if e.progress is None or e.progress < 1.0:
			return

		file_path = _resolve_pending_upload_path(e.file_name)
		if not file_path or not os.path.exists(file_path):
			upload_state["in_progress"] = False
			show_snackbar(page, "Uploaded file could not be found on server.")
			return

		try:
			finalize_cloudinary_upload(file_path)
		finally:
			try:
				os.remove(file_path)
			except OSError:
				pass

	if file_picker is not None:
		file_picker.on_upload = handle_upload_progress

	def on_menu_search_change(e):
		current_search["value"] = e.control.value.lower().strip()
		load_menu(current_menu_filter["value"])

	if search_field is not None:
		search_field.on_change = on_menu_search_change

	def update_menu_filter_buttons(active_filter):
		"""Update menu chip colors to show active filter"""
		button_map = {
			"All": menu_filter_buttons["all"],
			"Appetizers": menu_filter_buttons["appetizers"],
			"Mains": menu_filter_buttons["mains"],
			"Desserts": menu_filter_buttons["desserts"],
			"Drinks": menu_filter_buttons["drinks"],
			"Other": menu_filter_buttons["other"],
		}

		for filter_name, chip in button_map.items():
			if filter_name == active_filter:
				chip.bgcolor = ACCENT_DARK
				chip.content.color = "#FFFFFF"
			else:
				chip.bgcolor = "#E0E0E0"
				chip.content.color = TEXT_DARK

	def load_menu(filter_category="All"):
		current_menu_filter["value"] = filter_category
		update_menu_filter_buttons(filter_category)

		new_controls = []
		all_items = get_all_menu_items()

		if filter_category == "All":
			items = all_items
		else:
			items = [item for item in all_items if item.get("category") == filter_category]

		if current_search["value"]:
			query = current_search["value"]
			items = [
				item for item in items
				if query in item["name"].lower() or query in item.get("description", "").lower()
			]

		count_text = ft.Text(
			f"Showing {len(items)} item(s)" + (f" in category '{filter_category}'" if filter_category != "All" else ""),
			size=15,
			color="#000000",
			weight=ft.FontWeight.BOLD,
		)
		new_controls.append(count_text)

		if not items:
			new_controls.append(
				ft.Container(
					content=ft.Text(
						"No items found in this category.",
						size=16,
						color="#000000",
						weight=ft.FontWeight.W_500,
						text_align=ft.TextAlign.CENTER,
					),
					padding=30,
					alignment=ft.alignment.center,
					bgcolor="#F5F5F5",
					border_radius=10,
				)
			)

		for item in items:
			category_colors = {
				"Appetizers": {"bg": "#FFE5B4", "text": "#8B4513"},
				"Mains": {"bg": "#FFD4D4", "text": "#8B0000"},
				"Desserts": {"bg": "#FFB6C1", "text": "#C71585"},
				"Drinks": {"bg": "#B0E0E6", "text": "#00688B"},
				"Other": {"bg": "#E0E0E0", "text": "#505050"},
			}

			category = item.get("category", "Other")
			cat_color = category_colors.get(category, category_colors["Other"])

			is_on_sale = item.get("is_on_sale", 0)
			sale_percentage = item.get("sale_percentage", 0)
			original_price = item["price"]
			display_price = original_price

			if is_on_sale and sale_percentage > 0:
				discount_multiplier = (100 - sale_percentage) / 100
				display_price = original_price * discount_multiplier

			price_row_items = []
			if is_on_sale and sale_percentage > 0:
				price_row_items.append(
					ft.Text(
						f"₱{original_price:.2f}",
						size=13,
						color="#999999",
						weight=ft.FontWeight.W_400,
						style=ft.TextStyle(decoration=ft.TextDecoration.LINE_THROUGH),
					)
				)
			price_row_items.append(
				ft.Text(f"₱{display_price:.2f}", size=15, color=ACCENT_PRIMARY, weight=ft.FontWeight.BOLD)
			)

			card = ft.Container(
				content=ft.Row(
					[
						create_image_widget(item, 85, 85),
						ft.Column(
							[
								ft.Row(
									[
										ft.Text(item["name"], size=16, weight=ft.FontWeight.BOLD, color="#000000"),
										ft.Container(
											content=ft.Text(category, size=10, weight=ft.FontWeight.BOLD, color=cat_color["text"]),
											bgcolor=cat_color["bg"],
											padding=ft.padding.symmetric(horizontal=8, vertical=3),
											border_radius=10,
										),
										ft.Container(
											content=ft.Text(
												f"-{sale_percentage}% OFF",
												size=10,
												weight=ft.FontWeight.BOLD,
												color="#FFFFFF",
											),
											bgcolor="#E53935",
											padding=ft.padding.symmetric(horizontal=8, vertical=3),
											border_radius=10,
											visible=is_on_sale and sale_percentage > 0,
										),
									],
									spacing=8,
								),
								ft.Text(item["description"], size=13, color="#000000", weight=ft.FontWeight.W_500),
								ft.Row(price_row_items, spacing=6),
								ft.Text(f"Stock: {item.get('stock', 0)}", size=12, color="#000000", weight=ft.FontWeight.W_500),
							],
							expand=True,
							spacing=5,
						),
						ft.IconButton(
							icon=ft.Icons.EDIT_ROUNDED,
							icon_color="white",
							bgcolor="#0D4715",
							icon_size=20,
							on_click=lambda e, item=item: edit_item(item),
							tooltip="Edit",
						),
						ft.IconButton(
							icon=ft.Icons.DELETE_ROUNDED,
							icon_color="white",
							bgcolor="#D32F2F",
							icon_size=20,
							on_click=lambda e, id=item["id"]: delete_item(id),
							tooltip="Delete",
						),
					],
					vertical_alignment=ft.CrossAxisAlignment.CENTER,
				),
				padding=12,
				border=ft.border.all(1.5, FIELD_BORDER),
				border_radius=12,
				bgcolor=FIELD_BG,
			)

			new_controls.append(card)

		menu_list.controls = new_controls

		page.update()

	def delete_item(item_id):
		user_id = current_user["user"]["id"]
		delete_menu_item(item_id, user_id)
		show_snackbar(page, "Item deleted!")
		load_menu(current_menu_filter["value"])

	def edit_item(item):
		edit_mode["active"] = True
		edit_mode["item_id"] = item["id"]
		fields["name"].value = item["name"]
		fields["desc"].value = item["description"]
		fields["price"].value = str(item["price"])
		fields["stock"].value = str(item.get("stock", 0))
		fields["category"].value = item.get("category", "Other")
		fields["calories"].value = str(item.get("calories", 0)) if item.get("calories") else ""
		fields["ingredients"].value = item.get("ingredients", "")
		fields["recipe"].value = item.get("recipe", "")
		fields["allergens"].value = item.get("allergens", "")
		fields["is_on_sale"].value = bool(item.get("is_on_sale", 0))
		fields["sale_percentage"].value = str(item.get("sale_percentage", 0))

		if item.get("image"):
			uploaded_image["data"] = item["image"]
			uploaded_image["type"] = item.get("image_type", "emoji")
			fields["image_preview"].content = create_image_widget(item, 150, 150)

		form_container.visible = True
		page.update()

	def handle_file_pick(e: ft.FilePickerResultEvent):
		if not e.files:
			return
		file = e.files[0]
		if file.size > 3145728:
			show_snackbar(page, "Image size must be under 3MB")
			return
		if not file.name.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
			show_snackbar(page, "Only JPG, PNG, GIF allowed")
			return

		if not getattr(file, "path", None):
			if file_picker is None:
				show_snackbar(page, "Browser upload is not available right now.")
				return

			file_extension = os.path.splitext(file.name)[1].lower()
			server_name = f"{uuid.uuid4().hex}{file_extension}"
			server_path = os.path.join(UPLOAD_DIR, server_name)
			pending_uploads[file.name] = server_path
			pending_uploads[server_name] = server_path
			upload_state["in_progress"] = True
			upload_url = page.get_upload_url(server_name, 600)
			file_picker.upload([
				ft.FilePickerUploadFile(name=file.name, upload_url=upload_url)
			])
			show_snackbar(page, "Uploading image to Cloudinary...")
			return

		if not os.path.exists(file.path):
			show_snackbar(page, "Selected file is not accessible.")
			return
		finalize_cloudinary_upload(file.path)

	def save_item(e):
		if not fields["name"].value or not fields["desc"].value or not fields["price"].value:
			show_snackbar(page, "Please fill all fields!")
			return

		if upload_state["in_progress"]:
			show_snackbar(page, "Please wait for image upload to finish before saving.")
			return

		stock_value = fields["stock"].value.strip() if fields["stock"].value else "0"
		try:
			stock = int(stock_value)
			if stock < 0:
				raise ValueError()
		except Exception:
			show_snackbar(page, "Stock must be a non-negative whole number")
			return

		user_id = current_user["user"]["id"]
		image_data = uploaded_image["data"] if uploaded_image["data"] else "🍽️"
		image_type = uploaded_image["type"]
		category = fields["category"].value

		calories = int(fields["calories"].value) if fields["calories"].value and fields["calories"].value.isdigit() else 0
		ingredients = fields["ingredients"].value if fields["ingredients"].value else ""
		recipe = fields["recipe"].value if fields["recipe"].value else ""
		allergens = fields["allergens"].value if fields["allergens"].value else ""

		is_on_sale = 1 if fields["is_on_sale"].value else 0
		sale_percentage_value = fields["sale_percentage"].value if fields["sale_percentage"].value else "0"
		sale_percentage = int(sale_percentage_value) if sale_percentage_value.strip().isdigit() else 0
		sale_percentage = max(0, min(100, sale_percentage))

		if sale_percentage > 0:
			is_on_sale = 1

		if edit_mode["active"]:
			update_menu_item(
				edit_mode["item_id"],
				fields["name"].value,
				fields["desc"].value,
				float(fields["price"].value),
				stock,
				image_data,
				image_type,
				category,
				user_id,
				calories,
				ingredients,
				recipe,
				allergens,
				is_on_sale,
				sale_percentage,
			)
			show_snackbar(page, "Item updated!")
			edit_mode["active"] = False
		else:
			create_menu_item(
				fields["name"].value,
				fields["desc"].value,
				float(fields["price"].value),
				stock,
				image_data,
				image_type,
				category,
				user_id,
				calories,
				ingredients,
				recipe,
				allergens,
				is_on_sale,
				sale_percentage,
			)
			show_snackbar(page, "Item added!")

		fields["name"].value = ""
		fields["desc"].value = ""
		fields["price"].value = ""
		fields["stock"].value = "0"
		fields["category"].value = "Other"
		fields["calories"].value = ""
		fields["ingredients"].value = ""
		fields["recipe"].value = ""
		fields["allergens"].value = ""
		fields["is_on_sale"].value = False
		fields["sale_percentage"].value = "0"
		uploaded_image["data"] = None
		uploaded_image["type"] = "emoji"
		fields["image_preview"].content = ft.Icon(ft.Icons.IMAGE, size=100, color="grey")
		form_container.visible = False
		load_menu(current_menu_filter["value"])

	def show_form(e):
		edit_mode["active"] = False
		fields["name"].value = ""
		fields["desc"].value = ""
		fields["price"].value = ""
		fields["stock"].value = "0"
		fields["category"].value = "Other"
		fields["calories"].value = ""
		fields["ingredients"].value = ""
		fields["recipe"].value = ""
		fields["allergens"].value = ""
		fields["is_on_sale"].value = False
		fields["sale_percentage"].value = "0"
		uploaded_image["data"] = None
		uploaded_image["type"] = "emoji"
		fields["image_preview"].content = ft.Icon(ft.Icons.IMAGE, size=100, color="grey")

		form_container.visible = True
		page.update()

	return {
		"load_menu": load_menu,
		"handle_file_pick": handle_file_pick,
		"save_item": save_item,
		"show_form": show_form,
	}
