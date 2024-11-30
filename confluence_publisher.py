import json
import base64
from datetime import datetime, timedelta
from pathlib import Path
import requests
from atlassian import Confluence

class ConfluencePublisher:
    def __init__(self, config_file='confluence_config.json'):
        """Initialize Confluence publisher with configuration."""
        with open(config_file) as f:
            self.config = json.load(f)
        
        self.confluence = Confluence(
            url=self.config['url'],
            username=self.config['username'],
            password=self.config['api_token'],
            cloud=True  # Set to False for server installation
        )
        
        self.retention = {
            'weekly': 4,      # Keep 4 weeks
            'monthly': 6,     # Keep 6 months
            'quarterly': 4    # Keep 4 quarters
        }
    
    def _get_timestamp(self):
        """Get current timestamp in a readable format."""
        return datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    
    def _get_content_type(self, file_path):
        """Get content type based on file extension."""
        extension = file_path.suffix.lower()
        if extension == '.png':
            return 'image/png'
        elif extension == '.xlsx':
            return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        return 'application/octet-stream'
    
    def _attach_file(self, page_id, file_path):
        """Attach a file to a Confluence page."""
        with open(file_path, 'rb') as file:
            self.confluence.attach_file(
                filename=file_path.name,
                content_type=self._get_content_type(file_path),
                page_id=page_id,
                data=file
            )
    
    def _create_or_update_page(self, space_key, title, body):
        """Create or update a Confluence page."""
        existing_page = self.confluence.get_page_by_title(
            space=space_key,
            title=title
        )
        
        if existing_page:
            self.confluence.update_page(
                page_id=existing_page['id'],
                title=title,
                body=body
            )
            return existing_page['id']
        else:
            page = self.confluence.create_page(
                space=space_key,
                title=title,
                body=body
            )
            return page['id']
    
    def _get_retention_period(self, timestamp):
        """Determine which retention period a timestamp falls into."""
        date = datetime.strptime(timestamp, '%Y-%m-%d_%H-%M-%S')
        now = datetime.now()
        age = now - date
        
        if age <= timedelta(weeks=4):
            return 'weekly'
        elif age <= timedelta(days=180):  # ~6 months
            return 'monthly'
        else:
            return 'quarterly'
    
    def _clean_old_versions(self, space_key, base_title):
        """Clean up old versions based on retention policy."""
        # Get all pages with the base title
        pages = self.confluence.get_all_pages_by_title(space_key, base_title)
        
        # Group pages by retention period
        grouped_pages = {
            'weekly': [],
            'monthly': [],
            'quarterly': []
        }
        
        for page in pages:
            timestamp = page['title'].split('_')[-1]
            period = self._get_retention_period(timestamp)
            grouped_pages[period].append((timestamp, page))
        
        # Sort pages by timestamp and keep only the allowed number for each period
        for period, limit in self.retention.items():
            pages = sorted(grouped_pages[period], key=lambda x: x[0], reverse=True)
            # Delete excess pages
            for _, page in pages[limit:]:
                self.confluence.delete_page(page['id'])
    
    def publish_documentation(self, doc_dir: Path, database_name: str):
        """Publish database documentation to Confluence."""
        timestamp = self._get_timestamp()
        space_key = self.config['space_key']
        
        # Base title for the documentation
        base_title = f"Database Documentation - {database_name}"
        # Current version title
        title = f"{base_title}_{timestamp}"
        
        # Create page content
        body = f"""
        <h1>Database Documentation for {database_name}</h1>
        <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <h2>Schema Diagrams</h2>
        <p>The following schema diagrams show the database structure and relationships:</p>
        
        <h2>Data Dictionary</h2>
        <p>Detailed information about database objects can be found in the attached Excel file.</p>
        
        <h2>Attachments</h2>
        <p>The following files are attached to this page:</p>
        <ul>
            <li>Data Dictionary Excel file</li>
            <li>Schema Diagram(s)</li>
        </ul>
        """
        
        # Create or update the page
        page_id = self._create_or_update_page(space_key, title, body)
        
        # Attach files
        doc_path = Path(doc_dir) / database_name
        for file_path in doc_path.glob('*'):
            if file_path.is_file():
                self._attach_file(page_id, file_path)
        
        # Clean up old versions based on retention policy
        self._clean_old_versions(space_key, base_title)
        
        return page_id

def main():
    """Main function to publish documentation to Confluence."""
    # Example configuration file (confluence_config.json):
    # {
    #     "url": "https://your-domain.atlassian.net",
    #     "username": "your-email@domain.com",
    #     "api_token": "your-api-token",
    #     "space_key": "SPACE"
    # }
    
    publisher = ConfluencePublisher('confluence_config.json')
    
    # Get list of databases from the same connection file
    with open('connections.json') as f:
        connections = json.load(f)
    
    for db_config in connections['databases']:
        try:
            print(f"\nPublishing documentation for database: {db_config['name']}")
            page_id = publisher.publish_documentation('data_dictionary', db_config['name'])
            print(f"Documentation published successfully. Page ID: {page_id}")
        except Exception as e:
            print(f"Error publishing documentation for {db_config['name']}: {str(e)}")

if __name__ == "__main__":
    main()
