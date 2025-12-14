from flask import Blueprint, request, jsonify, session, current_app
from flask_login import login_required, current_user
from datetime import datetime
from repositories import UserRepository
from app import db
import os
from werkzeug.utils import secure_filename
from flask import send_from_directory

user_repo = UserRepository(db)
bp = Blueprint('users', __name__, url_prefix='/users')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
AVATARS_FOLDER = 'static/images/avatars'
DEFAULT_AVATAR = 'static/images/default-avatar.png'

os.makedirs(AVATARS_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/', methods=['GET'])
@login_required
def get_all_users():
    try:
        users = user_repo.all()
        return jsonify([dict(user) for user in users]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:user_id>', methods=['GET'])
@login_required
def get_user(user_id):
    user = user_repo.get_by_id(user_id)
    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404
    return jsonify(dict(user)), 200


@bp.route('/current', methods=['GET'])
@login_required
def get_current_user():
    user = user_repo.get_by_id(current_user.id)
    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404
    return jsonify(dict(user)), 200


@bp.route('/username/<string:username>', methods=['GET'])
@login_required
def get_user_by_username(username):
    user = user_repo.get_by_username(username)
    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404
    return jsonify(dict(user)), 200


@bp.route('/email/<string:email>', methods=['GET'])
@login_required
def get_user_by_email(email):
    user = user_repo.get_by_email(email)
    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404
    return jsonify(dict(user)), 200



@bp.route('/update', methods=['PUT'])
@login_required
def update_user():

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Нет данных для обновления'}), 400

    try:
        user_repo.update(
            user_id=current_user.id,
            username=data.get('username'),
            email=data.get('email'),
            avatar=data.get('avatar')
        )
        return jsonify({'message': 'Данные пользователя обновлены'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/admin/update/<int:user_id>', methods=['PUT'])
@login_required
def admin_update_user(user_id):
    if not current_user.role_name == 'admin':
        return jsonify({'error': 'Недостаточно прав'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Нет данных для обновления'}), 400

    try:
        user_repo.update(
            user_id=user_id,
            username=data.get('username'),
            email=data.get('email'),
            avatar=data.get('avatar'),
        )
        return jsonify({'message': 'Данные пользователя обновлены админом'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/password/<int:user_id>', methods=['PUT'])
@login_required
def update_user_password(user_id):
    if current_user.id != user_id:
        return jsonify({'error': 'Недостаточно прав'}), 403

    data = request.get_json()
    if 'new_password' not in data:
        return jsonify({'error': 'Не указан новый пароль'}), 400

    try:
        user_repo.update_password(
            user_id=user_id,
            new_password=data['new_password']
        )
        return jsonify({'message': 'Пароль успешно изменен'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    if current_user.id != user_id and not current_user.is_admin:
        return jsonify({'error': 'Недостаточно прав'}), 403

    try:
        user_repo.delete(user_id)
        return jsonify({'message': 'Пользователь успешно удален'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/authenticate', methods=['POST'])
def authenticate():
    data = request.get_json()
    if 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Необходимо указать имя пользователя и пароль'}), 400

    user = user_repo.authenticate(data['username'], data['password'])
    if not user:
        return jsonify({'error': 'Неверные учетные данные'}), 401

    return jsonify({'message': 'Аутентификация успешна', 'user': dict(user)}), 200


@bp.route('/avatar/<int:user_id>', methods=['POST'])
@login_required
def upload_avatar(user_id):
    if current_user.id != user_id and not current_user.is_admin:
        return jsonify({'error': 'Недостаточно прав'}), 403

    if 'file' not in request.files:
        return jsonify({'error': 'Файл не найден в запросе'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'Файл не выбран'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Недопустимый формат файла'}), 400

    try:
        user_folder = os.path.join(current_app.root_path, AVATARS_FOLDER, str(user_id))
        os.makedirs(user_folder, exist_ok=True)

        filename = secure_filename(file.filename)
        filepath = os.path.join(user_folder, filename)

        file.save(filepath)

        avatar_url = f"/{AVATARS_FOLDER}/{user_id}/{filename}"

        user_repo.update(user_id=user_id, avatar=avatar_url)

        return jsonify({
            'message': 'Аватар успешно загружен',
            'avatar_url': avatar_url
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error uploading avatar: {str(e)}")
        return jsonify({'error': str(e)}), 500


@bp.route('/avatar/<int:user_id>', methods=['GET'])
def get_avatar(user_id):
    try:
        user = user_repo.get_by_id(user_id)
        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 404

        if user['avatar']:
            avatar_path = user['avatar'].lstrip('/')
            avatar_path = os.path.join(current_app.root_path, avatar_path)
            if os.path.exists(avatar_path):
                return send_from_directory(
                    directory=os.path.dirname(avatar_path),
                    path=os.path.basename(avatar_path),
                    as_attachment=False
                )

        default_path = os.path.join(current_app.root_path, DEFAULT_AVATAR)
        if not os.path.exists(default_path):
            return jsonify({'error': 'Default avatar not found'}), 404

        return send_from_directory(
            directory=os.path.dirname(DEFAULT_AVATAR),
            path=os.path.basename(DEFAULT_AVATAR),
            as_attachment=False
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500