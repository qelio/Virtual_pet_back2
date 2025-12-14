from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from repositories import AchievementRepository
from app import db

achievement_repo = AchievementRepository(db)
bp = Blueprint('achievements', __name__, url_prefix='/achievements')


@bp.route('/', methods=['GET'])
def get_all_achievements():
    try:
        achievements = achievement_repo.all()
        return jsonify([achievement._asdict() for achievement in achievements]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:achievement_id>', methods=['GET'])
def get_achievement(achievement_id):
    achievement = achievement_repo.get_by_id(achievement_id)
    if not achievement:
        return jsonify({'error': 'Достижение не найдено'}), 404
    return jsonify(achievement._asdict()), 200


@bp.route('/user', methods=['GET'])
@login_required
def get_user_achievements():
    try:
        achievements = achievement_repo.get_user_achievements(current_user.id)
        return jsonify([{
            'id': a.id,
            'title': a.title,
            'description': a.description,
            'experience_num': a.experience_num,
            'icon_url': a.icon_url,
            'received_at': a.received_at.isoformat() if a.received_at else None
        } for a in achievements]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/', methods=['POST'])
@login_required
def create_achievement():
    if not current_user.role_name == 'admin':
        return jsonify({'error': 'Недостаточно прав'}), 403

    data = request.get_json()
    required_fields = ['title', 'description', 'icon_url']

    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Не все обязательные поля заполнены'}), 400

    try:
        achievement_id = achievement_repo.create(
            title=data['title'],
            description=data['description'],
            experience_num=data.get('experience_num', 0),
            icon_url=data['icon_url']
        )
        return jsonify({'id': achievement_id, 'message': 'Достижение создано'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:achievement_id>', methods=['PUT'])
@login_required
def update_achievement(achievement_id):
    if not current_user.role_name == 'admin':
        return jsonify({'error': 'Недостаточно прав'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Нет данных для обновления'}), 400

    try:
        achievement_repo.update(
            achievement_id=achievement_id,
            title=data.get('title'),
            description=data.get('description'),
            experience_num=data.get('experience_num'),
            icon_url=data.get('icon_url')
        )
        return jsonify({'message': 'Достижение обновлено'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:achievement_id>', methods=['DELETE'])
@login_required
def delete_achievement(achievement_id):
    if not current_user.role_name == 'admin':
        return jsonify({'error': 'Недостаточно прав'}), 403

    try:
        achievement_repo.delete(achievement_id)
        return jsonify({'message': 'Достижение удалено'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/grant/<int:achievement_id>', methods=['POST'])
@login_required
def grant_achievement(achievement_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Недостаточно прав'}), 403

    achievement = achievement_repo.get_by_id(achievement_id)
    if not achievement:
        return jsonify({'error': 'Достижение не найдено'}), 404

    data = request.get_json()
    if 'user_id' not in data:
        return jsonify({'error': 'Не указан пользователь'}), 400

    try:
        user_achievements = achievement_repo.get_user_achievements(data['user_id'])
        if any(a.id == achievement_id for a in user_achievements):
            return jsonify({'error': 'У пользователя уже есть это достижение'}), 400

        achievement_repo.add_user_achievement(data['user_id'], achievement_id)
        return jsonify({'message': 'Достижение присвоено пользователю'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/unlock', methods=['POST'])
@login_required
def unlock_achievement():
    data = request.get_json()
    if 'achievement_id' not in data:
        return jsonify({'error': 'Не указано достижение'}), 400

    achievement = achievement_repo.get_by_id(data['achievement_id'])
    if not achievement:
        return jsonify({'error': 'Достижение не найдено'}), 404

    try:
        user_achievements = achievement_repo.get_user_achievements(current_user.id)
        if any(a.id == data['achievement_id'] for a in user_achievements):
            return jsonify({'error': 'У вас уже есть это достижение'}), 400

        achievement_repo.add_user_achievement(current_user.id, data['achievement_id'])
        return jsonify({'message': 'Достижение разблокировано'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500