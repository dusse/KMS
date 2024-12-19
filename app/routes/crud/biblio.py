from flask import Blueprint, request, jsonify, flash, redirect, url_for, current_app, send_file, abort
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user

from app.decorators import role_required

from app.models import ProgressStatus, Log, File, Biblio, Role
from app import db
from datetime import datetime

import os
import uuid

bp = Blueprint('biblio', __name__)


def ensure_upload_folder_exists():

    uploads_dir = os.path.join(current_app.static_folder, current_app.config['BIBLIO_UPLOAD_FOLDER'])
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)
    return uploads_dir


def delete_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)


def save_file(uploaded_file):

    ensure_upload_folder_exists()
    filename = secure_filename(uploaded_file.filename)
    unique_filename = str(uuid.uuid4())
    _, file_extension = os.path.splitext(uploaded_file.filename)
    filename = f"{unique_filename}_{filename}"

    filepath = os.path.join(current_app.static_folder, current_app.config['BIBLIO_UPLOAD_FOLDER'], filename)
    uploaded_file.save(filepath)
    return filename


@bp.route('/add', methods=['POST'])
@login_required
@role_required(Role.OWNER, Role.WORKER)
def add_biblio():
    current_app.logger.debug("Entering add_biblio function")

    # Get form data with validation
    name = request.form.get('name')
    title = request.form.get('title')
    authors = request.form.get('authors')
    year = request.form.get('year')
    bibtex = request.form.get('bibtex')
    file = request.files.get('file')

    current_app.logger.debug(f"Form data - Title: {title}, Authors: {authors}, Year: {year}, BibTeX: {bibtex}")
    current_app.logger.debug(f"File received: {bool(file)}")

    # Check if required fields are provided
    if not name or not title or not authors or not year or not bibtex:
        current_app.logger.error("Missing required fields!")
        return jsonify({'message': 'Missing required fields'}), 400

    # Process file upload if a file was provided
    file_id = None
    if file:
        original_filename = secure_filename(file.filename)
        filename = f"{uuid.uuid4().hex}_{original_filename}"
        filepath = os.path.join( filename)

        # Ensure the upload directory exists
        upload_folder = current_app.config['BIBLIO_UPLOAD_FOLDER']
        if not os.path.exists(upload_folder):
            try:
                os.makedirs(upload_folder)
                current_app.logger.debug(f"Created upload directory at: {upload_folder}")
            except Exception as e:
                current_app.logger.error(f"Error creating directory: {e}")
                return jsonify({'message': f'Error creating directory: {e}'}), 500

        # Attempt to save the file
        try:
            filename = save_file(file)  # Save file and get filename
            current_app.logger.debug(f"File saved at: {filename}")
            # Create a new File entry in the database
            new_file = File(filename=filename, filepath=os.path.join(upload_folder, filename), uploaded_at=datetime.utcnow())
            db.session.add(new_file)
            db.session.flush()  # Ensure new_file.id is available
            file_id = new_file.id
            current_app.logger.debug(f"File ID: {file_id}")
        except Exception as e:
            current_app.logger.error(f"Error saving file: {e}")
            return jsonify({'message': f'Error saving file: {e}'}), 500
    else:
        current_app.logger.debug("No file uploaded.")
        file_id = None

    # Create the new Biblio entry
    try:
        current_app.logger.debug(f"Creating new Biblio entry with title: {title}, authors: {authors}, year: {year}, bibtex: {bibtex}, file_id: {file_id}")

        new_biblio = Biblio(name=name, title=title, authors=authors, year=year, bibtex=bibtex, file_id=file_id)
        db.session.add(new_biblio)
        db.session.commit()
        current_app.logger.debug(f"Biblio entry added successfully with ID: {new_biblio.id}")

    except Exception as e:
        current_app.logger.error(f"Error saving Biblio entry: {e}")
        db.session.rollback()
        return jsonify({'message': f'Error saving bibliography entry: {e}'}), 500
    current_app.logger.debug("Bibliography added successfully")
    return jsonify({'message': 'Bibliography added successfully'}), 201




