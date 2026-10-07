# Wingroo Digital Internship Certificate Management System

A working React/Vite/Bootstrap portal backed by Django REST Framework, MySQL, JWT authentication, ReportLab PDFs, and QR verification. The original Wingroo logo and certificate reference are retained in `assets/`; the supplied master specification is in `docs/master-specification.txt`.

## Features

- Student registration with personal, academic, internship, and password validation.
- Email login, role-based navigation, JWT refresh rotation, and logout with refresh-token revocation.
- Student dashboard showing internship progress, private certificate preview/download, and verification.
- Admin dashboard, searchable/paginated student and certificate lists, date/project/status filters, and student corrections before issuance.
- Strict Registered → In Progress → Completed → Certificate Issued workflow. No automatic completion or issuance. Completion cannot precede the end date.
- Watermarked PDF preview without database side effects; explicit confirmation before final generation.
- Server-controlled issue date, sequential `INT-YYYY-XXXXX` IDs, random verification tokens, and QR URLs configured through the environment.
- A4 certificate matching the reference's margins, serif typography, heading, date/location, and director section, with dynamic gender wording and project details.
- Public verification by ID or QR token, plus camera scanning with permission/error handling. Public results never expose contact data or PDF URLs.
- Revocation immediately changes public verification and blocks further downloads. Previously downloaded PDFs must be checked using their QR.
- Transactional issuance, row locks, unique constraints, rollback cleanup, and immutable issued snapshots.
- Django Admin inspection and React Admin business workflows.

## Prerequisites

- Windows PowerShell, Python 3.12 or 3.13, Node.js 22.12+ (Node 24 is supported), npm, and MySQL 8.0.11+.
- Google Chrome for the included Playwright browser tests, or configure another installed Playwright browser.
- The setup was tested here with Python 3.13, Node 24, and MySQL 8.0.43.

## Project structure

```text
internship-certificate-system/
  assets/                         Original logo and certificate reference
  backend/
    accounts/                     Custom email user, profiles, auth/admin APIs, tests
    internships/                  Internship model and migrations
    certificates/                 Models, content, layout, issuance services, APIs
    certificate_system/           Settings, URLs, WSGI/ASGI, isolated test settings
    requirements.txt              Dependency ranges
    requirements.lock.txt         Exact verified dependency versions
    manage.py
    .env.example
  frontend/
    src/components/               Shared fields, notices, scanner, certificate actions
    src/context/                  Authentication state
    src/layouts/                  Public/student header and admin sidebar
    src/pages/                    Public, student, and admin screens
    src/services/                 Axios, refresh logic, secure downloads
    src/utils/                    QR URL validation
    tests/                        Playwright browser workflow
  docs/                           Master specification, architecture, QA evidence
  scripts/                        Local convenience scripts
```

## Exact Windows setup

Open PowerShell at the project folder. For this workspace:

```powershell
Set-Location 'C:\Users\kaviy\Documents\Codex\2026-10-03\referenced-chatgpt-conversation-this-is-an\outputs\internship-certificate-system'
```

### 1. Create a MySQL database and application user

The existing MySQL service on this computer requires its own administrator password. Use that password at the prompt; do not paste it into source code.

```powershell
mysql -u root -p
```

Run inside the MySQL prompt (replace the example password):

```sql
CREATE DATABASE internship_certificate_db
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'wingroo'@'localhost' IDENTIFIED BY 'REPLACE_WITH_A_STRONG_LOCAL_PASSWORD';
GRANT ALL PRIVILEGES ON internship_certificate_db.* TO 'wingroo'@'localhost';
-- Needed only when running the MySQL test suite:
GRANT ALL PRIVILEGES ON test_internship_certificate_db.* TO 'wingroo'@'localhost';
EXIT;
```

If MySQL is not in PATH, invoke it with:

```powershell
& 'C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe' -u root -p
```

### 2. Backend setup

```powershell
Set-Location backend
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.lock.txt
Copy-Item .env.example .env
notepad .env
```

Set a new `DJANGO_SECRET_KEY`, the database password, and the matching database host/port in `.env`. Generate a random application secret using:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Do not overwrite the already configured `.env` if using this workspace's running isolated development instance. That instance uses **127.0.0.1:3307** with generated credentials; the normal setup example uses port **3306**. No existing MySQL service or root password was changed. See `docs/local-environment.md` for restarting the isolated instance.

