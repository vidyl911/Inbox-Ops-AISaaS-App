# InboxOps

**AI-powered email automation for business operations.**

InboxOps is a SaaS project designed to turn email data into structured, actionable business workflows. It aims to help small businesses reduce repetitive administrative work by connecting email accounts to automated processing pipelines and AI-powered capabilities.

## Features

- **Gmail Integration:** OAuth 2.0 authentication for connecting Gmail accounts.
- **Secure Credential Storage:** Encrypts stored OAuth credentials before saving them to the database.
- **REST API:** FastAPI-powered endpoints for managing email accounts and workflow operations.
- **Database & Migrations:** PostgreSQL, SQLAlchemy ORM, and Alembic schema migrations.
- **Workflow Foundation:** Data models for organizations, workflows, and workflow executions.
- **AI Integration Roadmap:** Foundation for incorporating LLM-powered email understanding and workflow automation.

## Tech Stack

| Component | Technology |
|---|---|
| Backend | Python, FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Email Integration | Gmail API |
| Authentication | Google OAuth 2.0 |
| Credential Encryption | Fernet |
| API Documentation | OpenAPI / Swagger UI |

## Architecture

```text
Gmail Account
     |
     v
Google OAuth 2.0
     |
     v
InboxOps API (FastAPI)
     |
     v
Credential Encryption
     |
     v
PostgreSQL
     |
     v
Workflow Execution
     |
     v
AI-Powered Processing (Planned)
```

## Getting Started

### Prerequisites

- Python 3.11
- PostgreSQL
- A Google Cloud project with the Gmail API enabled
- Google OAuth 2.0 credentials

### 1. Clone the repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd InboxOps_SaaS_App
```

### 2. Create and activate a virtual environment

```powershell
py -3.11 -m venv backend/.venv
.\backend\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

Install the project's backend dependencies using its dependency file, if present. If dependency management has not yet been configured, add a `requirements.txt` before publishing setup instructions.

### 4. Configure environment variables

Create `backend/.env` locally. Configure the required database connection, Google OAuth client credentials, redirect URI, and token encryption key.

Never commit `.env` files, OAuth client secrets, encryption keys, or access tokens.

### 5. Run database migrations

From the repository root, activate the virtual environment and run:

```powershell
$env:PYTHONPATH = "$PWD\backend"
alembic -c backend/alembic.ini upgrade head
Remove-Item Env:PYTHONPATH
```

Confirm that the Alembic configuration and database URL are correctly configured for your local environment before running migrations.

### 6. Start the backend

If the repository includes `start-backend.ps1`, run:

```powershell
.\start-backend.ps1
```

Open the interactive API documentation at:

`http://127.0.0.1:8000/docs`

## Security Notes

- OAuth credentials are encrypted before database storage.
- Gmail access currently uses the read-only scope.
- Keep all secrets in local environment variables, not in source control.
- The current development configuration is not, by itself, production-ready. Tenant authorization, deployment security, and Google OAuth production requirements must be addressed before serving customers.

## Project Status

**In development.** The current focus is establishing the backend, database schema, Gmail OAuth connection flow, and secure credential storage. Broader AI-powered processing and workflow automation are planned.

## License

The project's licensing terms will be specified in the `LICENSE` file.