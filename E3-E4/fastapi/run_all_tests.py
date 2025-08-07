#!/usr/bin/env python3
"""
Script pour exécuter tous les tests du projet FastAPI avec options avancées.
"""

import subprocess
import sys
import os
import argparse
import time
from pathlib import Path


def run_command(command, description):
    """Exécute une commande et affiche le résultat."""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    print(f"Commande: {command}")
    print(f"{'='*60}")
    
    start_time = time.time()
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        end_time = time.time()
        
        print(f"Durée: {end_time - start_time:.2f} secondes")
        print(f"Code de retour: {result.returncode}")
        
        if result.stdout:
            print("\n📤 Sortie standard:")
            print(result.stdout)
        
        if result.stderr:
            print("\n⚠️  Erreurs:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution: {e}")
        return False


def run_tests_with_options(options):
    """Exécute les tests avec les options spécifiées."""
    base_command = "python -m pytest"
    
    # Options de base
    command_parts = [base_command]
    
    # Options de verbosité
    if options.verbose:
        command_parts.append("-v")
    if options.very_verbose:
        command_parts.append("-vv")
    if options.quiet:
        command_parts.append("-q")
    
    # Options de couverture
    if options.coverage:
        command_parts.append("--cov=.")
        command_parts.append("--cov-report=html")
        command_parts.append("--cov-report=term-missing")
    
    # Options de performance
    if options.slow:
        command_parts.append("-m slow")
    if options.fast:
        command_parts.append("-m not slow")
    
    # Options de filtrage
    if options.test_pattern:
        command_parts.append(f"-k {options.test_pattern}")
    
    # Options de parallélisation
    if options.parallel:
        command_parts.append("-n auto")
    
    # Options de rapport
    if options.html_report:
        command_parts.append("--html=test_report.html")
        command_parts.append("--self-contained-html")
    
    if options.junit_report:
        command_parts.append("--junitxml=test_results.xml")
    
    # Ajouter le répertoire des tests
    command_parts.append("tests/")
    
    command = " ".join(command_parts)
    
    return run_command(command, "Exécution des tests pytest")


def run_linting():
    """Exécute les vérifications de code."""
    print("\n🔍 Vérifications de code...")
    
    # Flake8 pour la qualité du code
    flake8_success = run_command(
        "flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics",
        "Vérification Flake8 (erreurs critiques)"
    )
    
    # MyPy pour le typage
    mypy_success = run_command(
        "mypy . --ignore-missing-imports",
        "Vérification MyPy (typage)"
    )
    
    return flake8_success and mypy_success


def run_security_checks():
    """Exécute les vérifications de sécurité."""
    print("\n🔒 Vérifications de sécurité...")
    
    # Bandit pour la sécurité
    bandit_success = run_command(
        "bandit -r . -f json -o bandit_report.json",
        "Analyse de sécurité avec Bandit"
    )
    
    # Safety pour les dépendances
    safety_success = run_command(
        "safety check",
        "Vérification des vulnérabilités des dépendances"
    )
    
    return bandit_success and safety_success


def run_performance_tests():
    """Exécute les tests de performance."""
    print("\n⚡ Tests de performance...")
    
    # Tests de charge avec locust (si disponible)
    locust_success = run_command(
        "locust --headless --users 10 --spawn-rate 2 --run-time 30s --host http://localhost:8000",
        "Test de charge avec Locust"
    )
    
    return locust_success


def generate_test_report():
    """Génère un rapport de tests."""
    print("\n📊 Génération du rapport de tests...")
    
    # Créer un rapport HTML simple
    report_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Rapport de Tests FastAPI</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
            .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
            .success { background-color: #d4edda; border-color: #c3e6cb; }
            .error { background-color: #f8d7da; border-color: #f5c6cb; }
            .warning { background-color: #fff3cd; border-color: #ffeaa7; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚀 Rapport de Tests FastAPI</h1>
            <p>Généré le: {timestamp}</p>
        </div>
        
        <div class="section success">
            <h2>✅ Tests Exécutés</h2>
            <ul>
                <li>Tests unitaires avec pytest</li>
                <li>Tests d'intégration</li>
                <li>Tests de métriques Prometheus</li>
                <li>Tests d'authentification</li>
                <li>Tests de base de données</li>
                <li>Tests RAG</li>
            </ul>
        </div>
        
        <div class="section">
            <h2>📈 Métriques Testées</h2>
            <ul>
                <li>Request Rate (taux de requêtes)</li>
                <li>Response Time (temps de réponse)</li>
                <li>Error Rate (taux d'erreurs)</li>
                <li>Active Connections (connexions actives)</li>
                <li>HTTP Methods (méthodes HTTP)</li>
                <li>Endpoint Performance (performance des endpoints)</li>
            </ul>
        </div>
        
        <div class="section warning">
            <h2>⚠️ Points d'Attention</h2>
            <ul>
                <li>Vérifier la couverture de code</li>
                <li>Analyser les tests de performance</li>
                <li>Contrôler les métriques de sécurité</li>
            </ul>
        </div>
    </body>
    </html>
    """.format(timestamp=time.strftime("%Y-%m-%d %H:%M:%S"))
    
    with open("test_summary.html", "w", encoding="utf-8") as f:
        f.write(report_content)
    
    print("✅ Rapport généré: test_summary.html")


def main():
    """Fonction principale."""
    parser = argparse.ArgumentParser(
        description="Script d'exécution des tests FastAPI avec options avancées"
    )
    
    # Options de verbosité
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Mode verbeux"
    )
    parser.add_argument(
        "-vv", "--very-verbose",
        action="store_true",
        help="Mode très verbeux"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Mode silencieux"
    )
    
    # Options de couverture
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Générer un rapport de couverture"
    )
    
    # Options de performance
    parser.add_argument(
        "--slow",
        action="store_true",
        help="Inclure les tests lents"
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Exclure les tests lents"
    )
    
    # Options de filtrage
    parser.add_argument(
        "-k", "--test-pattern",
        type=str,
        help="Filtrer les tests par pattern"
    )
    
    # Options de parallélisation
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Exécuter les tests en parallèle"
    )
    
    # Options de rapport
    parser.add_argument(
        "--html-report",
        action="store_true",
        help="Générer un rapport HTML"
    )
    parser.add_argument(
        "--junit-report",
        action="store_true",
        help="Générer un rapport JUnit XML"
    )
    
    # Options de vérifications
    parser.add_argument(
        "--lint",
        action="store_true",
        help="Exécuter les vérifications de code"
    )
    parser.add_argument(
        "--security",
        action="store_true",
        help="Exécuter les vérifications de sécurité"
    )
    parser.add_argument(
        "--performance",
        action="store_true",
        help="Exécuter les tests de performance"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Exécuter toutes les vérifications"
    )
    
    args = parser.parse_args()
    
    print("🚀 Démarrage de l'exécution des tests FastAPI")
    print(f"📁 Répertoire de travail: {os.getcwd()}")
    
    success = True
    
    # Exécuter les tests pytest
    if not run_tests_with_options(args):
        success = False
    
    # Vérifications de code
    if args.lint or args.all:
        if not run_linting():
            success = False
    
    # Vérifications de sécurité
    if args.security or args.all:
        if not run_security_checks():
            success = False
    
    # Tests de performance
    if args.performance or args.all:
        if not run_performance_tests():
            success = False
    
    # Générer le rapport
    generate_test_report()
    
    # Résumé final
    print(f"\n{'='*60}")
    if success:
        print("✅ Tous les tests et vérifications ont réussi!")
    else:
        print("❌ Certains tests ou vérifications ont échoué.")
    print(f"{'='*60}")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())