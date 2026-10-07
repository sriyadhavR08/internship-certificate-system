import os
from datetime import datetime
from flask import Blueprint, jsonify, request, current_app, send_file, send_from_directory, g
from models import Certificate
from services.captcha import make_captcha, validate_captcha
from services.auth import jwt_required

public_bp = Blueprint("public", __name__)


@public_bp.route("/api/public/captcha/", methods=["GET"])
def get_captcha():
    return jsonify(make_captcha())


def _verify_certificate(cert):
    if not cert:
        return jsonify({"detail": "Certificate not found."}), 404

    profile = cert.internship.student.profile if (cert.internship and cert.internship.student) else None
    snapshot = cert.snapshot or {}
    cand_type = profile.candidate_type if profile else snapshot.get("candidate_type", "COLLEGE_INTERN")

    cand_label_map = {
        "SCHOOL_STUDENT": "School Student Intern",
        "COLLEGE_INTERN": "College Intern",
        "COLLEGE_COMPLETED": "College Completed Student Intern",
    }

    student_name = snapshot.get("student_name")
    if not student_name and cert.internship and cert.internship.student:
        student_name = cert.internship.student.full_name

    result = {
        "student_name": student_name,
        "candidate_type": cand_type,
        "candidate_type_label": cand_label_map.get(cand_type, "College Intern"),
        "certificate_id": cert.certificate_id,
        "status": cert.status,
        "verified_status": "Certified Verified" if cert.status == "VALID" else "Certificate Revoked",
        "college_name": profile.college_name if profile else snapshot.get("institution_name", ""),
        "department": profile.department if profile else snapshot.get("department", ""),
        "course": profile.course if profile else snapshot.get("course", ""),
        "register_number": profile.register_number if profile else snapshot.get("register_number", ""),
        "verified_at": datetime.now().strftime("%d %B %Y, %I:%M %p"),
    }

    if cert.status == "VALID":
        result.update({
            "project_name": snapshot.get("project_name", ""),
            "start_date": snapshot.get("start_date", ""),
            "end_date": snapshot.get("end_date", ""),
            "issue_date": cert.issue_date.isoformat() if cert.issue_date else None,
        })

    return jsonify(result)


@public_bp.route("/api/public/verify/token/<token>/", methods=["GET", "POST"])
def verify_token(token):
    data = request.get_json(silent=True) or {} if request.method == "POST" else request.args
    captcha_token = data.get("captcha_token")
    captcha_answer = data.get("captcha_answer")

    if not validate_captcha(captcha_token, captcha_answer):
        return jsonify({"captcha": "Security verification failed. Please enter the valid 6-digit OTP code."}), 400

    cert = Certificate.query.filter_by(verification_token=token).first()
    return _verify_certificate(cert)


@public_bp.route("/api/public/verify/id/<certificate_id>/", methods=["GET", "POST"])
def verify_id(certificate_id):
    data = request.get_json(silent=True) or {} if request.method == "POST" else request.args
    captcha_token = data.get("captcha_token")
    captcha_answer = data.get("captcha_answer")

    if not validate_captcha(captcha_token, captcha_answer):
        return jsonify({"captcha": "Security verification failed. Please enter the valid 6-digit OTP code."}), 400

    cert = Certificate.query.filter_by(certificate_id=certificate_id.strip().upper()).first()
    return _verify_certificate(cert)


@public_bp.route("/api/certificates/<int:pk>/download/", methods=["GET"])
@jwt_required
def download_certificate(pk):
    cert = Certificate.query.get(pk)
    if not cert:
        return jsonify({"detail": "Certificate not found."}), 404

    if g.current_user.role != "ADMIN" and (not cert.internship or cert.internship.student_id != g.current_user.id):
        return jsonify({"detail": "You can only access your own certificate."}), 403

    if cert.status == "REVOKED":
        return jsonify({"detail": "This certificate has been revoked."}), 403

    if not cert.pdf_file:
        return jsonify({"detail": "Certificate PDF file is missing."}), 404

    pdf_path = os.path.join(current_app.config["MEDIA_FOLDER"], cert.pdf_file)
    if not os.path.isfile(pdf_path):
        return jsonify({"detail": "Certificate file not found on disk."}), 404

    response = send_file(
        pdf_path,
        as_attachment=True,
        download_name=f"{cert.certificate_id}.pdf",
        mimetype="application/pdf",
    )
    response.headers["Cache-Control"] = "no-store"
    return response


@public_bp.route("/media/<path:filename>", methods=["GET"])
def serve_media(filename):
    return send_from_directory(current_app.config["MEDIA_FOLDER"], filename)
