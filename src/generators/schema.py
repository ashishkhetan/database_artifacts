import json
from pathlib import Path
from eralchemy import render_er
from sqlalchemy import create_engine, text

def generate_schema_diagrams(connection_file: str = 'config/connections.json', output_dir: str = 'output/data_dictionary'):
    """Generate ERD diagrams for all configured databases."""
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Load database connections
    with open(connection_file, 'r') as f:
        connections = json.load(f)
    
    for db_config in connections['databases']:
        try:
            print(f"\nProcessing database: {db_config['name']}")
            
            # Create directory for this database
            db_path = output_path / db_config['name']
            db_path.mkdir(exist_ok=True)
            
            # Get database URL
            db_url = f"postgresql://{db_config['username']}:{db_config['password']}@{db_config['endpoint_rw']}:{db_config['port']}/{db_config['database']}"
            
            # Generate ERD for each schema
            try:
                # Create engine for database connection
                engine = create_engine(db_url)
                with engine.connect() as connection:
                    result = connection.execute(text("""
                        SELECT 
                            nspname as schema_name
                        FROM pg_namespace 
                        WHERE nspname NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
                        ORDER BY nspname;
                    """))
                    schemas = result.fetchall()
                
                for schema in schemas:
                    try:
                        schema_name = schema[0]
                        print(f"\nProcessing schema: {schema_name}")
                        
                        # Add schema filter to URL
                        schema_url = f"{db_url}?options=-c%20search_path={schema_name}"
                        
                        # Generate PNG format
                        png_path = db_path / f"{schema_name}_schema.png"
                        render_er(schema_url, str(png_path))
                        print(f"Generated PNG for schema: {schema_name}")
                        
                        # Generate PDF format
                        pdf_path = db_path / f"{schema_name}_schema.pdf"
                        render_er(schema_url, str(pdf_path))
                        print(f"Generated PDF for schema: {schema_name}")
                        
                    except Exception as e:
                        print(f"Error processing schema {schema_name}: {str(e)}")
                        continue
                
            except Exception as e:
                print(f"Error getting schemas for database {db_config['name']}: {str(e)}")
                continue
            
            print(f"Completed processing database: {db_config['name']}")
            
        except Exception as e:
            print(f"Error processing database {db_config['name']}: {str(e)}")
            continue

def main():
    """Main function to run the schema diagram generation."""
    print("Starting schema diagram generation...")
    generate_schema_diagrams()
    print("Schema diagram generation complete!")

if __name__ == "__main__":
    main()
