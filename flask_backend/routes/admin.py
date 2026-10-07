from datetime import date, datetime, timezone
from flask import Blueprint, request, jsonify, make_response, current_app
from models import db, User, StudentProfile, Internship, Certificate
from services.auth import admin_required, student_data, certificate_data
from services.pdf import snapshot_data, render_certificate_pdf
from services.certificate import generate_certificate
from services.storage import save_base64_file

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/api/admin/dashboard/", methods=["GET"])
@admin_required
def dashboard():
    host_url = request.host_url.rstrip("/")
    students_query = User.query.filter_by(role="STUDENT").order_by(User.created_at.desc())
    recent_students = [student_data(u, host_url) for u in students_query.limit(5).all()]

    certs_query = Certificate.query.order_by(Certificate.created_at.desc())
    recent_certs = [certificate_data(c) for c in certs_query.limit(5).all()]

    counts = {
        "Total students": User.query.filter_by(role="STUDENT").count(),
        "Active internships": Internship.query.filter_by(status="IN_PROGRESS").count(),
        "Completed internships": Internship.query.filter(
            Internship.status.in_(["COMPLETED", "CERTIFICATE_ISSUED"])
        ).count(),
        "Certificates issued": Certificate.query.count(),
    }
    return jsonify({
        "counts": counts,
        "recent_students": recent_students,
        "recent_certificates": recent_certs,
    })


@admin_bp.route("/api/admin/students/", methods=["GET"])
@admin_required
def students():
    host_url = request.host_url.rstrip("/")
    query = User.query.filter_by(role="STUDENT").join(StudentProfile, User.profile).join(Internship, User.internship)

    search = request.args.get("search", "").strip()
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            db.or_(
                User.full_name.ilike(search_term),
                User.email.ilike(search_term),
                StudentProfile.register_number.ilike(search_term),
            )
        )

    status_filter = request.args.get("status")
    if status_filter:
        query = query.filter(Internship.status == status_filter)

    cand_type = request.args.get("candidate_type")
    if cand_type:
        query = query.filter(StudentProfile.candidate_type == cand_type)

    total_count = query.count()

    try:
        page = max(1, int(request.args.get("page", 1)))
    except ValueError:
        page = 1
    page_size = 20

    users = query.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    results = [student_data(u, host_url) for u in users]

    return jsonify({
        "count": total_count,
        "page": page,
        "results": results,
    })


@admin_bp.route("/api/admin/students/<int:pk>/", methods=["GET", "PUT"])
@admin_required
def student_detail(pk):
    host_url = request.host_url.rstrip("/")
    user = User.query.filter_by(id=pk, role="STUDENT").first()
    if not user:
        return jsonify({"detail": "Student not found."}), 404

    if request.method == "PUT":
        internship = user.internship
        if internship and internship.certificate:
            return jsonify({"detail": "Issued certificate details are immutable. Revoke the certificate if it is incorrect."}), 400

        data = request.get_json() or {}
        media_folder = current_app.config["MEDIA_FOLDER"]

        if "full_name" in data:
            user.full_name = data["full_name"]
        if "email" in data:
            user.email = data["email"].strip().lower()

        profile = user.profile
        if profile:
            for field in ["candidate_type", "gender", "mobile_number", "college_name", "department", "course", "register_number"]:
                if field in data:
                    setattr(profile, field, data[field])

            if "college_id_card" in data and data["college_id_card"]:
                saved = save_base64_file(data["college_id_card"], media_folder, "college_ids", "id_doc")
                if saved:
                    profile.college_id_card = saved
            if "selfie_photo" in data and data["selfie_photo"]:
                saved = save_base64_file(data["selfie_photo"], media_folder, "selfies", "selfie")
                if saved:
                    profile.selfie_photo = saved

        if internship:
            if "project_name" in data:
                internship.project_name = data["project_name"]
            if "start_date" in data and data["start_date"]:
                internship.start_date = date.fromisoformat(data["start_date"])
            if "end_date" in data and data["end_date"]:
                internship.end_date = date.fromisoformat(data["end_date"])

        db.session.commit()

    return jsonify(student_data(user, host_url))


