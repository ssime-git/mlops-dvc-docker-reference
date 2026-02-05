# MLOps Pipeline - Command Cheatsheet

Quick reference for daily workflows.

## 🚀 Getting Started

```bash
# Clone and setup
git clone https://github.com/ssime-git/mlops-dvc-docker-reference.git
cd mlops-dvc-docker-reference
make setup-env  # Create .env file
# Edit .env with your DagsHub credentials

# Build images
make build
```

## 📋 Daily Workflow

### Run Pipeline
```bash
make run              # Run complete pipeline
make run-train        # Run only training stage
make status           # Check what needs to run
```

### View Results
```bash
make dag              # Show pipeline structure
cat metrics/metrics.json           # View metrics
cat models/model_metadata.json     # View model info
```

### Push to DagsHub
```bash
make push             # Push data to DagsHub storage
```

### Commit Code
```bash
make git-sync         # Add, commit, push to GitHub
# Or manually:
git add .
git commit -m "Your message"
git push origin main
```

## 🔍 Inspection

### Check Status
```bash
make status           # Pipeline status
make dag              # Pipeline DAG
docker images | grep mlops  # List Docker images
```

### View Logs
```bash
# Check data files
ls -R data/
ls -R models/
ls -R metrics/

# View DVC state
cat dvc.lock

# View pipeline definition
cat dvc.yaml
```

## 🛠️ Development

### Modify Pipeline

**1. Change hyperparameters:**
```bash
vim params.yaml       # Edit train.n_estimators, train.max_depth, etc.
make run              # DVC will rerun train + evaluate
make push
```

**2. Modify stage code:**
```bash
vim stages/train/train.py
make run              # DVC reruns affected stages
make push
make git-sync         # Commit changes
```

**3. Add dependencies to stage:**
```bash
vim stages/train/requirements.txt
make build            # Rebuild images
make run
```

### Test Individual Stages
```bash
make run-ingest       # Test data download
make run-preprocess   # Test preprocessing
make run-train        # Test training
make run-evaluate     # Test evaluation
```

## 🧹 Cleanup

```bash
make clean            # Remove generated files (keeps images)
make clean-all        # Remove files + Docker images
```

## 📊 DVC Commands (via Docker)

```bash
# Status
docker-compose run --rm dvc-runner dvc status
docker-compose run --rm dvc-runner dvc dag

# Push/Pull
docker-compose run --rm dvc-runner dvc push
docker-compose run --rm dvc-runner dvc pull

# Force rerun
docker-compose run --rm dvc-runner dvc repro --force

# Run specific stage
docker-compose run --rm dvc-runner dvc repro train
```

## 🐳 Docker Commands

```bash
# Build
docker-compose build                    # Build all images
docker-compose build dvc-runner         # Build specific image

# Run
docker-compose run --rm dvc-runner bash # Interactive shell
docker-compose run --rm dvc-runner dvc repro

# Images
docker images | grep mlops              # List images
docker-compose down --rmi all           # Remove all images

# Logs
docker-compose logs dvc-runner
```

## 📂 File Structure Quick Reference

```
.env                    # Credentials (DO NOT COMMIT)
params.yaml             # Hyperparameters (commit this)
dvc.yaml                # Pipeline definition (commit this)
dvc.lock                # Pipeline state (commit this)
.dvc/config             # DVC remote URL (commit this)
.dvc/config.local       # DVC credentials (DO NOT COMMIT)

data/raw/               # Raw data (gitignored, DVC tracked)
data/processed/         # Processed data (gitignored, DVC tracked)
models/                 # Model metadata (gitignored, DVC tracked)
metrics/                # Metrics (gitignored)
```

## 🔗 Important URLs

```bash
# Your repositories
GitHub:   https://github.com/ssime-git/mlops-dvc-docker-reference
DagsHub:  https://dagshub.com/ssime-git/mlops-dvc-docker-reference
MLflow:   https://dagshub.com/ssime-git/mlops-dvc-docker-reference.mlflow
```

## ⚙️ Configuration

### Update Paths in dvc.yaml
If you clone to a different directory:
```bash
# Find and replace in dvc.yaml
/home/seb/project/mlops-dvc-docker-reference
# with
/your/actual/path
```

### Update .env
```bash
DAGSHUB_USER_NAME=your-username
DAGSHUB_TOKEN=your-token-here
MLFLOW_TRACKING_URI=https://dagshub.com/your-username/your-repo.mlflow
MLFLOW_TRACKING_USERNAME=your-username
MLFLOW_TRACKING_PASSWORD=your-token-here
```

### Update params.yaml (MLflow section)
```yaml
mlflow:
  tracking_uri: ${MLFLOW_TRACKING_URI}
  tracking_username: ${MLFLOW_TRACKING_USERNAME}
  tracking_password: ${MLFLOW_TRACKING_PASSWORD}
```

## 🐛 Common Issues

### "output does not exist"
```bash
# Check paths in dvc.yaml match your directory
pwd
# Update all paths in dvc.yaml to match
```

### MLflow authentication fails
```bash
# Verify .env exists and has credentials
cat .env
# Check params.yaml has mlflow section
cat params.yaml | grep -A 3 "mlflow:"
```

### DVC push fails
```bash
# Check credentials
cat .dvc/config.local
# Test connection
docker-compose run --rm dvc-runner dvc remote list
```

### Docker permission denied
```bash
sudo usermod -aG docker $USER
# Logout and login again
```

## 💡 Tips & Tricks

### Quick test without full pipeline
```bash
# Test just the train stage
docker-compose run --rm train python train.py
```

### View MLflow experiments locally
```bash
# MLflow UI (if you had local tracking)
# But we use DagsHub, so check:
# https://dagshub.com/your-username/your-repo
```

### Compare experiments
1. Go to DagsHub → Experiments tab
2. Select multiple runs
3. Compare metrics side-by-side

### Stage model to Production
1. Go to DagsHub → Models → iris-classifier
2. Click on version
3. Change stage from "None" to "Production"

### Pull someone else's data
```bash
git clone <repo>
make setup-env
# Edit .env with your credentials
make pull             # Download data from DagsHub
make run              # Run pipeline
```

## 📝 Experiment Tracking Workflow

```bash
# 1. Modify hyperparameters
vim params.yaml
# Change n_estimators: 100 → 200

# 2. Run pipeline
make run
# New MLflow run created automatically

# 3. Push data
make push

# 4. View on DagsHub
# Go to Experiments tab
# Compare metrics with previous runs

# 5. If better, commit
make git-sync
```

## 🎓 Learning Path

1. **Understand the DAG**: `make dag`
2. **Run pipeline**: `make run`
3. **Modify params**: Change values in `params.yaml`
4. **Compare experiments**: View in DagsHub
5. **Add new stage**: Copy existing stage, modify
6. **Translate to Airflow**: Next phase!

---

**Quick Help**: `make help` shows all Makefile commands
