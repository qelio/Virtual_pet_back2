from pyexpat.errors import messages

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta


def init_pet_mood_updater(app, pet_repository, pet_mood_history_repository, notification_repository):
    scheduler = BackgroundScheduler()

    def update_pets_mood():
        with app.app_context():
            connection = pet_repository.db_connector.connect()
            with connection.cursor(named_tuple=True) as cursor:
                cursor.execute("SELECT id, mood, created_at, life_status FROM pets WHERE life_status = 'alive'")
                pets = cursor.fetchall()

            for pet in pets:
                check_and_update_pet_mood(pet, pet_repository, pet_mood_history_repository)
                print(pet)

    def check_and_update_pet_mood(pet, pet_repo, mood_history_repo):
        last_mood_record = mood_history_repo.get_by_pet_id(pet.id, limit=1)

        if not last_mood_record:
            last_change_time = pet.created_at
            current_mood = pet.mood
        else:
            last_change_time = last_mood_record[0].changed_at
            current_mood = last_mood_record[0].last_mood

        time_since_last_change = datetime.now() - last_change_time

        new_mood = None
        new_life_status = None
        reason = None

        if time_since_last_change > timedelta(hours=24):
            new_life_status = 'dead'
            reason = 'Смерть питомца из-за того, что долго не было задач'
        elif time_since_last_change > timedelta(hours=5):
            new_mood = 'sad'
            reason = 'Не было выполнения задач в течение 5 часов'
        elif time_since_last_change > timedelta(hours=2):
            new_mood = 'neutral'
            reason = 'Не было выполнения задач в течение 2 часов'

        if new_mood or new_life_status:
            pet_repo.update(
                pet.id,
                mood=new_mood if new_mood else pet.mood,
                life_status=new_life_status if new_life_status else pet.life_status
            )

            mood_history_repo.create(
                last_mood=current_mood,
                reason=reason,
                changed_at=datetime.now(),
                pets_id=pet.id
            )

            if new_life_status == 'dead':
                notification_repository.create(
                    message="К сожалению, ваш питомец умер, поскольку вы не кормили питомца задачи в течение 24 часов",
                    created_at=datetime.now(),
                    is_read=0,
                    users_id=pet.users_id
                )


    scheduler.add_job(
        update_pets_mood,
        'interval',
        minutes=1,
        id='pet_mood_updater',
        replace_existing=True
    )

    scheduler.start()