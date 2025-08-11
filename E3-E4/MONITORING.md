## Monitoring de l’application d’IA — Rapport de certification (C20)

Ce document présente l’architecture et la mise en œuvre du monitorage de l’application d’intelligence artificielle développée dans le cadre du projet `E3-E4`. L’application est constituée d’une API FastAPI intégrant un modèle LLM (OpenAI), un moteur de recherche sémantique basé sur FAISS et une base de données PostgreSQL. Conformément à la compétence C20, l’objectif du dispositif de monitoring est de surveiller la disponibilité et les performances des composants, de détecter automatiquement les incidents et d’alimenter une boucle de rétroaction MLOps permettant l’amélioration continue du système, tout en respectant les principes de protection des données personnelles.

### Architecture de monitorage

L’architecture de surveillance repose sur la collecte de métriques instrumentées au sein de l’API et l’agrégation de métriques systèmes et bases de données, lesquelles sont centralisées puis visualisées. Concrètement, l’application FastAPI expose un endpoint `/metrics` conforme au format Prometheus. Un service Prometheus, déployé en environnement local via Docker Compose, interroge périodiquement cet endpoint ainsi que deux exporters standards: un exporter PostgreSQL pour les métriques de la base et un node exporter pour l’hôte. Les séries temporelles collectées sont consultées depuis un service Grafana, qui propose des tableaux de bord pré‑provisionnés et un moteur d’alerting. Cette architecture, simple et modulaire, garantit une séparation claire des responsabilités: l’application se concentre sur l’exposition de signaux pertinents, tandis que Prometheus et Grafana assurent respectivement la collecte, la conservation et l’exploitation des données de supervision.

La configuration de Prometheus précise des jobs de scraping pour l’application, l’exporter PostgreSQL et le node exporter, avec un intervalle adapté à la criticité de chaque source. L’extrait suivant illustre le paramétrage du job dédié à l’API FastAPI, qui interroge l’endpoint `/metrics` toutes les dix secondes.

```yaml
scrape_configs:
    - job_name: "fastapi-app"
      static_configs:
          - targets: ["web:8000"]
      metrics_path: "/metrics"
      scrape_interval: 10s
```

### Instrumentation applicative (FastAPI, OpenAI, FAISS)

L’instrumentation applicative est réalisée au plus près des parcours utilisateurs et des intégrations IA. Un middleware HTTP dans `app.py` mesure le volume de requêtes, la latence par point d’entrée et le nombre de requêtes en cours, et catégorise les erreurs en distinguant erreurs clientes et erreurs serveur. Cette approche permet d’obtenir une vision fiable de l’expérience perçue par les utilisateurs, notamment via le suivi de percentiles de latence. Au‑delà de la couche HTTP, l’application instrumente les appels au modèle OpenAI ainsi que les recherches FAISS. Les métriques exposées incluent le nombre de requêtes LLM par modèle et par endpoint, la durée d’exécution des appels, le volume de tokens envoyés et reçus, la durée des recherches FAISS et le nombre de résultats retournés. L’API expose également des compteurs décrivant l’activité conversationnelle (conversations par statut et messages par type) afin de relier l’activité fonctionnelle aux indicateurs techniques. L’endpoint d’exposition des métriques est minimaliste et s’appuie directement sur la bibliothèque `prometheus_client`.

