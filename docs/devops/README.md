# DevOps Guide

## Local Development

```bash
# Start everything
make up

# Start specific service
make up s=api-gateway

# View logs
make logs s=backend

# Open shell
make shell s=backend

# Run migrations
make db-migrate
```

## Deployment

### Railway (recommended for MVP)
1. Connect GitHub repo to Railway
2. Set environment variables (see .env.example)
3. Each service auto-deploys on push to main

### Kubernetes
```bash
# Apply base manifests
kubectl apply -f deploy/k8s/base/

# Or use Helm
helm upgrade --install venture-studio deploy/helm/venture-studio/ \
  --namespace venture-studio \
  --create-namespace \
  --set secrets.anthropicApiKey=sk-ant-... \
  --set secrets.notionToken=secret_...
```

### Terraform (Railway)
```bash
cd deploy/terraform/railway
terraform init
terraform plan -var="railway_token=..."
terraform apply
```
