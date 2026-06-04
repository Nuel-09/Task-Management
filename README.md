# Operations Task Management Component (DevOps phased)

This project implements an **Operations Task Management** component for a larger **Restaurant Management System**.  
The component focuses on operational workflow tracking (task creation, status updates, completion, and filtering) and is intentionally minimal while still large enough to demonstrate DevOps practices:

- Python backend (FastAPI)
- Cloud database integration (MongoDB Atlas)
- Automated tests (pytest)
- CI/CD pipeline (Jenkins)
- Containerization (Docker + Docker Compose)

## Stack

- `FastAPI` + `Uvicorn`
- `Motor` (async MongoDB driver)
- `python-jose` + `passlib` for JWT auth
- `Jinja2` templates for minimal UI
- `pytest` + `httpx` + `mongomock-motor` for tests

## Project Structure

```text
.
├── app/
│   ├── core/security.py
│   ├── config.py
│   ├── database.py
│   ├── main.py
│   ├── models/
│   ├── routers/
│   ├── schemas/
│   ├── static/
│   └── templates/
├── tests/
├── Dockerfile
├── docker-compose.yml
├── Jenkinsfile
├── requirements.txt
└── .env.example
```

## Environment Variables

Copy `.env.example` to `.env` and set your own values:

```env
MONGODB_URI=mongodb+srv://<username>:<password>@cluster0.mongodb.net/todo_management?retryWrites=true&w=majority
MONGODB_DB_NAME=todo_management
SECRET_KEY=replace-with-a-long-random-secret
ACCESS_TOKEN_EXPIRE_MINUTES=60
APP_PORT=8000
```

Notes:

- `.env` is ignored by Git and can safely hold your Atlas key.
- Docker Compose loads the same `.env`, so lecturer testing is straightforward.

## Run Locally (No Docker)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Open:

- `http://localhost:8000` for UI
- `http://localhost:8000/docs` for Swagger API docs

## Run with Docker

```bash
docker compose up --build
```

This starts the FastAPI app in a container and reads Atlas credentials from `.env`.

## API Endpoints

Authentication:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`

Operations Tasks (Todo-based API):

- `GET /api/todos`
- `POST /api/todos`
- `GET /api/todos/{id}`
- `PUT /api/todos/{id}`
- `PATCH /api/todos/{id}/status`
- `DELETE /api/todos/{id}`

## Tests

```bash
pytest tests -v
```

The tests use an in-memory Mongo mock (`mongomock-motor`) and do not need Atlas access.

## Jenkins Pipeline

`Jenkinsfile` now implements a branch-aware CI/CD flow with quality gates and Docker runtime deployment:

1. Checkout
2. Select deployment target by branch
   - `dev` -> deploy `dev` environment (`localhost:8000`)
   - `staging` -> deploy `staging` environment (`localhost:8001`)
   - `main`/`master` -> deploy `prod` environment (`localhost:8002`, with manual approval gate)
3. Install dependencies
4. Syntax check (`python -m compileall`)
5. Tests + coverage gate
   - `pytest` with JUnit XML
   - coverage threshold via `--cov-fail-under`
6. Docker build with commit-tag image
7. Deploy with Docker Compose overlays
8. Smoke tests (`/health` and `/`)
9. Update GitHub deployment status for environment tracking

It supports both Windows (`bat`) and Unix (`sh`) Jenkins agents.

## Docker Environments (Portable Local Setup)

The repository uses one base compose file plus environment overlays:

- `docker-compose.yml` (shared service definition)
- `docker-compose.dev.yml` (`localhost:8000`)
- `docker-compose.staging.yml` (`localhost:8001`)
- `docker-compose.prod.yml` (`localhost:8002`)

Manual commands:

```bash
# dev
docker compose -f docker-compose.yml -f docker-compose.dev.yml --project-name todo-dev up -d --build

# staging
docker compose -f docker-compose.yml -f docker-compose.staging.yml --project-name todo-staging up -d --build