```python
# E3-E4/fastapi/app.py
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

### Métriques à risque et seuils d’alerte

Le dispositif d’alerte s’appuie sur les règles de Grafana, provisionnées de manière déclarative. Trois scénarios d’incident majeurs sont couverts. D’abord, l’élévation anormale du taux d’erreurs HTTP est détectée par une règle calculant le taux d’occurrence des réponses dont le code est de la famille 4xx ou 5xx sur une fenêtre de cinq minutes; un dépassement du seuil fixé à dix pour cent maintenu pendant deux minutes déclenche une alerte de sévérité « warning ». Ensuite, la dégradation des performances est surveillée au travers du quantile 95 de la distribution des latences HTTP; lorsque le p95 excède deux secondes pendant deux minutes sur une fenêtre glissante de cinq minutes, une alerte « warning » est émise. Enfin, l’indisponibilité du service est traitée par une règle s’appuyant sur la métrique `up` issue de Prometheus: si le job `fastapi-app` est indisponible pendant une minute, une alerte de sévérité « critical » est générée. Ces seuils sont volontairement pragmatiques pour l’environnement local et peuvent être durcis en production en fonction des objectifs de service.

À titre d’illustration, l’expression PromQL utilisée pour détecter un temps de réponse excessif s’appuie sur la fonction `histogram_quantile` appliquée au taux des buckets d’histogramme de latence: `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2`. De manière similaire, le taux d’erreurs est évalué via `rate(http_requests_total{status=~"4..|5.."}[5m]) > 0.1`, tandis que la détection d’indisponibilité repose sur `up{job="fastapi-app"} == 0`. Les notifications sont émises vers un canal Discord par l’intermédiaire d’un « contact point » configuré à partir de la variable d’environnement `DISCORD_WEBHOOK_URL`.

```yaml
# E3-E4/monitoring/grafana/provisioning/alerting/contact-points.yaml
contactPoints:
    - name: discord-default
      receivers:
          - uid: discord-webhook
            type: discord
            settings:
                url: "${DISCORD_WEBHOOK_URL}"
                message: |
                    🚨 Alerte Grafana: {{ .CommonLabels.alertname }}\nStatut: {{ .Status }}
```

### Déploiement et exploitation locale

Le dispositif est entièrement opérable en environnement local au moyen de Docker Compose. Une fois les variables d’environnement renseignées (voir `.env_example`, notamment `DISCORD_WEBHOOK_URL`, `OPENAI_API_KEY` et `OPENAI_MODEL`), le lancement de la commande `docker-compose up -d` provisionne l’application, Prometheus, Grafana ainsi que les exporters PostgreSQL et Node. Prometheus conserve les séries temporelles avec une rétention adaptée à l’environnement de développement (environ deux cents heures) et expose sa console sur `http://localhost:9090`. Grafana est accessible sur `http://localhost:3000` avec des identifiants par défaut en local et charge automatiquement la source de données Prometheus ainsi que les tableaux de bord fournis, dont un tableau de bord dédié à FastAPI. L’application est accessible à l’adresse `http://localhost:8001`, tandis que le scraping des métriques s’effectue au sein du réseau Docker sur `web:8000/metrics`.

### Journalisation et conformité des données personnelles

La journalisation applicative utilise le module standard `logging` et se limite à des événements techniques contextualisés (succès ou échec d’appel OpenAI, durées d’exécution FAISS, statut des conversations), sans journaliser de contenu conversationnel ou de données identifiantes. Les métriques exposées par `prometheus_client` sont agrégées et utilisent des labels non identifiants (méthode, endpoint, statut HTTP, modèle), ce qui satisfait au principe de minimisation des données. Les secrets et informations sensibles sont fournis par variables d’environnement, et l’accès à l’endpoint `/metrics` est conçu pour rester interne au réseau dans une perspective de déploiement en production. Ces choix assurent un niveau de conformité cohérent avec les exigences de protection des données dans un contexte d’IA appliquée.

### Suivi et consultation des logs

En développement, les logs de l’application et des services sont consultés directement dans Docker Desktop (onglet « Logs » de chaque conteneur) ou en ligne de commande, selon préférence.

```bash
docker compose logs -f web
docker compose logs -f prometheus grafana
```

En production, les logs sont consultés via Portainer dans la vue « Logs » de chaque conteneur. La consultation en CLI reste possible si nécessaire.

```bash
docker logs -f <container_name>
```

Ce choix privilégie la simplicité: je connais des solutions de centralisation comme Grafana Loki avec Promtail (ou des stacks ELK/EFK), très utiles pour la recherche plein‑texte, la corrélation et la rétention avancée, mais elles seraient surdimensionnées pour cette application. Elles ajoutent des composants à exploiter (agents, stockage, politiques de rétention) sans bénéfice immédiat. Les métriques et alertes couvrent les signaux forts; l’inspection des logs conteneurisés via Docker Desktop et Portainer suffit aujourd’hui. Si la volumétrie, les exigences d’audit ou les SLO évoluent, une centralisation pourra être introduite ultérieurement sans modification du code applicatif.

### Procédures de test des alertes

