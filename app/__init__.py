from flask import Flask

from repositories import PetRepository, PetMoodHistoryRepository, UserRepository, AchievementRepository, \
    NotificationRepository
from .db import DBConnector
from flask_cors import CORS
from flask_login import LoginManager

from .services.achievement_checker import init_achievement_checker
from .services.pet_mood_updater import init_pet_mood_updater

db = DBConnector()

login_manager = LoginManager()

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=False)
    CORS(app, supports_credentials=True)
    app.config.from_pyfile('config.py', silent=False)

    if test_config:
        app.config.from_mapping(test_config)

    db.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.session_protection = "strong"

    pet_repo = PetRepository(db)
    mood_history_repo = PetMoodHistoryRepository(db)
    user_repository = UserRepository(db)
    achievement_repository = AchievementRepository(db)
    notification_repository = NotificationRepository(db)

    init_pet_mood_updater(app, pet_repo, mood_history_repo, notification_repository)
    init_achievement_checker(app, user_repository, achievement_repository, notification_repository)

    from app import auth
    app.register_blueprint(auth.bp)

    from app import pets
    app.register_blueprint(pets.bp)

    from app import tasks
    app.register_blueprint(tasks.bp)

    from app import users
    app.register_blueprint(users.bp)

    from app import pet_mood_history
    app.register_blueprint(pet_mood_history.bp)

    from app import achievements
    app.register_blueprint(achievements.bp)

    from app import logs
    app.register_blueprint(logs.bp)

    from app import notifications
    app.register_blueprint(notifications.bp)

    return app