from flask import Blueprint, current_app, render_template_string, jsonify, send_file, request
from collections import defaultdict
from sqlalchemy import text
from flask import send_from_directory
import os
from app import db

bp = Blueprint('misc', __name__)


@bp.route('/css/<path:filename>')
def custom_styles_path(filename):

    base_dir = current_app.config['BASEDIR']
    styles_path = os.path.join(current_app.static_folder, 'css')
    return send_from_directory(styles_path, filename)



@bp.route('/show_schema', methods=['GET'])
def show_schema():
    """List all tables, columns, and foreign key relationships in the PostgreSQL database in a structured HTML format."""
    
    # Get the database connection
    engine = current_app.extensions['sqlalchemy'].get_engine()
    connection = engine.connect()

    # Query to get all tables in the public schema
    tables_query = text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
    """)
    result = connection.execute(tables_query)
    tables = [row[0] for row in result]  # Access the first column of each row (table name)

    schema_info = []
    relationships = []

    # Query to get columns and foreign keys for each table
    for table_name in tables:
        # Get table columns
        columns_query = text(f"""
            SELECT column_name, data_type, is_nullable, column_default 
            FROM information_schema.columns 
            WHERE table_name = :table_name AND table_schema = 'public';
        """)
        result = connection.execute(columns_query, {'table_name': table_name})
        table_columns = []

        for column in result:
            table_columns.append({
                'Column': column[0],         # Column name (first value in the result tuple)
                'Type': column[1],           # Column type (second value in the result tuple)
                'Nullable': 'Yes' if column[2] == 'YES' else 'No',  # Nullable (third value in the result tuple)
                'Default': column[3]         # Default value (fourth value in the result tuple)
            })

        # Get table foreign keys (relationships)
        foreign_keys_query = text(f"""
            SELECT
                kcu.column_name, 
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM 
                information_schema.table_constraints AS tc
            JOIN 
                information_schema.key_column_usage AS kcu
            ON 
                tc.constraint_name = kcu.constraint_name
            AND 
                tc.table_schema = kcu.table_schema
            JOIN 
                information_schema.constraint_column_usage AS ccu
            ON 
                ccu.constraint_name = tc.constraint_name
            WHERE 
                tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_name = :table_name
                AND tc.table_schema = 'public';
        """)
        fk_result = connection.execute(foreign_keys_query, {'table_name': table_name})
        for fk in fk_result:
            relationships.append({
                'Table': table_name,
                'Column': fk[0],              # Column with the foreign key (first value)
                'References': fk[1],          # Referenced table (second value)
                'ReferencedColumn': fk[2]     # Referenced column (third value)
            })

        schema_info.append({
            'Table': table_name,
            'Columns': table_columns
        })

    # HTML template for displaying schema with relationships (unchanged)
    html_template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Schema Information</title>
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
        <style>
            body { padding: 20px; }
            .table-container { margin-bottom: 20px; }
            .table-title { font-weight: bold; font-size: 1em; margin-bottom: 10px; }
            .table { font-size: 0.9em; width: 100%; }
            .row-container {
                display: flex;
                flex-wrap: wrap;
                gap: 20px; /* Space between tables */
            }
            .table-wrapper {
                flex: 1 1 calc(33.333% - 20px); /* Three tables per row, accounting for the gap */
                box-sizing: border-box; /* Ensure padding and border are included in the width */
                min-width: 300px; /* Minimum width for each table */
            }
            .table-container table {
                table-layout: fixed; /* Ensure tables do not overflow their container */
            }
            .table-container th, .table-container td {
                width: 100px; /* Fixed width for the Type column */
                text-overflow: ellipsis; /* Handle long text */
                overflow: hidden;
                white-space: nowrap; /* Prevent text from wrapping */
            }
            .table-container th.type-column, .table-container td.type-column {
                width: 150px; /* Fixed width for the Type column */
                font-size: 0.9em; /* Optional: adjust font size for better readability */
            }
            h1 {
                text-align: center; /* Center-align the heading */
                margin-bottom: 40px; /* Optional: adjust margin for spacing */
            }
        </style>
    </head>
    <body>
        <h1>Schema Information</h1>
        
        <div class="container">
            <div class="row-container">
                {% for table_info in schema_info %}
                    <div class="table-wrapper">
                        <div class="table-container">
                            <div class="table-title">{{ table_info['Table'] }}</div>
                            <table class="table table-striped table-bordered">
                                <thead>
                                    <tr>
                                        <th style="width: 100px;">Column</th>
                                        <th style="width: 100px;">Type</th>
                                        <th style="width: 70px;">Nullable</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for column in table_info['Columns'] %}
                                        <tr>
                                            <td>{{ column['Column'] }}</td>
                                            <td class="type-column">{{ column['Type'] }}</td>
                                            <td>{{ column['Nullable'] }}</td>
                                        </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                    {% if loop.index % 3 == 0 and not loop.last %}
                        </div><div class="row-container">
                    {% endif %}
                {% endfor %}
            </div>
        </div>
        
        <h2>Table Relationships (Inheritance/Foreign Keys)</h2>
        <ul>
            {% for relationship in relationships %}
                <li class="relationship">
                    Table <strong>{{ relationship['Table'] }}</strong> column <strong>{{ relationship['Column'] }}</strong>
                    references table <strong>{{ relationship['References'] }}</strong> column <strong>{{ relationship['ReferencedColumn'] }}</strong>
                </li>
            {% endfor %}
        </ul>
        
        <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.5.3/dist/umd/popper.min.js"></script>
        <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
    </body>
    </html>
    '''

    return render_template_string(html_template, schema_info=schema_info, relationships=relationships)



@bp.route('/show_schema_sqlite', methods=['GET'])
def show_schema_sqlite():
    """List all tables, columns, and foreign key relationships in the SQLite database in a structured HTML format."""
    
    # Get the database connection
    engine = current_app.extensions['sqlalchemy'].get_engine()
    connection = engine.connect()

    # Query to get all tables
    tables_query = text("SELECT name FROM sqlite_master WHERE type='table'")
    result = connection.execute(tables_query)
    tables = [row[0] for row in result]  # Access the first column of each row (table name)

    schema_info = []
    relationships = []

    # Query to get columns and foreign keys for each table
    for table_name in tables:
        # Get table columns
        columns_query = text(f"PRAGMA table_info({table_name})")
        result = connection.execute(columns_query)
        table_columns = []

        for column in result:
            table_columns.append({
                'Column': column[1],  # Column name
                'Type': column[2],    # Column type
                'Nullable': 'Yes' if column[3] == 0 else 'No',  # 0 means NOT NULL
                'Default': column[4]  # Default value
            })

        # Get table foreign keys (relationships)
        foreign_keys_query = text(f"PRAGMA foreign_key_list({table_name})")
        fk_result = connection.execute(foreign_keys_query)
        for fk in fk_result:
            relationships.append({
                'Table': table_name,
                'Column': fk[3],          # Column with the foreign key
                'References': fk[2],      # Referenced table
                'ReferencedColumn': fk[4] # Referenced column
            })

        schema_info.append({
            'Table': table_name,
            'Columns': table_columns
        })

    # HTML template for displaying schema with relationships
    html_template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Schema Information</title>
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
        <style>
            body { padding: 20px; }
            .table-container { margin-bottom: 20px; }
            .table-title { font-weight: bold; font-size: 1em; margin-bottom: 10px; }
            .table { font-size: 0.9em; width: 100%; }
            .row-container {
                display: flex;
                flex-wrap: wrap;
                gap: 20px; /* Space between tables */
            }
            .table-wrapper {
                flex: 1 1 calc(33.333% - 20px); /* Three tables per row, accounting for the gap */
                box-sizing: border-box; /* Ensure padding and border are included in the width */
                min-width: 300px; /* Minimum width for each table */
            }
            .table-container table {
                table-layout: fixed; /* Ensure tables do not overflow their container */
            }
            .table-container th, .table-container td {
                width: 100px; /* Fixed width for the Type column */
                text-overflow: ellipsis; /* Handle long text */
                overflow: hidden;
                white-space: nowrap; /* Prevent text from wrapping */
            }
            .table-container th.type-column, .table-container td.type-column {
                width: 150px; /* Fixed width for the Type column */
                font-size: 0.9em; /* Optional: adjust font size for better readability */
            }
            h1 {
                text-align: center; /* Center-align the heading */
                margin-bottom: 40px; /* Optional: adjust margin for spacing */
            }
        </style>
    </head>
    <body>
        <h1>Schema Information</h1>
        
        <div class="container">
            <div class="row-container">
                {% for table_info in schema_info %}
                    <div class="table-wrapper">
                        <div class="table-container">
                            <div class="table-title">{{ table_info['Table'] }}</div>
                            <table class="table table-striped table-bordered">
                                <thead>
                                    <tr>
                                        <th style="width: 100px;">Column</th>
                                        <th style="width: 100px;">Type</th>
                                        <th style="width: 70px;">Nullable</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for column in table_info['Columns'] %}
                                        <tr>
                                            <td>{{ column['Column'] }}</td>
                                            <td class="type-column">{{ column['Type'] }}</td>
                                            <td>{{ column['Nullable'] }}</td>
                                        </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                    {% if loop.index % 3 == 0 and not loop.last %}
                        </div><div class="row-container">
                    {% endif %}
                {% endfor %}
            </div>
        </div>
        
        <h2>Table Relationships (Inheritance/Foreign Keys)</h2>
        <ul>
            {% for relationship in relationships %}
                <li class="relationship">
                    Table <strong>{{ relationship['Table'] }}</strong> column <strong>{{ relationship['Column'] }}</strong>
                    references table <strong>{{ relationship['References'] }}</strong> column <strong>{{ relationship['ReferencedColumn'] }}</strong>
                </li>
            {% endfor %}
        </ul>
        
        <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.5.3/dist/umd/popper.min.js"></script>
        <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
    </body>
    </html>
    '''

    return render_template_string(html_template, schema_info=schema_info, relationships=relationships)

    
@bp.route('/show_routes', methods=['GET'])
def show_routes():
    """List all routes in a structured HTML format, grouped by the first part of the endpoint with numbering."""
    
    routes = []
    count = 1  # Initialize the count for numbering

    for rule in current_app.url_map.iter_rules():
        routes.append({
            'id': count,
            'Endpoint': rule.endpoint,
            'Methods': ', '.join(rule.methods),
            'URL': rule.rule,
            'Arguments': ', '.join(rule.arguments),
        })
        count += 1

    # Group routes by the first part of the endpoint
    grouped_routes = defaultdict(list)
    for route in routes:
        # Extract the first part of the endpoint name for grouping
        group_name = route['Endpoint'].split('.')[0]
        grouped_routes[group_name].append(route)

    # HTML template for displaying routes
    html_template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Application Routes</title>
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
        <style>
            body { padding: 20px; }
            table { width: 100%; }
            th, td { text-align: left; }
            .group-header { background-color: #f8f9fa; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>Application Routes</h1>
        <table class="table table-striped table-bordered">
            <thead>
                <tr>
                    <th>#</th>
                    <th>Endpoint</th>
                    <th>Methods</th>
                    <th>URL</th>
                    <th>Arguments</th>
                </tr>
            </thead>
            <tbody>
                {% for group_name, routes in grouped_routes.items() %}
                    <tr class="group-header">
                        <td colspan="5">{{ group_name }}</td>
                    </tr>
                    {% for route in routes %}
                        <tr>
                            <td>{{ route['id'] }}</td>
                            <td>{{ route['Endpoint'] }}</td>
                            <td>{{ route['Methods'] }}</td>
                            <td>{{ route['URL'] }}</td>
                            <td>{{ route['Arguments'] }}</td>
                        </tr>
                    {% endfor %}
                {% endfor %}
            </tbody>
        </table>
        <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.5.3/dist/umd/popper.min.js"></script>
        <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
    </body>
    </html>
    '''

    return render_template_string(html_template, grouped_routes=grouped_routes)