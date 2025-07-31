#!/usr/bin/env python3
"""
Script principal pour exécuter tous les tests de l'API
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Exécuter tous les tests avec pytest"""
    print("🧪 Lancement des tests de l'API Chatbot SAV")
    print("=" * 60)
    
    # Exécuter pytest directement
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "--cov=.",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
                    "--cov-fail-under=50"
    ]
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    return result.returncode == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 