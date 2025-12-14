from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime

from app.auth import user_repo
from repositories import TaskRepository, PetRepository, PetMoodHistoryRepository, ExperienceCounterRepository, \
    LogActionRepository
from app import db

task_repo = TaskRepository(db)
pet_repo = PetRepository(db)
pet_mood_history_repo = PetMoodHistoryRepository(db)
experience_counter_repo = ExperienceCounterRepository(db)
log_action_repo = LogActionRepository(db)
bp = Blueprint('tasks', __name__, url_prefix='/tasks')


@bp.route('/', methods=['GET'])
@login_required
def get_user_tasks():
    try:
        completed = request.args.get('completed', type=lambda x: x.lower() == 'true')
        tasks = task_repo.get_by_user_id(current_user.id, completed)
        return jsonify([task._asdict() for task in tasks]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:task_id>', methods=['GET'])
@login_required
def get_task(task_id):
    task = task_repo.get_by_id(task_id)
    if not task:
        return jsonify({'error': 'Задача не найдена'}), 404

    if task.users_id != current_user.id:
        return jsonify({'error': 'Нет доступа к этой задаче'}), 403

    return jsonify(task._asdict()), 200

@bp.route('/paginated', methods=['GET'])
@login_required
def get_paginated_tasks():
    try:
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=10, type=int)
        sort_by = request.args.get('sort_by', default='created_at', type=str)
        sort_order = request.args.get('sort_order', default='desc', type=str)
        completed = request.args.get('completed', type=lambda x: x.lower() == 'true')

        result = task_repo.get_paginated_tasks(
            user_id=current_user.id,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            completed=completed
        )

        return jsonify({
            'tasks': [task._asdict() for task in result['tasks']],
            'pagination': {
                'page': result['page'],
                'per_page': result['per_page'],
                'total_items': result['total_count'],
                'total_pages': (result['total_count'] + result['per_page'] - 1) // result['per_page']
            },
            'sorting': {
                'sort_by': result['sort_by'],
                'sort_order': result['sort_order']
            },
            'filter': {
                'completed': result['completed_filter']
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/create', methods=['POST'])
@login_required
def create_task():
    data = request.get_json()
    required_fields = ['title', 'description']

    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Не все обязательные поля заполнены'}), 400

    try:
        task_id = task_repo.create(
            title=data['title'],
            description=data['description'],
            is_completed=False,
            created_at=datetime.utcnow(),
            experience_num=data.get('experience_num', 10),
            users_id=current_user.id
        )
        log_action_repo.create('Создание новой задачи', datetime.utcnow(), current_user.id)
        pets = pet_repo.get_by_user_id(current_user.id)
        active_pet = next((pet for pet in pets if pet.life_status == 'alive'), None)
        if active_pet:
            pet_mood_history_repo.create(
                active_pet.mood,
                'Добавление новой задачи',
                datetime.utcnow(),
                active_pet.id)

            pet_repo.update(
                pet_id=active_pet.id,
                mood='neutral'
            )

        return jsonify({'id': task_id, 'message': 'Задача успешно создана'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    existing_task = task_repo.get_by_id(task_id)
    if not existing_task:
        return jsonify({'error': 'Задача не найдена'}), 404
    if existing_task.users_id != current_user.id:
        return jsonify({'error': 'Нет прав для изменения этой задачи'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Нет данных для обновления'}), 400

    try:
        task_repo.update(
            task_id=task_id,
            title=data.get('title'),
            description=data.get('description'),
            is_completed=data.get('is_completed'),
            experience_num=data.get('experience_num')
        )
        return jsonify({'message': 'Задача успешно обновлена'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:task_id>/complete', methods=['PUT'])
@login_required
def complete_task(task_id):
    existing_task = task_repo.get_by_id(task_id)
    if not existing_task:
        return jsonify({'error': 'Задача не найдена'}), 404
    if existing_task.users_id != current_user.id:
        return jsonify({'error': 'Нет прав для изменения этой задачи'}), 403

    try:
        task_repo.update(
            task_id=task_id,
            is_completed=True
        )
        log_action_repo.create('Выполнение новой задачи', datetime.utcnow(), current_user.id)
        pets = pet_repo.get_by_user_id(current_user.id)
        active_pet = next((pet for pet in pets if pet.life_status == 'alive'), None)
        active_user = user_repo.get_by_id(current_user.id)
        print(active_user)
        if active_pet:
            pet_mood_history_repo.create(
                active_pet.mood,
                'Выполнение задачи',
                datetime.utcnow(),
                active_pet.id)

            experience_counter_repo.create(
                datetime.utcnow(),
                task_id,
                None,
                current_user.id,
                existing_task.experience_num,
                'adding'
            )

            user_repo.update(
                current_user.id,
                current_points=active_user['сurrent_points'] + existing_task.experience_num,
            )

            pet_repo.update(
                pet_id=active_pet.id,
                mood='happy'
            )
        return jsonify({'message': 'Задача отмечена как выполненная'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:task_id>/delete', methods=['DELETE'])
@login_required
def delete_task(task_id):
    existing_task = task_repo.get_by_id(task_id)
    if not existing_task:
        return jsonify({'error': 'Задача не найдена'}), 404
    if existing_task.users_id != current_user.id:
        return jsonify({'error': 'Нет прав для удаления этой задачи'}), 403

    try:
        log_action_repo.create('Удаление задачи', datetime.utcnow(), current_user.id)
        task_repo.delete(task_id)
        pets = pet_repo.get_by_user_id(current_user.id)
        active_pet = next((pet for pet in pets if pet.life_status == 'alive'), None)
        if active_pet:
            pet_mood_history_repo.create(
                active_pet.mood,
                'Удаление задачи',
                datetime.utcnow(),
                active_pet.id)
            pet_repo.update(
                pet_id=active_pet.id,
                mood='sad'
            )

        return jsonify({'message': 'Задача успешно удалена'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500