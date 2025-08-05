# Service IA – Projet E2

## I. Présentation du service IA

-   **Nom du service** : MyVanna (bibliothèque [Vanna](https://github.com/vanna-ai/vanna) + API OpenAI)
-   **Version** : 0.7.9 pour la bibliothèque `vanna[openai]`
-   **Modèle** : `gpt-4o-mini`, fourni par OpenAI et configuré via `OpenAI_Chat`
-   **Objectif** : générer automatiquement des requêtes SQL à partir de questions en langage naturel et interroger la base de données _Sakila_.

## II. Installation et accessibilité

1. **Clonage et environnement**

    ```bash
    git clone <URL_DU_DEPOT>
    cd Certif_DevIA/E2
    python -m venv .venv
    source .venv/bin/activate  # Windows : .venv\Scripts\activate
    pip install vanna[openai]
    ```

2. **Clé d’API OpenAI**
   Définissez la variable d’environnement OPENAI_API_KEY :

    ```bash
    export OPENAI_API_KEY="votre_cle_api"  # Windows : set OPENAI_API_KEY=...
    ```

3. **Lancement du service**

    Ouvrez et exécutez le notebook `sakila.ipynb` jusqu’à la cellule finale qui démarre l’application Flask :

    ```python
    VannaFlaskApp(
        vn=vn,
        auth=SimplePassword(users=[{"email": "admin@example.com", "password": "password"}]),
        allow_llm_to_see_data=True,
        title="E2 - Sakila",
        subtitle="Interrogez la base de données Sakila",
        show_training_data=True,
        sql=True,
        table=True,
        chart=False,
        summarization=True,
        ask_results_correct=True,
    ).run()
    ```

    L’interface est accessible sur http://localhost:5000.

4. **Tests d’accessibilité**

    - Vérifier que le port 5000 est ouvert.
    - Exemple : `curl http://localhost:5000` (retourne la page d’accueil du service).

5. **Gestion des accès**
    - Authentification SimplePassword (identifiants par défaut : admin@example.com / password).
    - Possibilité d’étendre la gestion des utilisateurs dans la configuration de VannaFlaskApp.

## III. Configuration fonctionnelle et technique

-   **Paramètres clés**

    -   `OPENAI_API_KEY` : clé d’API OpenAI.
    -   `model` : gpt-4o-mini.
    -   Base de données : `sqlite-sakila.db` connectée via `vn.connect_to_sqlite('sqlite-sakila.db')`.

-   **Conformité fonctionnelle**

    -   Répond aux besoins de génération de SQL, restitution de tableaux et résumés.
    -   Ressources nécessaires : connexion internet (accès API), CPU modeste, ~512 Mo RAM.

-   **Interconnexions**
    -   Données : `sqlite-sakila.db`.
    -   Documentation : `SAKILA_DOCUMENTATION.md`.
    -   Jeux de questions/tests : `QUESTIONS_TEST.md`.

## IV. Monitoring et supervision

-   **Logs** : le serveur Flask émet des logs sur la sortie standard ; redirigez-les vers un fichier ou un système de collecte (ex. journalctl, ELK).
-   **Tableaux de bord** : pour un suivi avancé, l’API peut être instrumentée via Prometheus ou **Langfuse**.
-   **Alertes** : à mettre en place en fonction de vos outils de supervision (ex. seuil d’erreur HTTP, temps de réponse).

### Monitoring avec Langfuse

Le projet intègre la solution [Langfuse](https://langfuse.com/) pour le monitoring des requêtes LLM et le suivi des performances du service IA. Langfuse permet de :

-   Visualiser les requêtes envoyées à l’API OpenAI (inputs/outputs, temps de réponse, erreurs, etc.)
-   Suivre l’utilisation du modèle, les métriques de coût, et l’historique des interactions
-   Auditer la qualité des réponses générées et détecter d’éventuels problèmes

**Mise en œuvre dans le notebook `sakila.ipynb` :**

-   Les variables d’environnement `LANGFUSE_SECRET_KEY` et `LANGFUSE_PUBLIC_KEY` doivent être définies (voir début du notebook).
-   L’intégration se fait via l’import `from langfuse.openai import openai` et la configuration des clés dans le code Python.
-   Lors de l’exécution du service Flask (cellule finale du notebook), toutes les requêtes et réponses sont automatiquement tracées et consultables sur le dashboard Langfuse (exemple : https://cloud.langfuse.com).

Pour activer le monitoring :

1. Créez un compte sur Langfuse et récupérez vos clés API.
2. Ajoutez-les dans un fichier `.env` ou dans vos variables d’environnement :
    ```bash
    export LANGFUSE_SECRET_KEY="votre_cle"
    export LANGFUSE_PUBLIC_KEY="votre_cle_publique"
    ```
3. Redémarrez le notebook pour que la prise en compte soit effective.

---

## V. Documentation et accessibilité

-   **Documentation utilisateur** :
    -   README actuel décrivant la classe MyCustomVectorDB.
    -   Notebook d’exemple : `sakila.ipynb` (démonstration complète).
-   **Données manipulées** : requêtes SQL sur la base Sakila (films, acteurs, clients, locations).
-   **Accessibilité** :
    -   Le présent fichier est en Markdown, exportable en HTML ou PDF accessible (via pandoc ou outils équivalents).
    -   Structuration en sections, titres et listes pour une lecture facilitée.
    -   Respect des bonnes pratiques WCAG : textes contrastés, absence de code couleur exclusive, langue explicitée.

## VI. Entraînement du modèle (fine-tuning)

L’entraînement du modèle (association questions/réponses SQL) est réalisé directement dans le notebook `sakila.ipynb` :

-   **Extraction du schéma** : le code extrait automatiquement tous les DDL (tables, vues, triggers) de la base `sqlite-sakila.db` et les ajoute à la base de connaissances du modèle via `vn.train(ddl=...)`.
-   **Ajout de paires question/SQL** : une liste de questions en français et leurs requêtes SQL correspondantes sont ajoutées à l’aide de `vn.train(question=..., sql=...)`.
-   **Visualisation** : il est possible de visualiser l’ensemble des données d’entraînement via `vn.get_training_data()` (voir exemple dans le notebook).

**À retenir :**

-   L’entraînement n’est pas un fine-tuning du modèle OpenAI, mais un enrichissement de la base de connaissances locale utilisée pour la génération de SQL.
-   Vous pouvez ajouter vos propres exemples pour améliorer la pertinence des réponses.

---

## Exemples d’usage

```python
from vanna.openai import OpenAI_Chat
from my_module import MyVanna  # défini dans sakila.ipynb

vn = MyVanna(config={'api_key': 'VOTRE_CLE', 'model': 'gpt-4o-mini'})
vn.connect_to_sqlite('sqlite-sakila.db')
print(vn.ask("Combien de films durent plus de 2h ?"))
```

## Références

-   Définition de MyVanna et configuration du modèle OpenAI
-   Connexion à la base SQLite
-   Paramétrage du serveur Flask et de l’authentification
