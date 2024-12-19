from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import  login_user, login_required, logout_user, current_user

from datetime import datetime, timedelta

from app.models import User, Role, LoginForm, ChangeCredentialsForm
import os
from app import db, login_manager

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from werkzeug.security import generate_password_hash

bp = Blueprint('auth', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(name=form.name.data).first()
        session.clear()
        if user and user.check_password(form.password.data):
            login_user(user)
            if user.first_login:
                return redirect(url_for('auth.change_credentials'))

            if user.role == Role.WORKER:
                return redirect(url_for('workerflow.worker_space'))
            elif user.role == Role.OWNER:                
                return redirect(url_for('ownerflow.owner_space'))
        else:
            flash('wrong name or password!', 'danger')
            
    return render_template('auth/login.html', form=form)



@bp.route('/change_credentials', methods=['GET', 'POST'])
@login_required
def change_credentials():
    form = ChangeCredentialsForm()
    if form.validate_on_submit():
        current_user.set_password(form.new_password.data)
        current_user.first_login = False
        db.session.commit()
        flash('password is updated.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/change_credentials.html', form=form)


@bp.route('/reset_password', methods=['POST'])
@login_required
def reset_password():
    data = request.get_json()
    user_id = data['user_id']
    new_password = data['new_password']

    user = User.query.get(user_id)
    if not user:
        flash('User not found', 'danger')
        return jsonify({'error': 'User not found'}), 404

    user.reset_password(new_password)
    flash('passowrd is updated.', 'success')
    return jsonify({'message': 'пароль обновлен'}), 200



@bp.route('/logout')
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('auth.login'))