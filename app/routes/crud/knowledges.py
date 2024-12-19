from flask import Blueprint, request, jsonify, flash, redirect, url_for, current_app, send_file, abort
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user

import json

from app.decorators import role_required
from app.models import Role, Knowledge, KnownItem
from app.models import ProgressStatus, Log, File
from app import db
from datetime import datetime
from sqlalchemy import or_, and_
from sqlalchemy.orm import joinedload

import os
import uuid

bp = Blueprint('knowledges', __name__)


import zipfile
from io import BytesIO

def generate_knowledge_zip(knowledge_id):
    # Fetch the knowledge object
    knowledge = Knowledge.query.get(knowledge_id)
    if not knowledge:
        return None, 'Knowledge not found'

    # Initialize a BytesIO object to store the zip file in memory
    zip_buffer = BytesIO()

    # Create a zip file in memory
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Create a JSON representation of the knowledge and known items
        knowledge_data = {
            'id': knowledge.id,
            'name': knowledge.name,
            'description': knowledge.description,
            'theme_name': knowledge.theme_name,
            'created_at': knowledge.created_at.isoformat(),
            'updated_at': knowledge.updated_at.isoformat(),
            'known_items': []
        }

        # Add the known items to the knowledge data
        for item in knowledge.known_items:
            item_data = {
                'id': item.id,
                'name': item.name,
                'description': item.description,
                'typename': item.typename,
                'imgsrc': item.imgsrc,
                'filename': item.file.filename if item.file else None,
                'content': item.content,
                'created_at': item.created_at.isoformat(),
                'order': item.order
            }

            knowledge_data['known_items'].append(item_data)
            upld_fld = os.path.join(current_app.static_folder, current_app.config['UPLOAD_FOLDER'])
            # Add the file associated with the known item, if it exists
            if item.file:
                file_path = os.path.join(upld_fld, item.file.filename)
                if os.path.exists(file_path):
                    filename = secure_filename(item.file.filename)
                    zip_file.write(file_path, arcname=f"files/{filename}")
                else:
                    current_app.logger.debug(f"File not found: {file_path}")

            # Add the image associated with the known item, if it exists
            if item.imgsrc:
                img_path = os.path.join(upld_fld, item.imgsrc)
                if os.path.exists(img_path):
                    img_filename = secure_filename(os.path.basename(item.imgsrc))
                    zip_file.write(img_path, arcname=f"images/{img_filename}")
                else:
                    current_app.logger.debug(f"Image not found: {img_path}")
        
        # Add the knowledge data as a JSON file in the zip
        json_filename = f'knowledge_{knowledge.id}.json'
        zip_file.writestr(json_filename, json.dumps(knowledge_data, indent=4))

    # Go back to the start of the BytesIO buffer
    zip_buffer.seek(0)
    
    return zip_buffer, None

