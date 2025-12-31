from datetime import datetime
from extensions import db

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(
    db.String(80),
    nullable=True
)


    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    auth_provider = db.Column(
        db.String(20), 
        nullable=False
    )

    xp = db.Column(
        db.Integer,
        default=0
    )

    questions_solved = db.Column(
        db.Integer,
        default=0
    )

    joined_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )
