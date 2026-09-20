from app.database.database import SessionLocal
from app.models.models import User
from app.services.auth import hash_password


username = input("Admin username: ")
password = input("Admin password: ")

db = SessionLocal()

admin = User(
    full_name=username,
    email=f"{username}@janatha-library.local",
    username=username,
    password_hash=hash_password(password),
    role="admin",
    is_active=True,
)

db.add(admin)
db.commit()
db.close()

print("Admin created successfully.")