from flask import Blueprint, render_template, session, redirect, url_for, request, make_response, flash
from flask import Flask, request, jsonify, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from app import login_manager
from repositories import PetRepository, LogActionRepository
from app import db
from datetime import datetime
pet_repo = PetRepository(db)
log_action_repo = LogActionRepository(db)
bp = Blueprint('pets', __name__, url_prefix='/pets')


@bp.route('/<int:pet_id>', methods=['GET'])
def get_pet(pet_id):
    pet = pet_repo.get_by_id(pet_id)
    if not pet:
        return jsonify({'error': 'Питомец не найден'}), 404
    return jsonify(pet._asdict()), 200


@bp.route('/active', methods=['GET'])
@login_required
def get_active_pet():
    pets = pet_repo.get_by_user_id(current_user.id)
    active_pet = next((pet for pet in pets if pet.life_status == 'alive'), None)

    if not active_pet:
        return jsonify({'error': 'Активный питомец не найден'}), 404

    return jsonify(active_pet._asdict()), 200


@bp.route('/user/<int:user_id>', methods=['GET'])
def get_user_pets(user_id):
    pets = pet_repo.get_by_user_id(user_id)
    return jsonify([pet._asdict() for pet in pets]), 200


@bp.route('/create', methods=['POST'])
def create_pet():
    data = request.get_json()
    required_fields = ['name', 'mood', 'picture_url', 'life_status', 'experience_dead']

    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Не все обязательные поля заполнены'}), 400

    try:
        pet_id = pet_repo.create(
            name=data['name'],
            mood=data['mood'],
            picture_url=data['picture_url'],
            created_at=datetime.utcnow(),
            life_status=data['life_status'],
            users_id=current_user.id,
            experience_dead=data['experience_dead']
        )
        log_action_repo.create('Создание нового питомца', datetime.utcnow(), current_user.id)
        return jsonify({'id': pet_id, 'message': 'Питомец успешно создан'}), 201
    except Exception as e:
        print(str(e))
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:pet_id>', methods=['PUT'])
def update_pet(pet_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Нет данных для обновления'}), 400

    try:
        pet_repo.update(
            pet_id=pet_id,
            name=data.get('name'),
            mood=data.get('mood'),
            picture_url=data.get('picture_url'),
            life_status=data.get('life_status'),
            experience_dead=data.get('experience_dead')
        )
        return jsonify({'message': 'Информация о питомце обновлена'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:pet_id>', methods=['DELETE'])
def delete_pet(pet_id):
    try:
        pet_repo.delete(pet_id)
        return jsonify({'message': 'Питомец успешно удален'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500