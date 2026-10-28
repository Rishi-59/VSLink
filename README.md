# VSLink

VSLink is a customer loyalty and referral management prototype developed for VS Software Lab. Customers can register, browse products, complete simulated purchases, earn loyalty and referral points, and redeem eligible rewards for discounts.

The application is built with Django and uses SQLite for local development. Staff manage products, rewards, and referral settings through custom pages rather than the Django Admin site.

## Features

### Customer accounts
- Customer registration and login using Django authentication.
- Automatically generated unique referral codes.
- Optional referral codes during registration, with server-side validation.
- Referral relationships that cannot be changed after registration.
- Customer dashboard with points balance, purchase activity, and recent transactions.

### Products and purchases
- Product catalogue containing active products and their prices.
- Simulated checkout without a real payment gateway.
- Purchase records that preserve product name, original price, final price, discount, and points earned at checkout.
- Duplicate checkout submission protection.
- Purchase history and points transaction history.

### Loyalty and referral points
- Points awarded according to each product's configuration.
- Direct and second-level referral bonuses.
- Configurable referral bonus percentages.
- A points transaction ledger used to calculate customer balances.
- Referral hierarchy and tree visualisation.

### Rewards
- Fixed INR discounts.
- Percentage discounts with a maximum discount cap.
- Reward activation and deactivation.
- Server-side validation of reward eligibility and available points.
- One reward per purchase, with redemption associated with the purchase.
- Point deductions recorded in the transaction ledger.

### Custom staff workspace
- Create, edit, activate, and deactivate products.
- Configure product prices and points awarded.
- Create, edit, activate, and deactivate rewards.
- Configure direct and second-level referral bonus percentages.
- Inspect customer referral trees through the custom interface.

Staff permissions are checked in the server-side views. The built-in Django Admin website is not used as the application's management interface.

## Technology stack

- **Language:** Python 3.12 or later
- **Framework:** Django
- **Database:** SQLite
- **Frontend:** HTML, CSS, Bootstrap 5
- **Icons:** Bootstrap Icons
- **Typography:** Inter
- **Dependency management:** `uv`
- **Configuration:** `.env` files loaded using `python-dotenv`
- **Authentication:** Django's built-in authentication system

## Prerequisites

Install the following before setting up the project:

- Python 3.12 or later
- `uv`
- Git

## Local setup

### 1. Clone the repository

```bash
git clone https://github.com/Rishi-59/VSLink.git
cd VSLink
```

### 2. Install dependencies

```bash
uv sync
```

This installs the project's dependencies using `uv` and the lockfile.

### 3. Configure environment variables

Create your local environment file from the example:

```bash
cp .env.example .env
```

Generate a secure Django secret key:

```bash
uv run python -c "import secrets; print(secrets.token_urlsafe(50))"
```

Copy the generated value into `.env`, replacing the placeholder secret key.

Your local `.env` should contain:

```dotenv
DJANGO_SECRET_KEY=replace-with-your-generated-secret-key
DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
```

Replace the placeholder with the actual key you generated before starting Django.

The application loads `.env` automatically through `python-dotenv`. You do not need to export these variables manually for ordinary local development.

**Security notes:**
- Never commit your actual `.env` file.
- `.env.example` contains placeholders only and is safe to commit.
- Never expose your Django secret key publicly.
- Before a production deployment, set `DJANGO_DEBUG=false`, use a strong secret key, configure the actual allowed hostnames, and follow Django's deployment security checklist.

### 4. Apply database migrations

```bash
uv run python manage.py migrate
```

This creates the required database tables in the local SQLite database.

### 5. Create a staff account

```bash
uv run python manage.py createsuperuser
```

Follow the prompts to create an account. Django's superuser account has staff privileges, which allow access to the application's custom staff workspace.

The project does not use the Django Admin website for its management interface.

### 6. Start the development server

```bash
uv run python manage.py runserver
```

Open the application in your browser:

http://127.0.0.1:8000/

## Main application routes

| Route | Purpose |
|---|---|
| `/` | Home page |
| `/accounts/register/` | Customer registration |
| `/accounts/login/` | Customer login |
| `/accounts/logout/` | Customer logout |
| `/accounts/profile/` | Customer dashboard |
| `/accounts/referrals/` | Referral hierarchy |
| `/loyalty/products/` | Product catalogue |
| `/loyalty/purchases/` | Purchase and points history |
| `/loyalty/staff/products/` | Staff product management |
| `/loyalty/staff/rewards/` | Staff reward management |
| `/loyalty/staff/referral-config/` | Referral bonus configuration |

Some pages require an authenticated customer or a staff account.

## Running tests

Run the complete automated test suite:

```bash
uv run python manage.py test
```

Run the Django system check:

```bash
uv run python manage.py check
```

The test suite covers registration and referral validation, referral integrity, duplicate checkout protection, reward redemption, referral bonus calculations, and staff access restrictions.

## Environment configuration reference

| Variable | Purpose | Local development default |
|---|---|---|
| `DJANGO_SECRET_KEY` | Django's secret key | Must be configured in `.env` |
| `DJANGO_DEBUG` | Enables or disables debug mode | `true` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated allowed hostnames | `localhost,127.0.0.1` |

The secret key is required. Debug mode and allowed hosts are read from the environment, with the local defaults shown above when those variables are omitted.

For deployment, use a secure secret and configure hostnames appropriate to the target environment. Do not use the local development configuration as a production security configuration.

## Project structure

```text
VSLink/
├── accounts/          # Registration, profiles, and referrals
├── config/            # Django settings and URL configuration
├── docs/              # Requirements and design documentation
├── loyalty/           # Products, checkout, rewards, and points
├── static/            # CSS and other static assets
├── templates/         # Shared and application templates
├── .env.example       # Safe environment configuration template
├── .gitignore
├── manage.py
├── pyproject.toml
├── requirements.txt
└── uv.lock
```

The project also contains application migrations and automated tests within the respective Django apps.

## Project documentation

Refer to the `docs/` directory for the requirements and design documentation.

In particular, `docs/REQUIREMENTS-FREEZE.md` defines the agreed scope, business rules, integrity requirements, and acceptance criteria for the prototype.

## Scope limitations

VSLink is a prototype. Checkout simulates a successful purchase; it does not collect payments or integrate with a live ordering or fulfilment system.

A production deployment, external order fulfilment, payment gateway integration, and integration with VS Software Lab's live systems are outside the initial prototype scope.