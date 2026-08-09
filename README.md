# Marvelam Backend API

Marvelam is an e-commerce backend built with Django 6.0 and Django REST Framework. It supports a dual-catalog system for finished ready-made products and raw customizable materials, integrated cart and checkout workflows, Paystack payment verification via webhooks, and Celery background tasks for transactional email dispatches.

---

## Technical Stack

* **Framework:** Python 3.12+, Django 6.0, Django REST Framework 3.16.1
* **Authentication:** SimpleJWT (JWT with token blacklisting), Django Allauth (Social Auth support)
* **Asynchronous Queue:** Celery 5.6.2 with Redis 6.4.0
* **Payment Gateway:** Paystack API integration (HMAC-SHA512 webhook signature validation)
* **API Documentation:** OpenAPI 3.0 via `drf-spectacular` (Swagger UI and ReDoc)
* **Database:** SQLite (development default) / PostgreSQL compatible
* **Formatting & Linting:** Black, Isort, Ruff, Flake8, Pre-commit
* **Environment Configuration:** `python-decouple`

---

## Repository Structure

```text
Marvelam/
├── MAC/                        # Project configuration directory
│   ├── settings.py             # Main settings (decoupled via .env)
│   ├── urls.py                 # Root URL router & documentation endpoints
│   ├── celery.py               # Celery app instance configuration
│   ├── asgi.py                 # ASGI configuration
│   └── wsgi.py                 # WSGI configuration
├── accounts/                   # User authentication & user profile management
│   ├── models.py               # CustomUser (UUID PK, Email as identifier)
│   ├── views.py                # Registration, Login, Profile, Password Reset
│   ├── tasks.py                # Celery tasks for account emails
│   └── urls.py                 # /api/ endpoints
├── products/                   # Finished products catalog
│   ├── models.py               # Products, ProductVariant, ProductSpecification, Images, Videos
│   ├── views.py                # Catalog listing, creation, and management
│   └── urls.py                 # /products/ endpoints
├── materials/                  # Raw materials catalog
│   ├── models.py               # Materials, MaterialVariant, MaterialSpecification, Images, Videos
│   ├── views.py                # Material catalog endpoints
│   └── urls.py                 # /materials/ endpoints
├── cart/                       # Cart processing
│   ├── models.py               # Cart & GenericForeignKey CartItem models
│   ├── views.py                # Add, update, remove items, cart view
│   └── urls.py                 # /cart/ endpoints
├── order/                      # Orders & checkout processing
│   ├── models.py               # Order, OrderItem, Address, DeliveryMethod, PaymentMethod
│   ├── tasks.py                # Order confirmation and update emails
│   ├── views.py                # Address management, checkout preview, place order
│   └── urls.py                 # /order/ and /checkout/ endpoints
├── payments/                   # Paystack payment flows & refunds
│   ├── models.py               # Payment model, RefundRequest model
│   ├── tasks.py                # Refund notification background tasks
│   ├── views.py                # Payment initialization, callback, webhook handler, refund API
│   └── urls.py                 # /payments/ endpoints
├── review/                     # Product & Material reviews
│   ├── models.py               # GenericForeignKey Reviews model with rating math
│   ├── views.py                # Review creation, list, update, and deletion
│   └── urls.py                 # /review/ endpoints
├── core/                       # Shared abstract models, utilities, and home API
│   ├── models.py               # TimeStampModel, CatalogBaseModel, Category, Banner
│   ├── choices.py              # Status, Color, Quality, ProductSize choices
│   └── views.py                # HomePageAPIView endpoint
├── utils/                      # Helper logic for stock and calculation utilities
├── static/                     # Project static assets
├── templates/                  # Email HTML templates
├── manage.py                   # Django CLI management script
├── run.bat                     # Quick script to run Django dev server
├── update.bat                  # Quick script to run database migrations
└── requirements.txt            # Python dependencies
```

---