@bp.route('/edit', methods=['POST'])
@login_required
@role_required(Role.OWNER, Role.WORKER)
def edit_biblio():
    # Retrieve the biblio ID and form data
    biblio_id = request.form['id']
    name = request.form.get('name')
    title = request.form.get('title')
    authors = request.form.get('authors')
    year = request.form.get('year')
    bibtex = request.form.get('bibtex')
    file = request.files.get('file')

    # Find the Biblio entry to be updated
    biblio = Biblio.query.get(biblio_id)
    if not biblio:
        return jsonify({'message': 'Bibliography not found'}), 404

    # Update only the fields that are provided
    if name:
        biblio.name = name
    if title:
        biblio.title = title
    if authors:
        biblio.authors = authors
    if year:
        biblio.year = year
    if bibtex:
        biblio.bibtex = bibtex

    # Process file upload if a file was provided
    if file:
        original_filename = secure_filename(file.filename)
        filename = f"{uuid.uuid4().hex}_{original_filename}"
        filepath = os.path.join(current_app.config['BIBLIO_UPLOAD_FOLDER'], filename)

        # Ensure the upload directory exists
        upload_folder = current_app.config['BIBLIO_UPLOAD_FOLDER']
        if not os.path.exists(upload_folder):
            try:
                os.makedirs(upload_folder)
            except Exception as e:
                return jsonify({'message': f'Error creating directory: {e}'}), 500

        # Attempt to save the file
        try:
            file.save(filepath)
            # Create a new File entry in the database
            new_file = File(filename=filename, filepath=filepath, uploaded_at=datetime.utcnow())
            db.session.add(new_file)
            db.session.flush()  # Ensure new_file.id is available

            # Update the Biblio entry with the new file_id
            biblio.file_id = new_file.id
        except Exception as e:
            return jsonify({'message': f'Error saving file: {e}'}), 500

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error updating bibliography entry: {e}'}), 500

    return jsonify({'message': 'Bibliography updated successfully'}), 200


@bp.route('/delete/<int:id>', methods=['DELETE'])
@login_required
@role_required(Role.OWNER, Role.WORKER)
def delete_biblio(id):
    biblio = Biblio.query.get(id)
    if not biblio:
        return jsonify({'message': 'Bibliography not found'}), 404

    # If there is an associated file, delete it
    if biblio.file_id:
        file = File.query.get(biblio.file_id)
        if file:
            file_path = os.path.join(current_app.static_folder, current_app.config['BIBLIO_UPLOAD_FOLDER'], file.filename)
            delete_file(file_path) 
            db.session.delete(file)

    # Delete Biblio entry from database
    db.session.delete(biblio)
    db.session.commit()
    return jsonify({'message': 'Bibliography deleted successfully'}), 200


@bp.route('/download/<int:id>', methods=['GET'])
@login_required
@role_required(Role.OWNER, Role.WORKER)
def download_biblio_file(id):
    # Find the Biblio entry
    biblio = Biblio.query.get(id)
    if not biblio:
        return jsonify({'message': 'Bibliography not found'}), 404

    # Check if the Biblio entry has an associated file
    if not biblio.file_id:
        return jsonify({'message': 'No file associated with this bibliography entry'}), 404

    # Get the File entry using the file_id
    file_entry = File.query.get(biblio.file_id)
    if not file_entry:
        return jsonify({'message': 'File record not found'}), 404

    path = os.path.join(current_app.static_folder, current_app.config['BIBLIO_UPLOAD_FOLDER'], file_entry.filename)
    # Verify the file exists on the filesystem
    if not os.path.isfile(path):
        return jsonify({'message': 'File not found on the server'}), 404

    # Send the file to the user
    return send_file(path, as_attachment=True, download_name=file_entry.filename)



