import json
from pathlib import Path
from eralchemy import render_er

def generate_schema_diagrams(connection_file: str = 'connections.json', output_dir: str = 'data_dictionary'):
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
            schemas = []
            try:
                # Create temporary connection to get schemas
                from sqlalchemy import create_engine
                engine = create_engine(db_url)
                with engine.connect() as connection:
                    schemas = connection.execute("""
                        SELECT 
                            nspname as schema_name
                        FROM pg_namespace 
                        WHERE nspname NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
                        ORDER BY nspname;
                    """).fetchall()
            except Exception as e:
                print(f"Error getting schemas for database {db_config['name']}: {str(e)}")
                continue

            for schema in schemas:
                try:
                    schema_name = schema[0]
                    print(f"\nProcessing schema: {schema_name}")
                    
                    # Generate ERD for this schema
                    schema_path = db_path / f"{schema_name}_schema"
                    
                    # Use ERAlchemy's native rendering with schema filter
                    schema_url = f"{db_url}?options=-c%20search_path={schema_name}"
                    render_er(schema_url, str(schema_path) + '.png')
                    print(f"Generated ERD for schema: {schema_name}")
                    
                except Exception as e:
                    print(f"Error processing schema {schema_name}: {str(e)}")
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
