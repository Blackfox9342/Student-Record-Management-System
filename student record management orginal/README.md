# Prakash University Academic Record Management System

A phase-based university ERP starter built with Flask, MySQL-ready SQLAlchemy models, Bootstrap 5, Chart.js, ReportLab, and OpenPyXL.

## What is in Phase 1

- Landing page with a polished university ERP introduction
- Separate Student, Faculty, and Admin login entry points
- Role-based dashboards for the first usable shell
- Seeded demo users for quick testing
- Flask-Login authentication with hashed passwords
- SHA-256 hash-chained academic ledger for tamper-evident marks and attendance audit records

## Demo logins

- Student: `student@prakashuniversity.edu` / `Student@123`
- Faculty: `faculty@prakashuniversity.edu` / `Faculty@123`
- Admin: `admin@prakashuniversity.edu` / `Admin@123`

## Run locally

1. Create and activate a Python virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and update `SECRET_KEY` and `DATABASE_URL`.
4. Start the app with `python run.py`.

## Notes

- The project defaults to SQLite for local startup if `DATABASE_URL` is not set.
- Set `DATABASE_URL` to a MySQL connection string when you are ready to move to MySQL.
- The current structure is ready for later modules: students, faculty, academics, attendance, marks, GPA, CGPA, reports, and audit logs.
- The admin Audit Logs module verifies the academic ledger chain at request time. This is a permissioned audit feature backed by the application database, not a public cryptocurrency network.
