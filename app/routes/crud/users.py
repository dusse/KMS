from flask import Blueprint, request, jsonify, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from app.decorators import role_required
from app.models import User, Role
from app.models.crud_base import CRUDBase
from app import db

bp = Blueprint('users', __name__)

crud_user = CRUDBase(User)

@bp.route('/users', methods=['POST'])
@login_required
@role_required(Role.OWNER)
def create_user():
    data = request.get_json()

    # Convert the incoming role to uppercase to match the Enum values
    role = data.get('role', '').upper()
    if role not in [role.name for role in Role]:
        return jsonify({'error': f'Invalid role specified. Allowed roles are: {[role.name for role in Role]}'}), 400

    # Validate required fields
    if 'name' not in data or 'password' not in data or 'role' not in data:
        return jsonify({'error': 'Name, password, and role are required.'}), 400

    # Convert role to Enum before saving
    data['role'] = Role[role]

    # Create a new User instance and set the password
    new_user = crud_user.create({k: v for k, v in data.items() if k != 'password'})
    new_user.set_password(data['password'])

    try:
        db.session.add(new_user)
        db.session.commit()
        flash('user is added.', 'success')
        return jsonify({'message': 'User added successfully'}), 200
    except IntegrityError as e:
        db.session.rollback()
        current_app.logger.error("IntegrityError:", str(e))
        return jsonify({'error': 'User with this name already exists.'}), 400
    except Exception as e:
        current_app.logger.error("Exception:", str(e))
        return jsonify({'error': 'An unexpected error occurred.'}), 500


@bp.route('/users/<int:user_id>', methods=['PUT'])
@login_required
@role_required(Role.OWNER)
def update_user(user_id):
    data = request.get_json()
    try:
        updated_user = crud_user.update(user_id, data)
        if updated_user is None:
            return jsonify({'error': 'User not found'}), 404

        flash('user is updated.', 'success')
        return jsonify({'message': 'User updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400



@bp.route('/users/<int:user_id>', methods=['DELETE'])
@login_required
@role_required(Role.OWNER)
def delete_user(user_id):
    user = crud_user.get(user_id)

    if user is None:
        return jsonify({'error': 'User not found'}), 404

    # Prevent deletion of the owner
    if user.role == Role.OWNER:
        return jsonify({'error': 'Cannot delete an owner'}), 403

    try:
        crud_user.delete(user_id)
        return jsonify({'message': 'User deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
