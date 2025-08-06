#!/usr/bin/env python3
"""
Test simple pour vérifier que les corrections du monitoring fonctionnent.
"""

import sys
import os

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_monitoring_import():
    """Test que le module de monitoring peut être importé sans erreur."""
    try:
        from monitoring import (
            PrometheusMiddleware,
            create_metrics_response,
            record_chat_request,
            record_chat_response_time,
            record_ai_model_call
        )
        print("✅ Import du module monitoring réussi")
        return True
    except Exception as e:
        print(f"❌ Erreur d'import du module monitoring: {e}")
        return False

def test_auth_functions():
    """Test que les fonctions d'authentification peuvent être importées."""
    try:
        from auth import is_client_only, get_client_user
        print("✅ Import des fonctions d'authentification réussi")
        return True
    except Exception as e:
        print(f"❌ Erreur d'import des fonctions d'authentification: {e}")
        return False

def test_app_import():
    """Test que l'application peut être importée."""
    try:
        from app import app
        print("✅ Import de l'application réussi")
        return True
    except Exception as e:
        print(f"❌ Erreur d'import de l'application: {e}")
        return False

def test_metrics_endpoint():
    """Test que l'endpoint /metrics fonctionne."""
    try:
        from monitoring import create_metrics_response
        response = create_metrics_response()
        print("✅ Endpoint /metrics fonctionne")
        return True
    except Exception as e:
        print(f"❌ Erreur de l'endpoint /metrics: {e}")
        return False

def main():
    """Fonction principale de test."""
    print("🔍 Test des corrections du monitoring")
    print("=" * 50)
    
    tests = [
        ("Import monitoring", test_monitoring_import),
        ("Import auth", test_auth_functions),
        ("Import app", test_app_import),
        ("Metrics endpoint", test_metrics_endpoint),
    ]
    
    all_passed = True
    for test_name, test_func in tests:
        print(f"\n🧪 Test: {test_name}")
        if test_func():
            print(f"   ✅ {test_name} - PASS")
        else:
            print(f"   ❌ {test_name} - FAIL")
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 TOUS LES TESTS SONT PASSÉS !")
        print("✅ Les corrections du monitoring sont fonctionnelles")
    else:
        print("⚠️  CERTAINS TESTS ONT ÉCHOUÉ")
        print("🔧 Vérifiez les erreurs ci-dessus")
    
    print("=" * 50)

if __name__ == "__main__":
    main()