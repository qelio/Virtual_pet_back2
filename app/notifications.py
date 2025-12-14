from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from repositories import NotificationRepository
from app import db

notification_repo = NotificationRepository(db)
bp = Blueprint('notifications', __name__, url_prefix='/notifications')


@bp.route('/', methods=['GET'])
@login_required
def get_user_notifications():
    try:
        is_read = request.args.get('is_read', type=lambda x: x.lower() == 'true' if x else None)
        limit = request.args.get('limit', type=int)

        notifications = notification_repo.get_by_user_id(
            user_id=current_user.id,
            is_read=is_read,
            limit=limit
        )
        return jsonify([notification._asdict() for notification in notifications]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:notification_id>', methods=['GET'])
@login_required
def get_notification(notification_id):
    notification = notification_repo.get_by_id(notification_id)
    if not notification:
        return jsonify({'error': 'Уведомление не найдено'}), 404

    if notification.users_id != current_user.id:
        return jsonify({'error': 'Нет доступа к этому уведомлению'}), 403

    return jsonify(notification._asdict()), 200


@bp.route('/', methods=['POST'])
@login_required
def create_notification():
    data = request.get_json()
    required_fields = ['message', 'icon_url']

    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Не все обязательные поля заполнены'}), 400

    try:
        notification_id = notification_repo.create(
            message=data['message'],
            created_at=datetime.utcnow(),
            is_read=False,
            users_id=current_user.id,
            icon_url=data['icon_url']
        )
        return jsonify({'id': notification_id, 'message': 'Уведомление успешно создано'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:notification_id>/read', methods=['PUT'])
@login_required
def mark_notification_as_read(notification_id):
    existing_notification = notification_repo.get_by_id(notification_id)
    if not existing_notification:
        return jsonify({'error': 'Уведомление не найдено'}), 404
    if existing_notification.users_id != current_user.id:
        return jsonify({'error': 'Нет прав для изменения этого уведомления'}), 403

    try:
        notification_repo.mark_as_read(notification_id)
        return jsonify({'message': 'Уведомление отмечено как прочитанное'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/read-all', methods=['PUT'])
@login_required
def mark_all_notifications_as_read():
    try:
        notification_repo.mark_all_as_read(current_user.id)
        return jsonify({'message': 'Все уведомления отмечены как прочитанные'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:notification_id>', methods=['DELETE'])
@login_required
def delete_notification(notification_id):
    existing_notification = notification_repo.get_by_id(notification_id)
    if not existing_notification:
        return jsonify({'error': 'Уведомление не найдено'}), 404
    if existing_notification.users_id != current_user.id:
        return jsonify({'error': 'Нет прав для удаления этого уведомления'}), 403

    try:
        notification_repo.delete(notification_id)
        return jsonify({'message': 'Уведомление успешно удалено'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/all', methods=['GET'])
@login_required
def get_all_notifications():
    if not current_user.role_name == 'admin':
        return jsonify({'error': 'Доступ запрещен'}), 403

    try:
        user_id = request.args.get('user_id', type=int)
        is_read = request.args.get('is_read', type=lambda x: x.lower() == 'true' if x else None)
        limit = request.args.get('limit', type=int)

        notifications = notification_repo.get_all_notifications(
            user_id=user_id,
            is_read=is_read,
            limit=limit
        )
        return jsonify([notification._asdict() for notification in notifications]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500