# Database Documentation Generator

Automatically generates and publishes database documentation including schema diagrams and data dictionaries to Confluence.

## Features

- Schema diagram generation (PNG and PDF)
- Data dictionary generation (Excel)
- Automated Confluence publishing
- Comprehensive logging
- Error handling and recovery
- Support for multiple databases and schemas

## Project Structure

```
.
├── config/
│   ├── confluence_config.json     # Confluence connection settings
│   └── connections.json          # Database connection settings
├── src/
│   ├── generators/
│   │   ├── schema.py            # Generates ERD diagrams
│   │   └── data_dictionary.py   # Generates Excel documentation
│   ├── publishers/
│   │   └── confluence.py        # Publishes to Confluence
│   └── utils/
│       └── db.py               # Database utilities
├── output/                     # Generated documentation
│   └── {database_name}/       # Per-database outputs
├── logs/                      # Log files
├── test_databases/            # Test database init scripts
├── docker-compose.yml         # Docker configuration
├── Dockerfile                 # Container definition
├── generate_docs.bat          # Main execution script
└── requirements.txt           # Python dependencies
```

## Setup

1. Configure database connections in `config/connections.json`:
   ```json
   {
     "databases": [
       {
         "name": "database_name",
         "endpoint_rw": "hostname",
         "port": 5432,
         "database": "dbname",
         "username": "user",
         "password": "pass"
       }
     ]
   }
   ```

2. Configure Confluence settings in `config/confluence_config.json`:
   ```json
   {
     "url": "https://your-domain.atlassian.net",
     "username": "your-email@domain.com",
     "api_token": "your-api-token",
     "space_key": "SPACE",
     "parent_page_id": "12345"
   }
   ```

## Usage

### Manual Execution

Run the documentation generator:
```bash
.\generate_docs.bat
```

The script will:
1. Generate schema diagrams (PNG/PDF)
2. Create data dictionaries (Excel)
3. Publish everything to Confluence
4. Save logs to `logs/generate_docs_TIMESTAMP.log`

### Automated Execution

Schedule with Windows Task Scheduler:
1. Program/script: `C:\Windows\System32\cmd.exe`
2. Arguments: `/c "cd /d PATH_TO_PROJECT && generate_docs.bat"`
3. Start in: `PATH_TO_PROJECT`

### Development/Testing

To run with test databases:
```bash
docker-compose --profile test up -d
```

This will start PostgreSQL containers with sample databases for testing.

## Output

1. Schema Diagrams:
   - `output/{database_name}/{schema_name}_schema.png`
   - `output/{database_name}/{schema_name}_schema.pdf`

2. Data Dictionaries:
   - `output/{database_name}/{database_name}_data_dictionary.xlsx`

3. Log Files:
   - `logs/generate_docs_TIMESTAMP.log`
   - Logs are automatically cleaned up after 7 days

## Error Handling

The system includes comprehensive error handling:
- Connection testing before processing
- Per-database error isolation
- Detailed error logging
- Automatic recovery and continuation
- Clear error messages and suggestions
