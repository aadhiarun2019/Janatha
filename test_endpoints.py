from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("Testing unauthenticated member rentals GET:")
resp1 = client.get("/api/member/rentals")
print(f"  Status: {resp1.status_code}")
print(f"  Body: {resp1.json()}")

print("\nTesting unauthenticated admin rentals GET:")
resp2 = client.get("/api/admin/rentals")
print(f"  Status: {resp2.status_code}")
print(f"  Body: {resp2.json()}")
