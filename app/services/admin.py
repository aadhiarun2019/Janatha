from app.database.database import SessionLocal
from app.models.models import Admin
from app.services.auth import hash_password


username = input("Admin username: ")
password = input("Admin password: ")

db = SessionLocal()

admin = Admin(
    username=username,
    password_hash=hash_password(password)
)

db.add(admin)
db.commit()
db.close()

print("Admin created successfully.")