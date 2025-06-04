import pandas as pd
import os
import json
import sqlite3
from sqlalchemy import create_engine
from ..utils.logger import get_logger

logger = get_logger(__name__)

class DataExporter:
    def __init__(self, export_dir):
        self.export_dir = export_dir
        os.makedirs(export_dir, exist_ok=True)
    
    def export_to_csv(self, data, filename, structured=False):
        """Export extracted data to CSV"""
        try:
            file_path = os.path.join(self.export_dir, filename)
            
            if structured:
                # If data is already structured (e.g., DataFrame or dict of DataFrames)
                if isinstance(data, pd.DataFrame):
                    data.to_csv(file_path, index=False)
                elif isinstance(data, dict):
                    # If multiple tables/dataframes, save each to a separate CSV
                    for key, df in data.items():
                        if isinstance(df, pd.DataFrame):
                            name, ext = os.path.splitext(filename)
                            df_path = os.path.join(self.export_dir, f"{name}_{key}{ext}")
                            df.to_csv(df_path, index=False)
            else:
                # Convert unstructured text data to DataFrame
                if isinstance(data, dict):
                    # Convert text data to rows
                    rows = []
                    for page, text in data.items():
                        rows.append({'page': page, 'content': text})
                    
                    df = pd.DataFrame(rows)
                    df.to_csv(file_path, index=False)
                elif isinstance(data, str):
                    # Single text string
                    df = pd.DataFrame([{'content': data}])
                    df.to_csv(file_path, index=False)
            
            logger.info(f"Data exported successfully to {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Error exporting data to CSV: {str(e)}")
            return None
    
    def export_to_json(self, data, filename):
        """Export extracted data to JSON"""
        try:
            file_path = os.path.join(self.export_dir, filename)
            
            # Convert DataFrames to dict for JSON serialization
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, pd.DataFrame):
                        data[key] = value.to_dict(orient='records')
            elif isinstance(data, pd.DataFrame):
                data = data.to_dict(orient='records')
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            
            logger.info(f"Data exported successfully to {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Error exporting data to JSON: {str(e)}")
            return None
    
    def export_to_sql(self, data, filename, connection_string=None):
        """Export extracted data to SQLite or other SQL database"""
        try:
            # Determine if we're using SQLite or another database
            if connection_string:
                # Use SQLAlchemy for other databases
                engine = create_engine(connection_string)
                table_name = os.path.splitext(filename)[0]
                
                if isinstance(data, pd.DataFrame):
                    data.to_sql(table_name, engine, if_exists='replace', index=False)
                elif isinstance(data, dict):
                    for key, df in data.items():
                        if isinstance(df, pd.DataFrame):
                            df.to_sql(f"{table_name}_{key}", engine, if_exists='replace', index=False)
                
                logger.info(f"Data exported successfully to SQL database")
                return connection_string
            else:
                # Use SQLite
                db_path = os.path.join(self.export_dir, filename.replace('.sql', '.db'))
                conn = sqlite3.connect(db_path)
                
                if isinstance(data, pd.DataFrame):
                    table_name = os.path.splitext(os.path.basename(filename))[0]
                    data.to_sql(table_name, conn, if_exists='replace', index=False)
                elif isinstance(data, dict):
                    for key, df in data.items():
                        if isinstance(df, pd.DataFrame):
                            table_name = f"{os.path.splitext(os.path.basename(filename))[0]}_{key}"
                            df.to_sql(table_name, conn, if_exists='replace', index=False)
                
                conn.commit()
                conn.close()
                
                logger.info(f"Data exported successfully to SQLite database: {db_path}")
                return db_path
        except Exception as e:
            logger.error(f"Error exporting data to SQL: {str(e)}")
            return None
    
    def export_to_excel(self, data, filename):
        """Export extracted data to Excel"""
        try:
            file_path = os.path.join(self.export_dir, filename)
            if not file_path.endswith('.xlsx'):
                file_path += '.xlsx'
            
            if isinstance(data, pd.DataFrame):
                data.to_excel(file_path, index=False)
            elif isinstance(data, dict):
                with pd.ExcelWriter(file_path) as writer:
                    for key, value in data.items():
                        if isinstance(value, pd.DataFrame):
                            value.to_excel(writer, sheet_name=key[:31], index=False)  # Excel limita nome de sheet a 31 caracteres
                        elif isinstance(value, str):
                            pd.DataFrame({'content': [value]}).to_excel(writer, sheet_name=key[:31], index=False)
            
            logger.info(f"Data exported successfully to Excel: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Error exporting data to Excel: {str(e)}")
            return None