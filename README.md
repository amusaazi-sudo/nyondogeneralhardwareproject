# Nyondo General Hardware Management System

A Django web application for managing day-to-day operations at Nyondo General Hardware. It brings inventory, sales, customer accounts, supplier purchases, deposits, receipts, and business reports into one system.

## Live demo

**[Open the app](https://nyondogeneralhardwareproject-1.onrender.com)**

Log in with the demo account:
- **Username:** `demo`
- **Password:** `Nyondo2026`

The app runs on Render's free plan, so the first visit may take up to a minute while it wakes up. Demo data resets regularly.

## Features

- **Inventory:** maintain stock quantities, product specifications, buying prices, and selling prices.
- **Sales:** record sales, track payment methods and delivery, adjust sales, and issue receipts.
- **Customers:** keep customer contact details and view purchase and payment activity.
- **Deposit scheme:** record customer deposits and installments, follow balances, and issue payment receipts.
- **Suppliers:** record supply orders, track supplier payments and balances, and view supplier receipts and reports.
- **Dashboards and reports:** review sales and stock summaries; access to reports is restricted to administrators.
- **Role-based access:** separate permissions for administrators, stock managers, and sales managers.

## Technology

- Python and Django 6
- SQLite by default; PostgreSQL can be used through `DATABASE_URL`
- Gunicorn and WhiteNoise for deployment
- Server-rendered Django templates

## Requirements

- Python 3.12 or newer (Django 6 requires a supported modern Python version)
- `pip`

## Run locally

From the repository root, open a terminal and run:

```bash
python -m venv .venv
```

Activate the virtual environment:

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
source .venv/bin/activate
```

Install dependencies and initialize the database:

```bash
pip install -r requirements.txt
cd nyondogeneralhardware
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open <http://127.0.0.1:8000/> and sign in. The Django admin is at <http://127.0.0.1:8000/admin/>.

The project uses SQLite by default and creates `db.sqlite3` in the `nyondogeneralhardware` directory. To use PostgreSQL or another supported database URL, set `DATABASE_URL` before starting Django; the application reads this setting through `dj-database-url`.

## User roles

The application recognizes Django groups named exactly:

- `admin` — full access, including dashboards and reports.
- `stock_manager` — inventory and supplier management, plus sales and customer/deposit pages.
- `sales_manager` — sales and customer/deposit pages.

Create these groups and assign users in Django admin (`/admin/`). Users must belong to one of these groups to sign in. A Django superuser has administrator access.

## Configuration and deployment

The settings support these environment variables:

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | Django secret key. Set a unique, private value for deployment. |
| `DEBUG` | Enables Django debug mode when set to `true`; defaults to `true` for local development. Set to `false` in production. |
| `DATABASE_URL` | Optional database connection URL. If omitted, SQLite is used. |

The project includes Gunicorn and WhiteNoise for serving the application and static files. For a production deployment, configure a secure `SECRET_KEY`, set `DEBUG=false`, set `DATABASE_URL` to a persistent database, run migrations, and collect static files:

```bash
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn nyondogeneralhardware.wsgi:application
```

The current settings allow localhost, `127.0.0.1`, and Render subdomains in `ALLOWED_HOSTS`. Update `ALLOWED_HOSTS` in `nyondogeneralhardware/nyondogeneralhardware/settings.py` if deploying on another host.

## Project layout

```text
nyondogeneralhardware/       Django project directory
├── manage.py                Django management commands
├── nyondogeneralhardware/   Project settings and URL configuration
└── nyondo/                  Business app: models, views, migrations, templates
requirements.txt             Python dependencies
```

## License

No license file is currently included in this repository. Contact the project owner for reuse and distribution terms.
