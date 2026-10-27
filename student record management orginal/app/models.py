import hashlib
import json
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash

from app import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)


class AcademicLedgerBlock(db.Model):
    __tablename__ = "academic_ledger_blocks"

    id = db.Column(db.Integer, primary_key=True)
    block_index = db.Column(db.Integer, unique=True, nullable=False)
    record_type = db.Column(db.String(40), nullable=False)
    record_key = db.Column(db.String(120), nullable=False)
    payload = db.Column(db.Text, nullable=False)
    previous_hash = db.Column(db.String(64), nullable=False)
    block_hash = db.Column(db.String(64), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


def _block_hash(block_index, record_type, record_key, payload, previous_hash):
    content = "|".join(
        [str(block_index), record_type, record_key, payload, previous_hash]
    )
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def seed_academic_ledger(marks, attendance):
    if AcademicLedgerBlock.query.count():
        return

    records = [
        ("marks", item["subject"], item)
        for item in marks
    ] + [
        ("attendance", subject, {"status": status, "attendance": percent})
        for subject, status, percent in attendance
    ]
    previous_hash = "0" * 64

    for block_index, (record_type, record_key, record) in enumerate(records, start=1):
        payload = json.dumps(record, sort_keys=True, separators=(",", ":"))
        block_hash = _block_hash(
            block_index, record_type, record_key, payload, previous_hash
        )
        db.session.add(
            AcademicLedgerBlock(
                block_index=block_index,
                record_type=record_type,
                record_key=record_key,
                payload=payload,
                previous_hash=previous_hash,
                block_hash=block_hash,
            )
        )
        previous_hash = block_hash

    db.session.commit()


def verify_academic_ledger():
    blocks = AcademicLedgerBlock.query.order_by(AcademicLedgerBlock.block_index).all()
    previous_hash = "0" * 64

    for expected_index, block in enumerate(blocks, start=1):
        expected_hash = _block_hash(
            block.block_index,
            block.record_type,
            block.record_key,
            block.payload,
            block.previous_hash,
        )
        if (
            block.block_index != expected_index
            or block.previous_hash != previous_hash
            or block.block_hash != expected_hash
        ):
            return False, blocks
        previous_hash = block.block_hash

    return True, blocks


def seed_demo_users():
    demo_users = [
        {
            "full_name": "System Administrator",
            "email": "admin@prakashuniversity.edu",
            "password": "Admin@123",
            "role": "admin",
        },
        {
            "full_name": "Prakash",
            "email": "student@prakashuniversity.edu",
            "password": "Student@123",
            "role": "student",
        },
        {
            "full_name": "Dr. Priya Nair",
            "email": "faculty@prakashuniversity.edu",
            "password": "Faculty@123",
            "role": "faculty",
        },
    ]

    for demo in demo_users:
        user = User.query.filter_by(email=demo["email"]).first()
        if user is None:
            user = User(
                full_name=demo["full_name"],
                email=demo["email"],
                role=demo["role"],
            )
            db.session.add(user)
        else:
            user.full_name = demo["full_name"]
            user.role = demo["role"]

        user.set_password(demo["password"])

    db.session.commit()
