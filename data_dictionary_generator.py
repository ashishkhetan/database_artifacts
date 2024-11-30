import json
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
from pathlib import Path

def generate_data_dictionary(connection_file: str = 'connections.json', output_dir: str = 'data_dictionary'):
    """Generate Excel-based data dictionary for configured databases."""
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
            
            # Connect to database
            conn = psycopg2.connect(
                dbname=db_config['database'],
                user=db_config['username'],
                password=db_config['password'],
                host=db_config['endpoint_rw'],
                port=db_config['port']
            )
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Lists to store information
            all_tables_info = []
            all_columns_info = []
            all_constraints_info = []
            all_indexes_info = []
            
            # Get schemas
            cursor.execute("""
                SELECT 
                    nspname as schema_name,
                    obj_description(oid, 'pg_namespace') as schema_description
                FROM pg_namespace 
                WHERE nspname NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
                ORDER BY nspname;
            """)
            schemas = cursor.fetchall()
            
            # Process each schema
            for schema in schemas:
                try:
                    schema_name = schema['schema_name']
                    print(f"\nProcessing schema: {schema_name}")
                    
                    # Get tables in schema
                    cursor.execute("""
                        SELECT 
                            schemaname,
                            tablename,
                            tableowner,
                            obj_description(pgc.oid, 'pg_class') as table_description
                        FROM pg_tables pt
                        JOIN pg_class pgc ON pt.tablename = pgc.relname
                        WHERE schemaname = %s
                        ORDER BY tablename;
                    """, (schema_name,))
                    tables = cursor.fetchall()
                    
                    if not tables:
                        print(f"No tables found in schema: {schema_name}")
                        continue
                    
                    print(f"Found {len(tables)} tables in schema {schema_name}")
                    
                    # Process each table
                    for table in tables:
                        try:
                            print(f"Processing table: {table['tablename']}")
                            table['schema_description'] = schema['schema_description']
                            all_tables_info.append(table)
                            
                            # Get columns
                            cursor.execute("""
                                WITH pk_info AS (
                                    SELECT a.attname
                                    FROM pg_index i
                                    JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                                    WHERE i.indrelid = %s::regclass
                                    AND i.indisprimary
                                ),
                                fk_info AS (
                                    SELECT
                                        kcu.column_name,
                                        ccu.table_schema AS foreign_schema,
                                        ccu.table_name AS foreign_table,
                                        ccu.column_name AS foreign_column
                                    FROM information_schema.table_constraints tc
                                    JOIN information_schema.key_column_usage kcu 
                                        ON tc.constraint_name = kcu.constraint_name
                                    JOIN information_schema.constraint_column_usage ccu
                                        ON ccu.constraint_name = tc.constraint_name
                                    WHERE tc.constraint_type = 'FOREIGN KEY'
                                    AND tc.table_schema = %s
                                    AND tc.table_name = %s
                                )
                                SELECT 
                                    %s as schema_name,
                                    %s as table_name,
                                    a.attname as column_name,
                                    pg_catalog.format_type(a.atttypid, a.atttypmod) as data_type,
                                    col_description(a.attrelid, a.attnum) as column_description,
                                    a.attnotnull as is_not_null,
                                    (
                                        SELECT pg_get_expr(adbin, adrelid)
                                        FROM pg_attrdef
                                        WHERE adrelid = a.attrelid
                                        AND adnum = a.attnum
                                        AND a.atthasdef
                                    ) as default_value,
                                    CASE WHEN pk.attname IS NOT NULL THEN true ELSE false END as is_primary_key,
                                    fk.foreign_schema,
                                    fk.foreign_table,
                                    fk.foreign_column
                                FROM pg_catalog.pg_attribute a
                                JOIN pg_catalog.pg_class c ON a.attrelid = c.oid
                                JOIN pg_catalog.pg_namespace n ON c.relnamespace = n.oid
                                LEFT JOIN pk_info pk ON a.attname = pk.attname
                                LEFT JOIN fk_info fk ON a.attname = fk.column_name
                                WHERE c.relname = %s
                                AND n.nspname = %s
                                AND a.attnum > 0
                                AND NOT a.attisdropped
                                ORDER BY a.attnum;
                            """, (f"{schema_name}.{table['tablename']}", schema_name, table['tablename'], 
                                  schema_name, table['tablename'], table['tablename'], schema_name))
                            columns = cursor.fetchall()
                            all_columns_info.extend(columns)
                            
                            # Get constraints
                            cursor.execute("""
                                SELECT
                                    %s as schema_name,
                                    %s as table_name,
                                    con.conname as constraint_name,
                                    CASE con.contype
                                        WHEN 'p' THEN 'PRIMARY KEY'
                                        WHEN 'f' THEN 'FOREIGN KEY'
                                        WHEN 'u' THEN 'UNIQUE'
                                        WHEN 'c' THEN 'CHECK'
                                        ELSE con.contype::text
                                    END as constraint_type,
                                    pg_get_constraintdef(con.oid) as constraint_definition
                                FROM pg_catalog.pg_constraint con
                                JOIN pg_catalog.pg_class rel ON rel.oid = con.conrelid
                                JOIN pg_catalog.pg_namespace nsp ON nsp.oid = rel.relnamespace
                                WHERE rel.relname = %s
                                AND nsp.nspname = %s;
                            """, (schema_name, table['tablename'], table['tablename'], schema_name))
                            constraints = cursor.fetchall()
                            all_constraints_info.extend(constraints)
                            
                            # Get indexes
                            cursor.execute("""
                                SELECT
                                    %s as schema_name,
                                    %s as table_name,
                                    i.relname as index_name,
                                    am.amname as index_type,
                                    pg_get_indexdef(i.oid) as index_definition
                                FROM pg_index x
                                JOIN pg_class c ON c.oid = x.indrelid
                                JOIN pg_class i ON i.oid = x.indexrelid
                                JOIN pg_am am ON i.relam = am.oid
                                JOIN pg_namespace n ON n.oid = c.relnamespace
                                WHERE c.relname = %s
                                AND n.nspname = %s;
                            """, (schema_name, table['tablename'], table['tablename'], schema_name))
                            indexes = cursor.fetchall()
                            all_indexes_info.extend(indexes)
                            
                        except Exception as e:
                            print(f"Error processing table {table['tablename']}: {str(e)}")
                            continue
                    
                except Exception as e:
                    print(f"Error processing schema {schema_name}: {str(e)}")
                    continue
            
            # Create consolidated Excel file
            try:
                excel_path = db_path / f"{db_config['name']}_data_dictionary.xlsx"
                with pd.ExcelWriter(excel_path) as writer:
                    # Write tables information
                    pd.DataFrame(all_tables_info).to_excel(
                        writer, sheet_name='Tables', index=False
                    )
                    
                    # Write columns information
                    pd.DataFrame(all_columns_info).to_excel(
                        writer, sheet_name='Columns', index=False
                    )
                    
                    # Write constraints information
                    pd.DataFrame(all_constraints_info).to_excel(
                        writer, sheet_name='Constraints', index=False
                    )
                    
                    # Write indexes information
                    pd.DataFrame(all_indexes_info).to_excel(
                        writer, sheet_name='Indexes', index=False
                    )
                print(f"Generated Excel data dictionary for database: {db_config['name']}")
            except Exception as e:
                print(f"Error generating Excel file for database {db_config['name']}: {str(e)}")
            
            cursor.close()
            conn.close()
            print(f"Completed processing database: {db_config['name']}")
            
        except Exception as e:
            print(f"Error processing database {db_config['name']}: {str(e)}")
            continue

def main():
    """Main function to run the data dictionary generation."""
    print("Starting data dictionary generation...")
    generate_data_dictionary()
    print("Data dictionary generation complete!")

if __name__ == "__main__":
    main()
