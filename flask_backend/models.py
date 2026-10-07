import secrets
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


def utcnow():
    return datetime.now(timezone.utc)


def generate_verification_token():
    return secrets.token_urlsafe(32)


class User(db.Model):
    __tablename__ = "accounts_user"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(254), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(10), default="STUDENT", nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    is_staff = db.Column(db.Boolean, default=False)
    is_superuser = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime, nullable=True)
    date_joined = db.Column(db.DateTime, default=utcnow)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    profile = db.relationship("StudentProfile", backref="user", uselist=False, cascade="all, delete-orphan")
    internship = db.relationship("Internship", backref="student", uselist=False, cascade="all, delete-orphan")

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        # Support both Werkzeug hashes and Django PBKDF2 hashes
        if not self.password:
            return False
        if self.password.startswith("pbkdf2_sha256$"):
            # Django PBKDF2 format: pbkdf2_sha256$iterations$salt$hash
            import base64
            import hashlib
            try:
                parts = self.password.split("$")
                if len(parts) == 4:
                    _, iterations_str, salt, expected_hash = parts
                    iterations = int(iterations_str)
                    derived = hashlib.pbkdf2_hmac(
                        "sha256",
                        raw_password.encode("utf-8"),
                        salt.encode("utf-8"),
                        iterations,
                    )
                    calculated_hash = base64.b64encode(derived).decode("ascii").strip()
                    return calculated_hash == expected_hash
            except Exception:
                pass
        return check_password_hash(self.password, raw_password)


class StudentProfile(db.Model):
    __tablename__ = "accounts_studentprofile"

    CANDIDATE_TYPES = {
        "SCHOOL_STUDENT": "School Student Intern",
        "COLLEGE_INTERN": "College Intern",
        "COLLEGE_COMPLETED": "College Completed Student Intern",
    }

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("accounts_user.id"), unique=True, nullable=False)
    candidate_type = db.Column(db.String(30), default="COLLEGE_INTERN", nullable=False)
    gender = db.Column(db.String(6), nullable=False)
    mobile_number = db.Column(db.String(16), nullable=False)
    college_name = db.Column(db.String(200), nullable=False)
    department = db.Column(db.String(120), nullable=False)
    course = db.Column(db.String(100), nullable=False)
    register_number = db.Column(db.String(60), unique=True, nullable=False, index=True)
    college_id_card = db.Column(db.String(255), nullable=True)
    selfie_photo = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)


class Internship(db.Model):
    __tablename__ = "internships_internship"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("accounts_user.id"), unique=True, nullable=False)
    project_name = db.Column(db.String(150), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default="REGISTERED", nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    # Relationship
    certificate = db.relationship("Certificate", backref="internship", uselist=False, cascade="all, delete-orphan")


class Certificate(db.Model):
    __tablename__ = "certificates_certificate"

    id = db.Column(db.Integer, primary_key=True)
    internship_id = db.Column(db.Integer, db.ForeignKey("internships_internship.id"), unique=True, nullable=False)
    certificate_id = db.Column(db.String(30), unique=True, nullable=False, index=True)
    verification_token = db.Column(
        db.String(64),
        unique=True,
        default=generate_verification_token,
        nullable=False,
        index=True,
    )
    issue_date = db.Column(db.Date, nullable=False)
    pdf_file = db.Column(db.String(255), default="", nullable=True)
    snapshot = db.Column(db.JSON, default=dict, nullable=False)
    status = db.Column(db.String(10), default="VALID", nullable=False)
    generated_at = db.Column(db.DateTime, default=utcnow)
    revoked_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)


class CertificateSequence(db.Model):
    __tablename__ = "certificates_certificatesequence"

    year = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer, default=0, nullable=False)
