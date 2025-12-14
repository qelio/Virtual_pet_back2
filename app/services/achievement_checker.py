from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime


def init_achievement_checker(app, user_repository, achievement_repository, notification_repository):
    scheduler = BackgroundScheduler()

    def check_user_achievements():
        with app.app_context():
            users = user_repository.all()

            achievements = achievement_repository.all()

            for user in users:
                check_and_award_achievements(user, achievements)

    def check_and_award_achievements(user, all_achievements):
        user_achievements = achievement_repository.get_user_achievements(user['id'])

        user_achievement_ids = {ach.id for ach in user_achievements}

        for achievement in all_achievements:
            if achievement.id not in user_achievement_ids:
                if user['сurrent_points'] >= achievement.experience_num:
                    achievement_repository.add_user_achievement(
                        user['id'],
                        achievement.id
                    )
                    notification_repository.create(
                        message="Поздравляю, вы получили новое достижение",
                        created_at=datetime.now(),
                        is_read=0,
                        users_id=user['id']
                    )
                    print(f"User {user['id']} получил достижение {achievement.title}")

    scheduler.add_job(
        check_user_achievements,
        'interval',
        minutes=1,
        id='achievement_checker',
        replace_existing=True
    )

    scheduler.start()