La validité des règles d’alerte est vérifiée par des scénarios d’inductions contrôlées. L’indisponibilité du service est testée en arrêtant temporairement le conteneur `web`, ce qui entraîne, après une minute, l’émission d’une alerte critique « ServiceDown ». Le taux d’erreurs est éprouvé en forçant des réponses 5xx sur un endpoint de test pendant plus de deux minutes, permettant d’observer le déclenchement de l’alerte « HighErrorRate ». La surveillance de la latence est évaluée en introduisant, côté application, une temporisation volontaire portant la durée de traitement au‑delà de deux secondes, puis en soumettant la route concernée à une charge continue pendant environ cinq minutes; l’alerte « HighResponseTime » doit alors apparaître. Dans chaque cas, la réception des notifications sur Discord et l’évolution de l’état dans Grafana (ouverture, acquittement, résolution) sont contrôlées.

### Boucle de rétroaction MLOps

Les métriques et alertes alimentent une boucle de rétroaction qui structure l’amélioration continue du système. Les indicateurs de latence et d’erreur des appels OpenAI conduisent à revisiter les choix de modèles, les paramètres de timeout, la stratégie de retry et la conception des prompts. Les mesures de performance de FAISS, notamment les temps de recherche et le nombre de résultats pertinents retournés, éclairent l’optimisation de l’index, la valeur de `k` et la qualité du corpus indexé. Le suivi des volumes de tokens permet de maîtriser les coûts en adaptant la longueur du contexte et en rationalisant les prompts. Enfin, l’analyse du taux d’erreurs HTTP et des exceptions corrélées aboutit à des correctifs ciblés sur les endpoints et à l’introduction de mécanismes de repli et de backoff. Cette démarche est consignée et opérée de manière itérative pour renforcer conjointement robustesse, performance et efficience économique.

### Alignement avec la compétence C20

Le dispositif présenté répond aux attendus de la compétence C20. Les métriques clés liées aux risques (erreurs, latence, disponibilité, coûts via tokens) sont définies et assorties de seuils et d’alertes effectifs. Les choix technologiques — instrumentation `prometheus_client` dans l’API, collecte par Prometheus, visualisation et alerting par Grafana, exporters Postgres et Node — sont justifiés par leur maturité, leur faible empreinte et leur interopérabilité. L’ensemble des outils est installé et opérationnel en environnement local, et l’instrumentation nécessaire est intégrée au code source dans `app.py` et `monitoring_utils.py`. Les alertes, enfin, sont configurées et fonctionnelles avec un acheminement vers Discord; elles constituent le point de départ d’actions correctrices concrètes dans la boucle MLOps. Le respect de la protection des données personnelles est pris en compte par la minimisation des informations exposées, l’absence de journalisation de contenu sensible et l’usage de variables d’environnement pour les secrets.

### Annexes techniques

L’exemple suivant rappelle le principe d’exposition des métriques côté application, qui repose sur la génération du format Prometheus à partir du registre interne de `prometheus_client`.

```python
# E3-E4/fastapi/app.py
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

Le contact de notification Grafana est défini pour diffuser les alertes vers Discord à l’aide d’un webhook configurable par variable d’environnement.

```yaml
# E3-E4/monitoring/grafana/provisioning/alerting/contact-points.yaml
contactPoints:
    - name: discord-default
      receivers:
          - uid: discord-webhook
            type: discord
            settings:
                url: "${DISCORD_WEBHOOK_URL}"
                message: |
                    🚨 Alerte Grafana: {{ .CommonLabels.alertname }}\nStatut: {{ .Status }}
```

Pour la collecte, Prometheus interroge l’API à un intervalle de dix secondes, ce qui fournit une résolution suffisante pour l’observation fine des pics de latence et des incidents en environnement de développement.

```yaml
# E3-E4/monitoring/prometheus/prometheus.yml
scrape_configs:
    - job_name: "fastapi-app"
      static_configs:
          - targets: ["web:8000"]
      metrics_path: "/metrics"
      scrape_interval: 10s
