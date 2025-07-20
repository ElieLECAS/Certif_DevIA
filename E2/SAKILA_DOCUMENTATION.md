# Documentation Base de Données Sakila

## Vue d'ensemble

Sakila est une base de données exemple qui simule un système de location de films. Elle a été créée par MySQL pour démontrer les fonctionnalités d'une base de données relationnelle complexe.

## Structure de la Base de Données

### Tables Principales

#### 1. Film (`film`)

-   **Objectif** : Stocke les informations sur les films
-   **Champs principaux** :
    -   `film_id` : Identifiant unique du film
    -   `title` : Titre du film
    -   `description` : Synopsis du film
    -   `release_year` : Année de sortie
    -   `language_id` : Langue originale
    -   `rental_duration` : Durée de location par défaut
    -   `rental_rate` : Prix de location
    -   `length` : Durée du film
    -   `replacement_cost` : Coût de remplacement
    -   `rating` : Classification (G, PG, PG-13, R, NC-17)
    -   `special_features` : Fonctionnalités spéciales

#### 2. Client (`customer`)

-   **Objectif** : Informations sur les clients
-   **Champs principaux** :
    -   `customer_id` : Identifiant unique
    -   `first_name`, `last_name` : Nom du client
    -   `email` : Adresse email
    -   `address_id` : Lien vers l'adresse
    -   `store_id` : Magasin préféré
    -   `active` : Statut du compte
    -   `create_date` : Date de création du compte

#### 3. Location (`rental`)

-   **Objectif** : Gestion des locations
-   **Champs principaux** :
    -   `rental_id` : Identifiant unique
    -   `rental_date` : Date de location
    -   `inventory_id` : Film loué
    -   `customer_id` : Client
    -   `return_date` : Date de retour
    -   `staff_id` : Employé ayant géré la location

### Tables de Support

#### 4. Magasin (`store`)

-   **Objectif** : Informations sur les magasins
-   **Champs** :
    -   `store_id` : Identifiant unique
    -   `manager_staff_id` : Responsable du magasin
    -   `address_id` : Adresse du magasin

#### 5. Personnel (`staff`)

-   **Objectif** : Informations sur les employés
-   **Champs** :
    -   `staff_id` : Identifiant unique
    -   `first_name`, `last_name` : Nom de l'employé
    -   `address_id` : Adresse
    -   `email` : Email
    -   `store_id` : Magasin d'affectation
    -   `username` : Identifiant de connexion
    -   `password` : Mot de passe

#### 6. Inventaire (`inventory`)

-   **Objectif** : Stock des films par magasin
-   **Champs** :
    -   `inventory_id` : Identifiant unique
    -   `film_id` : Film
    -   `store_id` : Magasin

### Tables de Référence

#### 7. Acteur (`actor`)

-   `actor_id`, `first_name`, `last_name`
-   Lié aux films via `film_actor`

#### 8. Catégorie (`category`)

-   `category_id`, `name`
-   Lié aux films via `film_category`

#### 9. Langue (`language`)

-   `language_id`, `name`
-   Utilisé pour la langue des films

#### 10. Adresse (`address`)

-   Système d'adressage complet avec :
    -   `address`
    -   `district`
    -   `city_id` (lié à `city`)
    -   `postal_code`
    -   `phone`

### Vues

1. **`customer_list`**

    - Vue consolidée des informations clients
    - Inclut nom, adresse, ville et pays

2. **`film_list`**

    - Informations détaillées sur les films
    - Inclut catégorie et acteurs

3. **`staff_list`**

    - Informations sur le personnel
    - Inclut adresse complète

4. **`sales_by_store`**

    - Chiffre d'affaires par magasin
    - Inclut le nom du gérant

5. **`sales_by_film_category`**
    - Ventes totales par catégorie de film

## Fonctionnalités Clés

### 1. Gestion des Locations

-   Suivi des locations en cours
-   Historique des locations
-   Calcul des retards
-   Gestion des paiements

### 2. Gestion de l'Inventaire

-   Stock par magasin
-   Disponibilité des films
-   Suivi des copies de films

### 3. Gestion des Clients

-   Profils clients
-   Historique des locations
-   Statut d'activité

### 4. Reporting

-   Chiffre d'affaires par magasin
-   Performance par catégorie
-   Activité des clients

## Particularités Techniques

### Triggers

1. **Triggers de mise à jour automatique**
    - Chaque table principale a des triggers `AFTER INSERT` et `AFTER UPDATE`
    - Mise à jour automatique des timestamps `last_update`

### Contraintes

1. **Intégrité référentielle**

    - Clés étrangères avec `ON DELETE NO ACTION`
    - `ON UPDATE CASCADE` pour propager les mises à jour

2. **Contraintes de validation**
    - Ratings de films valides
    - Fonctionnalités spéciales prédéfinies

### Indexation

-   Index sur les clés étrangères
-   Index sur les noms (clients, acteurs)
-   Index composites pour les recherches fréquentes

## Cas d'Utilisation Typiques

1. **Recherche de Films**

```sql
SELECT f.title, c.name as category, f.rental_rate
FROM film f
JOIN film_category fc ON f.film_id = fc.film_id
JOIN category c ON fc.category_id = c.category_id
WHERE f.rating = 'PG' AND f.rental_rate < 3.00;
```

2. **Historique Client**

```sql
SELECT c.first_name, c.last_name, f.title, r.rental_date, r.return_date
FROM customer c
JOIN rental r ON c.customer_id = r.customer_id
JOIN inventory i ON r.inventory_id = i.inventory_id
JOIN film f ON i.film_id = f.film_id
WHERE c.customer_id = 1;
```

3. **Performance des Magasins**

```sql
SELECT s.store_id,
       COUNT(r.rental_id) as total_rentals,
       SUM(p.amount) as total_revenue
FROM store s
JOIN inventory i ON s.store_id = i.store_id
JOIN rental r ON i.inventory_id = r.inventory_id
JOIN payment p ON r.rental_id = p.rental_id
GROUP BY s.store_id;
```

## Bonnes Pratiques d'Utilisation

1. **Performance**

    - Utiliser les index existants
    - Éviter les jointures inutiles
    - Profiter des vues pour les requêtes complexes

2. **Intégrité des Données**

    - Respecter les contraintes de clés étrangères
    - Utiliser les transactions pour les opérations multiples
    - Vérifier les retours de films avant nouvelles locations

3. **Maintenance**
    - Archiver les anciennes locations
    - Mettre à jour les statuts clients
    - Surveiller les films populaires pour la gestion du stock
