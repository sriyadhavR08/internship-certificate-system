# This workspace's local development environment

The implementation was tested with an isolated MySQL 8.0.43 instance bound to `127.0.0.1:3307`. Its files are in the task's `work/mysql-data` directory. The pre-existing MySQL service on port 3306 and its credentials were not modified.

The ignored `backend/.env` is already configured with a generated application secret and generated MySQL application password. This file is excluded from the source archive. Database administrator credentials for the isolated instance are private in `work/mysql-root-password.txt`; they are not part of the source project or README.

From this project root, restart the isolated database after a reboot:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Start-LocalDatabase.ps1
```

Then run the backend in one terminal:

```powershell
Set-Location backend
.\venv\Scripts\python.exe manage.py createsuperuser
.\venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Create your admin once; subsequent runs only need `runserver`. Use a second terminal for the frontend:

```powershell
Set-Location frontend
npm.cmd run dev
```

The app and database were started during verification. If those processes are still running, use the existing local URLs instead of starting duplicate servers. Terminal logs are in the task's `work` directory.

The full browser test creates synthetic QA accounts and a revoked certificate. Those records are retained as development-only evidence; they are not real internship credentials. Create a new database for real records, using the README's normal port-3306 setup. The temporary QA administrator is deactivated after verification. There is no shared default admin password.

When moving the source ZIP to another folder/computer, follow the normal README setup: the archive deliberately excludes virtual environments, node_modules, private .env files, database files, private PDFs, and test credentials.