```

### Fonctionnement de Prometheus

Prometheus adopte un modèle de collecte de type « pull » dans lequel le serveur Prometheus interroge périodiquement des cibles HTTP exposant des métriques au format texte. Chaque cible — l’application FastAPI, l’exporter PostgreSQL et le node exporter — publie un endpoint HTTP (`/metrics`) décrivant l’état de la cible sous forme de séries temporelles nommées, enrichies de labels. À chaque scrutation, Prometheus échantillonne la valeur courante de ces séries et les stocke dans sa base de données temporelle (TSDB) locale, en conservant pour chaque point un horodatage, une valeur et le jeu de labels associé. La TSDB organise les données par « chunks » sur disque avec un mécanisme de compaction, ce qui permet des requêtes temporelles efficaces et une rétention configurable adaptée aux contraintes de l’environnement.

Les types de métriques standard — Counter, Gauge, Histogram et Summary — répondent à des usages distincts. Les compteurs sont strictement croissants et mesurent des événements (par exemple `http_requests_total`). Les jauges représentent des grandeurs instantanées pouvant monter ou descendre (par exemple `http_requests_in_flight`). Les histogrammes accumulent des observations dans des « buckets » de seuils croissants et exposent automatiquement des séries `*_bucket`, `*_count` et `*_sum` permettant d’estimer des quantiles avec `histogram_quantile`. Les summaries calculent localement des quantiles, mais dans ce projet, les histogrammes ont été privilégiés pour permettre l’agrégation côté serveur. Dans notre configuration, l’intervalle de scrutation est de dix secondes pour l’application, ce qui offre une résolution suffisante pour suivre les pics de latence et de charge en phase de développement, tout en limitant la cardinalité et le volume de données.

Lors de l’exécution, Prometheus étiquette chaque série avec des labels clé/valeur (par exemple `method`, `endpoint`, `status` pour les métriques HTTP, `model` et `endpoint` pour les métriques OpenAI). Ces labels rendent possible des agrégations par dimension (somme ou moyenne par endpoint, quantiles par modèle, etc.). Le serveur expose ensuite une API de requêtage (PromQL) utilisée à la fois par l’interface Prometheus et par Grafana pour réaliser des graphiques, des statistiques et des règles d’alerte. Enfin, la métrique spéciale `up` permet de vérifier la disponibilité d’une cible: une valeur de `1` indique que le scrape a réussi, `0` signale une indisponibilité.

### Fonctionnement de Grafana

Grafana se connecte à Prometheus en tant que source de données et fournit une couche de visualisation, de tableaux de bord et d’alerting. Dans ce projet, la source de données Prometheus est provisionnée automatiquement au démarrage de Grafana. Les tableaux de bord sont décrits au format JSON et montés dans le conteneur, puis Grafana les charge selon la configuration de provisioning. Chaque panneau d’un tableau de bord contient une ou plusieurs requêtes PromQL et un rendu (courbe temporelle, statistique unique, jauge, etc.). Grafana permet d’appliquer des transformations simples (agrégations, changements d’unité, renommage), de configurer des seuils visuels et de définir des intervalles de rafraîchissement.

Le moteur d’alerting de Grafana évalue périodiquement des expressions PromQL associées à des conditions sur une durée. Lorsqu’une condition est satisfaite pendant la fenêtre d’évaluation, une alerte passe à l’état « firing ». Les notifications sont expédiées via des « contact points »; ici, un webhook Discord paramétré par la variable `DISCORD_WEBHOOK_URL` diffuse un message résumant l’alerte, sa gravité et un lien de contexte vers Grafana. Cette approche centralise la gestion des alertes au même endroit que les dashboards tout en se reposant sur Prometheus pour l’exécution des requêtes sous‑jacentes.

### Intégration et exploitation des métriques OpenAI

Les métriques OpenAI sont instrumentées directement dans l’API FastAPI. Des compteurs et histogrammes sont déclarés dans `app.py` avec les labels `model` et `endpoint`. Des décorateurs et context managers définis dans `monitoring_utils.py` enveloppent les appels au LLM et enregistrent pour chaque exécution le succès ou l’échec (`openai_requests_total` avec `status`), la durée d’exécution (`openai_request_duration_seconds` via la série `*_bucket`) ainsi que le volume de tokens utilisés (`openai_request_tokens` et `openai_response_tokens` lorsque l’information est disponible). L’application expose ces séries sur `/metrics` et Prometheus les scrute à intervalle régulier. Dans Grafana, les panneaux dédiés se contentent d’interroger Prometheus en PromQL.

Le taux de requêtes OpenAI s’obtient par la dérivée temporelle du compteur `openai_requests_total` avec la fonction `rate` sur une fenêtre de cinq minutes. La latence perçue est estimée par `histogram_quantile(0.95, rate(openai_request_duration_seconds_bucket[5m]))`, qui reconstruit le quantile 95 à partir des buckets d’histogramme. Il est ensuite possible de filtrer par modèle ou endpoint à l’aide des labels, ou de regrouper les séries pour calculer des agrégations par dimension. Si l’on souhaite suivre les coûts, il suffit d’ajouter un panneau interrogeant `increase(openai_request_tokens[5m])` et `increase(openai_response_tokens[5m])` pour mesurer la consommation de tokens sur la fenêtre.

### Explication des métriques des dashboards Grafana

Le tableau de bord « FastAPI Monitoring Dashboard » regroupe les principaux indicateurs de l’API et des intégrations IA. Le panneau « Request Rate » représente le débit de requêtes HTTP, calculé par `rate(http_requests_total[5m])` et ventilé par méthode et endpoint. Il permet d’identifier les périodes de charge et de vérifier la stabilité du trafic. Le panneau « Response Time » affiche le 95e percentile des temps de réponse à l’aide de `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))`. Une élévation persistante de ce quantile traduit une dégradation de l’expérience utilisateur, et constitue souvent un précurseur d’incident plus large. Le panneau « Error Rate » suit le taux d’erreurs HTTP (codes 4xx et 5xx) via `rate(http_requests_total{status=~"4..|5.."}[5m])`. Une montée des 5xx signale un problème serveur; les 4xx peuvent révéler un défaut de validation ou d’usage côté client.

Un panneau de type statistique, « Active Connections », agrège `http_requests_in_flight` pour fournir une mesure instantanée de la charge en cours de traitement. Deux panneaux d’infrastructure, « CPU Usage » et « Memory Usage », proviennent du node exporter. Le premier estime l’utilisation CPU par `100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)`, ce qui reflète la part non idle du CPU. Le second calcule le pourcentage de mémoire utilisée à partir des métriques `node_memory_MemTotal_bytes` et `node_memory_MemAvailable_bytes`. Ces deux panneaux permettent de corréler les anomalies applicatives avec la saturation éventuelle de la machine hôte.

Les intégrations IA disposent de trois panneaux dédiés. « OpenAI Requests Rate » retrace le débit d’appels LLM via `rate(openai_requests_total[5m])`, libellé par modèle, endpoint et statut; il met en évidence la charge adressée au fournisseur et la proportion d’erreurs. « OpenAI Response Time » présente le p95 des durées des appels au modèle grâce à `histogram_quantile(0.95, rate(openai_request_duration_seconds_bucket[5m]))`, indicateur clef pour l’UX et les timeouts. « FAISS Search Duration » restitue le p95 des durées de recherche via `histogram_quantile(0.95, rate(faiss_search_duration_seconds_bucket[5m]))`. Une hausse simultanée de ces latences oriente l’investigation vers la saturation I/O, la taille de contexte, ou la configuration de l’index FAISS. Deux panneaux de synthèse, « Chatbot Conversations » et « Chatbot Messages », exposent respectivement `chatbot_conversations_total` (par statut) et `chatbot_messages_total` (par type). Ils relient l’activité fonctionnelle à la santé technique du système.

Le tableau de bord « PostgreSQL Monitoring Dashboard » se focalise sur l’activité de la base. Le panneau « Active Connections » affiche `pg_stat_database_numbackends`, indicateur de connexions actives par base. Une croissance rapide peut signaler un pool mal dimensionné ou des fuites de connexions. « Database Size » s’appuie sur `pg_database_size_bytes` pour suivre l’évolution du volume occupé par les données, utile pour planifier la capacité et détecter une croissance inattendue. « Transactions per Second » combine `rate(pg_stat_database_xact_commit[5m])` et `rate(pg_stat_database_xact_rollback[5m])` pour fournir un débit global de transactions, reflet direct de l’activité applicative. Enfin, « Cache Hit Ratio » mesure l’efficacité du cache en calculant `rate(pg_stat_database_blks_hit[5m]) / (rate(pg_stat_database_blks_hit[5m]) + rate(pg_stat_database_blks_read[5m]))`. Un ratio élevé, proche de 1, indique que la plupart des lectures sont servies depuis le cache; une chute durable invite à revoir la taille des buffers ou les schémas d’accès.

Dans l’ensemble, ces dashboards offrent une vue cohérente de bout‑en‑bout: charge et qualité de service côté HTTP, performance et coût côté LLM, pertinence et latence côté FAISS, ainsi que l’état de l’infrastructure et de la base de données. Leur lecture conjointe permet de diagnostiquer efficacement les incidents, d’identifier les goulets d’étranglement et d’alimenter la boucle d’amélioration continue MLOps en données objectives.
