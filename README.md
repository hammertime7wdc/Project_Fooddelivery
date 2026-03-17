# LK Martin Food Systems — App Documentation (Overall)

This README is based on the **current overall application** in this workspace.

## 1) Application Summary

LK Martin Food Systems is a multi-role food ordering platform built with Python + Flet.

It supports:
- Customer ordering flow (browse, cart, checkout, order timeline)
- Owner operations (menu management, order handling, sales analytics/export)
- Admin controls (user management, audit review, fraud-risk monitoring)
- Security-focused auth (password hashing, lockout, OTP verification/reset)

---

## 2) Tech Stack

- **UI/App Runtime:** Flet (`flet==0.28.3`)
- **Language:** Python
- **Database:** SQLite + SQLAlchemy (`sqlalchemy==2.0.44`)
- **Security:** bcrypt (`bcrypt==5.0.0`)
- **Config:** python-dotenv (`python-dotenv==1.0.1`)
- **HTTP/OAuth calls:** requests (`requests==2.31.0`)
- **Google OAuth libs:** `google-auth`, `google-auth-oauthlib`
- **Cloud media storage:** Cloudinary (`cloudinary==1.41.0`)

---

## 3) Main Modules (Current)

### Entry Point
- `ui/main.py`
  - Initializes DB
  - Starts OAuth callback server
  - Sets global app navigation
  - Starts session timeout/warning behavior
  - Runs app in browser mode via `ft.app(..., view=ft.WEB_BROWSER)`

### Core Services (`core/`)
- `auth.py`: validation, password hashing, login attempts/lockout, OTP signup & reset flows
- `auth_login.py`: login implementation internals
- `database.py`: menu/order/favorites/audit operations, status transitions, pagination helpers
- `session_manager.py`: inactivity timeout + warning callback orchestration
- `google_oauth.py`: OAuth URL generation, callback listener on `localhost:9000`, token exchange, userinfo retrieval
- `email_sender.py`: SMTP-based verification/reset emails
- `cloudinary_storage.py`: Cloudinary upload helpers for menu/profile images
- Utilities: `datetime_utils.py`, `image_utils.py`, `phone_utils.py`

### Domain Models (`models/models.py`)
- `User`, `PendingSignup`, `MenuItem`, `Order`, `AuditLog`, `Favorite`
- Includes lightweight schema migrations for existing DBs when app starts

### Screen Layer (`screens/`)
- Auth/entry: `splash.py`, `login.py`, `signup.py`, `email_verification.py`, `reset_password.py`, `login_loading.py`
- Customer: `browse_menu/`, `cart.py`, `order_confirmation.py`, `order_history/`, `profile/`
- Owner: `owner_dashboard/` (menu handling, order handling, sales dashboard)
- Admin: `admin_dashboard/` (users, orders, fraud risk, details pages)

### Assets & Data
- `assets/`: UI/menu/profile assets + JSON content (`carousel_items.json`, `login_messages.json`, `welcome_messages.json`)
- `uploads/menu/`: uploaded files
- `exports/`: generated sales CSV exports

### Utility Scripts
- `check_users.py`: list users in DB
- `add_missing_users.py`: ensure owner/admin users exist

---

## 4) Functional Features (Overall)

### Authentication & Security
- Password hashing with bcrypt
- Validation: email, full name, password complexity, password strength scoring
- Login protection: max failed attempts + temporary lockout
- Session timeout with warning notification before expiration
- Email-based OTP verification for signup
- Email-based OTP password reset
- Google OAuth login integration

### Customer Features
- Browse menu with search/category and pagination behavior
- View menu details including pricing and metadata
- Add items to cart and place orders
- Track order history/timeline by status
- Mark/unmark favorite menu items
- Manage profile information and profile image

### Owner Features
- Create/update/delete menu items
- Maintain stock, sale flags, sale percentage, ingredients/allergens/recipe metadata
- Process and update order statuses
- Sales dashboard KPIs and trend views
- Export sales reports to CSV

### Admin Features
- Manage users (create/enable/disable/delete constraints)
- Monitor audit logs
- Manage orders at system level
- Fraud-risk tab with risk scoring, thresholds, and quick account block/unblock actions

---

## 5) Order Lifecycle Rules

Implemented state transition rules in `core/database.py`:

- `placed` → `preparing` | `out for delivery` | `cancelled`
- `preparing` → `out for delivery` | `cancelled`
- `out for delivery` → `delivered`
- `delivered` and `cancelled` are terminal states

Additional behavior:
- Stock is reduced when order is placed
- Stock is restored when cancelling from `placed`
- Timeline timestamps are set per status update

---

## 6) Environment Variables

Create a `.env` file in project root for production-like setup.

### Required/Important App Variables
- `FLET_SECRET_KEY` (fallback exists in code, but set your own secure key)
- `PORT` (default: `8080`)

### Default Seed Accounts (used by DB initialization)
- `ADMIN_EMAIL`, `ADMIN_PASSWORD`
- `CUSTOMER_EMAIL`, `CUSTOMER_PASSWORD`
- `OWNER_EMAIL`, `OWNER_PASSWORD`

### SMTP (for OTP verification/reset emails)
- `SMTP_SERVER` (default: `smtp.gmail.com`)
- `SMTP_PORT` (default: `587`)
- `SMTP_EMAIL`
- `SMTP_PASSWORD`
- `SMTP_FROM_EMAIL` (optional)
- `SMTP_SENDER_NAME` (optional)

### Google OAuth
Use **either** env vars or `client_secret.json`.
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `OAUTH_CALLBACK_URL` (default behavior uses local callback)
- `GOOGLE_AUTH_URI` (optional override)
- `GOOGLE_TOKEN_URI` (optional override)

### Cloudinary (optional media offloading)
- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_API_KEY`
- `CLOUDINARY_API_SECRET`
- `CLOUDINARY_FOLDER` (optional)
- `CLOUDINARY_PROFILE_FOLDER` (optional)

---

## 7) Installation & Run

1. Create and activate virtual environment

```bash
python -m venv venv
venv\Scripts\activate
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Configure `.env` values as needed (SMTP/OAuth/seed users)

4. Run app

```bash
python ui/main.py
```

5. Open browser if not auto-opened
- Default URL uses configured `PORT` (e.g., `http://localhost:8080`)

---

## 8) Data & Outputs

- SQLite DB file: `food_delivery.db` (created/updated automatically)
- Upload path: `uploads/`
- Export path: `exports/` (sales CSV reports)
- Static resources and JSON content: `assets/`

---

## 9) Notes for Developers

- The app currently runs in **web-browser mode** via Flet.
- OAuth callback listener runs on port `9000`; avoid port conflicts.
- Existing DBs are auto-migrated for several schema additions at startup.
- For local testing without OAuth/email, you can keep those integrations unconfigured, but related flows will be limited.

---

## 10) License

MIT License (see `LICENSE`).