# Lagniappe Sign-Up

Lagniappe Sign-Up is an existing web application enhanced for the CSCE 553 M1 baseline. It allows users in the Acadiana area to create events, browse and search events, register for events, manage their registrations, and provide feedback.

This is a class demonstration application, not a production service. All demo users, events, and other records are fake and must not contain real personal information.

## Live application

* Application: https://csce-553-team.onrender.com/
* Health endpoint: https://csce-553-team.onrender.com/health/
* GitHub: https://github.com/Tyler-Van-Beek/CSCE-553-Team

Render’s free tier may put the application to sleep after inactivity. The first request can take approximately one minute while the service starts.

The Supabase free-tier database can also be paused after extended inactivity. Resume the project from the Supabase dashboard if the database is unavailable.

## Architecture

```text
Browser UI ──────────────┐
                         ├──> Render / Django ───> Supabase PostgreSQL
Postman, curl, scripts ──┘          │
                                    └──> Optional OpenAI/Pinecone integration
```

The application provides two interfaces:

* Server-rendered Django HTML pages using session authentication.
* Django REST Framework JSON APIs using token authentication.

Both interfaces share the same Django models and PostgreSQL database.

## Technology stack

* Python
* Django 5.1.6
* Django REST Framework
* PostgreSQL hosted by Supabase
* Render
* Gunicorn
* HTML, CSS, and JavaScript
* Optional OpenAI and Pinecone integration

## Demo accounts

Run the seed command before using these accounts:

```powershell
python manage.py seed_demo_data
```

| Email                    | Password        | Name       |
| ------------------------ | --------------- | ---------- |
| `alex.demo@example.com`  | `ClassDemo123!` | Alex Demo  |
| `blair.demo@example.com` | `ClassDemo123!` | Blair Demo |
| `casey.demo@example.com` | `ClassDemo123!` | Casey Demo |

The seed command is idempotent. Running it repeatedly reuses the same demo users, categories, and events instead of creating duplicates.

## Local setup

Clone the repository and enter the Django project directory:

```powershell
git clone https://github.com/Tyler-Van-Beek/CSCE-553-Team.git
cd CSCE-553-Team\lagniappe_signup
```

Create and activate a virtual environment:

```powershell
python -m venv env
.\env\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env`:

```powershell
Copy-Item .env.example .env
```

Configure the following variables in the local `.env` file:

```text
DJANGO_SECRET_KEY
DJANGO_DEBUG
DJANGO_ALLOWED_HOSTS
DJANGO_CSRF_TRUSTED_ORIGINS
DATABASE_URL
PINECONE_API_KEY
OPENAI_API_KEY
```

Do not commit `.env` or paste secret values into the README.

Apply migrations, seed demo data, and start the server:

```powershell
python manage.py migrate
python manage.py seed_demo_data
python manage.py check
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

## Automated tests

Run:

```powershell
python manage.py test -v 2
```

The test suite covers:

* Health endpoint
* API registration, login, authenticated user, and logout
* Event creation, listing, searching, retrieval, and update
* Event ownership authorization
* Idempotent demo-data seeding
* Event registration creation, listing, duplicate prevention, ownership, and cancellation

## REST API

Protected endpoints require this header:

```text
Authorization: Token <token>
```

| Method | Endpoint                               | Authentication      | Purpose                                |
| ------ | -------------------------------------- | ------------------- | -------------------------------------- |
| GET    | `/health/`                             | No                  | Application health                     |
| POST   | `/api/auth/register`                   | No                  | Create a user                          |
| POST   | `/api/auth/login`                      | No                  | Log in and receive a token             |
| GET    | `/api/auth/me`                         | Token               | Return the authenticated user          |
| POST   | `/api/auth/logout`                     | Token               | Revoke the current token               |
| GET    | `/api/events`                          | Token               | List events                            |
| GET    | `/api/events?q=<term>`                 | Token               | Search events                          |
| POST   | `/api/events`                          | Token               | Create an event                        |
| GET    | `/api/events/<event_id>`               | Token               | Retrieve an event                      |
| PATCH  | `/api/events/<event_id>`               | Token and ownership | Update an event                        |
| GET    | `/api/registrations`                   | Token               | List the current user’s registrations  |
| POST   | `/api/registrations`                   | Token               | Register the current user for an event |
| DELETE | `/api/registrations/<registration_id>` | Token and ownership | Cancel a registration                  |

An organizer can update only their own events. A user can cancel only their own registrations. Duplicate registrations return HTTP `409 Conflict`.

## Hosted PowerShell curl examples

Set the hosted URL:

```powershell
$BASE = "https://csce-553-team.onrender.com"
```

Health check:

```powershell
curl.exe -i "$BASE/health/"
```

Create a JSON login file:

```powershell
$loginJson = @{
    email = "alex.demo@example.com"
    password = "ClassDemo123!"
} | ConvertTo-Json -Compress

