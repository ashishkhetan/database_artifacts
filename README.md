# Database Documentation Generator

A utility to generate and publish comprehensive database documentation including data dictionaries and schema diagrams for PostgreSQL databases.

## Features

- Generate detailed Excel-based data dictionaries
- Create ERD diagrams for database schemas
- Support for multiple databases and schemas
- Configurable through JSON connection files
- Automatic publishing to Confluence with retention policies:
  * Weekly versions: Keeps last 4 weeks
  * Monthly versions: Keeps last 6 months
  * Quarterly versions: Keeps last 4 quarters

## Installation

1. Ensure you have Docker installed
2. Clone this repository
3. Build the Docker image:
```bash
docker-compose build
```

## Configuration

### Database Connections

Create a `connections.json` file with your database connection details:

```json
{
    "databases": [
        {
            "name": "employees_db",
            "database": "employees",
            "username": "postgres",
            "password": "password",
            "endpoint_rw": "db1",
            "port": 5432
        },
        {
            "name": "orders_db",
            "database": "orders",
            "username": "postgres",
            "password": "password",
            "endpoint_rw": "db2",
            "port": 5432
        }
    ]
}
```

### Confluence Configuration

Create a `confluence_config.json` file for Confluence integration:

```json
{
    "url": "https://your-domain.atlassian.net",
    "username": "your-email@domain.com",
    "api_token": "your-api-token",
    "space_key": "SPACE"
}
```

To get an API token:
1. Log in to https://id.atlassian.com/manage/api-tokens
2. Click "Create API token"
3. Copy the token and paste it in your configuration file

## Usage

### Generate Documentation

1. Generate both data dictionary and schema diagrams:
```bash
docker-compose run --rm datadictionary python data_dictionary.py --type all
```

2. Generate only data dictionary:
```bash
docker-compose run --rm datadictionary python data_dictionary.py --type dictionary
```

3. Generate only schema diagrams:
```bash
docker-compose run --rm datadictionary python data_dictionary.py --type schema
```

### Publish to Confluence

Generate and publish documentation:
```bash
docker-compose run --rm datadictionary python data_dictionary.py --type all --publish
```

You can also specify custom configuration files:
```bash
docker-compose run --rm datadictionary python data_dictionary.py --type all --publish \
    --connection-file my_connections.json \
    --confluence-config my_confluence_config.json \
    --output-dir documentation
```

### Automation

To automate weekly documentation updates, you can set up a cron job or scheduled task:

#### Linux Cron Example
```bash
# Run every Monday at 2 AM
0 2 * * 1 cd /path/to/project && docker-compose run --rm datadictionary python data_dictionary.py --type all --publish
```

#### Windows Task Scheduler
Create a batch file `update_docs.bat`:
```batch
cd C:\path\to\project
docker-compose run --rm datadictionary python data_dictionary.py --type all --publish
```
Then schedule it to run weekly using Task Scheduler.

## Output Structure

### Local Files

The utility creates a directory structure like this:

```
output_dir/
├── database1/
│   ├── database1_data_dictionary.xlsx
│   └── schema1_schema.png
└── database2/
    ├── database2_data_dictionary.xlsx
    └── schema2_schema.png
```

### Confluence Pages

For each database, the utility creates:
- A new page with the current timestamp
- Attachments for all generated files
- Automatic cleanup of old versions based on retention policy:
  * Keeps the last 4 weekly versions
  * Keeps the last 6 monthly versions
  * Keeps the last 4 quarterly versions

### Data Dictionary Excel Format

Each Excel file contains multiple sheets:
- Tables: List of all tables with descriptions
- Columns: Detailed column information including data types and constraints
- Constraints: Table constraints (PRIMARY KEY, FOREIGN KEY, etc.)
- Indexes: Table indexes and their definitions

### Schema Diagrams

ERD diagrams are generated in PNG format showing:
- Tables and their columns
- Primary keys
- Foreign key relationships
- Data types
