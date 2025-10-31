#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

echo "🚀 Proximity 2.0 Backend Starting..."
echo "=========================================="

echo "⏳ Waiting for PostgreSQL to start..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "✅ PostgreSQL started."

echo "⏳ Waiting for Redis to start..."
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

# The CMD from docker-compose will be executed here.
# The Dockerfile ENV PATH ensures that "python" resolves to the venv python.
exec "$@"
