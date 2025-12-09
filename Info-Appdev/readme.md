# Food Delivery Application

A comprehensive food delivery management system built with Python and Flet, featuring role-based access control, real-time order tracking, and secure authentication.

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Security Features](#security-features)
- [Default Credentials](#default-credentials)
- [License](#license)

## Features

### Authentication & Security
- Secure password hashing with bcrypt (12 rounds)
- Account lockout after 5 failed login attempts (1-minute lockout)
- Password strength validation with real-time feedback
- Email format validation
- Session management with automatic timeout (15 minutes default)
- Session activity tracking across all user interactions

### Role-Based Access Control (RBAC)

**Customer:**
- Browse menu with search and category filters
- Add items to cart with quantity selection
- Place orders with delivery details
- View order history with status filters
- Cancel orders (placed/preparing status only)
- Update profile and change password
- Upload profile pictures

**Restaurant Owner:**
- Full menu management (CRUD operations)
- Image upload for menu items (up to 3MB with MIME validation)
- Category-based menu organization
- Order management with status updates
- Filter orders by status
- Profile management

**Administrator:**
- User management (create, disable, enable, delete users)
- Advanced user filtering (role, status, search)
- View failed login attempts and locked accounts
- System-wide order management
- Audit log access
- Override order statuses

### Menu Management
- Category-based organization (Appetizers, Mains, Desserts, Drinks, Other)
- Image support (file upload or emoji)
- Search functionality
- Real-time filtering
- Price management
- Server-side pagination (10 items per page)

### Order Management
- Order placement with delivery details
- Real-time status tracking
- State machine for order status transitions
- Per-customer order numbering
- Order history with filters
- Automatic status polling (30-second intervals)

### User Interface
- Dark theme with gradient backgrounds
- Responsive design
- Real-time validation with visual feedback
- Snackbar notifications
- Tab-based navigation
- Shadow effects and modern UI elements

### Architecture Diagram
![ARCHI](./assets/Archi.jpg)
### Data Model
![ERD](./assets/ERD.jpg)
## Tech Stack

- **Framework:** Flet (Python GUI framework)
- **Database:** SQLite with SQLAlchemy ORM
- **Authentication:** bcrypt for password hashing
- **Session Management:** Custom SessionManager with threading
- **File Handling:** UUID-based file naming with imghdr MIME validation
- **Environment:** python-dotenv for configuration

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Steps

1. **Clone the repository:**
```bash
git clone https://github.com/hammertime7wdc/Project_Fooddelivery.git
cd food-delivery-app
```

2. **Create virtual environment:**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Create required directories:**
```bash
mkdir -p assets/menu
mkdir -p assets/profiles
```

5. **Run the application:**
```bash
python ui/main.py
```

## Quick Start

### On First Run
The application will automatically:
1. Create the SQLite database
2. Initialize tables
3. Create default users (admin, customer, owner)
4. Add sample menu items

### Logging In
1. Select your role (Customer/Restaurant Owner/Administrator)
2. Enter email and password
3. Click "Log in"

### Customer Workflow
1. **Browse Menu:** Search or filter by category
2. **Add to Cart:** Select quantity and add items
3. **Checkout:** Fill delivery details
4. **Place Order:** Confirm order
5. **Track Order:** View order history and real-time status

### Owner Workflow
1. **Manage Menu:** Add/edit/delete menu items
2. **Upload Images:** Choose food images (JPG, PNG, GIF)
3. **Process Orders:** Update order statuses
4. **Filter Orders:** View orders by status

### Admin Workflow
1. **User Management:** Create/disable/enable/delete users
2. **Monitor Activity:** View failed login attempts
3. **Manage Orders:** Override any order status
4. **Filter Users:** Search by name, email, role, or status

## Project Structure

```
Project/
├── ui/
│   └── main.py                    # Application entry point
├── screens/
│   ├── login.py                   # Authentication screen
│   ├── signup.py                  # User registration
│   ├── reset_password.py          # Password recovery
│   ├── profile.py                 # User profile management
│   ├── browse_menu.py             # Menu browsing with pagination
│   ├── cart.py                    # Shopping cart
│   ├── order_confirmation.py      # Order review & placement
│   ├── order_history.py           # Order tracking
│   ├── owner_dashboard.py         # Restaurant management
│   └── admin_dashboard.py         # Admin panel
├── core/
│   ├── auth.py                    # Authentication & validation
│   ├── database.py                # Database operations
│   ├── session_manager.py         # Session handling
│   └── datetime_utils.py          # Timezone utilities
├── models/
│   └── models.py                  # SQLAlchemy ORM models
├── assets/
│   ├── menu/                      # Menu item images
│   └── profiles/                  # User profile pictures
├── utils.py                       # UI helpers & constants
├── requirements.txt               # Python dependencies
└── food_delivery.db              # SQLite database (auto-created)
```

## Security Features

### Password Requirements
- Minimum 8 characters
- At least one uppercase letter (A-Z)
- At least one lowercase letter (a-z)
- At least one number (0-9)
- At least one special character (!@#$%^&*(),.?":{}|<>)
- Maximum 128 characters

### Password Strength Indicator
- **Weak (0-39%):** Red indicator
- **Medium (40-59%):** Orange indicator
- **Strong (60-79%):** Yellow indicator
- **Very Strong (80-100%):** Green indicator

### Account Protection
- Failed login attempt tracking
- Automatic account lockout after 5 failures
- 1-minute lockout duration
- Auto-unlock after lockout period
- Visual countdown timer during lockout

### Session Security
- Activity-based timeout (15 minutes default)
- Warning notification (2 minutes before expiry)
- Automatic logout on timeout
- Session tracking across all interactions
- Secure session cleanup on logout

### Image Upload Security
- File size validation (max 3MB for menu items, 1MB for profiles)
- Extension validation (.jpg, .jpeg, .png, .gif only)
- MIME type detection using imghdr (prevents masqueraded files)
- UUID-based filename generation
- Secure file storage in `assets/menu` and `assets/profiles`

### Data Validation
- Email format validation (RFC 5321 compliant)
- Full name validation (letters, spaces, hyphens, apostrophes)
- Phone number format validation
- Real-time field validation with visual feedback
- SQL injection prevention through ORM

## Default Credentials

### Administrator
```
Email: admin@fooddelivery.com
Password: Admin@123
Role: Administrator
```

### Customer
```
Email: customer@fooddelivery.com
Password: Customer@123
Role: Customer
```

### Restaurant Owner
```
Email: owner@fooddelivery.com
Password: Owner@123
Role: Restaurant Owner
```

**Important:** Change these passwords immediately after first login in a production environment!

## UI Color Scheme

- **Primary Background:** Linear gradient (#9A031E → #6B0113)
- **Accent Primary:** #9A031E (Burgundy)
- **Accent Dark:** #6B0113 (Dark Red)
- **Text Light:** #E5E5E5 (Light Gray)
- **Text Dark:** #1A1A1A (Dark Gray)
- **Field Background:** #2A2A2A (Dark Gray)
- **Field Border:** #444444 (Gray)

## Known Issues & Limitations

1. **Single Restaurant:** Currently supports one restaurant
2. **Payment Integration:** No payment gateway integration
3. **Real-time Updates:** Order status updates use polling (30s interval)
4. **Email Verification:** Password reset is placeholder
5. **Image Storage:** File-based storage (consider cloud storage for production)

## Future Enhancements

- Multi-restaurant support
- Payment gateway integration (Stripe, PayPal)
- Email verification and password reset
- Real-time notifications using websockets
- Mobile app version
- Admin analytics dashboard
- Customer ratings and reviews
- Delivery tracking with maps
- Multi-language## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues, questions, or contributions:
- Create an issue on GitHub
- Review CODE_DOCUMENTATION.md for technical details

## Individual Reflections

### John Joshua Bora
Working on this food delivery application strengthened my understanding of full-stack development and security practices. I gained hands-on experience implementing role-based access control, which taught me how critical authorization is in multi-user systems. The password hashing implementation using bcrypt deepened my appreciation for cryptographic best practices. Debugging session management issues across different user roles helped me understand concurrent programming challenges. The real-time order status tracking system showed me how polling mechanisms work as alternatives to websockets. I learned that security isn't just about passwords—it encompasses validation, file handling, and authorization at every layer. This project demonstrated the importance of planning architecture early to avoid massive refactoring later. The collaborative workflow and code reviews improved my ability to write cleaner, more maintainable code. Overall, this experience reinforced that backend development requires meticulous attention to detail and forward-thinking design decisions.

### Nasser Astibe
This project provided invaluable exposure to database design and ORM frameworks. Implementing SQLAlchemy models and migrations taught me how to structure data relationships effectively while maintaining referential integrity. I developed a deeper understanding of how proper database normalization prevents data anomalies and improves query performance. Working on the order management system with state machine logic showed me the importance of enforcing business rules at the database level. The pagination implementation in the menu browsing feature demonstrated how to optimize queries for large datasets. I learned that database decisions early in development have cascading effects on system performance and maintainability. Troubleshooting N+1 query problems and optimizing database indexes proved that even small improvements yield significant performance gains. The audit logging functionality introduced me to how to track system activities for compliance and debugging. This experience solidified my belief that a well-designed database is the foundation of any robust application, and poor database decisions are costly to fix later.

### Jacob Angel Sabio
Developing the frontend with Flet expanded my perspective on GUI design and user experience principles. Creating responsive interfaces for different screen sizes taught me how layout management and component organization directly impact usability. Implementing real-time validation with visual feedback showed me that good UX is about guiding users, not just enforcing rules. The dark theme gradient design enhanced my appreciation for color theory and accessibility considerations. Building role-specific dashboards for customers, owners, and admins required understanding different user needs and workflows. The image upload features with error handling reminded me that graceful failure handling is crucial for user trust. Implementing the snackbar notification system demonstrated how micro-interactions improve user feedback loops. I learned that frontend development isn't just about making things look good—it's about creating intuitive experiences that reduce user friction. The pagination controls and order tracking interface showed how thoughtful design can make complex workflows feel simple. This project convinced me that investing in UX early prevents frustration and support burden later.

---

