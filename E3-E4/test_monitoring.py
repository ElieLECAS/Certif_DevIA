#!/usr/bin/env python3
"""
Script de test pour vérifier le monitoring Prometheus/Grafana.
"""

import requests
import time
import json
from datetime import datetime

def test_health_endpoint():
    """Test de l'endpoint de santé."""
    try:
        response = requests.get("http://localhost:8001/health")
        print(f"✅ Health check: {response.status_code}")
        print(f"   Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_metrics_endpoint():
    """Test de l'endpoint des métriques."""
    try:
        response = requests.get("http://localhost:8001/metrics")
        print(f"✅ Metrics endpoint: {response.status_code}")
        
        # Vérifier quelques métriques clés
        content = response.text
        metrics_to_check = [
            "http_requests_total",
            "http_request_duration_seconds",
            "memory_usage_bytes",
            "cpu_usage_percent"
        ]
        
        for metric in metrics_to_check:
            if metric in content:
                print(f"   ✅ {metric} found")
            else:
                print(f"   ⚠️  {metric} not found")
        
        return True
    except Exception as e:
        print(f"❌ Metrics endpoint failed: {e}")
        return False

def test_prometheus_targets():
    """Test des cibles Prometheus."""
    try:
        response = requests.get("http://localhost:9090/api/v1/targets")
        print(f"✅ Prometheus targets: {response.status_code}")
        
        data = response.json()
        targets = data.get("data", {}).get("activeTargets", [])
        
        for target in targets:
            name = target.get("labels", {}).get("job", "unknown")
            health = target.get("health", "unknown")
            print(f"   📊 {name}: {health}")
        
        return True
    except Exception as e:
        print(f"❌ Prometheus targets failed: {e}")
        return False

def test_grafana_datasource():
    """Test de la source de données Grafana."""
    try:
        # Test de connexion à Grafana
        response = requests.get("http://localhost:3000/api/health")
        print(f"✅ Grafana health: {response.status_code}")
        
        # Test de la source de données Prometheus
        response = requests.get("http://localhost:3000/api/datasources")
        print(f"✅ Grafana datasources: {response.status_code}")
        
        return True
    except Exception as e:
        print(f"❌ Grafana test failed: {e}")
        return False

def generate_test_traffic():
    """Génère du trafic de test pour voir les métriques."""
    print("\n🚀 Génération de trafic de test...")
    
    # Simuler quelques requêtes
    endpoints = [
        "/health",
        "/metrics",
        "/",
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"http://localhost:8001{endpoint}")
            print(f"   📡 {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"   ❌ {endpoint}: {e}")
    
    print("   ⏳ Attente de 5 secondes pour laisser le temps aux métriques de se mettre à jour...")
    time.sleep(5)

def main():
    """Fonction principale de test."""
    print("🔍 Test du système de monitoring FastAPI/Prometheus/Grafana")
    print("=" * 60)
    
    # Tests de base
    health_ok = test_health_endpoint()
    metrics_ok = test_metrics_endpoint()
    
    # Tests des services de monitoring
    prometheus_ok = test_prometheus_targets()
    grafana_ok = test_grafana_datasource()
    
    # Génération de trafic de test
    generate_test_traffic()
    
    # Vérification finale des métriques
    print("\n📊 Vérification finale des métriques...")
    test_metrics_endpoint()
    
    # Résumé
    print("\n" + "=" * 60)
    print("📋 RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    tests = [
        ("Health Check", health_ok),
        ("Metrics Endpoint", metrics_ok),
        ("Prometheus Targets", prometheus_ok),
        ("Grafana Health", grafana_ok),
    ]
    
    all_passed = True
    for test_name, passed in tests:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 TOUS LES TESTS SONT PASSÉS !")
        print("\n📊 Accès aux interfaces :")
        print("   • FastAPI App: http://localhost:8001")
        print("   • Prometheus: http://localhost:9090")
        print("   • Grafana: http://localhost:3000 (admin/admin)")
        print("\n📈 Métriques disponibles :")
        print("   • /metrics - Métriques Prometheus")
        print("   • /health - État de l'application")
    else:
        print("⚠️  CERTAINS TESTS ONT ÉCHOUÉ")
        print("\n🔧 Vérifications à faire :")
        print("   1. Vérifier que docker-compose est démarré")
        print("   2. Vérifier les logs: docker-compose logs")
        print("   3. Vérifier les ports: 8001, 9090, 3000")
    
    print("=" * 60)

if __name__ == "__main__":
    main()