[System.IO.File]::WriteAllText(
    "$PWD\login.json",
    $loginJson
)
```

Log in and save the temporary token:

```powershell
$loginResponse = curl.exe -sS -X POST "$BASE/api/auth/login" `
    -H "Content-Type: application/json" `
    --data-binary "@login.json"

$TOKEN = ($loginResponse | ConvertFrom-Json).token
Write-Host "Token received:" ([bool]$TOKEN)
```

Get the authenticated user:

```powershell
curl.exe -i "$BASE/api/auth/me" `
    -H "Authorization: Token $TOKEN"
```

List events:

```powershell
curl.exe -i "$BASE/api/events" `
    -H "Authorization: Token $TOKEN"
```

Search events:

```powershell
curl.exe -i "$BASE/api/events?q=workshop" `
    -H "Authorization: Token $TOKEN"
```

Register for an event:

```powershell
$registrationJson = @{
    EventID = 1
} | ConvertTo-Json -Compress

[System.IO.File]::WriteAllText(
    "$PWD\registration.json",
    $registrationJson
)

curl.exe -i -X POST "$BASE/api/registrations" `
    -H "Authorization: Token $TOKEN" `
    -H "Content-Type: application/json" `
    --data-binary "@registration.json"
```

List the authenticated user’s registrations:

```powershell
curl.exe -i "$BASE/api/registrations" `
    -H "Authorization: Token $TOKEN"
```

Log out and revoke the token:

```powershell
curl.exe -i -X POST "$BASE/api/auth/logout" `
    -H "Authorization: Token $TOKEN"
```

Delete temporary local request files:

```powershell
Remove-Item login.json, registration.json -ErrorAction SilentlyContinue
```

## Browser routes

| Method   | Route                       | Purpose                    |
| -------- | --------------------------- | -------------------------- |
| GET      | `/`                         | Homepage                   |
| GET/POST | `/signup/`                  | Create a browser account   |
| GET/POST | `/signin/`                  | Browser session login      |
| GET      | `/signout/`                 | Browser logout             |
| GET      | `/event/list`               | List events                |
| GET      | `/event/create`             | Display the event form     |
| POST     | `/event/event-list/`        | Submit an event            |
| GET      | `/event/<id>`               | Event details              |
| GET/POST | `/event/update/<id>`        | Update an event            |
| POST     | `/registration/create/<id>` | Register for an event      |
| POST     | `/registration/delete/<id>` | Cancel a registration      |
| GET      | `/map/`                     | Event map                  |
| GET      | `/faq/`                     | Frequently asked questions |

## Environment and security

Secrets and database credentials are loaded from environment variables. The repository must not contain:

* `.env`
* Database passwords
* Django secret keys
* OpenAI or Pinecone keys
* Local SQLite database files

Before deploying, configure the required environment variables in Render. If a credential is accidentally committed, rotate it immediately because deleting it from the latest file does not remove it from Git history.