@bp.route('/download_knowledge/<int:knowledge_id>', methods=['GET'])
@login_required
@role_required(Role.OWNER, Role.WORKER)
def download_knowledge(knowledge_id):
    try:
        # Generate the knowledge zip file
        zip_buffer, error = generate_knowledge_zip(knowledge_id)
        if error:
            return jsonify({'error': error}), 404
        
        # Send the zip file as a response
        return send_file(
            zip_buffer,
            as_attachment=True,
            download_name=f'knowledge_{knowledge_id}.zip',
            mimetype='application/zip'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def handle_uploaded_file(uploaded_file):
    """Handle the uploaded file and extract the knowledge."""
    upload_folder = os.path.join(current_app.static_folder, current_app.config['UPLOAD_FOLDER'])
    zip_path = os.path.join(upload_folder, secure_filename(uploaded_file.filename))
    temp_extract_folder = os.path.join(upload_folder, f"temp_{generate_random_string()}")

    # Save the uploaded file and extract it
    uploaded_file.save(zip_path)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_extract_folder)
        
        # Find and read the JSON data file
        knowledge_json_file = next((f for f in zip_ref.namelist() if f.endswith('.json')), None)
        if not knowledge_json_file:
            raise ValueError("Knowledge JSON file not found in the ZIP.")
        
        knowledge_data = json.loads(zip_ref.read(knowledge_json_file))
        
        # Generate a unique knowledge name
        unique_name = get_unique_knowledge_name(knowledge_data['name'])

        # Create the new Knowledge object with a unique name
        new_knowledge = Knowledge(
            name=unique_name,
            description=knowledge_data['description'],
            theme_name=knowledge_data['theme_name'],
            creator_name=current_user.name
        )
        db.session.add(new_knowledge)
        db.session.commit()

        # Process known items
        for item_data in knowledge_data['known_items']:
            new_item = KnownItem(
                name=item_data['name'],
                description=item_data['description'],
                typename=item_data['typename'],
                content=item_data['content'],
                knowledgename=new_knowledge.name,
                order=item_data['order']
            )
            db.session.add(new_item)

            # Handle file restoration (if a file is present)
            if item_data.get('filename'):

                file_relative_path = os.path.join("files", item_data['filename'])
                file_abs_path = os.path.join(temp_extract_folder, file_relative_path)
                if os.path.exists(file_abs_path):
                    # Save file with a unique name
                    new_file_name = f"{generate_random_string()}_{item_data['filename']}"
                    new_file_path = os.path.join(upload_folder, new_file_name)
                    with open(new_file_path, 'wb') as f:
                        f.write(open(file_abs_path, 'rb').read())

                    # Create File record in DB
                    new_file = File(filename=new_file_name, filepath=new_file_path)
                    db.session.add(new_file)
                    db.session.commit()
                    new_item.file_id = new_file.id


            # Handle image restoration (if an image is present)
            if item_data.get('imgsrc'):
                img_relative_path = os.path.join("images", item_data['imgsrc'])
                img_abs_path = os.path.join(temp_extract_folder, img_relative_path)
                if os.path.exists(img_abs_path):
                    # Save image with a unique name
                    new_img_name = f"{generate_random_string()}_{item_data['imgsrc']}"
                    new_img_path = os.path.join(upload_folder, new_img_name)
                    with open(new_img_path, 'wb') as f:
                        f.write(open(img_abs_path, 'rb').read())

                    # Set the imgsrc to the new image path
                    new_item.imgsrc = new_img_name

            db.session.commit()

    # Clean up: remove the ZIP file and the temporary extraction folder
    os.remove(zip_path)
    rmtree(temp_extract_folder)

