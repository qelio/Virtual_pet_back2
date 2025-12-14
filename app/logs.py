from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from repositories import LogActionRepository, LogAuthRepository

log_action_repo = LogActionRepository(db)
log_auth_repo = LogAuthRepository(db)

bp = Blueprint('logs', __name__, url_prefix='/logs')


@bp.route('/actions', methods=['GET'])
@login_required
def get_all_actions():
    if not current_user.role_name == 'admin':
        return jsonify({'error': 'Доступ запрещен. Требуются права администратора'}), 403
    logs = log_action_repo.get_all()
    return jsonify([log._asdict() for log in logs]), 200


@bp.route('/actions/<int:log_id>', methods=['GET'])
@login_required
def get_action(log_id):
    log = log_action_repo.get_by_id(log_id)
    if not log:
        return jsonify({'error': 'Лог не найден'}), 404

    if not current_user.role_name == 'admin' and log.users_id != current_user.id:
        return jsonify({'error': 'Доступ запрещен'}), 403

    return jsonify(log._asdict()), 200


@bp.route('/actions/user/<int:user_id>', methods=['GET'])
@login_required
def get_user_actions(user_id):
    if not current_user.role_name == 'admin' and user_id != current_user.id:
        return jsonify({'error': 'Доступ запрещен'}), 403

    limit = request.args.get('limit', default=None, type=int)
    logs = log_action_repo.get_by_user_id(user_id, limit)
    return jsonify([log._asdict() for log in logs]), 200


@bp.route('/actions/cleanup', methods=['POST'])
@login_required
def clean_up_actions():
    if not current_user.role_name == 'admin':
        return jsonify({'error': 'Доступ запрещен. Требуются права администратора'}), 403

    days = request.json.get('days', 30)
    log_action_repo.delete_old_logs(days)
    return jsonify({'message': f'Старые логи (старше {days} дней) удалены'}), 200


@bp.route('/auth', methods=['GET'])
@login_required
def get_all_auth_logs():
    if not current_user.role_name == 'admin':
        return jsonify({'error': 'Доступ запрещен. Требуются права администратора'}), 403
    logs = log_auth_repo.get_all()
    return jsonify([log._asdict() for log in logs]), 200


@bp.route('/auth/<int:log_id>', methods=['GET'])
@login_required
def get_auth_log(log_id):
    log = log_auth_repo.get_by_id(log_id)
    if not log:
        return jsonify({'error': 'Лог аутентификации не найден'}), 404

    if not current_user.role_name == 'admin' and log.users_id != current_user.id:
        return jsonify({'error': 'Доступ запрещен'}), 403

    return jsonify(log._asdict()), 200


@bp.route('/auth/user/<int:user_id>', methods=['GET'])
@login_required
def get_user_auth_logs(user_id):
    if not current_user.role_name == 'admin' and user_id != current_user.id:
        return jsonify({'error': 'Доступ запрещен'}), 403

    logs = log_auth_repo.get_by_user_id(user_id)
    return jsonify([log._asdict() for log in logs]), 200


@bp.route('/auth/cleanup', methods=['POST'])
@login_required
def clean_up_auth_logs():
    if not current_user.role_name == 'admin':
        return jsonify({'error': 'Доступ запрещен. Требуются права администратора'}), 403

    user_id = request.json.get('user_id')
    keep_last = request.json.get('keep_last', 5)

    if user_id:
        log_auth_repo.delete_old_logs(user_id, keep_last)
        return jsonify(
            {'message': f'Для пользователя {user_id} сохранены последние {keep_last} логов аутентификации'}), 200
    else:
        return jsonify({'error': 'Не указан user_id'}), 400