# Proximity 2.0 Backend Dockerfile (SOTA Edition v2)

FROM python:3.12-slim

# Set environment variables for Python best practices
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set path for the virtual environment
ENV VENV_PATH=/app/venv

# Create the virtual environment
RUN python -m venv $VENV_PATH

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# SOTA FIX: Use the absolute path to the venv's pip to install dependencies.
# This is the most explicit and robust method, avoiding any PATH ambiguity.
RUN $VENV_PATH/bin/pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Ensure the entrypoint is executable
COPY ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose the application port
EXPOSE 8000

# Set the entrypoint for the container
ENTRYPOINT ["/entrypoint.sh"]

# Default command (can be overridden in docker-compose)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
