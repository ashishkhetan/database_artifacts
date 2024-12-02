@echo off
setlocal enabledelayedexpansion

:: Set timestamp for log file
set "timestamp=%date:~10,4%-%date:~4,2%-%date:~7,2%_%time:~0,2%-%time:~3,2%-%time:~6,2%"
set "timestamp=!timestamp: =0!"
set "logfile=logs\generate_docs_%timestamp%.log"

:: Create logs directory if it doesn't exist
if not exist logs mkdir logs

:: Delete logs older than 7 days
forfiles /p logs /s /m *.log /d -7 /c "cmd /c del @path" 2>nul

echo Starting database documentation generation at %date% %time% > "%logfile%"

:: Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker is not running. Please start Docker Desktop and try again. >> "%logfile%"
    echo Docker is not running. Please start Docker Desktop and try again.
    exit /b 1
)

:: Set working directory to script location
cd /d %~dp0

:: Clean output directory
echo Cleaning output directory... >> "%logfile%"
echo Cleaning output directory...
if exist output (
    rmdir /s /q output
)
mkdir output

echo. >> "%logfile%"
echo Step 1: Running schema generator... >> "%logfile%"
echo Running schema generator...
docker-compose run --rm datadictionary python src/generators/schema.py >> "%logfile%" 2>&1
if %errorlevel% neq 0 (
    echo Schema generation failed with error code %errorlevel% >> "%logfile%"
    echo Schema generation failed. Check %logfile% for details.
    exit /b %errorlevel%
)

echo. >> "%logfile%"
echo Step 2: Running data dictionary generator... >> "%logfile%"
echo Running data dictionary generator...
docker-compose run --rm datadictionary python src/generators/data_dictionary.py >> "%logfile%" 2>&1
if %errorlevel% neq 0 (
    echo Data dictionary generation failed with error code %errorlevel% >> "%logfile%"
    echo Data dictionary generation failed. Check %logfile% for details.
    exit /b %errorlevel%
)

echo. >> "%logfile%"
echo Step 3: Publishing to Confluence... >> "%logfile%"
echo Publishing to Confluence...
docker-compose run --rm datadictionary python src/publishers/confluence.py >> "%logfile%" 2>&1
if %errorlevel% neq 0 (
    echo Confluence publishing failed with error code %errorlevel% >> "%logfile%"
    echo Confluence publishing failed. Check %logfile% for details.
    exit /b %errorlevel%
)

echo. >> "%logfile%"
echo Documentation generation completed successfully at %date% %time% >> "%logfile%"
echo Documentation generation completed successfully. Log file: %logfile%

exit /b 0
