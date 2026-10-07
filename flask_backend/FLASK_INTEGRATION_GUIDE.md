# 🚀 Wingroo Internship Certificate System - Flask Backend Integration Guide

இந்த guide-ல், Django-வில் இருந்த backend-ஐ Flask-க்கு முழுமையாக migrate செய்துள்ளோம். உங்கள் மற்றொரு Flask project-ல் இதை எவ்வாறு include செய்வது அல்லது standalone-ஆக எவ்வாறு run செய்வது என்பது குறித்த முழு விவரங்கள் கீழே கொடுக்கப்பட்டுள்ளன.

---

## 📁 1. Directory Structure

Flask backend structure (`flask_backend/`):

```text
flask_backend/
├── app.py                      # Flask Application Factory & Server Entrypoint
├── config.py                   # Database, JWT, Secret Key, Media Config
├── models.py                   # SQLAlchemy Models (User, StudentProfile, Internship, Certificate)
├── create_admin.py             # Admin User Seed Script
├── requirements.txt            # Python Dependencies
├── routes/
│   ├── auth.py                 # /api/auth/ (register, login, me, logout, refresh)
│   ├── student.py              # /api/student/ (profile, internship, certificate)
│   ├── admin.py                # /api/admin/ (dashboard, students, status, certificate issue/revoke)
│   └── public.py               # /api/public/ (captcha, verify/token, verify/id, download)
└── services/
    ├── auth.py                 # JWT Token creation, @jwt_required, @admin_required decorators
    ├── captcha.py              # 6-Digit Security OTP Generator & HMAC-SHA256 Validator
    ├── pdf.py                  # ReportLab Professional PDF Certificate Generator (Pure Python)
    ├── certificate.py          # Certificate sequence counter & issue logic
    └── storage.py              # Base64 ID Proof / Selfie image decoder & file saver
```

---

## ⚡ 2. Quick Start: Standalone Run

### Step 1: Install Dependencies
```bash
cd flask_backend
pip install -r requirements.txt
```

### Step 2: Create / Verify Admin User
```bash
python create_admin.py admin@wingroo.com Admin@12345 "Wingroo Administrator"
```

### Step 3: Start Flask Server
```bash
python app.py
```
> Flask server default-ஆக `http://127.0.0.1:5000`-ல் இயங்கும்.

---

## 🔗 3. Connecting to Existing MySQL Database

Flask backend-ல் உள்ள `models.py` Django-வின் அதே database table names-ஐ (`accounts_user`, `accounts_studentprofile`, `internships_internship`, `certificates_certificate`) பயன்படுத்துகிறது.

எனவே, நீங்கள் ஏற்கனவே Django-வில் register செய்த மாணவர்கள், admin users மற்றும் certificates-ஐ அப்படியே எவ்வித மாற்றமும் இன்றி Flask-லும் பயன்படுத்த முடியும்:

- **Password Compatibility:** Django பயன்படுத்திய `pbkdf2_sha256$` password hashes-ஐ Flask `User.check_password()` தானாகவே verify செய்யும். Users password reset செய்ய தேவையில்லை!
- **Database Configuration (`config.py`):**
  `backend/.env` அல்லது `flask_backend/.env` file-ல்:
  ```env
  DB_NAME=internship_certificate_db
  DB_USER=wingroo
  DB_PASSWORD=your_password
  DB_HOST=127.0.0.1
  DB_PORT=3306
  SECRET_KEY=your_secret_key
  ```

---

## 🧩 4. Integrating into Your Existing Flask Project

உங்களிடம் ஏற்கனவே ஒரு Flask Web App (`my_flask_project/`) இருந்தால், அதை எளிதாக integrate செய்ய:

1. **Copy Folders:**
   `routes/` மற்றும் `services/` folder-களை உங்கள் Flask project-க்குள் copy செய்யவும்.
2. **Register Blueprints in your `app.py`:**
   ```python
   from routes.auth import auth_bp
   from routes.student import student_bp
   from routes.admin import admin_bp
   from routes.public import public_bp

   app.register_blueprint(auth_bp)
   app.register_blueprint(student_bp)
   app.register_blueprint(admin_bp)
   app.register_blueprint(public_bp)
   ```
3. **Database Setup:**
   உங்கள் existing `db = SQLAlchemy()` object-ஐ `models.py`-க்கு pass செய்யவும் அல்லது `flask_backend/models.py`-ல் உள்ள classes-ஐ import செய்து `db.create_all()` run செய்யவும்.

---

## 🌐 5. Connecting the React/Vite Frontend to Flask

Frontend-ல் API base URL-ஐ Flask port-க்கு (Default `5000`) மாற்ற:

File: `frontend/src/services/api.js`
```javascript
// Before (Django):
const API_BASE = 'http://127.0.0.1:8001/api';

// After (Flask):
const API_BASE = 'http://127.0.0.1:5000/api';
```
அல்லது `.env` file-ல்:
```env
VITE_API_BASE_URL=http://127.0.0.1:5000/api
```

---

## 📋 6. API Endpoints Reference (100% Django Parity)

| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/api/auth/register/` | POST | Public | Student Registration (with selfie & ID proof) |
| `/api/auth/login/` | POST | Public | Email & Password Login (JWT) |
| `/api/auth/me/` | GET | Token | Current logged-in user profile |
| `/api/auth/token/refresh/` | POST | Public | Refresh expired JWT access token |
| `/api/auth/logout/` | POST | Token | Logout session |
| `/api/student/profile/` | GET | Student | Student details & documents |
| `/api/student/internship/` | GET | Student | Current internship progress |
| `/api/student/certificate/` | GET | Student | Download/View issued certificate |
| `/api/admin/dashboard/` | GET | Admin | Stats: counts, recent registrations |
| `/api/admin/students/` | GET | Admin | Filter students by type & status |
| `/api/admin/students/<id>/` | GET | Admin | View student docs (Selfie, ID) |
| `/api/admin/internships/<id>/status/` | PATCH | Admin | Update status (APPROVED / REJECTED) |
| `/api/admin/internships/<id>/end-date/` | PATCH | Admin | Set completion end date |
| `/api/admin/certificates/` | GET | Admin | List of all certificates |
| `/api/admin/certificates/preview/<id>/` | GET | Admin | Preview certificate before generation |
| `/api/admin/certificates/generate/<id>/` | POST | Admin | Generate ReportLab PDF & Issue Certificate |
| `/api/admin/certificates/<id>/revoke/` | PATCH | Admin | Revoke certificate |
| `/api/certificates/<id>/download/` | GET | Auth | Download Certificate PDF |
| `/api/public/captcha/` | GET | Public | 6-digit Security OTP code generator |
| `/api/public/verify/token/<token>/` | GET/POST| Public | Verify Certificate by QR Token + OTP |
| `/api/public/verify/id/<id>/` | GET/POST| Public | Verify Certificate by ID (INT-YYYY-XXXXX) + OTP |