# prod
docker compose -f docker-compose.yml -f docker-compose.prod.yml --project-name todo-prod up -d --build
```

## GitHub Environments Setup (Required for Tracking)

Environments are already provisioned on `Nuel-09/Task-Management`:

- `dev`
- `staging`
- `prod`

Verify anytime:

```powershell
gh auth status
gh api repos/Nuel-09/Task-Management/environments --jq '.environments[].name'
```

The Jenkins pipeline posts deployment statuses to these environments using GitHub Deployment API.

Important: GitHub deployment API requires at least one pushed branch/ref (for example `main`) before Jenkins can report deployment status.

## Jenkins Credentials and Job Setup

Create **two** Jenkins credentials (stored in Jenkins permanently — not in Git).

### 1) GitHub API token

- **Type**: Secret text
- **ID**: `github-api-token` (must match exactly)
- **Value**: GitHub personal access token with repo/deployment permissions

Quick way to reuse your local `gh` login token (PowerShell):

```powershell
gh auth token
```

Paste that value into Jenkins credential `github-api-token`.

### 2) Application `.env` file (Option C — recommended)

Docker Compose needs `MONGODB_URI` and `SECRET_KEY` at deploy time. `.env` is gitignored, so Jenkins must load it from a **Secret file** credential.

**One-time setup in Jenkins UI:**

1. Open Jenkins → **Manage Jenkins** → **Credentials**.
2. Click **System** → **Global credentials (unrestricted)** → **Add Credentials**.
3. Configure:
   - **Kind**: `Secret file`
   - **File**: upload your real `c:\devopsAssignment\.env` (create it from `.env.example` first if needed)
   - **ID**: `todo-app-dotenv` (must match exactly — pipeline uses this ID)
   - **Description**: `Todo app .env for Docker deploy`
4. Click **Create**.

**Required Jenkins plugin:** `Credentials Binding` (usually installed with “Pipeline” / suggested plugins). If the build fails with “file” step unknown, install **Pipeline: Credentials Binding** under **Manage Jenkins → Plugins**.

**What the pipeline does:** on `dev`, `staging`, and `main` builds, stage **Prepare .env from Credentials** copies that secret file into the job workspace as `.env` immediately before Docker deploy. The file is recreated every build, so you do not need to copy `.env` by hand into `C:\Users\emman\.jenkins\workspace\...`.

**Updating secrets later:** edit the credential in Jenkins (upload a new file) — no Git push required.

**Verify after a build:** in the job console you should see:

```text
.env prepared from Jenkins secret file (values are not printed in logs).
```

Do not commit `.env` to GitHub.

Recommended Jenkins job mode:

- Multibranch Pipeline (or branch-aware Pipeline job)
- Triggers on `dev`, `staging`, and `main`
- Docker available on Jenkins agent

The pipeline has parameter `ENABLE_GITHUB_DEPLOYMENTS` (default `true`).
Set to `false` if you want to run locally without GitHub API calls.

## Baseline Git Push (Manual, no bot co-authoring)

This repository was prepared so you can commit and push manually.
Typical first push:

```powershell
git add .
git commit -m "Initial Python task management app with Jenkins and Docker pipeline"
git push -u origin main

git branch dev
git push -u origin dev

git branch staging
git push -u origin staging
```

All commits and pushes should be run by you directly.

After first push, Jenkins GitHub deployment status reporting will work (it needs a real `main` ref).

## One-Command Local Verification

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify_devops_setup.ps1
```

## Lecturer Quick Test Steps

1. Clone/copy project.
2. Add `.env` with valid MongoDB Atlas URI and secret key.
3. Run tests:
   - `python -m pytest tests -v`
4. Run dev environment:
   - `docker compose -f docker-compose.yml -f docker-compose.dev.yml --project-name todo-dev up -d --build`
5. Open `http://localhost:8000`.
6. Register user, login, create/update/toggle/delete todo.
7. Verify health endpoint:
   - `http://localhost:8000/health`

## Evidence Capture Checklist (Assessment)

Capture screenshots/logs for:

1. Successful Jenkins run (all stages green)
2. Failed Jenkins run (deliberately failing test to prove gate)
3. Docker build/deploy success
4. Running containers for env ports `8000`, `8001`, `8002`
5. GitHub Environments deployment history (`dev`, `staging`, `prod`)
6. UI working in browser (`/`, `/register`, `/dashboard`)

## Demo Flow (2-4 minutes)

1. Show architecture briefly (Jenkins + Docker + GitHub environments)
2. Run or show a successful `dev` pipeline
3. Open app on `localhost:8000` and perform task flow
4. Show `staging`/`prod` environment mappings (`8001`/`8002`)
5. Show GitHub Environments deployment statuses
6. Show one failed test example blocking deploy (quality enforcement)

## Component Attribution in Larger System

This module is positioned as one component inside a broader Restaurant Management platform that could also include:

- Menu catalog management
- POS and billing
- Reservations
- Inventory
- Staff scheduling
- Reporting

Within that ecosystem, this component provides the operational task workflow layer used by staff and managers to track day-to-day actions.

## Why Mongo Atlas Instead of Local SQL

- Keeps setup simple for assessment demonstration.
- Avoids heavy SQL schema/integration overhead.
- Shows cloud database integration in a containerized workflow.

