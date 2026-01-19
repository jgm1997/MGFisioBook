#!/bin/bash
# Setup script for MGFisioBook local development

set -e

echo "🚀 MGFisioBook - Setup Script"
echo "=============================="

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.12"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Error: Python $REQUIRED_VERSION or higher is required. Found: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python version: $PYTHON_VERSION"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip -q

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt -q

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration"
else
    echo "✅ .env file already exists"
fi

# Create test database directory
mkdir -p tests

echo ""
echo "✅ Setup completed!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your credentials"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Run migrations: alembic upgrade head"
echo "4. Start server: uvicorn app.main:app --reload"
echo "5. Visit: http://localhost:8000/docs"
echo ""
echo "To run tests:"
echo "  pytest tests/ -v"
echo ""
echo "Happy coding! 🎉"
