import json
import base64
from datetime import datetime, timedelta
from pathlib import Path
import requests
from atlassian import Confluence
import logging
import sys
from collections import defaultdict

# Configure logging to output to both file and console
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for more verbose output
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('confluence_publisher.log')
    ]
)
logger = logging.getLogger(__name__)

# Enable debug logging for requests
logging.getLogger('urllib3').setLevel(logging.DEBUG)
logging.getLogger('requests').setLevel(logging.DEBUG)

class ConfluencePublisher:
    def __init__(self, config_file='config/confluence_config.json'):
        """Initialize Confluence publisher with configuration."""
        try:
            logger.debug("Starting Confluence publisher initialization")
            
            with open(config_file) as f:
                self.config = json.load(f)
                logger.debug(f"Loaded configuration from {config_file}")
            
            # Format URL for Confluence Cloud
            base_url = self.config['url'].rstrip('/')
            if not base_url.endswith('.atlassian.net'):
                base_url = f"https://{base_url}.atlassian.net"
            
            logger.info(f"Connecting to Confluence at {base_url}")
            logger.info(f"Using username: {self.config['username']}")
            
            # Initialize Confluence client with basic auth using API token
            logger.debug("Initializing Confluence client")
            self.confluence = Confluence(
                url=base_url,
                username=self.config['username'],
                password=self.config['api_token']  # Use API token as password
            )
            
            # Test connection by getting space info
            try:
                space = self.confluence.get_space(self.config['space_key'])
                logger.info(f"Successfully connected to space: {space['name']} ({space['key']})")
            except Exception as e:
                logger.error(f"Failed to get space info: {str(e)}")
                raise
            
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_file}")
            logger.info(f"Please copy {config_file}.template to {config_file} and update with your credentials")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {config_file}")
            logger.error(f"JSON Error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error initializing Confluence connection: {str(e)}")
            logger.exception("Full exception details:")
            raise
    
    def _get_timestamp(self):
        """Get current timestamp in a readable format."""
        return datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    
    def _get_content_type(self, file_path):
        """Get content type based on file extension."""
        extension = file_path.suffix.lower()
        if extension == '.png':
            return 'image/png'
        elif extension == '.pdf':
            return 'application/pdf'
        elif extension == '.xlsx':
            return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        return 'application/octet-stream'
    
    def _attach_file(self, page_id, file_path):
        """Attach a file to a Confluence page."""
        try:
            with open(file_path, 'rb') as file:
                logger.info(f"Attaching file: {file_path.name}")
                content_type = self._get_content_type(file_path)
                self.confluence.attach_content(
                    content=file.read(),
                    name=file_path.name,
                    content_type=content_type,
                    page_id=page_id,
                    title=file_path.name,
                    space=self.config['space_key'],
                    comment='Automatically attached by documentation generator'
                )
                logger.info(f"Successfully attached: {file_path.name}")
        except Exception as e:
            logger.error(f"Error attaching file {file_path.name}: {str(e)}")
            raise
    
    def _create_or_update_page(self, space_key, title, body):
        """Create or update a Confluence page."""
        try:
            existing_page = self.confluence.get_page_by_title(
                space=space_key,
                title=title
            )
            
            if existing_page:
                logger.info(f"Updating existing page: {title}")
                self.confluence.update_page(
                    page_id=existing_page['id'],
                    title=title,
                    body=body,
                    type='page',
                    representation='storage'
                )
                return existing_page['id']
            else:
                logger.info(f"Creating new page: {title}")
                page = self.confluence.create_page(
                    space=space_key,
                    title=title,
                    body=body,
                    parent_id=None,  # Create at root level
                    type='page',
                    representation='storage'
                )
                return page['id']
        except Exception as e:
            logger.error(f"Error creating/updating page {title}: {str(e)}")
            raise
    
    def _get_schema_info(self, doc_path):
        """Get schema information including files."""
        schema_files = {}
        for file_path in doc_path.glob('*_schema.*'):
            schema_name = file_path.stem.replace('_schema', '')
            ext = file_path.suffix.lower()
            if schema_name not in schema_files:
                schema_files[schema_name] = {'png': None, 'pdf': None}
            schema_files[schema_name][ext[1:]] = file_path.name
        return schema_files
    
    def publish_documentation(self, doc_dir: str = 'output', databases=None):
        """Publish database documentation to Confluence."""
        try:
            logger.info("Starting documentation publish")
            timestamp = self._get_timestamp()
            space_key = self.config['space_key']
            title = self.config['page_title']  # Use fixed title from config
            
            # Start building the page content
            body = f"""
            <h1>Database Documentation</h1>
            <p>Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <ac:structured-macro ac:name="info" ac:schema-version="1">
                <ac:rich-text-body>
                    <p>This page contains documentation for all databases including schema diagrams and data dictionaries.</p>
                    <p>Documentation is automatically generated and updated regularly.</p>
                </ac:rich-text-body>
            </ac:structured-macro>
            
            <table>
                <tr>
                    <th>Database</th>
                    <th>Schema</th>
                    <th>Schema Diagram</th>
                    <th>Schema Documentation</th>
                    <th>Data Dictionary</th>
                </tr>
            """
            
            # Create or update the page first to get the page ID
            page_id = self._create_or_update_page(space_key, title, body + "</table>")
            
            # Process each database
            for db_config in databases:
                db_name = db_config['name']
                doc_path = Path(doc_dir) / db_name
                
                if not doc_path.exists():
                    logger.warning(f"Documentation directory not found for {db_name}, skipping...")
                    continue
                
                # Get schema information
                schema_files = self._get_schema_info(doc_path)
                
                # Find data dictionary Excel file
                data_dict_file = doc_path / f'{db_name}_data_dictionary.xlsx'
                if data_dict_file.exists():
                    self._attach_file(page_id, data_dict_file)
                
                # Process each schema
                num_schemas = len(schema_files)
                for i, (schema_name, files) in enumerate(schema_files.items()):
                    # Attach files first
                    if files['png']:
                        png_path = doc_path / files['png']
                        self._attach_file(page_id, png_path)
                    
                    if files['pdf']:
                        pdf_path = doc_path / files['pdf']
                        self._attach_file(page_id, pdf_path)
                    
                    # Add row to table
                    body += "<tr>"
                    
                    # Database column with rowspan for first schema only
                    if i == 0:
                        body += f"""
                        <td rowspan="{num_schemas}">{db_name}</td>
                        """
                    
                    # Schema info
                    body += f"""
                        <td>{schema_name.upper()}</td>
                        <td>
                            <ac:image ac:thumbnail="true" ac:width="200">
                                <ri:attachment ri:filename="{files['png']}" />
                            </ac:image>
                        </td>
                        <td>
                            <ac:link>
                                <ri:attachment ri:filename="{files['pdf']}" />
                                <ac:plain-text-link-body>View Schema (PDF)</ac:plain-text-link-body>
                            </ac:link>
                        </td>
                    """
                    
                    # Data dictionary column with rowspan for first schema only
                    if i == 0:
                        body += f"""
                        <td rowspan="{num_schemas}">
                            <ac:link>
                                <ri:attachment ri:filename="{db_name}_data_dictionary.xlsx" />
                                <ac:plain-text-link-body>View Data Dictionary (Excel)</ac:plain-text-link-body>
                            </ac:link>
                        </td>
                        """
                    
                    body += "</tr>"
            
            # Close the table
            body += "</table>"
            
            # Add version information
            body += f"""
            <h2>Version Information</h2>
            <ul>
                <li>Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                <li>Update ID: {timestamp}</li>
            </ul>
            """
            
            # Update the page with the complete content
            self.confluence.update_page(
                page_id=page_id,
                title=title,
                body=body,
                type='page',
                representation='storage'
            )
            
            logger.info("Successfully published documentation")
            return page_id
            
        except Exception as e:
            logger.error(f"Error publishing documentation: {str(e)}")
            raise

def main():
    """Main function to publish documentation to Confluence."""
    try:
        logger.info("Starting Confluence publisher")
        publisher = ConfluencePublisher()
        
        # Get list of databases from connections file
        with open('config/connections.json') as f:
            connections = json.load(f)
        
        # Publish documentation for all databases
        page_id = publisher.publish_documentation(
            databases=connections['databases']
        )
        logger.info(f"Documentation published successfully. Page ID: {page_id}")
                
    except Exception as e:
        logger.error(f"Error initializing publisher: {str(e)}")
        logger.exception("Full exception details:")

if __name__ == "__main__":
    main()
