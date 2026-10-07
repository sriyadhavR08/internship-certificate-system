import sys
from app import create_app
from models import db, User

app = create_app()

def make_admin(email, password, full_name="System Administrator"):
    with app.app_context():
        user = User.query.filter_by(email=email.strip().lower()).first()
        if user:
            user.set_password(password)
            user.role = "ADMIN"
            user.is_staff = True
            user.is_superuser = True
            user.full_name = full_name
            db.session.commit()
            print(f"Updated existing user '{email}' to ADMIN with new password.")
        else:
            user = User(
                email=email.strip().lower(),
                full_name=full_name,
                role="ADMIN",
                is_staff=True,
                is_superuser=True,
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            print(f"Created new ADMIN user: {email}")

if __name__ == "__main__":
    email = sys.argv[1] if len(sys.argv) > 1 else "admin@wingroo.com"
    password = sys.argv[2] if len(sys.argv) > 2 else "Admin@12345"
    full_name = sys.argv[3] if len(sys.argv) > 3 else "Wingroo Admin"
    make_admin(email, password, full_name)
