import datetime
from functools import wraps
import jwt
from flask import request, jsonify, current_app, g
from models import User, StudentProfile


def generate_tokens(user):
    """
    Generate JWT access and refresh tokens.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    access_payload = {
        "user_id": user.id,
        "email": user.email,
        "role": user.role,
        "exp": now + datetime.timedelta(hours=current_app.config.get("JWT_EXPIRATION_HOURS", 24)),
        "type": "access",
    }
    refresh_payload = {
        "user_id": user.id,
        "exp": now + datetime.timedelta(days=7),
        "type": "refresh",
    }
    secret = current_app.config["SECRET_KEY"]
    access_token = jwt.encode(access_payload, secret, algorithm="HS256")
    refresh_token = jwt.encode(refresh_payload, secret, algorithm="HS256")
    return access_token, refresh_token


def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"detail": "Authentication credentials were not provided."}), 401
        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
            if payload.get("type") != "access":
                return jsonify({"detail": "Invalid token type."}), 401
            user = User.query.get(payload["user_id"])
            if not user or not user.is_active:
                return jsonify({"detail": "User not found or inactive."}), 401
            g.current_user = user
        except jwt.ExpiredSignatureError:
            return jsonify({"detail": "Token has expired."}), 401
        except Exception:
            return jsonify({"detail": "Invalid token."}), 401
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    @jwt_required
    def decorated(*args, **kwargs):
        if g.current_user.role != "ADMIN":
            return jsonify({"detail": "Admin access required."}), 403
        return f(*args, **kwargs)
    return decorated


def student_required(f):
    @wraps(f)
    @jwt_required
    def decorated(*args, **kwargs):
        if g.current_user.role != "STUDENT":
            return jsonify({"detail": "Student access required."}), 403
        return f(*args, **kwargs)
    return decorated


def certificate_data(cert):
    if not cert:
        return None
    return {
        "id": cert.id,
        "certificate_id": cert.certificate_id,
        "issue_date": cert.issue_date.isoformat() if cert.issue_date else None,
        "status": cert.status,
        "verification_url": f"/verify/{cert.verification_token}",
        "student_name": cert.snapshot.get("student_name") if cert.snapshot else None,
        "project_name": cert.snapshot.get("project_name") if cert.snapshot else None,
    }


def student_data(user, request_host_url="http://127.0.0.1:5000"):
    p = user.profile
    i = user.internship
    if not p or not i:
        return {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
        }

    def format_media_url(file_path):
        if not file_path:
            return None
        if file_path.startswith("http://") or file_path.startswith("https://"):
            return file_path
        clean_path = file_path.lstrip("/")
        return f"{request_host_url}/media/{clean_path}"

    duration = (i.end_date - i.start_date).days + 1 if (i.end_date and i.start_date) else None
    cand_type = getattr(p, "candidate_type", "COLLEGE_INTERN")
    cand_label_map = {
        "SCHOOL_STUDENT": "School Student Intern",
        "COLLEGE_INTERN": "College Intern",
        "COLLEGE_COMPLETED": "College Completed Student Intern",
    }

    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "candidate_type": cand_type,
        "candidate_type_display": cand_label_map.get(cand_type, "College Intern"),
        "gender": p.gender,
        "mobile_number": p.mobile_number,
        "college_name": p.college_name,
        "department": p.department,
        "course": p.course,
        "register_number": p.register_number,
        "college_id_card": format_media_url(p.college_id_card),
        "selfie_photo": format_media_url(p.selfie_photo),
        "internship_id": i.id,
        "project_name": i.project_name,
        "start_date": i.start_date.isoformat() if i.start_date else None,
        "end_date": i.end_date.isoformat() if i.end_date else None,
        "status": i.status,
        "completed_at": i.completed_at.isoformat() if i.completed_at else None,
        "duration_days": duration,
        "certificate": certificate_data(i.certificate),
    }