@bp.route('/upload_knowledge', methods=['POST'])
@login_required
@role_required(Role.OWNER, Role.WORKER)
def upload_knowledge():
    try:
        uploaded_file = request.files['file']
        handle_uploaded_file(uploaded_file)
        return jsonify({'message': 'Knowledge uploaded successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def ensure_upload_folder_exists():

    uploads_dir = os.path.join(current_app.static_folder, 'uploads')
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

    filepath = os.path.join(current_app.static_folder, 'uploads', filename)
    uploaded_file.save(filepath)
    return filename

import subprocess

def generate_tex_content(title, items, bib_file_path):
    """Generate LaTeX content with support for Unicode."""
    all_bibs = {}
    for item in items:
        for biblio in item.get_bibliographies():
            if biblio.id not in all_bibs:
                all_bibs[biblio.id] = biblio.bibtex

    os.makedirs(os.path.dirname(bib_file_path), exist_ok=True)
    with open(bib_file_path, "w", encoding="utf-8") as bib_file:
        for bibtex in all_bibs.values():
            bib_file.write(bibtex + "\n\n")

    content = r"""
            \documentclass{article}
            \usepackage[utf8]{inputenc}
            \usepackage[T1]{fontenc}
            \usepackage{amsmath}
            \usepackage{amsfonts}
            \usepackage{graphicx}
            \usepackage{subcaption}
            \usepackage{natbib}
            \usepackage{float}
            
            \begin{document}
            """
    content += f"\\title{{{title}}}\n\\maketitle\n\n"
    sorted_items = sorted(items, key=lambda item: item.order, reverse=False) 
    for item in sorted_items:

        content += f"% {item.name}\n"  # Add item name as a comment        
        
        item_content = item.content        

        if r"\begin{array}" in item_content and r"\end{array}" in item_content:
            item_content = (
                item_content.replace(r"\begin{array}", r"$\newline \centering \begin{array}")
                            .replace(r"\end{array}", r"\end{array}$")
            )

        # If the item has an image, include it
        if item.imgsrc:
            content += f"\\section*{{{item.name}}}\n\n{item_content}\n\n"
            caption = item.description
            content += f"\\begin{{figure}}[H]\\centering\\includegraphics[width=0.7\\textwidth]{{figures/{item.imgsrc}}}\\caption{{{caption}}}\\end{{figure}}\n\n"

        else:
            content += f"\\section*{{{item.name}}}\n{item.description}\n\n{item_content}\n\n"

    content += r"""
            \newpage
            \bibliographystyle{unsrt}
            \bibliography{biblio}
            """

    content += r"\end{document}"
    return content


def generate_tex_and_zip(knowledge, figures_path="figures"):
    items = knowledge.known_items
    title = knowledge.name
    # Step 1: Create a temporary directory inside the static folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_dir = os.path.join(current_app.static_folder, "temp", f"latex_output_{timestamp}")
    os.makedirs(temp_dir, exist_ok=True)
    os.chdir(temp_dir)

    tex_filename = os.path.join(temp_dir, "document.tex")
    aux_filename = os.path.join(temp_dir, "document.aux")
    bib_filename = os.path.join(temp_dir, "biblio.bib")
    pdf_filename = os.path.join(temp_dir, "document.pdf")
    zip_filename = os.path.join(temp_dir, "latex_output.zip")

    figures_dir = os.path.join(temp_dir, "figures")
    os.makedirs(figures_dir, exist_ok=True)
    upload_folder = os.path.join(current_app.static_folder, current_app.config['UPLOAD_FOLDER'])
    for item in items:
        if item.imgsrc:
            src_image_path = os.path.join(upload_folder, item.imgsrc)
            dest_image_path = os.path.join(figures_dir, os.path.basename(item.imgsrc))
            if os.path.exists(src_image_path):
                shutil.copy(src_image_path, dest_image_path)

    # Step 2: Generate LaTeX content from items
    content = generate_tex_content(title, items, bib_filename)


    with open(tex_filename, 'w') as tex_file:
        tex_file.write(content)

    # Step 3: Compile the LaTeX file to PDF, with error handling
    try:
        result = subprocess.run(
            ["pdflatex", "-output-directory", temp_dir, tex_filename],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        if result.returncode != 0:
            current_app.logger.error(f"Error during LaTeX compilation: {result.stderr.decode()}")
            return None

        result = subprocess.run(
            ["bibtex", "document.aux"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        if result.returncode != 0:
            current_app.logger.error(f"Error during BibTeX compilation: {result.stderr.decode()}")
        else:
            current_app.logger.debug(f"BibTeX output:\n{result.stdout.decode()}")

        # Second LaTeX compilation to incorporate bibliography
        result = subprocess.run(
            ["pdflatex", "-output-directory", temp_dir, tex_filename],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        if result.returncode != 0:
            current_app.logger.error(f"Error during second LaTeX compilation: {result.stderr.decode()}")
            return None

        result = subprocess.run(
            ["pdflatex", "-output-directory", temp_dir, tex_filename],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        if result.returncode != 0:
            current_app.logger.error(f"Error during second LaTeX compilation: {result.stderr.decode()}")
            return None
        

    except Exception as e:
        current_app.logger.error(f"Exception during PDF generation: {e}")
        return None

    zip_buffer = BytesIO()
    # Step 4: Create ZIP containing .tex file, PDF, and any figures
    with zipfile.ZipFile(zip_buffer, 'w') as zipf:
        zipf.write(tex_filename, os.path.basename(tex_filename))
        if os.path.exists(pdf_filename):
            zipf.write(pdf_filename, os.path.basename(pdf_filename))
        if os.path.exists(bib_filename):
            zipf.write(bib_filename, os.path.basename(bib_filename))
        
        # Include figures if any exist and the item references an image
        if os.path.exists(figures_dir):
            for root, _, files in os.walk(figures_dir):
                for file in files:
                    img_file_path = os.path.join(root, file)
                    zipf.write(img_file_path, os.path.join("figures", file))

    remove_files_in_directory(temp_dir)        

    zip_buffer.seek(0)
    return zip_buffer


def remove_files_in_directory(directory):
    # Ensure the directory exists
    if os.path.exists(directory) and os.path.isdir(directory):
        # Iterate over all files and subdirectories in the directory
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            try:
                if os.path.isdir(file_path):
                    # Recursively delete subdirectories
                    shutil.rmtree(file_path)
                else:
                    # Remove individual files
                    os.remove(file_path)
            except Exception as e:
                current_app.logger.error(f"Error removing {file_path}: {e}")
        
        # Now remove the empty directory
        try:
            os.rmdir(directory)
            current_app.logger.debug(f"Directory {directory} removed successfully.")
        except Exception as e:
            current_app.logger.error(f"Error removing directory {directory}: {e}")
    else:
        current_app.logger.error(f"The directory {directory} does not exist or is not a valid directory.")



@bp.route('/download_pdf/<int:knowledge_id>')
@login_required
@role_required(Role.OWNER, Role.WORKER)
def download_pdf(knowledge_id):
    # Fetch the knowledge item by ID, including related items
    knowledge = Knowledge.query.get_or_404(knowledge_id)

    # If no items are associated with this knowledge, return an error
    if not knowledge.known_items:
        return jsonify({"error": "No known items found for this knowledge entry."}), 404

    # Generate LaTeX and compile to PDF, packaged as a zip file
    zip_path = generate_tex_and_zip(knowledge)

    if zip_path is None or zip_path.getbuffer().nbytes == 0:
        return jsonify({"error": "Failed to generate the export file."}), 500

    # Serve the zip file as a response
    return send_file(
        zip_path,
        as_attachment=True,
        download_name=f"knowledge_{knowledge_id}_export.zip"
    )



@bp.route('/saveOrder', methods=['POST'])
@login_required
@role_required(Role.OWNER, Role.WORKER)
def save_order():
    try:
        # Receive the order data from the client
        data = request.get_json()  # This is the list of item ids and new orders
        order_data = data.get('order')

        # If order data is not provided, return an error
        if not order_data:
            return jsonify({'success': True, 'message': 'No order data provided.'}), 200

        # Iterate over the order data and update the order of each KnownItem
        for item in order_data:
            item_id = item['itemId']
            new_order = item['newOrder']

            # Find the KnownItem by id and update its order
            known_item = KnownItem.query.get(item_id)
            if known_item:
                known_item.order = new_order
                db.session.commit()

        return jsonify({'success': True, 'message': 'Order saved successfully.'})

    except Exception as e:
        # If there is an error, roll back the transaction
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/item/add', methods=['POST'])
@login_required
@role_required(Role.OWNER, Role.WORKER)
def add_item():
    try:
        # Extract data from the request
        item_name = request.form.get('itemName')
        item_description = request.form.get('itemDescription')
        item_content = request.form.get('itemContent')
        knowledgename = request.form.get('selectedKnowledgeName') 
        typename = request.form.get('selectedKnowledgeTypeName')

        # Validate required fields
        if not item_name or not knowledgename or not typename:
            return jsonify({'error': 'Item name, knowledgename, and selectedKnowledgeTypeName are required.'}), 400

        # Check if the item already exists by name and associated knowledge name
        existing_item = KnownItem.query.filter_by(name=item_name, knowledgename=knowledgename).first()
        if existing_item:
            return jsonify({'error': f'An item with the name "{item_name}" already exists under knowledge "{knowledgename}".'}), 400

        # Handle file uploads
        imgsrc_filename = None
        file_id = None
        
        # Process the imgsrc file upload
        if 'imgsrc' in request.files:
            imgsrc = request.files['imgsrc']
            if imgsrc and imgsrc.filename:
                imgsrc_filename = save_file(imgsrc)

        # Process the file upload
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename:
                filename = save_file(file)  # Save file and get filename
                new_file = File(filename=filename, filepath=os.path.join('uploads', filename))
                db.session.add(new_file)
                db.session.flush()
                file_id = new_file.id

        # Create a new KnownItem instance
        new_item = KnownItem(
            name=item_name,
            description=item_description,
            content=item_content,
            imgsrc=imgsrc_filename if imgsrc_filename else None,
            file_id=file_id,
            knowledgename=knowledgename,
            typename=typename,
            progress_status=ProgressStatus.inprogress
        )

        db.session.add(new_item)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Item added successfully.'}), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@bp.route('/copy/<int:id>', methods=['POST'])
@login_required
@role_required(Role.OWNER, Role.WORKER)
def copy_knowledge_route(id):
    try:
        # Call the `copy_knowledge` function to duplicate the knowledge with the specified ID
        new_knowledge = copy_knowledge(db.session, id)

        # Return the details of the newly copied knowledge
        return jsonify({
            'id': new_knowledge.id,
            'name': new_knowledge.name,
            'description': new_knowledge.description,
            'creator_name': new_knowledge.creator_name,
            'theme_name': new_knowledge.theme_name,
            'created_at': new_knowledge.created_at,
            'updated_at': new_knowledge.updated_at
        })

    except ValueError as e:
        # Handle specific errors like 'knowledge not found'
        db.session.rollback()
        return jsonify({'error': str(e)}), 404
    
    except Exception as e:
        # Roll back session in case of any other exception and return a 500 error
        db.session.rollback()
        current_app.logger.error(f"Error: {str(e)}")
        return jsonify({'error': 'An error occurred while copying knowledge.'}), 500


from sqlalchemy.orm import Session

import shutil
from shutil import rmtree

import string
import random

def generate_random_string(length=3):
    """Generate a random string of fixed length."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def get_unique_knowledge_name(name):
    """Generate a unique name for Knowledge by appending a random string if a duplicate exists."""
    unique_name = name
    while Knowledge.query.filter_by(name=unique_name).first() is not None:
        unique_name = f"{name}_{generate_random_string()}"
    return unique_name


def copy_knowledge(session: Session, knowledge_id: int) -> Knowledge:
    # Retrieve the original knowledge instance
    original_knowledge = session.query(Knowledge).get(knowledge_id)
    
    random_suffix = generate_random_string()

    if not original_knowledge:
        raise ValueError(f"Knowledge with id {knowledge_id} does not exist.")
    # TODO check if name with extension _copy length exeeds the db limit
    # Create a new Knowledge instance with attributes copied from the original
    new_knowledge = Knowledge(
        unique_number=None,
        creator_name=current_user.name,
        theme_name=original_knowledge.theme_name,
        name=f"{original_knowledge.name} {random_suffix}", 
        description=original_knowledge.description
    )

    # Add the new Knowledge instance to the session so it gets a primary key
    session.add(new_knowledge)
    session.flush()  # This assigns an id to new_knowledge

    # Base directory for uploads inside the static folder
    upload_folder = os.path.join(current_app.static_folder, current_app.config['UPLOAD_FOLDER'])

    # Copy all KnownItem instances related to the original knowledge
    for item in original_knowledge.known_items:
        # Copy the file if it exists
        new_file = None
        if item.file:
            # Create a new unique filename and filepath
            _, file_extension = os.path.splitext(item.file.filename)
            original_filename = item.file.filename.split("_", 1)[-1]  # Get the original filename part after the first "_"
            new_filename = f"{uuid.uuid4()}_{original_filename}"
            new_filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], new_filename)
            
            # Construct absolute source and destination paths
            source_path = os.path.join(current_app.static_folder, item.file.filepath)
            destination_path = os.path.join(upload_folder, new_filename)
            
            # Physically copy the file to the new location
            shutil.copy2(source_path, destination_path)
            
            # Create a new File instance with the modified filename and filepath
            new_file = File(
                filename=new_filename,
                filepath=new_filepath,
                uploaded_at=item.file.uploaded_at
            )
            session.add(new_file)
            session.flush()  # Assigns an id to new_file

        # Copy and update imgsrc with new UUID prefix if it exists
        new_imgsrc = None
        if item.imgsrc:
            original_imgsrc = item.imgsrc.split("_", 1)[-1]
            new_imgsrc = f"{uuid.uuid4()}_{original_imgsrc}"
            
            # Construct absolute source and destination paths for imgsrc
            source_img_path = os.path.join(upload_folder, item.imgsrc)
            destination_img_path = os.path.join(upload_folder, new_imgsrc)
            shutil.copy2(source_img_path, destination_img_path)

        # Create a new KnownItem with copied details
        new_item = KnownItem(
            name=f"{item.name}",
            description=item.description,
            imgsrc=new_imgsrc,  # New image source path
            content=item.content,
            file_id=new_file.id if new_file else None,  # Link to new file if applicable
            knowledgename=new_knowledge.name,  # Reference the new knowledge
            typename=item.typename,
            progress_status=item.progress_status,
            order=item.order
        )
        
        # Add the new item to the new knowledge's known_items relationship
        new_knowledge.known_items.append(new_item)
    
    # Commit the session to save changes to the database
    session.commit()
    
    return new_knowledge


@bp.route('/register', methods=['POST'])
@login_required
@role_required(Role.OWNER, Role.WORKER)
def register():
    try:
        name = request.form.get('name')
        description = request.form.get('description')
        theme_name = request.form.get('theme_name')
        items = json.loads(request.form.get('items', '[]'))

        if not name or not theme_name:
            return jsonify({'error': 'Name, theme are required.'}), 400

        new_knowledge = Knowledge(
            creator_name=current_user.name,
            name=name,
            theme_name=theme_name,
            description=description
        )

        for index, item in enumerate(items):
            knowledgetype_name = item['knowledgetype_name']
            item_name = item['item_name']
            item_description = item['item_description']
            
            file_id = None
            imgsrc_filename = None  # Initialize imgsrc_filename to None
            
            # Handle file uploads
            file_key = f'file_{index}'
            if file_key in request.files:
                file = request.files[file_key]
                if file:
                    current_app.logger.debug(f"File found for {file_key}: {file.filename}")
                    filename = save_file(file)  # Save file
                    new_file = File(filename=filename, filepath=os.path.join('uploads', filename))
                    db.session.add(new_file)  # Add to database
                    db.session.flush()  # Ensure the ID is available
                    file_id = new_file.id  # Save the file ID
                else:
                    current_app.logger.debug(f"No file found for {file_key}.")
            
            imgsrc_key = f'imgsrc_{index}'
            if imgsrc_key in request.files:
                imgsrc = request.files[imgsrc_key]
                if imgsrc:
                    current_app.logger.debug(f"Image found for {imgsrc_key}: {imgsrc.filename}")
                    imgsrc_filename = save_file(imgsrc)  # Save image
                    new_imgsrc_file = File(filename=imgsrc_filename, filepath=os.path.join('uploads', imgsrc_filename))
                    db.session.add(new_imgsrc_file)  # Add to database
                    db.session.flush()  # Ensure the ID is available
                    imgsrc_id = new_imgsrc_file.id  # Save the image file ID
                else:
                    current_app.logger.debug(f"No image found for {imgsrc_key}.")

            # Create the KnownItem with a check for imgsrc_filename
            new_item = KnownItem(
                name=item_name,
                description=item_description,
                content=item.get('item_content', ''),
                imgsrc=imgsrc_filename if imgsrc_filename else '',  # Ensure imgsrc is initialized
                file_id=file_id,  # Save the file ID
                knowledgename=name,
                typename=knowledgetype_name,
                progress_status=ProgressStatus.inprogress
            )

            new_knowledge.known_items.append(new_item)

        db.session.add(new_knowledge)
        db.session.commit()
        
        message = (
            f"[{current_user.name}] added new knowledge "
            f"<a href='#' onclick=\"loadTabContent('knowledges', 1, '{new_knowledge.unique_number}', '');\">"
            f"'{new_knowledge.unique_number}'</a>"
        )
        log_entry = Log(
            message=message,
            date=datetime.utcnow()
        )
        db.session.add(log_entry)

        db.session.commit()

        return jsonify({'success': True, 'message': 'Knowledge registered successfully.'}), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500



@bp.route('/item/delete-image/<int:item_id>', methods=['DELETE'])
@login_required
@role_required(Role.OWNER, Role.WORKER)
def delete_image(item_id):
    try:
        item = KnownItem.query.get_or_404(item_id)
        if item.imgsrc:
            os.remove(os.path.join(current_app.static_folder, 'uploads', item.imgsrc))
            item.imgsrc = None
            db.session.commit()
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'No image to delete'}), 404
    except Exception as e:
        current_app.logger.error(f"Error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/item/delete-datafile/<int:item_id>', methods=['DELETE'])
@login_required
@role_required(Role.OWNER, Role.WORKER)
def delete_datafile(item_id):
    try:
        item = KnownItem.query.get_or_404(item_id)
        if item.imgsrc:
            os.remove(os.path.join(current_app.static_folder, 'uploads', item.file.filename))
            item.file_id = None
            db.session.commit()
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'No datafile to delete'}), 404
    except Exception as e:
        current_app.logger.error(f"Error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/item/<int:item_id>/download-image', methods=['GET'])
@login_required
@role_required(Role.OWNER, Role.WORKER)
def download_image(item_id):
    item = KnownItem.query.get_or_404(item_id)
    if item.imgsrc:
        file_path = os.path.join(current_app.static_folder, 'uploads', item.imgsrc)
        return send_file(file_path, as_attachment=True, download_name=item.imgsrc)
    else:
        return jsonify({'success': False, 'message': 'No image to download'}), 404


@bp.route('/item/<int:item_id>/download-file', methods=['GET'])
@login_required
@role_required(Role.OWNER, Role.WORKER)
def download_data_file(item_id):
    # Get the KnownItem from the database
    item = KnownItem.query.get_or_404(item_id)
    
    # Check if a file is associated with the item
    if not item.file_id:
        return jsonify({'error': 'No file associated with this item.'}), 404

    # Get the associated file from the database
    file = item.file
    if not file:
        return jsonify({'error': 'File not found.'}), 404
    
    # Construct the file path
    file_path = os.path.join(current_app.static_folder, 'uploads', file.filename)
    
    # Return the file to the client
    return send_file(file_path, as_attachment=True, download_name=file.filename)

@bp.route('/item/<int:item_id>/upload-files', methods=['POST'])
@login_required
@role_required(Role.OWNER, Role.WORKER)
def upload_files(item_id):
    item = KnownItem.query.get_or_404(item_id)  # Fetch the KnownItem by ID
    
    # Initialize variables
    imgsrc_filename = None
    file_id = None

    # Process the imgsrc file upload
    if 'imgsrc' in request.files:
        imgsrc = request.files['imgsrc']
        if imgsrc and imgsrc.filename:
            imgsrc_filename = save_file(imgsrc)
            if item.imgsrc:
                old_img_path = os.path.join(current_app.static_folder, 'uploads', item.imgsrc)        
                delete_file(old_img_path)

            item.imgsrc = imgsrc_filename


    # Process the file upload
    if 'file' in request.files:
        file = request.files['file']
        if file and file.filename:
            filename = save_file(file)
            old_file = File.query.get(item.file_id)
            if old_file:
                old_file_path = os.path.join(current_app.static_folder, 'uploads', old_file.filename)
                delete_file(old_file_path)
                item.file_id = None
                db.session.delete(old_file)
            

            new_file = File(filename=filename, filepath=os.path.join('uploads', filename), uploaded_at=datetime.utcnow())
            db.session.add(new_file)
            db.session.flush()  # Flush to generate the file_id before committing
            file_id = new_file.id
            # Update the KnownItem with the new file_id
            item.file_id = file_id

    # Commit changes to the KnownItem and File models
    db.session.commit()

    return jsonify({'success': True, 'image_filename': imgsrc_filename, 'file_id': file_id}), 200
