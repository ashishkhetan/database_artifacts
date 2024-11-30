import argparse
from data_dictionary_generator import generate_data_dictionary
from schema_generator import generate_schema_diagrams
from confluence_publisher import ConfluencePublisher

def main():
    parser = argparse.ArgumentParser(description='Generate and publish database documentation')
    parser.add_argument('--type', choices=['all', 'dictionary', 'schema'], 
                      default='all', help='Type of documentation to generate')
    parser.add_argument('--connection-file', default='connections.json',
                      help='Path to the database connection configuration file')
    parser.add_argument('--output-dir', default='data_dictionary',
                      help='Output directory for generated documentation')
    parser.add_argument('--publish', action='store_true',
                      help='Publish documentation to Confluence')
    parser.add_argument('--confluence-config', default='confluence_config.json',
                      help='Path to Confluence configuration file')
    
    args = parser.parse_args()
    
    # Generate documentation
    if args.type in ['all', 'dictionary']:
        print("\nGenerating data dictionary...")
        generate_data_dictionary(args.connection_file, args.output_dir)
    
    if args.type in ['all', 'schema']:
        print("\nGenerating schema diagrams...")
        generate_schema_diagrams(args.connection_file, args.output_dir)
    
    # Publish to Confluence if requested
    if args.publish:
        try:
            print("\nPublishing to Confluence...")
            publisher = ConfluencePublisher(args.confluence_config)
            
            # Get list of databases from the connection file
            with open(args.connection_file) as f:
                connections = json.load(f)
            
            for db_config in connections['databases']:
                try:
                    print(f"\nPublishing documentation for database: {db_config['name']}")
                    page_id = publisher.publish_documentation(args.output_dir, db_config['name'])
                    print(f"Documentation published successfully. Page ID: {page_id}")
                except Exception as e:
                    print(f"Error publishing documentation for {db_config['name']}: {str(e)}")
                    
        except Exception as e:
            print(f"Error initializing Confluence publisher: {str(e)}")
            print("Documentation was generated but could not be published to Confluence.")

if __name__ == "__main__":
    main()