```powershell
python manage.py migrate
python manage.py check
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

`createsuperuser` prompts for your email, full name, and password and automatically assigns `role=ADMIN`. There is no public admin registration or built-in admin password. Sign into either the React login page or Django Admin using this account.

Committed migrations are ready to run. For model changes, use `python manage.py makemigrations` before `migrate`.

If activation is blocked, avoid changing your machine execution policy by invoking the virtual environment directly:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.lock.txt
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py createsuperuser
.\venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Alternatively, `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` affects only the current PowerShell session.

### 3. Frontend setup — second terminal

From the project root:

```powershell
Set-Location frontend
Copy-Item .env.example .env
npm.cmd ci
npm.cmd run dev
```

Using `npm.cmd` avoids PowerShell's script execution policy restriction on `npm.ps1`.

- Frontend: http://localhost:5173
- API base: http://127.0.0.1:8000/api
- Django Admin: http://127.0.0.1:8000/admin/
- Public verification: http://localhost:5173/verify

The backend root `/` is not a separate landing page; use `/api/...` or `/admin/`.

## Environment variables

| Variable | Purpose |
|---|---|
| `DJANGO_SECRET_KEY` | Required long random Django/JWT signing secret |
| `DJANGO_DEBUG` | `True` locally; `False` in production |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated backend hostnames |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | MySQL connection settings |
| `FRONTEND_BASE_URL` | Public portal origin embedded in newly issued QR codes |
| `CORS_ALLOWED_ORIGINS` | Explicit allowed frontend origins, comma-separated |
| `VITE_API_BASE_URL` | Frontend API URL; contains no private secrets |

Use the canonical frontend origin consistently. The scanner accepts only verification links from the current portal origin. Changing the frontend origin does not rewrite QR codes in previously issued PDFs; preserve redirects from the old host.

## Daily workflow

1. Student registers. The internship remains Registered and has no certificate.
2. Admin signs in, opens Students, searches for the student, and selects View / Review.
3. Admin checks or edits the details, marks In Progress, then marks Completed after the end date.
4. Admin opens Preview Certificate, reviews the actual PDF, and selects Generate Final Certificate. The confirmation dialog is the final issuance step.
5. Student signs in and can view/download the issued PDF. The QR and visible ID lead to public verification.
6. Admin can revoke an issued certificate from Certificates after confirmation. Public verification then shows Revoked.

Internship length uses **inclusive calendar months**: September 1–September 30 is one month, and September 1–November 30 is three months. Invalid ranges are rejected on the backend.

Issued details are locked in the portal, including after revocation. Reissue/replacement is a future workflow; it is not silently implemented as overwriting a certificate. A certificate snapshot ensures public verification remains consistent with the original PDF even if an operator changes a user record through Django Admin.

## Certificate implementation

- `certificates/content.py` turns a snapshot into escaped, gender-aware wording.
- `certificates/layout.py` renders a single real PDF page with ReportLab. The reference is A4, one-inch margins, 16 pt heading and 14 pt body. Long content reduces the body to at least 12 pt; text that cannot fit is rejected instead of clipped.
- `certificates/services.py` controls transactions, per-internship locking, the yearly sequence, token generation, FileField storage, and state transitions.
- `BOND_SHEET_PRINT` is a layout mode that omits the logo. Physical printer offsets and preprinted-sheet calibration remain a future task; no unverified printer alignment is claimed.
- No signature image was supplied, so the director name and title are printed with an empty signing area. This is a QR-verifiable PDF, not a cryptographically signed PDF.
- The built-in Times font supports Western characters. For broader scripts, provide a licensed font and shaping-aware layout before issuing certificates in those scripts.

## Checks

Backend, from `backend/`:

```powershell
.\venv\Scripts\python.exe manage.py check
.\venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\venv\Scripts\python.exe manage.py test --noinput
```

The normal tests use MySQL and a separate `test_internship_certificate_db`, including a simultaneous-issuance test. To run most functional tests without a MySQL server:

```powershell
.\venv\Scripts\python.exe manage.py test --settings=certificate_system.test_settings --noinput
```

SQLite is used only by this explicit test settings module; the application defaults to MySQL. The row-lock concurrency test is skipped on SQLite.

Frontend, from `frontend/`:

```powershell
npm.cmd run lint
npm.cmd run build
npm.cmd test
```

Run both servers before browser tests. Public and QR-parser tests need no credentials. The full workflow needs a dedicated development administrator. Put its email/password in `work/browser-credentials.json` outside the source project and set the directory:

```powershell
$env:WINGROO_QA_DIR = 'C:\path\to\private\work'
npm.cmd test
```

JSON shape: `{"email":"your-qa-admin@example.test","password":"your-private-test-password"}`. Without that file the admin workflow test is explicitly skipped. The full test creates synthetic students and a revoked certificate in the development database; never run it against production. The test saves downloaded PDFs privately in that work directory. Browser screenshots are in `docs/qa/`.

## Security and deployment notes

- Backend permissions are the security boundary. Students cannot fetch other students' PDFs or invoke admin endpoints.
- PDFs are not exposed through Django's media URL; serve them only through authenticated API endpoints. Do not configure the web server to publish the private media directory.
- Access and refresh tokens are stored in tab-scoped `sessionStorage`, not permanently in localStorage. Protect the frontend from injected scripts. Logout blacklists the refresh token; previously issued access tokens expire within 10 minutes.
- Register/login and public endpoints have throttles. The default development cache is per process. Use a shared cache/reverse-proxy rate limiter for multiworker production.
- Production needs HTTPS, a production WSGI/ASGI server, explicit host/origin settings, protected persistent storage, backups, and SPA route fallback to `index.html`. Run `collectstatic` for Django Admin assets.
- Camera access requires HTTPS, except on localhost. A phone cannot reach this PC through the phone's own `localhost`; use a reachable HTTPS deployment and set `FRONTEND_BASE_URL` accordingly before issuance.
- IDs are intentionally searchable publicly as required. Verification exposes only the approved certificate fields; tokens are random but are not substitutes for download authorization.

## Troubleshooting

- **MySQL access denied:** check `.env` credentials/port and grants. The standard server is port 3306; this workspace's isolated server is 3307.
- **Cannot connect to database:** start MySQL first. For the isolated instance use `scripts/Start-LocalDatabase.ps1`.
- **CORS/network error:** confirm backend is running, `VITE_API_BASE_URL` is correct, and the exact browser origin is in `CORS_ALLOWED_ORIGINS`.
- **429 Too Many Requests:** wait for the stated throttle window. This can happen after repeated login attempts.
- **No admin access:** create an account with `createsuperuser`; public registration always creates students.
- **Certificate generation disabled:** progress through In Progress and Completed first, and preview before final generation.
- **Camera unavailable:** grant permission or enter the certificate ID manually.
- **PDF does not open inline on mobile:** use Download Certificate and the device's PDF viewer.
- **Port already in use:** use the running instance or stop that development server before starting another; Vite deliberately uses strict port 5173.

See `docs/architecture.md` and `docs/verification-report.md` for API routes, design choices, and the actual verification results.
