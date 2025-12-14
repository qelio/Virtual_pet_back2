from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from repositories import ExperienceCounterRepository
from app import db

exp_repo = ExperienceCounterRepository(db)
bp = Blueprint('experience', __name__, url_prefix='/experience')


@bp.route('/', methods=['GET'])
@login_required
def get_user_experience_logs():
    try:
        limit = request.args.get('limit', type=int)

        logs = exp_repo.get_by_user_id(
            user_id=current_user.id,
            limit=limit
        )
        return jsonify([log._asdict() for log in logs]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:counter_id>', methods=['GET'])
@login_required
def get_experience_entry(counter_id):
    entry = exp_repo.get_by_id(counter_id)
    if not entry:
        return jsonify({'error': 'Запись не найдена'}), 404

    if entry.users_id != current_user.id:
        return jsonify({'error': 'Нет доступа к этой записи'}), 403

    return jsonify(entry._asdict()), 200


@bp.route('/', methods=['POST'])
@login_required
def create_experience_entry():
    data = request.get_json()
    required_fields = ['action_type', 'total_points']

    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Не все обязательные поля заполнены'}), 400

    try:
        entry_id = exp_repo.create(
            action_date=datetime.utcnow(),
            experience_adding_tasks_id=data.get('task_id'),
            experience_subtraction_pets_id=data.get('pet_id'),
            users_id=current_user.id,
            total_points=data['total_points'],
            action_type=data['action_type']
        )
        return jsonify({'id': entry_id, 'message': 'Запись опыта создана'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/total', methods=['GET'])
@login_required
def get_total_experience():
    try:
        total = exp_repo.get_user_total_points(current_user.id)
        return jsonify({'total_points': total}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/history', methods=['GET'])
@login_required
def get_experience_history():
    try:
        logs = exp_repo.get_by_user_id(current_user.id)

        history = {}
        for log in logs:
            date = log.action_date.date().isoformat()
            if date not in history:
                history[date] = {
                    'date': date,
                    'total': 0,
                    'actions': []
                }
            history[date]['total'] += log.total_points
            history[date]['actions'].append({
                'type': log.action_type,
                'points': log.total_points,
                'time': log.action_date.time().isoformat()
            })

        result = sorted(history.values(), key=lambda x: x['date'], reverse=True)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500