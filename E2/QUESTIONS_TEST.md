# Questions de Test pour la Base de Données Sakila

Ce document liste différentes questions que vous pouvez utiliser pour tester la base de données Sakila et le système de génération de requêtes SQL.

## 🎬 Questions sur les Films

### Inventaire et Disponibilité

1. "Quels sont les films actuellement disponibles ?"
2. "Liste des films qui n'ont jamais été loués"
3. "Combien de copies avons-nous pour chaque film ?"
4. "Quels films sont actuellement en location ?"

### Performance et Statistiques

1. "Quels sont les films d'action les plus loués ?"
2. "Quel est le film qui rapporte le plus d'argent ?"
3. "Combien y a-t-il de films par catégorie ?"
4. "Quels sont les films les plus populaires du mois dernier ?"
5. "Top 10 des films les plus rentables"

### Caractéristiques des Films

1. "Quels sont les films disponibles en version originale anglaise ?"
2. "Liste des films par classification (rating)"
3. "Films avec des fonctionnalités spéciales (behind the scenes)"
4. "Durée moyenne des films par catégorie"
5. "Films sortis cette année"

## 👥 Questions sur les Clients

### Analyse Comportementale

1. "Qui sont les 10 meilleurs clients en termes de montant dépensé ?"
2. "Quels clients n'ont pas rendu leurs films à temps ?"
3. "Fréquence de location moyenne par client"
4. "Quel est le profil type de nos clients les plus fidèles ?"
5. "Clients qui n'ont pas fait de location depuis 3 mois"

### Géographie et Distribution

1. "Liste des clients par ville"
2. "Combien de clients actifs avons-nous par magasin ?"
3. "Distribution géographique de notre clientèle"
4. "Villes avec le plus de clients actifs"
5. "Pays représentant le plus gros de notre clientèle"

## 📅 Questions sur les Locations

### Analyse Temporelle

1. "Quelle est la durée moyenne de location ?"
2. "Quels sont les jours où nous avons le plus de locations ?"
3. "Combien de locations avons-nous par mois ?"
4. "Périodes de l'année les plus actives"
5. "Évolution des locations sur les 6 derniers mois"

### Performance et Qualité

1. "Quel est le taux de retour en retard ?"
2. "Pourcentage de films rendus à temps"
3. "Durée moyenne des retards"
4. "Impact des retards sur le chiffre d'affaires"
5. "Films les plus souvent rendus en retard"

## 💰 Questions Business

### Analyse Financière

1. "Quel est le chiffre d'affaires par magasin ?"
2. "Quelle catégorie de film est la plus rentable ?"
3. "Revenu moyen par location"
4. "Évolution du chiffre d'affaires mensuel"
5. "Comparaison des revenus entre magasins"

### Performance des Employés

1. "Qui sont nos meilleurs vendeurs ?"
2. "Nombre de locations par employé"
3. "Chiffre d'affaires par employé"
4. "Taux de fidélisation client par vendeur"
5. "Performance des managers de magasin"

### Gestion des Stocks

1. "Quel est le taux d'occupation de notre inventaire ?"
2. "Films nécessitant plus de copies"
3. "Rotation du stock par catégorie"
4. "Impact du nombre de copies sur les revenus"
5. "Optimisation suggérée du stock"

## 🔄 Questions Complexes

### Analyses Croisées

1. "Y a-t-il une corrélation entre le prix de location et la fréquence des locations ?"
2. "Quel est le profil des films qui ne sont jamais en retard ?"
3. "Impact de la durée du film sur sa popularité"
4. "Relation entre la catégorie du film et le profil client"
5. "Influence de la saison sur les préférences de location"

### Analyses Avancées

1. "Prédiction des films à fort potentiel de location"
2. "Suggestions d'achat basées sur les tendances"
3. "Optimisation des prix par période"
4. "Segmentation client avancée"
5. "Analyse des patterns de location"

### Requêtes Spécifiques

1. "Quels acteurs apparaissent le plus souvent ensemble ?"
2. "Films populaires nécessitant plus de copies"
3. "Clients susceptibles de devenir inactifs"
4. "Catégories sous-exploitées par magasin"
5. "Opportunités d'expansion géographique"

## 🔍 Comment Utiliser ces Questions

Pour tester une question :

```python
question = "Votre question ici"
sql = vn.generate_sql(question)
result = vn.run_sql(sql)
print(result)
```

## 📊 Exemples de Résultats Attendus

Pour la question "Top 10 des films les plus loués" :

```sql
SELECT f.title, COUNT(r.rental_id) as rental_count
FROM film f
JOIN inventory i ON f.film_id = i.film_id
JOIN rental r ON i.inventory_id = r.inventory_id
GROUP BY f.film_id, f.title
ORDER BY rental_count DESC
LIMIT 10;
```

## 🚀 Conseils d'Utilisation

1. Commencez par des questions simples
2. Testez différentes formulations
3. Vérifiez la cohérence des résultats
4. Explorez les relations entre les tables
5. Combinez plusieurs aspects dans vos questions
