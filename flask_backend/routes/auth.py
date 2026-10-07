from datetime import date
from flask import Blueprint, request, jsonify, current_app, g
from models import db, User, StudentProfile, Internship
from services.auth import generate_tokens, jwt_required
from services.storage import save_base64_file

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/api/auth/register/", methods=["POST"])
def register():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    full_name = data.get("full_name", "").strip()
    password = data.get("password", "")
    confirm_password = data.get("confirm_password", "")

    if not email:
        return jsonify({"email": ["Email is required."]}), 400
    if not full_name:
        return jsonify({"full_name": ["Full name is required."]}), 400
    if not password:
        return jsonify({"password": ["Password is required."]}), 400
    if password != confirm_password:
        return jsonify({"confirm_password": ["Passwords do not match."]}), 400
    if len(password) < 8:
        return jsonify({"password": ["Password must be at least 8 characters."]}), 400

    if User.query.filter(db.func.lower(User.email) == email).first():
        return jsonify({"email": ["Email already registered."]}), 400

    reg_no = data.get("register_number", "").strip().upper()
    if not reg_no:
        return jsonify({"register_number": ["Register number is required."]}), 400

    if StudentProfile.query.filter(db.func.upper(StudentProfile.register_number) == reg_no).first():
        return jsonify({"register_number": ["Register number already exists."]}), 400

    start_date_str = data.get("start_date")
    if not start_date_str:
        return jsonify({"start_date": ["Start date is required."]}), 400
    try:
        start_date = date.fromisoformat(start_date_str)
    except ValueError:
        return jsonify({"start_date": ["Invalid start date format (YYYY-MM-DD)."]}), 400

    end_date = None
    if data.get("end_date"):
        try:
            end_date = date.fromisoformat(data["end_date"])
            if end_date <= start_date:
                return jsonify({"end_date": ["End date must be after start date."]}), 400
        except ValueError:
            return jsonify({"end_date": ["Invalid end date format (YYYY-MM-DD)."]}), 400

    cand_type = data.get("candidate_type", "COLLEGE_INTERN")

    # Save uploaded identity documents
    media_folder = current_app.config["MEDIA_FOLDER"]
    college_id_path = save_base64_file(data.get("college_id_card"), media_folder, "college_ids", "id_doc")
    selfie_path = save_base64_file(data.get("selfie_photo"), media_folder, "selfies", "selfie")

    try:
        user = User(
            email=email,
            full_name=full_name,
            role="STUDENT",
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        profile = StudentProfile(
            user=user,
            candidate_type=cand_type,
            gender=data.get("gender", "MALE"),
            mobile_number=data.get("mobile_number", ""),
            college_name=data.get("college_name", ""),
            department=data.get("department", ""),
            course=data.get("course", ""),
            register_number=reg_no,
            college_id_card=college_id_path,
            selfie_photo=selfie_path,
        )
        db.session.add(profile)

        internship = Internship(
            student=user,
            project_name=data.get("project_name", ""),
            start_date=start_date,
            end_date=end_date,
            status="REGISTERED",
        )
        db.session.add(internship)
        db.session.commit()

        return jsonify({"success": True, "message": "Registration successful. Please sign in."}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"detail": f"Registration failed: {str(e)}"}), 500


@auth_bp.route("/api/auth/login/", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"detail": "Must provide both email and password."}), 400

    user = User.query.filter(db.func.lower(User.email) == email).first()
    if not user or not user.check_password(password):
        return jsonify({"detail": "No active account found with the given credentials"}), 401

    if not user.is_active:
        return jsonify({"detail": "This account is inactive."}), 401

    access_token, refresh_token = generate_tokens(user)
    return jsonify({
        "access": access_token,
        "refresh": refresh_token,
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
        },
    }), 200


@auth_bp.route("/api/auth/me/", methods=["GET"])
@jwt_required
def me():
    u = g.current_user
    return jsonify({
        "id": u.id,
        "full_name": u.full_name,
        "email": u.email,
        "role": u.role,
    }), 200


@auth_bp.route("/api/auth/logout/", methods=["POST"])
def logout():
    return jsonify({"message": "Signed out."}), 200


@auth_bp.route("/api/auth/token/refresh/", methods=["POST"])
def token_refresh():
    import jwt
    data = request.get_json() or {}
    refresh_token = data.get("refresh")
    if not refresh_token:
        return jsonify({"detail": "Refresh token required."}), 400
    try:
        payload = jwt.decode(refresh_token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
        if payload.get("type") != "refresh":
            return jsonify({"detail": "Invalid token type."}), 400
        user = User.query.get(payload["user_id"])
        if not user or not user.is_active:
            return jsonify({"detail": "User not found or inactive."}), 401
        access_token, _ = generate_tokens(user)
        return jsonify({"access": access_token}), 200
    except Exception:
        return jsonify({"detail": "Token is invalid or expired."}), 401
