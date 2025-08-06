# 🔧 Guide de Résolution des Conflits de Dépendances

## 🚨 Problème Résolu

Le projet a été configuré pour éviter les conflits de dépendances avec les solutions suivantes :

## ✅ Solutions Appliquées

### 1. **Versions Assouplies**
- Remplacé `==` par `>=` pour permettre la résolution automatique
- Exemple : `fastapi==0.104.1` → `fastapi>=0.104.0`

### 2. **Séparation des Dépendances**
- **`requirements.txt`** : Dépendances de production uniquement
- **`requirements-dev.txt`** : Dépendances de développement
- **`pyproject.toml`** : Configuration moderne avec dépendances optionnelles

### 3. **Dépendances Corrigées**
- Supprimé `starlette-prometheus` (conflit potentiel)
- Utilisé `psutil` pour les métriques système
- Ajouté gestion d'erreurs dans le monitoring

## 🚀 Installation

### Option 1 : Installation Simple
```bash
cd E3-E4
pip install -r fastapi/requirements.txt
```

### Option 2 : Installation avec Développement
```bash
cd E3-E4/fastapi
pip install -e ".[dev]"
```

### Option 3 : Script Automatique
```bash
cd E3-E4
./install_dependencies.sh --dev
```

## 📦 Structure des Dépendances

### Production (`requirements.txt`)
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
psycopg2-binary>=2.9.0
sqlalchemy>=2.0.0
python-jose[cryptography]>=3.3.0
bcrypt>=4.0.0
passlib[bcrypt]>=1.7.0
python-multipart>=0.0.6
jinja2>=3.1.0
aiofiles>=23.0.0
pydantic[email]>=2.0.0
python-dotenv>=1.0.0
prometheus-client>=0.19.0
psutil>=5.9.0
langchain>=0.1.0
langchain-openai>=0.1.0
langchain-text-splitters>=0.1.0
langchain-community>=0.1.0
faiss-cpu>=1.7.0
pymupdf>=1.23.0
pandas>=2.0.0
numpy>=1.24.0
matplotlib>=3.7.0
plotly>=5.0.0
scikit-learn>=1.3.0
joblib>=1.3.0
requests>=2.31.0
httpx>=0.24.0
thefuzz>=0.19.0
fuzzywuzzy>=0.18.0
alembic>=1.12.0
fastapi-cors>=0.0.6
```

### Développement (`requirements-dev.txt`)
```
-r requirements.txt
pytest>=7.4.0
pytest-mock>=3.11.0
pytest-cov>=4.1.0
pytest-asyncio>=0.21.0
black>=23.0.0
flake8>=6.0.0
isort>=5.12.0
sphinx>=7.0.0
sphinx-rtd-theme>=1.3.0
ipython>=8.0.0
ipdb>=0.13.0
```

## 🔍 Vérification

### Test d'Installation
```bash
python3 -c "
import fastapi
import prometheus_client
import psutil
import langchain
import pandas
import numpy
print('✅ Toutes les dépendances sont installées!')
"
```

### Test du Monitoring
```bash
cd E3-E4
python test_monitoring.py
```

## 🛠️ Dépannage

### Problème : Conflit de Versions
```bash
# Solution 1 : Nettoyer et réinstaller
pip uninstall -y -r fastapi/requirements.txt
pip install -r fastapi/requirements.txt

# Solution 2 : Utiliser un environnement virtuel
python3 -m venv venv
source venv/bin/activate
pip install -r fastapi/requirements.txt
```

### Problème : Dépendances Manquantes
```bash
# Vérifier les dépendances
pip check

# Installer les dépendances manquantes
pip install --upgrade pip setuptools wheel
```

### Problème : Versions Incompatibles
```bash
# Forcer la résolution
pip install --no-deps -r fastapi/requirements.txt
pip install -r fastapi/requirements.txt
```

## 📊 Métriques de Monitoring

Le monitoring utilise maintenant :
- **`prometheus-client`** : Métriques Prometheus
- **`psutil`** : Métriques système (CPU, mémoire)
- **Gestion d'erreurs** : Évite les crashs de l'application

## 🔄 CI/CD

Le workflow GitHub Actions utilise :
```yaml
- name: Install dependencies
  run: |
      python -m pip install --upgrade pip
      cd E3-E4/fastapi
      pip install -e ".[dev]"
```

## ✅ Résultat

Après ces corrections :
- ✅ **Aucun conflit de dépendances**
- ✅ **Installation robuste**
- ✅ **Monitoring fonctionnel**
- ✅ **CI/CD opérationnel**
- ✅ **Développement facilité**

## 🎯 Bonnes Pratiques

1. **Utiliser `>=`** au lieu de `==` pour les versions
2. **Séparer** les dépendances de production et développement
3. **Tester** l'installation après chaque modification
4. **Documenter** les changements de dépendances
5. **Utiliser** des environnements virtuels en développement

---

Le projet est maintenant **stable** et **prêt pour la production** ! 🚀