# Rapport de Certification - Système de Gestion des Données de Production Industrielle

## Table des matières
1. Introduction
2. Contexte et Problématique
3. Architecture Technique
4. Implémentation
5. Résultats et Bénéfices
6. Conclusion

## 1. Introduction

Ce rapport présente le développement et l'implémentation d'un système de gestion des données de production pour une entreprise industrielle spécialisée dans la menuiserie. Le projet vise à moderniser la collecte et l'analyse des données de production en centralisant les informations provenant de différents centres d'usinage.

## 2. Contexte et Problématique

### 2.1 Situation Initiale
L'entreprise dispose de trois types de centres d'usinage :
- Centres PVC (DEM12)
- Centres ALU (DEMALU)
- Centres HYBRIDES (SU12)

Ces machines génèrent quotidiennement des fichiers LOG stockés sur un serveur FTP, contenant des informations cruciales sur leur fonctionnement.

### 2.2 Problématiques Identifiées
- Données dispersées entre un serveur FTP et une base MySQL
- Absence de traitement automatisé des fichiers LOG
- Difficulté d'accès aux données historiques
- Manque de visibilité sur les performances machines

### 2.3 Objectifs du Projet
1. Centraliser les données dans une base PostgreSQL
2. Automatiser la collecte et le traitement des logs
3. Développer une API REST pour l'accès aux données
4. Permettre une analyse en temps réel des performances

## 3. Architecture Technique

### 3.1 Vue d'Ensemble
Le système s'articule autour de trois composants principaux :
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   SERVEUR FTP   │    │     PARSER      │    │   POSTGRESQL    │
│                 │    │                 │    │                 │
│ Reçoit les      │───▶│ Traite les      │───▶│ Stocke les      │
│ fichiers LOG    │    │ logs et calcule │    │ résultats       │
│ des machines    │    │ les métriques   │    │ d'analyse       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 3.2 Technologies Utilisées
- **Docker et Docker Compose** : Conteneurisation des services
- **Python** : Développement du parser et de l'API
- **FastAPI** : Framework API REST
- **PostgreSQL** : Base de données centrale
- **SQLAlchemy** : ORM pour la gestion des données
- **Cron** : Automatisation des tâches

### 3.3 Structure des Données
Le système gère six tables principales :
1. `centre_usinage` : Informations sur les machines
2. `session_production` : Sessions de production
3. `job_profil` : Profils des jobs
4. `periode_attente` : Périodes d'attente
5. `periode_arret` : Périodes d'arrêt
6. `piece_production` : Pièces produites

## 4. Implémentation

### 4.1 Service de Synchronisation FTP
- Exécution automatique toutes les 15 minutes
- Exploration récursive des dossiers par type de centre
- Traitement des fichiers LOG au format standardisé
- Gestion des variables d'environnement sécurisée

### 4.2 Parser de Logs
Le parser analyse quatre types d'événements principaux :
- `StukUitgevoerd` : Production de pièces
- `MachineWait` : Périodes d'attente
- `MachineStop/Start` : Cycles d'arrêt/démarrage
- `JobProfiel` : Caractéristiques des jobs

### 4.3 API REST
L'API expose les fonctionnalités suivantes :
- Gestion CRUD des centres d'usinage
- Consultation des sessions de production
- Accès aux données détaillées (jobs, attentes, arrêts)
- Statistiques de production

### 4.4 Sécurité et Robustesse
- Isolation des services via Docker
- Gestion sécurisée des credentials
- Journalisation des opérations
- Gestion des erreurs et reprises

## 5. Résultats et Bénéfices

### 5.1 Métriques Calculées
Le système fournit automatiquement :
- Temps de production effectif
- Taux d'occupation des machines
- Temps d'attente et d'arrêt
- Productivité par type de centre

### 5.2 Bénéfices Opérationnels
1. **Automatisation**
   - Synchronisation automatique des données
   - Calcul automatisé des KPIs
   - Réduction des tâches manuelles

2. **Centralisation**
   - Données consolidées dans PostgreSQL
   - API REST unique pour l'accès aux données
   - Vue unifiée des performances

3. **Analyse**
   - Statistiques en temps réel
   - Historique complet des productions
   - Identification des points d'amélioration

## 6. Conclusion

Le projet a permis de mettre en place une solution robuste et évolutive pour la gestion des données de production. Les objectifs initiaux ont été atteints avec :
- Une automatisation complète de la collecte des données
- Une centralisation réussie dans PostgreSQL
- Une API REST performante et bien documentée
- Des outils d'analyse pertinents

Le système est actuellement en production et démontre sa fiabilité au quotidien. Les perspectives d'évolution incluent :
- L'ajout de nouveaux types d'analyses
- L'intégration avec d'autres systèmes
- L'extension à d'autres types de machines

Cette réalisation constitue une base solide pour l'amélioration continue des processus de production de l'entreprise. 