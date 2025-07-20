# Documentation MyCustomVectorDB

Cette classe hérite de `VannaBase` et implémente une base de données vectorielle simple pour stocker et gérer les données SQL.

## Constructeur

```python
def __init__(self, config=None):
    super().__init__(config)
    self.ddl_list = []
    self.documentation_list = []
    self.question_sql_list = []
```

-   Initialise la classe avec trois listes vides
-   `ddl_list` : stocke les instructions DDL (CREATE TABLE, etc.)
-   `documentation_list` : stocke la documentation
-   `question_sql_list` : stocke les paires question/SQL

## Méthodes d'ajout de données

### `add_ddl`

```python
def add_ddl(self, ddl: str, **kwargs) -> str:
    self.ddl_list.append(ddl)
    return ddl
```

-   **Objectif** : Ajoute une instruction DDL à la liste
-   **Usage** : Enregistre la structure de la base de données (tables, index, etc.)
-   **Retour** : L'instruction DDL ajoutée

### `add_documentation`

```python
def add_documentation(self, doc: str, **kwargs) -> str:
    self.documentation_list.append(doc)
    return doc
```

-   **Objectif** : Ajoute de la documentation
-   **Usage** : Enrichit le contexte pour les futures requêtes
-   **Retour** : La documentation ajoutée

### `add_question_sql`

```python
def add_question_sql(self, question: str, sql: str, **kwargs) -> str:
    self.question_sql_list.append((question, sql))
    return sql
```

-   **Objectif** : Enregistre une paire question/SQL
-   **Usage** : Apprentissage - associe une question en langage naturel à sa requête SQL
-   **Retour** : La requête SQL ajoutée

## Méthodes de récupération

### `get_related_ddl`

```python
def get_related_ddl(self, question: str, **kwargs) -> list:
    return self.ddl_list
```

-   **Objectif** : Retourne les DDL pertinents pour une question
-   **Note** : Implémentation basique - retourne tous les DDL
-   **Retour** : Liste de tous les DDL

### `get_related_documentation`

```python
def get_related_documentation(self, question: str, **kwargs) -> list:
    return self.documentation_list
```

-   **Objectif** : Retourne la documentation pertinente
-   **Note** : Implémentation basique - retourne toute la documentation
-   **Retour** : Liste de toute la documentation

### `get_similar_question_sql`

```python
def get_similar_question_sql(self, question: str, **kwargs) -> list:
    return self.question_sql_list
```

-   **Objectif** : Retourne les questions/SQL similaires
-   **Note** : Implémentation basique - retourne toutes les paires
-   **Retour** : Liste de toutes les paires question/SQL

## Méthodes de gestion des données

### `get_training_data`

```python
def get_training_data(self, **kwargs) -> pd.DataFrame:
    max_len = max(len(self.ddl_list), len(self.documentation_list), len(self.question_sql_list))
    ddl_extended = self.ddl_list + [None] * (max_len - len(self.ddl_list))
    doc_extended = self.documentation_list + [None] * (max_len - len(self.documentation_list))
    qs_extended = self.question_sql_list + [None] * (max_len - len(self.question_sql_list))

    data = {
        'ddl': ddl_extended,
        'documentation': doc_extended,
        'question_sql': qs_extended
    }
    return pd.DataFrame(data)
```

-   **Objectif** : Crée un DataFrame avec toutes les données d'entraînement
-   **Note** : Égalise la longueur des listes avec `None`
-   **Retour** : DataFrame pandas avec toutes les données

### `remove_training_data`

```python
def remove_training_data(self, id: str, **kwargs) -> bool:
    return True
```

-   **Objectif** : Devrait supprimer des données d'entraînement
-   **Note** : Implémentation factice - ne fait rien
-   **Retour** : Toujours True

### `generate_embedding`

```python
def generate_embedding(self, text: str, **kwargs) -> list:
    return [0] * 10
```

-   **Objectif** : Génère un vecteur d'embedding pour un texte
-   **Note** : Implémentation factice - retourne un vecteur de 10 zéros
-   **Retour** : Liste de 10 zéros

## Limitations

Cette implémentation est basique et présente plusieurs limitations :

1. Pas de vraie recherche sémantique (retourne toutes les données)
2. Pas de persistance (données en mémoire uniquement)
3. Pas de vrais embeddings (vecteurs de zéros)
4. Pas de gestion de la suppression des données

Pour une utilisation en production, il est recommandé d'utiliser `VannaDB_VectorStore` qui fournit une implémentation complète et optimisée de toutes ces fonctionnalités.
