from flask import Blueprint, jsonify, g, request
from services.auth import student_required, student_data, certificate_data

student_bp = Blueprint("student", __name__)


@student_bp.route("/api/student/profile/", methods=["GET"])
@student_required
def profile():
    host_url = request.host_url.rstrip("/")
    return jsonify(student_data(g.current_user, host_url))


@student_bp.route("/api/student/internship/", methods=["GET"])
@student_required
def internship():
    host_url = request.host_url.rstrip("/")
    return jsonify(student_data(g.current_user, host_url))


@student_bp.route("/api/student/certificate/", methods=["GET"])
@student_required
def my_certificate():
    cert = getattr(g.current_user.internship, "certificate", None)
    return jsonify(certificate_data(cert))
