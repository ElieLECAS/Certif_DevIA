# GMAO - Gestion de Stock

Application de gestion de stock développée avec Streamlit.

## Installation

### Option 1 : Installation locale

1. Créez un environnement virtuel Python :

```bash
python -m venv venv
```

2. Activez l'environnement virtuel :

-   Windows :

```bash
venv\Scripts\activate
```

-   Linux/Mac :

```bash
source venv/bin/activate
```

3. Installez les dépendances :

```bash
pip install -r requirements.txt
```

4. Lancez l'application :

```bash
streamlit run app.py
```

### Option 2 : Déploiement avec Docker

1. Assurez-vous d'avoir Docker et Docker Compose installés sur votre machine.

2. Construisez et lancez l'application avec Docker Compose :

```bash
docker-compose up --build
```

3. L'application sera accessible à l'adresse : http://localhost:8501

Pour arrêter l'application :

```bash
docker-compose down
```

## Fonctionnalités

-   Visualisation de l'inventaire
-   Ajout de nouveaux produits
-   Modification des produits existants
-   Recherche de produits par référence ou nom
-   Visualisation graphique des stocks
-   Gestion des emplacements et fournisseurs

## Structure des données

L'application utilise un fichier Excel (`data/inventaire.xlsx`) pour stocker les données avec les colonnes suivantes :

-   Produits : Nom du produit
-   Reference : Code-barres ou référence unique
-   Quantite : Quantité en stock
-   Emplacement : Localisation du produit
-   Fournisseur : Fournisseur du produit
-   Date_Entree : Date d'entrée en stock
-   Prix_Unitaire : Prix unitaire du produit
