"""PaperAssistant Desktop - Entry Point."""
import sys
import os

# Ensure project root is on path for .env loading
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import main

if __name__ == '__main__':
    main()
