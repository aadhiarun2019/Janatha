# Janatha authentication update

## 1. Replace the files

Copy these into your project:

- `app/models/models.py`
- `app/routes/auth.py`
- `app/services/dependencies.py`
- `app/main.py`
- `templates/index.html`
- `templates/member.html`

Do not keep the old login JavaScript/modal from `index.html`.

## 2. Create the database migration

Because your current Alembic revision ID is specific to your project, do NOT copy a guessed `down_revision`.

After replacing `models.py`, run:

```powershell
alembic revision --autogenerate -m "Add unified users authentication"
```

Then inspect the generated migration.

It should create a `users` table with:

- id
- full_name
- email
- phone
- username
- password_hash
- role
- is_active
- created_at

It should also contain a data migration that copies the existing rows from `admins` into `users` with:

```text
role = admin
```

If Alembic does not generate the data-copy part automatically, add this inside `upgrade()`:

```python
op.execute(
    """
    INSERT INTO users
        (full_name, email, phone, username, password_hash,
         role, is_active, created_at)
    SELECT
        username,
        username || '@janatha-library.local',
        NULL,
        username,
        password_hash,
        'admin',
        is_active,
        created_at
    FROM admins
    """
)
```

Then run:

```powershell
alembic upgrade head
```

## 3. Important

Do NOT run the old `app/services/admin.py` script again.

Your existing admin account is copied into `users`.

Public registration always creates:

```text
role = member
```

There is no public admin registration.

## 4. Authentication flow

```text
Login
 ├── Member Login
 │     ├── Register
 │     └── Member Area
 │
 └── Admin Login
       └── Admin Dashboard
```

Members cannot access `/admin`.

Admins cannot use the member login because the login query checks `role`.

## 5. Test

1. Restart FastAPI.
2. Open the homepage.
3. Click Login.
4. Verify you see:
   - Member Login
   - Admin Login
   - Create an account
5. Register a test member.
6. Log in as that member.
7. Confirm `/member` opens.
8. Logout.
9. Log in as the existing admin.
10. Confirm `/admin` opens.
11. Log in as member and manually visit `/admin`.
12. It must redirect back to `/`.
