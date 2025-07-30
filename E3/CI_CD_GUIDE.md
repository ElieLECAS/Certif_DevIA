# 🚀 Guide CI/CD - Projet E3

## 📋 Table des matières

-   [Configuration GitHub Actions](#configuration-github-actions)
-   [Protection de branche](#protection-de-branche)
-   [Workflow de développement](#workflow-de-développement)
-   [Configuration recommandée](#configuration-recommandée)
-   [Dépannage](#dépannage)

---

## ⚙️ Configuration GitHub Actions

### 📁 Structure des fichiers

```
Certif_DevIA/
├── .github/                    ← CI/CD à la racine
│   └── workflows/
│       └── ci-cd.yml          ← Workflow principal
├── E3/                        ← Votre projet
│   └── fastapi/
│       ├── tests/             ← Tests pytest
│       ├── requirements.txt   ← Dépendances
│       └── pytest.ini        ← Configuration tests
└── ...
```

### 🔧 Fichier `.github/workflows/ci-cd.yml`

```yaml
name: CI/CD Pipeline

on:
    push:
        branches: [main, master, develop, feature/*]
    pull_request:
        branches: [main, master]

jobs:
    test:
        runs-on: ubuntu-latest

        services:
            postgres:
                image: postgres:13
                env:
                    POSTGRES_PASSWORD: postgres
                    POSTGRES_DB: test_db
                options: >-
                    --health-cmd pg_isready
                    --health-interval 10s
                    --health-timeout 5s
                    --health-retries 5
                ports:
                    - 5432:5432

        steps:
            - name: Checkout code
              uses: actions/checkout@v4

            - name: Set up Python
              uses: actions/setup-python@v4
              with:
                  python-version: "3.11"

            - name: Cache pip dependencies
              uses: actions/cache@v4
              with:
                  path: ~/.cache/pip
                  key: ${{ runner.os }}-pip-${{ hashFiles('E3/fastapi/requirements.txt') }}
                  restore-keys: |
                      ${{ runner.os }}-pip-

            - name: Install dependencies
              run: |
                  python -m pip install --upgrade pip
                  pip install -r E3/fastapi/requirements.txt

            - name: Run tests with pytest
              env:
                  DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
                  SECRET_KEY: test_secret_key_for_ci
                  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
              run: |
                  cd E3/fastapi
                  pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html:htmlcov

            - name: Upload coverage reports
              uses: actions/upload-artifact@v4
              with:
                  name: coverage-reports
                  path: E3/fastapi/htmlcov/
                  retention-days: 30
```

---

## 🛡️ Protection de branche

### 📍 Localisation

-   **Settings** → **Branches** → **Add rule**
-   **Nom de la branche** : `main`

### ✅ Cases à cocher OBLIGATOIRES

#### **1. Require a pull request before merging**

-   ☑️ **Cocher** cette case
-   ☑️ **Require approvals** : `1` (pour équipe)
-   ☐ **Require approvals** : Décocher (pour développeur seul)
-   ☑️ **Dismiss stale PR approvals when new commits are pushed**

#### **2. Require status checks to pass before merging**

-   ☑️ **Cocher** cette case
-   ☑️ **Require branches to be up to date before merging**
-   **Status checks requis** : Sélectionner `test`

### ✅ Cases à cocher RECOMMANDÉES

#### **3. Require conversation resolution before merging**

-   ☑️ **Cocher** pour résoudre les discussions

#### **4. Do not allow bypassing the above settings**

-   ☑️ **Cocher** pour appliquer aux admins aussi

### ❌ Cases à cocher OPTIONNELLES

#### **5. Require signed commits**

-   ☐ **Décocher** (optionnel)

#### **6. Require linear history**

-   ☐ **Décocher** (optionnel)

#### **7. Lock branch**

-   ☐ **Décocher** (optionnel)

---

## 🔄 Workflow de développement

### **Étape 1 : Créer une branche feature**

```bash
git checkout -b feature/nouvelle-fonctionnalite
```

### **Étape 2 : Développer et tester localement**

```bash
cd E3/fastapi
pytest tests/ -v
```

### **Étape 3 : Pousser la branche**

```bash
git add .
git commit -m "Ajout nouvelle fonctionnalité"
git push origin feature/nouvelle-fonctionnalite
```

### **Étape 4 : CI/CD automatique**

-   ✅ **Tests se lancent** automatiquement sur `feature/nouvelle-fonctionnalite`
-   ✅ **Status check** apparaît sur GitHub
-   ✅ **Rapports de couverture** générés

### **Étape 5 : Créer Pull Request**

-   **Sur GitHub** : Cliquer sur "Compare & pull request"
-   **Remplir** la description de la PR
-   **Créer** la PR

### **Étape 6 : Tests sur PR**

-   ✅ **Tests se relancent** automatiquement sur la PR
-   ✅ **Status check** mis à jour
-   ✅ **Merge possible** après validation

### **Étape 7 : Merge vers main**

-   ✅ **Code mergé** vers `main`
-   ✅ **Tests relancés** sur `main`
-   ✅ **Branche feature supprimée** (si configuré)

---

## ⚙️ Configuration recommandée

### **Pour développeur seul :**

#### **✅ Protections à activer :**

-   ☑️ **Require a pull request before merging**
-   ☑️ **Require status checks to pass before merging**
-   ☑️ **Require branches to be up to date before merging**
-   ☑️ **Status check "test"** requis
-   ☑️ **Do not allow bypassing the above settings**

#### **❌ Protections à désactiver :**

-   ☐ **Require approvals** → Décocher (pour développeur seul)

### **Pour équipe :**

#### **✅ Toutes les protections :**

-   ☑️ **Require a pull request before merging**
-   ☑️ **Require approvals** : `1` ou plus
-   ☑️ **Require status checks to pass before merging**
-   ☑️ **Require branches to be up to date before merging**
-   ☑️ **Status check "test"** requis
-   ☑️ **Do not allow bypassing the above settings**

---

## 🔧 Configuration automatique

### **Suppression automatique des branches feature**

#### **Settings → General → Pull Requests**

-   ☑️ **Automatically delete head branches**

### **Secrets GitHub (si nécessaire)**

#### **Settings → Secrets and variables → Actions**

```
OPENAI_API_KEY=votre_clé_openai
DATABASE_URL=url_de_votre_base_production
SECRET_KEY=clé_secrète_production
```

---

## 🚨 Dépannage

### **Problème : CI/CD ne se lance pas**

-   ✅ **Vérifier** que `.github/workflows/` est à la racine
-   ✅ **Vérifier** que le repository est public (ou GitHub Pro)
-   ✅ **Vérifier** les permissions GitHub Actions

### **Problème : Tests échouent**

-   ✅ **Vérifier** les variables d'environnement
-   ✅ **Vérifier** les dépendances dans `requirements.txt`
-   ✅ **Vérifier** la configuration `pytest.ini`

### **Problème : Push bloqué sur main**

-   ✅ **Normal** : Utiliser des branches feature
-   ✅ **Workflow** : feature → PR → merge

### **Problème : Merge bloqué**

-   ✅ **Vérifier** que les tests passent
-   ✅ **Vérifier** la configuration des protections
-   ✅ **Vérifier** les approbations requises

---

## 📊 Résultats attendus

### **✅ Workflow réussi :**

1. **Branche feature** créée
2. **Tests automatiques** sur feature
3. **Pull Request** créée
4. **Tests relancés** sur PR
5. **Code review** (si configuré)
6. **Merge** vers main
7. **Tests relancés** sur main
8. **Branche feature supprimée**

### **📈 Métriques :**

-   **Couverture de code** : Minimum 50%
-   **Tests** : Tous les tests passent
-   **Temps de build** : ~2-5 minutes
-   **Sécurité** : Code validé avant merge

---

## 🎯 Avantages du CI/CD

### **✅ Qualité garantie :**

-   Tests automatiques à chaque push
-   Couverture de code maintenue
-   Code review obligatoire (si configuré)

### **✅ Sécurité :**

-   Pas de push direct sur main
-   Tests obligatoires avant merge
-   Historique complet des changements

### **✅ Productivité :**

-   Détection précoce des bugs
-   Workflow standardisé
-   Déploiement automatisé

### **✅ Collaboration :**

-   Code review facilitée
-   Tests partagés
-   Communication améliorée

---

## 📝 Notes importantes

### **⚠️ Points d'attention :**

-   **Repository public** : Nécessaire pour certaines protections
-   **Secrets** : Configurer les variables sensibles
-   **Permissions** : Vérifier les droits GitHub Actions
-   **Branches** : Toujours utiliser des branches feature

### **🔄 Maintenance :**

-   **Mettre à jour** les dépendances régulièrement
-   **Vérifier** les logs GitHub Actions
-   **Optimiser** les temps de build
-   **Maintenir** la couverture de code

---

_Guide créé pour le projet E3 - Certif_DevIA_
