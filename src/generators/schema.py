import json
from pathlib import Path
from eralchemy import render_er
from sqlalchemy import create_engine, text
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('schema_generator.log')
    ]
)
logger = logging.getLogger(__name__)

def ensure_directory(path: Path):
    """Ensure directory and all its parents exist."""
    path.mkdir(parents=True, exist_ok=True)

def has_physical_tables(engine, schema_name):
    """Check if the schema has at least one physical table."""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = :schema 
                AND table_type = 'BASE TABLE'
            """), {'schema': schema_name})
            count = result.scalar()
            return count > 0
    except Exception as e:
        logger.error(f"Error checking for physical tables in schema {schema_name}: {str(e)}")
        return False

def test_connection(db_config):
    """Test database connection and return (success, error_message)."""
    try:
        db_url = f"postgresql://{db_config['username']}:{db_config['password']}@{db_config['endpoint_rw']}:{db_config['port']}/{db_config['database']}"
        engine = create_engine(db_url)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True, None
    except Exception as e:
        error_msg = str(e)
        if "password authentication failed" in error_msg.lower():
            return False, f"Authentication failed for database {db_config['name']}. Please check username and password."
        elif "could not connect to server" in error_msg.lower():
            return False, f"Could not connect to database {db_config['name']} at {db_config['endpoint_rw']}:{db_config['port']}. Please check host and port."
        elif "database" in error_msg.lower() and "does not exist" in error_msg.lower():
            return False, f"Database {db_config['database']} does not exist at {db_config['endpoint_rw']}."
        else:
            return False, f"Error connecting to database {db_config['name']}: {error_msg}"

def generate_schema_diagrams(connection_file: str = 'config/connections.json', output_dir: str = 'output'):
    """Generate ERD diagrams for all configured databases."""
    success_count = 0
    failure_count = 0
    skipped_count = 0
    
    # Create output directory with all parent directories
    output_path = Path(output_dir)
    ensure_directory(output_path)
    
    try:
        # Load database connections
        with open(connection_file, 'r') as f:
            connections = json.load(f)
    except FileNotFoundError:
        logger.error(f"Connection file not found: {connection_file}")
        return
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in connection file: {connection_file}")
        return
    
    logger.info(f"Processing {len(connections['databases'])} databases...")
    
    for db_config in connections['databases']:
        try:
            logger.info(f"\nProcessing database: {db_config['name']}")
            
            # Test connection first
            connection_success, error_message = test_connection(db_config)
            if not connection_success:
                logger.error(error_message)
                failure_count += 1
                continue
            
            # Create directory for this database
            db_path = output_path / db_config['name']
            ensure_directory(db_path)
            
            # Get database URL
            db_url = f"postgresql://{db_config['username']}:{db_config['password']}@{db_config['endpoint_rw']}:{db_config['port']}/{db_config['database']}"
            
            # Generate ERD for each schema
            try:
                # Create engine for database connection
                engine = create_engine(db_url)
                
                # Get list of schemas
                with engine.connect() as connection:
                    result = connection.execute(text("""
                        SELECT 
                            nspname as schema_name
                        FROM pg_namespace 
                        WHERE nspname NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
                        ORDER BY nspname;
                    """))
                    schemas = result.fetchall()
                
                if not schemas:
                    logger.warning(f"No user schemas found in database {db_config['name']}")
                    skipped_count += 1
                    continue
                
                schema_success = False
                for schema in schemas:
                    try:
                        schema_name = schema[0]
                        logger.info(f"\nChecking schema: {schema_name}")
                        
                        # Skip schemas with no physical tables
                        if not has_physical_tables(engine, schema_name):
                            logger.info(f"Skipping schema {schema_name} - no physical tables found")
                            continue
                        
                        logger.info(f"Processing schema: {schema_name}")
                        
                        # Add schema filter to URL
                        schema_url = f"{db_url}?options=-c%20search_path={schema_name}"
                        
                        # Generate PNG format
                        png_path = db_path / f"{schema_name}_schema.png"
                        render_er(schema_url, str(png_path))
                        logger.info(f"Generated PNG for schema: {schema_name}")
                        
                        # Generate PDF format
                        pdf_path = db_path / f"{schema_name}_schema.pdf"
                        render_er(schema_url, str(pdf_path))
                        logger.info(f"Generated PDF for schema: {schema_name}")
                        
                        schema_success = True
                        
                    except Exception as e:
                        logger.error(f"Error processing schema {schema_name}: {str(e)}")
                        continue
                
                if schema_success:
                    success_count += 1
                else:
                    failure_count += 1
                
            except Exception as e:
                logger.error(f"Error getting schemas for database {db_config['name']}: {str(e)}")
                failure_count += 1
                continue
            
            logger.info(f"Completed processing database: {db_config['name']}")
            
        except Exception as e:
            logger.error(f"Error processing database {db_config['name']}: {str(e)}")
            failure_count += 1
            continue
    
    # Print summary
    logger.info("\nSchema Generation Summary:")
    logger.info(f"Successful: {success_count}")
    logger.info(f"Failed: {failure_count}")
    logger.info(f"Skipped: {skipped_count}")
    logger.info(f"Total: {len(connections['databases'])}")

def main():
    """Main function to run the schema diagram generation."""
    logger.info("Starting schema diagram generation...")
    generate_schema_diagrams()
    logger.info("Schema diagram generation complete!")

if __name__ == "__main__":
    main()
