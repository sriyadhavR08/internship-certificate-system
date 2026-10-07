import os
from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from models import db
from routes.auth import auth_bp
from routes.student import student_bp
from routes.admin import admin_bp
from routes.public import public_bp


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    # Setup CORS for Frontend
    CORS(
        app,
        resources={r"/*": {"origins": app.config.get("CORS_ALLOWED_ORIGINS", "*")}},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    )

    # Ensure required folders exist
    media_dir = app.config["MEDIA_FOLDER"]
    for sub in ["id_proofs", "selfies", "certificates"]:
        os.makedirs(os.path.join(media_dir, sub), exist_ok=True)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(public_bp)

    @app.route("/", methods=["GET"])
    def index():
        return jsonify({
            "name": "Wingroo Internship Certificate API (Flask)",
            "version": "1.0.0",
            "status": "online",
            "docs": {
                "auth": "/api/auth/*",
                "student": "/api/student/*",
                "admin": "/api/admin/*",
                "public": "/api/public/*",
            }
        })

    @app.route("/api/health/", methods=["GET"])
    def health():
        return jsonify({"status": "healthy"})

    return app


app = create_app()

if __name__ == "__main__":
    with app.app_context():
        # Ensure database tables exist (safe if they already exist in MySQL)
        db.create_all()

    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Wingroo Flask Backend starting on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
