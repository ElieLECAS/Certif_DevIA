# 🔍 Monitoring Vanna AI avec Langfuse

Ce projet intègre **Langfuse** à votre application **Vanna AI** pour un monitoring complet des appels API IA, incluant les tokens, coûts, latence et performances.

## 🚀 Installation rapide

### Option 1: Installation automatique
```bash
chmod +x install_langfuse.sh
./install_langfuse.sh
```

### Option 2: Installation manuelle
```bash
pip install langfuse>=2.0.0
```

## ⚙️ Configuration

1. **Créez un compte Langfuse** sur [cloud.langfuse.com](https://cloud.langfuse.com)
2. **Créez un nouveau projet** et récupérez vos clés API
3. **Configurez votre fichier `.env`** :

```bash
# Configuration Langfuse
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com

# Vos clés existantes
OPENAI_API_KEY=sk-...
```

## 📊 Utilisation

### Avec Jupyter Notebook
Votre notebook existant `vanna_ai_UI.ipynb` est maintenant automatiquement instrumenté ! Exécutez-le normalement et toutes les métriques seront envoyées à Langfuse.

### Test indépendant
```bash
python test_langfuse_integration.py
```

## 🎯 Métriques trackées

- **💰 Coûts et tokens** : Consommation détaillée par requête
- **⚡ Latence** : Temps de réponse en millisecondes
- **🏷️ Métadonnées** : Utilisateur, session, tags, user-agent
- **🔍 Traces complètes** : Input/output de chaque appel
- **📈 Tendances** : Évolution dans le temps
- **🚨 Erreurs** : Capture et analyse des échecs

## 📈 Dashboard Langfuse

Accédez à votre dashboard sur [cloud.langfuse.com](https://cloud.langfuse.com) pour :

- Visualiser les traces en temps réel
- Analyser les coûts et performances
- Déboguer les problèmes
- Configurer des alertes
- Générer des rapports

## 📁 Fichiers créés

```
vanna/
├── vanna_ai_UI.ipynb           # Notebook modifié avec Langfuse
├── test_langfuse_integration.py # Script de test
├── install_langfuse.sh         # Installation automatique
├── requirements_langfuse.txt   # Dépendances
├── env_example.txt            # Template .env
├── guide_langfuse_integration.md # Guide détaillé
└── README_Langfuse.md         # Ce fichier
```

## 🔧 Configuration avancée

### Filtrage par échantillonnage
```python
# Ne tracker que 10% des requêtes
langfuse = Langfuse(sample_rate=0.1)
```

### Mode debug
```bash
export LANGFUSE_DEBUG=true
```

### Métadonnées personnalisées
```python
with langfuse.trace(
    name="requete-custom",
    user_id="user-123",
    tags=["production", "sql"]
) as trace:
    result = vn.ask("Votre question")
```

## 🆘 Dépannage

### Problèmes courants

**Pas de traces visibles ?**
```python
langfuse.flush()  # Force l'envoi
```

**Erreur d'authentification ?**
```bash
echo $LANGFUSE_PUBLIC_KEY  # Vérifiez vos clés
```

**Test de connexion ?**
```python
langfuse.auth_check()  # Doit retourner True
```

## 📚 Documentation

- 📖 [Guide complet](guide_langfuse_integration.md)
- 🌐 [Documentation Langfuse](https://langfuse.com/docs)
- 💬 [Support Discord](https://discord.gg/7NXusRtqYU)

## ✨ Fonctionnalités

- ✅ **Zero-config** : Fonctionne avec votre code existant
- ✅ **Temps réel** : Monitoring instantané
- ✅ **Open-source** : Langfuse est entièrement open-source
- ✅ **Scalable** : Supporte des milliers de requêtes
- ✅ **Sécurisé** : Vos données restent privées
- ✅ **Alertes** : Notifications proactives
- ✅ **Évaluations** : Score de qualité des réponses

## 🎉 Résultat

Votre application Vanna dispose maintenant d'un monitoring professionnel :

🔍 **Observabilité complète** de tous les appels IA  
💰 **Suivi automatique des coûts** et tokens  
📊 **Dashboard en temps réel** avec métriques  
🚨 **Alertes intelligentes** sur les problèmes  
📈 **Analyses de tendances** pour l'optimisation  

**Prêt pour la production !** 🚀 