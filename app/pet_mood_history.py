from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime

from repositories import PetRepository, PetMoodHistoryRepository
from app import db

pet_repo = PetRepository(db)
pet_mood_history_repo = PetMoodHistoryRepository(db)
bp = Blueprint('pet_mood_history', __name__, url_prefix='/pet-mood-history')


@bp.route('/', methods=['GET'])
@login_required
def get_pet_mood_history():
    try:
        pets = pet_repo.get_by_user_id(current_user.id)
        active_pet = next((pet for pet in pets if pet.life_status == 'alive'), None)

        if not active_pet:
            return jsonify({'error': 'Нет активного питомца'}), 404

        limit = request.args.get('limit', type=int)
        history = pet_mood_history_repo.get_by_pet_id(active_pet.id, limit)

        return jsonify([record._asdict() for record in history]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:history_id>', methods=['GET'])
@login_required
def get_mood_history_record(history_id):
    try:
        record = pet_mood_history_repo.get_by_id(history_id)
        if not record:
            return jsonify({'error': 'Запись не найдена'}), 404

        pets = pet_repo.get_by_user_id(current_user.id)
        if not any(pet.id == record.pets_id for pet in pets):
            return jsonify({'error': 'Нет доступа к этой записи'}), 403

        return jsonify(record._asdict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/', methods=['POST'])
@login_required
def create_mood_history_record():
    data = request.get_json()
    required_fields = ['last_mood', 'reason']

    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Не все обязательные поля заполнены'}), 400

    try:
        pets = pet_repo.get_by_user_id(current_user.id)
        active_pet = next((pet for pet in pets if pet.life_status == 'alive'), None)

        if not active_pet:
            return jsonify({'error': 'Нет активного питомца'}), 404

        record_id = pet_mood_history_repo.create(
            last_mood=data['last_mood'],
            reason=data['reason'],
            changed_at=datetime.utcnow(),
            pets_id=active_pet.id,
            tasks_id=data.get('tasks_id')
        )

        return jsonify({
            'id': record_id,
            'message': 'Запись истории настроения создана'
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/cleanup', methods=['POST'])
@login_required
def cleanup_mood_history():
    try:
        pets = pet_repo.get_by_user_id(current_user.id)
        active_pet = next((pet for pet in pets if pet.life_status == 'alive'), None)

        if not active_pet:
            return jsonify({'error': 'Нет активного питомца'}), 404

        keep_last = request.args.get('keep_last', default=50, type=int)
        pet_mood_history_repo.delete_old_records(active_pet.id, keep_last)

        return jsonify({
            'message': f'Удалены старые записи, сохранено последних {keep_last} записей'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500