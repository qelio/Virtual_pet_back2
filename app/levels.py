from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from repositories import LevelRepository
from app import db

level_repo = LevelRepository(db)
bp = Blueprint('levels', __name__, url_prefix='/levels')


@bp.route('/', methods=['GET'])
def get_all_levels():
    try:
        levels = level_repo.all()
        return jsonify([level._asdict() for level in levels]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:level_num>', methods=['GET'])
def get_level(level_num):
    level = level_repo.get_by_level_num(level_num)
    if not level:
        return jsonify({'error': 'Уровень не найден'}), 404
    return jsonify(level._asdict()), 200


@bp.route('/current', methods=['GET'])
@login_required
def get_current_user_level():
    try:
        level = level_repo.get_user_level(current_user.id)
        if not level:
            return jsonify({'message': 'У пользователя еще нет уровня'}), 404
        return jsonify(level._asdict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/next', methods=['GET'])
@login_required
def get_next_level():
    try:
        current_level = level_repo.get_user_level(current_user.id)
        if not current_level:
            first_level = level_repo.get_by_level_num(1)
            return jsonify(first_level._asdict()), 200

        next_level = level_repo.get_next_level(current_level.level_num)
        if not next_level:
            return jsonify({'message': 'Это максимальный уровень'}), 404

        return jsonify(next_level._asdict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/by-experience/<int:experience>', methods=['GET'])
def get_level_by_experience(experience):
    try:
        level = level_repo.get_by_experience(experience)
        if not level:
            return jsonify({'error': 'Нет уровня для указанного опыта'}), 404
        return jsonify(level._asdict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/set-level/<int:level_num>', methods=['PUT'])
@login_required
def set_user_level(level_num):
    target_level = level_repo.get_by_level_num(level_num)
    if not target_level:
        return jsonify({'error': 'Указанный уровень не существует'}), 404

    try:
        level_repo.set_user_level(current_user.id, level_num)
        return jsonify({'message': f'Уровень пользователя установлен на {level_num}'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/progress', methods=['GET'])
@login_required
def get_level_progress():
    try:
        current_level = level_repo.get_user_level(current_user.id)
        if not current_level:
            current_level = level_repo.get_by_level_num(1)
            if not current_level:
                return jsonify({'error': 'Система уровней не настроена'}), 404
            return jsonify({
                'current_level': current_level._asdict(),
                'progress': 0,
                'next_level': None,
                'experience_remaining': current_level.experience_num
            }), 200

        next_level = level_repo.get_next_level(current_level.level_num)

        user_points = getattr(current_user, 'current_points', 0)

        if next_level:
            progress = min(100, (user_points - current_level.experience_num) /
                           (next_level.experience_num - current_level.experience_num) * 100)
            experience_remaining = next_level.experience_num - user_points
        else:
            progress = 100
            experience_remaining = 0

        return jsonify({
            'current_level': current_level._asdict(),
            'progress': round(progress, 2),
            'next_level': next_level._asdict() if next_level else None,
            'experience_remaining': max(0, experience_remaining)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500