## Architectural & Design Overview

### 1. Dual-Catalog Architecture
The application handles two distinct inventory types:
* **Products:** Finished goods with size choices (`XS`, `S`, `M`, `L`, `XL`, `XXL`, `3XL`) and color variants.
* **Materials:** Fabrics and raw materials with specific parameters such as width, thread count, and pattern types (`PLAIN`, `FLORAL`, `STRIPED`, `CHECKERED`, `POLKA_DOT`, `ABSTRACT`).

Both inherit from abstract base models (`CatalogBaseModel`, `VariantBaseModel`, `SpecificationBaseModel`) to keep standard fields (pricing, stock, discount, slug generation, image/video paths) consistent across apps.

### 2. Generic Foreign Keys (Cart, OrderItems & Reviews)
Rather than creating separate cart/order models or nullable foreign keys for products and materials, `CartItem`, `OrderItem`, and `Reviews` use Django ContentTypes (`content_type` + `object_id`). This links item listings directly to `ProductVariant` or `MaterialVariant` without duplicating database schema logic.

### 3. Custom User Model (`CustomUser`)
* Extends `AbstractUser` using UUID primary keys instead of auto-incrementing integers.
* Uses `email` as the `USERNAME_FIELD` for authentication.
* Profile attributes (phone number via `phonenumber_field`, address, country, state, city, profile image) are attached directly to the user model to eliminate additional table joins.

### 4. Address Book Default Flag Logic
When saving a user delivery address in `order.models.Address`, setting `is_default=True` automatically resets `is_default=False` on all other addresses owned by that user.

### 5. Paystack Integration & Webhook Handler
* **Initialization:** Generates payment reference and calls Paystack's transaction initialization endpoint.
* **Webhook Processing:** Public listener at `/payments/webhook/paystack/` validates incoming `x-paystack-signature` using HMAC-SHA512 before updating payment and order status to `CONFIRMED`, decreasing item stock, locking the order (`is_active = False`), generating a tracking ID (`MAC-XXXXX`), and triggering an email dispatch.

### 6. Background Asynchronous Processing
Celery processes long-running or external operations asynchronously:
* Account registration and email verification links.
* Welcome emails and password reset tokens.
* Order confirmation emails and shipment status updates.
* Refund request state notification dispatches.

---

## API Endpoints Overview

