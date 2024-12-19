from app import db
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from flask import current_app
import pandas as pd
from io import BytesIO

class CRUDBase:
    def __init__(self, model):
        self.model = model    

    def create(self, data):
        obj = self.model(**data)
        db.session.add(obj)
        db.session.commit()
        return obj


    def get(self, obj_id):
        return self.model.query.get(obj_id)

    def get_all_paginated(self, page=1, per_page=10):
        return self.model.query.paginate(page, per_page, False)

        
    def update(self, obj_id, data):
        obj = self.get(obj_id)
        if not obj:
            current_app.logger.error(f"Object with ID {obj_id} not found")
            return None
                
        for key, value in data.items():
            setattr(obj, key, value)
        
        try:
            db.session.commit()
        except Exception as e:
            current_app.logger.error(f"Error committing to database: {e}")
            db.session.rollback()
            raise
        return obj


    def delete(self, obj_id):
        obj = self.get(obj_id)
        if not obj:
            current_app.logger.error(f"Object with ID {obj_id} not found")
            return None
        
        db.session.delete(obj)
        
        try:
            db.session.commit()
            current_app.logger.debug(f"Deleted object with ID {obj_id}")
        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Error deleting object with ID {obj_id}: {e}")
            return None
        return obj


    def fetch_records(self):
        """
        Fetch all records from the model class and return them as a list of dictionaries.
        Excludes the 'id' field from the results.
        """
        try:
            query = self.model.query.order_by(self.model.id.desc())
            records = query.all()

            records_list = [
                {column.name: getattr(record, column.name) for column in self.model.__table__.columns if column.name != 'id'}
                for record in records
            ]

            return records_list
        except SQLAlchemyError as e:
            return {'error': str(e)}, 500


    def create_excel_from_records(self):
        """
        Create an Excel file from the records of the specified model class.
        """
        records = self.fetch_records()

        if isinstance(records, tuple):
            return records  # Return error response if any

        df = pd.DataFrame(records)

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)

        output.seek(0)
        return output


    def process_records_from_excel(self, data):
        """
        Process uploaded records and add them to the model class.
        Skips records that already exist based on the 'name' field.
        """
        try:
            for entry in data:
                current_app.logger.debug("Processing entry: ", entry)
                
                # Create a new model object from the entry data, replacing NaN/None with empty fields
                new_record_data = {}
                for column in self.model.__table__.columns:
                    if column.name != 'id':  # Skip 'id' field
                        value = entry.get(column.name)
                        
                        # Replace NaN or None with an empty string if the field is a string
                        if pd.isna(value):
                            value = '' if column.type.python_type == str else None
                        
                        new_record_data[column.name] = value
                current_app.logger.debug(f"Creating new record with data: {new_record_data}")
                
                # Check if a record with the same unique field (e.g., 'name') already exists
                if 'name' in self.model.__table__.columns:
                    unique_field = 'name'
    
                    # Check if a record with the same unique field already exists
                    existing_record = self.model.query.filter_by(**{unique_field: new_record_data.get(unique_field)}).first()
                    if existing_record:
                        current_app.logger.debug(f"Skipping existing record with name: {new_record_data.get('name')} (ID: {existing_record.id})")
                        continue  # Skip adding if it already exists
                
                # Create a new record
                new_record = self.model(**new_record_data)
                db.session.add(new_record)
            
            db.session.commit()  # Commit all changes in one go
            current_app.logger.debug("All records processed and committed successfully.")
            
        except SQLAlchemyError as e:
            db.session.rollback()  # Rollback on error
            current_app.logger.error(f"Database error occurred: {str(e)}")
            raise ValueError(f"Database error: {str(e)}")
        except Exception as e:
            db.session.rollback()  # Ensure rollback on any other exceptions
            current_app.logger.error(f"Unexpected error occurred: {str(e)}")
            raise ValueError(f"Unexpected error: {str(e)}")
    
    
    
    
    
    
    