FROM python:3.8-slim

# Install system dependencies including build tools
RUN apt-get update && \
    apt-get install -y \
    graphviz \
    graphviz-dev \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Add src directory to Python path
ENV PYTHONPATH=/app/src

# Command to run the script
CMD ["python", "-m", "generators.data_dictionary"]
