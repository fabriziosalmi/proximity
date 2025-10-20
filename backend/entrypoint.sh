#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

echo "🚀 Proximity 2.0 Backend Starting..."
echo "=========================================="

echo "⏳ Waiting for PostgreSQL to start..."
# Wait for PostgreSQL to be ready
while ! nc -z db 5432; do
  sleep 0.1
done
echo "✅ PostgreSQL started."

echo "⏳ Waiting for Redis to start..."
# Wait for Redis to be ready
while ! nc -z redis 6379; do
  sleep 0.1
done
echo "✅ Redis started."

echo "🔧 Applying database migrations..."
python manage.py migrate --noinput

echo "📦 Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "=========================================="
echo "✨ Backend initialization complete!"
echo "🎯 Starting application server..."
echo "=========================================="

# Execute the command passed to the container (e.g., runserver or gunicorn)
exec "$@"
