from extensions import db
from models.user import User

def get_or_create_user(email, provider, name=None):
    user = User.query.filter_by(email=email).first()

    if not user:
        user = User(
            email=email,
            auth_provider=provider,
            name=name
        )
        db.session.add(user)
        db.session.commit()

    return user



def mark_question_solved(user_id, xp_earned):
    user = User.query.get(user_id)

    if not user:
        return None

    user.questions_solved += 1
    user.xp += xp_earned

    db.session.commit()
    return user
