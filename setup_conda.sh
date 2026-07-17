#!/bin/bash
set -e

ENV_NAME="paper_assistant"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "================================================"
echo "  PaperAssistant - Conda Env Setup"
echo "================================================"
echo ""

# Init conda
init_conda() {
    if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
        source "$HOME/miniconda3/etc/profile.d/conda.sh"
    elif [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
        source "$HOME/anaconda3/etc/profile.d/conda.sh"
    elif [ -f "$HOME/miniforge3/etc/profile.d/conda.sh" ]; then
        source "$HOME/miniforge3/etc/profile.d/conda.sh"
    elif [ -f "/opt/conda/etc/profile.d/conda.sh" ]; then
        source "/opt/conda/etc/profile.d/conda.sh"
    elif command -v conda &>/dev/null; then
        eval "$(conda shell.bash hook)"
    else
        echo "[ERROR] conda not found."
        echo "  Install Miniconda: https://docs.conda.io/en/latest/miniconda.html"
        exit 1
    fi
}

init_conda

# Step 1: Create environment
echo "[1/3] Creating environment: $ENV_NAME (Python 3.11)"
if conda env list 2>/dev/null | grep -q "^$ENV_NAME "; then
    echo "      Already exists, skipping."
else
    conda create -n "$ENV_NAME" python=3.11 -y
fi

# Find the env's Python
CONDA_BASE=$(conda info --base 2>/dev/null)
ENV_PYTHON="$CONDA_BASE/envs/$ENV_NAME/bin/python"
if [ ! -f "$ENV_PYTHON" ]; then
    # Windows conda uses python.exe
    ENV_PYTHON="$CONDA_BASE/envs/$ENV_NAME/python.exe"
fi
if [ ! -f "$ENV_PYTHON" ]; then
    echo "[ERROR] Cannot find Python in $ENV_NAME environment."
    exit 1
fi
echo "      OK: $ENV_PYTHON"

# Step 2: Install dependencies
echo ""
echo "[2/3] Installing Python packages..."
"$ENV_PYTHON" -m pip install -r "$SCRIPT_DIR/requirements.txt" -q
echo "      OK"

# Step 3: Migrate database
echo ""
echo "[3/3] Initializing database..."
"$ENV_PYTHON" "$SCRIPT_DIR/manage.py" migrate --run-syncdb
echo "      OK"

echo ""
echo "================================================"
echo "  Setup complete!"
echo ""
echo "  1. Edit .env and set OPENAI_API_KEY"
echo "  2. Start:  bash run_lan.sh"
echo "     Or:     conda activate $ENV_NAME"
echo "             python manage.py runserver"
echo "  3. Open    http://127.0.0.1:8000"
echo "================================================"
