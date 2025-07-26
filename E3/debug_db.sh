#!/bin/bash

echo "🔍 Diagnostic PostgreSQL"
echo "========================"

# Vérifier si le conteneur PostgreSQL est en cours d'exécution
echo "1. Vérification du conteneur PostgreSQL:"
if docker ps | grep -q chatbot_sav_db; then
    echo "✅ Conteneur PostgreSQL en cours d'exécution"
else
    echo "❌ Conteneur PostgreSQL non trouvé"
    exit 1
fi

# Vérifier les logs PostgreSQL
echo ""
echo "2. Logs PostgreSQL (dernières 20 lignes):"
docker logs chatbot_sav_db --tail 20

# Vérifier la connectivité réseau
echo ""
echo "3. Test de connectivité réseau:"
if nc -z db 5432; then
    echo "✅ Port 5432 accessible (interne)"
else
    echo "❌ Port 5432 non accessible (interne)"
fi

# Tester la connexion externe
echo ""
echo "4. Test de connectivité externe:"
if nc -z localhost 5433; then
    echo "✅ Port 5433 accessible (externe)"
else
    echo "❌ Port 5433 non accessible (externe)"
fi

# Tester la connexion avec psql
echo ""
echo "5. Test de connexion avec psql:"
if PGPASSWORD=password psql -h db -U postgres -d chatbot_sav -c "SELECT version();" 2>/dev/null; then
    echo "✅ Connexion psql réussie"
else
    echo "❌ Connexion psql échouée"
fi

# Vérifier les variables d'environnement
echo ""
echo "6. Variables d'environnement PostgreSQL:"
docker exec chatbot_sav_db env | grep POSTGRES

echo ""
echo "🏁 Diagnostic terminé" 