@admin_bp.route("/api/admin/internships/<int:pk>/status/", methods=["PATCH"])
@admin_required
def update_status(pk):
    host_url = request.host_url.rstrip("/")
    internship = Internship.query.get(pk)
    if not internship:
        return jsonify({"detail": "Internship not found."}), 404

    data = request.get_json() or {}
    target = data.get("status")
    if target not in ["REGISTERED", "IN_PROGRESS", "COMPLETED"]:
        return jsonify({"detail": "Invalid status target."}), 400

    internship.status = target
    if target == "COMPLETED":
        internship.completed_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify(student_data(internship.student, host_url))


@admin_bp.route("/api/admin/internships/<int:pk>/end-date/", methods=["PATCH", "POST"])
@admin_required
def set_end_date(pk):
    host_url = request.host_url.rstrip("/")
    internship = Internship.query.get(pk)
    if not internship:
        return jsonify({"detail": "Internship not found."}), 404

    data = request.get_json() or {}
    end_date_str = data.get("end_date")
    if not end_date_str:
        return jsonify({"end_date": "End date is required."}), 400

    try:
        d = date.fromisoformat(end_date_str)
    except ValueError:
        return jsonify({"end_date": "Invalid date format (YYYY-MM-DD)."}), 400

    if internship.start_date and d <= internship.start_date:
        return jsonify({"end_date": "End date must be after start date."}), 400

    internship.end_date = d
    db.session.commit()
    return jsonify(student_data(internship.student, host_url))


@admin_bp.route("/api/admin/certificates/", methods=["GET"])
@admin_required
def certificates():
    query = Certificate.query.order_by(Certificate.created_at.desc())
    search = request.args.get("search", "").strip()
    if search:
        query = query.filter(Certificate.certificate_id.ilike(f"%{search}%"))

    status_filter = request.args.get("status")
    if status_filter:
        query = query.filter_by(status=status_filter)

    total = query.count()
    try:
        page = max(1, int(request.args.get("page", 1)))
    except ValueError:
        page = 1
    page_size = 20

    certs = query.offset((page - 1) * page_size).limit(page_size).all()
    return jsonify({
        "count": total,
        "page": page,
        "results": [certificate_data(c) for c in certs],
    })


@admin_bp.route("/api/admin/certificates/preview/<int:pk>/", methods=["GET"])
@admin_required
def preview(pk):
    internship = Internship.query.get(pk)
    if not internship:
        return jsonify({"detail": "Internship not found."}), 404

    data = snapshot_data(internship)
    pdf_bytes = render_certificate_pdf(data, date.today(), certificate_id="PREVIEW")

    response = make_response(pdf_bytes)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = 'inline; filename="certificate-preview.pdf"'
    response.headers["Cache-Control"] = "no-store"
    return response


@admin_bp.route("/api/admin/certificates/generate/<int:pk>/", methods=["POST"])
@admin_required
def issue(pk):
    try:
        cert = generate_certificate(pk)
        return jsonify(certificate_data(cert)), 201
    except ValueError as e:
        return jsonify({"detail": str(e)}), 400
    except Exception as e:
        return jsonify({"detail": f"Generation failed: {str(e)}"}), 500


@admin_bp.route("/api/admin/certificates/<int:pk>/revoke/", methods=["PATCH"])
@admin_required
def revoke(pk):
    cert = Certificate.query.get(pk)
    if not cert:
        return jsonify({"detail": "Certificate not found."}), 404

    if cert.status != "REVOKED":
        cert.status = "REVOKED"
        cert.revoked_at = datetime.now(timezone.utc)
        db.session.commit()
    return jsonify(certificate_data(cert))
