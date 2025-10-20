#!/bin/bash
# Proximity 2.0 - Setup Script
# Initializes the Django backend and database

set -e  # Exit on error

echo "🚀 Proximity 2.0 - Backend Setup"
echo "================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    exit 1
fi

echo "✅ Docker is running"

# Start database services
echo ""
echo "📦 Starting database services..."
docker-compose up -d db redis

# Wait for database to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5

# Run migrations
echo ""
echo "🔨 Running database migrations..."
docker-compose exec -T backend python manage.py migrate

echo ""
echo "✅ Database migrations complete"

# Create superuser (interactive)
echo ""
read -p "Do you want to create a superuser? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker-compose exec backend python manage.py createsuperuser
fi

# Collect static files
echo ""
echo "📁 Collecting static files..."
docker-compose exec -T backend python manage.py collectstatic --noinput

echo ""
echo "✨ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Start all services: docker-compose up -d"
echo "  2. Access frontend: http://localhost:5173"
echo "  3. Access API docs: http://localhost:8000/api/docs"
echo "  4. Access Django admin: http://localhost:8000/admin"