| App | Method | Endpoint | Description |
| :--- | :--- | :--- | :--- |
| **Documentation** | `GET` | `/api/docs/` | Interactive Swagger UI |
| | `GET` | `/api/redoc/` | Interactive ReDoc interface |
| | `GET` | `/api/schema/` | Raw OpenAPI Schema JSON/YAML |
| **Core** | `GET` | `/` | Homepage aggregate payload (banners, categories, new arrivals, featured) |
| **Accounts** | `POST` | `/api/register/` | Register user account |
| | `POST` | `/api/login/` | Obtain JWT access and refresh token pair |
| | `GET` | `/api/verify-email/<user_id>/<verification_token>/` | Confirm email activation link |
| | `POST` | `/api/password-reset/` | Request password reset email |
| | `POST` | `/api/password-reset/<user_id>/<password_reset_token>/` | Confirm password reset |
| | `POST` | `/api/logout/` | Logout and blacklist refresh token |
| | `POST` | `/api/token/refresh/` | Obtain new access token using refresh token |
| | `GET` | `/api/profile/<pk>/` | Retrieve user profile |
| | `PUT` | `/api/update-profile/<pk>/` | Update user profile details |
| | `PUT` | `/api/update-password/<pk>/` | Change user password |
| **Products** | `GET` | `/products/` | List products |
| | `POST` | `/products/create/` | Create product record |
| | `GET` | `/products/<slug>/<pk>/` | Get product details |
| | `PUT/DELETE` | `/products/<slug>/<pk>/manage/` | Update or delete product |
| **Materials** | `GET` | `/materials/` | List materials |
| | `POST` | `/materials/create/` | Create material record |
| | `GET` | `/materials/<slug>/<pk>/` | Get material details |
| | `PUT/DELETE` | `/materials/<slug>/<pk>/manage/` | Update or delete material |
| **Cart** | `GET` | `/cart/` | Fetch user active cart items and totals |
| | `POST` | `/cart/add/` | Add product/material variant to cart |
| | `PATCH` | `/cart/<pk>/update/` | Update cart item quantity |
| | `DELETE` | `/cart/<pk>/remove/` | Remove item from cart |
| **Orders & Checkout** | `GET` | `/order/preview/` | Preview order calculations and shipping dates |
| | `POST` | `/order/address/` | Create shipping address |
| | `PUT` | `/order/address/<pk>/` | Update existing address |
| | `POST` | `/order/place_order/` | Convert active cart into an unpaid Order |
| | `GET` | `/order/` | List user order history |
| | `GET` | `/order/<pk>/` | Retrieve single order details |
| **Payments** | `POST` | `/payments/<pk>/initialize/` | Initialize Paystack transaction |
| | `GET` | `/payments/callback/` | Paystack redirect callback listener |
| | `POST` | `/payments/webhook/paystack/` | Paystack webhook event handler |
| | `POST` | `/payments/refund/<order_id>/create/` | Submit refund request for an order |
| | `PATCH` | `/payments/refund/<return_id>/update/` | Admin status review on refund request |
| **Reviews** | `POST` | `/review/<model_name>/<slug>/<pk>/create/` | Create item review (Verified purchase) |
| | `GET` | `/review/<model_name>/<slug>/<pk>/all/` | List item reviews |
| | `PUT` | `/review/<pk>/update/` | Update review comment/rating |
| | `DELETE` | `/review/<pk>/delete/` | Delete review |

---

## Local Setup & Installation

### Prerequisites
* Python 3.12+
* Redis Server (running on `localhost:6379`)

### 1. Clone Repository & Environment Setup
```powershell
git clone <repository_url> Marvelam
cd Marvelam

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Environment Variables Configuration
Create a `.env` file in the root directory (same folder as `manage.py`):

```ini
DEBUG=True
SECRET_KEY=your_django_secret_key

# Database & Domain Configuration
WEBSITE_DOMAIN=http://127.0.0.1:8000/
ALLOWED_HOSTS=127.0.0.1, localhost, *
CSRF_TRUSTED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000

# Social Authentication Keys (Optional)
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY=your_google_client_id
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET=your_google_client_secret
SOCIAL_AUTH_FACEBOOK_KEY=your_facebook_app_id
SOCIAL_AUTH_FACEBOOK_SECRET=your_facebook_app_secret

# Email Configuration (SMTP / SendGrid)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your_sendgrid_api_key
DEFAULT_FROM_EMAIL=your_verified_sender@example.com

# Paystack API Keys
PAYSTACK_SECRET_KEY=sk_test_your_secret_key
PAYSTACK_PUBLIC_KEY=pk_test_your_public_key

# Celery & Redis Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 4. Run Migrations & Setup Admin
Using `update.bat` or standard commands:

```powershell
# Using update.bat
.\update.bat

# Or manually:
python manage.py makemigrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser
```

### 5. Running the Application

#### A. Web Server
```powershell
# Using run.bat
.\run.bat

# Or manually:
python manage.py runserver
```

#### B. Celery Worker (Windows)
```powershell
celery -A MAC worker --loglevel=info -P solo
```

#### C. Celery Beat (Optional, for scheduled tasks)
```powershell
celery -A MAC beat --loglevel=info
```

---

## Code Quality & Linting

The repository uses `pre-commit`, `ruff`, `black`, `isort`, and `flake8` for formatting and code quality checks.

```powershell
# Run code formatting
black .
isort .

# Run lint checks
ruff check .
flake8 .
```
