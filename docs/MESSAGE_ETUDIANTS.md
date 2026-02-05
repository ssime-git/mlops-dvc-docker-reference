# Message aux Étudiants - Phase 2: Architecture DVC + Docker

Bonjour à tous,

Pour la Phase 2, vous allez décomposer votre pipeline ML en microservices containerisés, orchestrés par DVC.

## 📦 Repository de Référence

J'ai créé un exemple complet qui montre le pattern à suivre:

**[mlops-dvc-docker-reference](lien-vers-repo)**

⚠️ **Important:** Ce n'est PAS du code à copier-coller. C'est une **implémentation de référence** pour comprendre l'architecture.

## 🎯 Ce que vous devez comprendre

### 1. Architecture Générale

```
DVC Orchestrator (conteneur)
    ↓ via Docker socket
Microservices: [Ingest] → [Preprocess] → [Train] → [Evaluate]
```

**Questions clés:**
- Pourquoi DVC tourne dans un conteneur ?
- Comment un conteneur peut-il lancer d'autres conteneurs ?
- Qu'est-ce que `/var/run/docker.sock` et pourquoi le monter ?

### 2. Pattern Docker Socket

Le conteneur DVC doit pouvoir spawner vos microservices (autres conteneurs).

**À rechercher:**
- Docker socket sharing vs Docker-in-Docker
- Sibling containers pattern
- Sécurité et implications

📖 Voir `docs/DOCKER_SOCKET.md` dans le repo de référence.

### 3. DVC + DagsHub Integration

**Ce que DagsHub vous offre:**
- **DVC Remote**: Storage S3-compatible (100GB gratuit)
- **MLflow Server**: Tracking des expériences
- **Model Registry**: Versioning des modèles

**À comprendre:**
- Comment configurer le remote DVC avec DagsHub
- Pourquoi ne PAS sauvegarder les modèles localement
- Integration MLflow → Model Registry automatique

📖 Voir `docs/DAGSHUB_SETUP.md` dans le repo de référence.

## 🔍 Concepts à Maîtriser

1. **DVC Pipeline**
   - Définition des stages dans `dvc.yaml`
   - Dependencies (`deps`), outputs (`outs`), metrics
   - Comment DVC détecte les changements

2. **Containerisation par Stage**
   - Un Dockerfile par microservice
   - Partage de volumes entre conteneurs
   - Variables d'environnement pour configuration

3. **Orchestration**
   - DVC comme orchestrateur simple (Phase 2)
   - Préparation pour Airflow (Phase 3)

## 📋 Livrables Phase 2

Pour votre projet, vous devez créer:

1. **Architecture Microservices**
   - [ ] Un conteneur par stage (minimum 3 stages)
   - [ ] `dvc.yaml` définissant le pipeline
   - [ ] Volumes partagés pour data/models

2. **DagsHub Integration**
   - [ ] DVC remote configuré
   - [ ] MLflow tracking actif
   - [ ] Modèles dans le registry (pas en local!)

3. **Orchestration Containerisée**
   - [ ] DVC runner en conteneur
   - [ ] Docker socket correctement monté
   - [ ] `docker-compose.yml` pour dev local

4. **Documentation**
   - [ ] README expliquant l'architecture
   - [ ] Instructions de setup
   - [ ] Choix techniques justifiés

## 💡 Conseils

**Ne PAS faire:**
- ❌ Copier-coller sans comprendre
- ❌ Mélanger code host et code container
- ❌ Sauvegarder les modèles en local avec DVC

**À faire:**
- ✅ Comprendre le pattern Docker socket
- ✅ Tester chaque stage individuellement
- ✅ Vérifier l'intégration DagsHub
- ✅ Documenter vos choix

## 🚀 Pour Démarrer

1. **Clonez le repo de référence** et étudiez la structure
2. **Lisez les docs** (`DOCKER_SOCKET.md`, `DAGSHUB_SETUP.md`)
3. **Testez localement** le pipeline de référence
4. **Adaptez à votre projet** (pas de copier-coller!)

## ❓ Questions de Recherche

Avant de commencer, assurez-vous de pouvoir répondre à:

1. Quelle est la différence entre Docker-in-Docker et socket sharing?
2. Comment DVC sait-il quand re-exécuter un stage?
3. Pourquoi utiliser le Model Registry plutôt que DVC pour les modèles?
4. Comment les conteneurs siblings partagent-ils des données?
5. Quel est l'avantage de containeriser DVC lui-même?

## 📅 Timeline

- **30 janv - 2 fév**: Setup architecture + DagsHub
- **3-4 fév**: Microservices + tests individuels
- **5-6 fév**: Orchestration complète + validation

## 🆘 Support

Si vous bloquez:
1. **D'abord**: Recherchez le concept (Docker socket, DVC pipeline, etc.)
2. **Ensuite**: Consultez le repo de référence
3. **En dernier**: Posez des questions spécifiques (pas "ça marche pas")

**Bon courage!** La Phase 2 est challenging mais elle vous prépare parfaitement pour Airflow en Phase 3.

L'objectif n'est pas juste de faire fonctionner un pipeline, mais de **comprendre l'architecture** qui vous servira en production.

— Sébastien
