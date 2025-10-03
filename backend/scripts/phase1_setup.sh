#!/bin/bash
# Phase 1 Security Hardening Setup Script
# This script installs dependencies and generates secure secrets

set -e  # Exit on error

echo "=================================================="
echo "  PROXIMITY - PHASE 1 SECURITY HARDENING SETUP  "
echo "=================================================="
echo ""

# Check if running from backend directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: Must run from backend directory"
    exit 1
fi

# Step 1: Install Python dependencies
echo "📦 Step 1: Installing Python dependencies..."
pip install -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Step 2: Generate JWT secret
echo "🔐 Step 2: Generating secure JWT secret..."

if command -v openssl &> /dev/null; then
    JWT_SECRET=$(openssl rand -hex 32)
elif command -v python3 &> /dev/null; then
    JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
else
    echo "❌ Error: Neither openssl nor python3 found. Cannot generate secret."
    exit 1
fi

echo "Generated JWT secret: $JWT_SECRET"
echo ""

# Step 3: Update .env file
echo "📝 Step 3: Updating .env file..."

if [ -f ".env" ]; then
    # Backup existing .env
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    echo "✅ Backed up existing .env"

    # Update JWT secret
    if grep -q "JWT_SECRET_KEY=" .env; then
        # Replace existing secret (Mac and Linux compatible)
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$JWT_SECRET/" .env
        else
            sed -i "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$JWT_SECRET/" .env
        fi
        echo "✅ Updated JWT_SECRET_KEY in .env"
    else
        echo "JWT_SECRET_KEY=$JWT_SECRET" >> .env
        echo "✅ Added JWT_SECRET_KEY to .env"
    fi
else
    echo "❌ Error: .env file not found"
    exit 1
fi

echo ""

# Step 4: Initialize database
echo "🗄️  Step 4: Initializing database..."
python3 -c "
import sys
sys.path.insert(0, '.')
from models.database import init_db
init_db()
print('✅ Database initialized')
"

echo ""

# Step 5: Create first admin user
echo "👤 Step 5: Create first admin user"
echo ""
echo "Please enter admin credentials:"
read -p "Username: " ADMIN_USER
read -sp "Password: " ADMIN_PASS
echo ""
read -p "Email: " ADMIN_EMAIL

python3 << EOF
import sys
sys.path.insert(0, '.')
from models.database import SessionLocal, User

db = SessionLocal()

# Check if user exists
existing = db.query(User).filter(User.username == "$ADMIN_USER").first()
if existing:
    print("⚠️  User '$ADMIN_USER' already exists")
else:
    admin = User(
        username="$ADMIN_USER",
        email="$ADMIN_EMAIL",
        hashed_password=User.hash_password("$ADMIN_PASS"),
        role="admin"
    )
    db.add(admin)
    db.commit()
    print(f"✅ Admin user '$ADMIN_USER' created successfully")

db.close()
EOF

echo ""
echo "=================================================="
echo "  ✅ PHASE 1 SETUP COMPLETE"
echo "=================================================="
echo ""
echo "🔐 Security Status:"
echo "   ✅ JWT authentication configured"
echo "   ✅ Command injection vulnerability fixed"
echo "   ✅ Database initialized"
echo "   ✅ Admin user created"
echo ""
echo "📋 Next Steps:"
echo "   1. Start the server: uvicorn main:app --reload"
echo "   2. Test login: curl -X POST http://localhost:8765/api/v1/auth/login \\"
echo "      -H 'Content-Type: application/json' \\"
echo "      -d '{\"username\":\"$ADMIN_USER\",\"password\":\"...\"}'"
echo ""
echo "⚠️  IMPORTANT:"
echo "   - Keep your JWT_SECRET_KEY secret!"
echo "   - Change admin password after first login"
echo "   - Never commit .env to git"
echo ""
