"""Helper: writes all infra/deploy files for the enterprise architecture."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..")

def w(path, content):
    full = os.path.join(BASE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print(f"  wrote {path}")


# ── Terraform Railway ─────────────────────────────────────────────────────────
w("deploy/terraform/railway/main.tf", '''terraform {
  required_version = ">= 1.6"
  required_providers {
    railway = {
      source  = "terraform-community-providers/railway"
      version = "~> 0.3"
    }
  }
}

provider "railway" {
  token = var.railway_token
}

resource "railway_project" "venture_studio" {
  name        = "venture-studio-os"
  description = "AI Venture Studio OS - Enterprise Platform"
}

locals {
  services = {
    "api-gateway"         = { port = 8000 }
    "backend"             = { port = 8020 }
    "agent-orchestrator"  = { port = 8001 }
    "market-intel"        = { port = 8002 }
    "opportunity-engine"  = { port = 8003 }
    "product-factory"     = { port = 8004 }
    "startup-generator"   = { port = 8005 }
    "investment-pipeline" = { port = 8006 }
    "growth-engine"       = { port = 8007 }
    "founder-copilot"     = { port = 8008 }
    "auth-service"        = { port = 8010 }
    "org-service"         = { port = 8011 }
    "billing-service"     = { port = 8012 }
  }
}

resource "railway_service" "apps" {
  for_each   = local.services
  project_id = railway_project.venture_studio.id
  name       = each.key
}

output "project_id" {
  value = railway_project.venture_studio.id
}
''')

w("deploy/terraform/railway/variables.tf", '''variable "railway_token" {
  description = "Railway API token"
  type        = string
  sensitive   = true
}

variable "github_repo" {
  description = "GitHub repository owner/repo"
  type        = string
  default     = "aegalindezarraiz/venture-studio-platform"
}

variable "anthropic_api_key" {
  type      = string
  sensitive = true
}

variable "notion_token" {
  type      = string
  sensitive = true
}

variable "secret_key" {
  type      = string
  sensitive = true
}
''')

# ── K8s manifests ─────────────────────────────────────────────────────────────
w("deploy/k8s/base/namespace.yaml", """apiVersion: v1
kind: Namespace
metadata:
  name: venture-studio
  labels:
    app.kubernetes.io/managed-by: helm
""")

w("deploy/k8s/base/configmap.yaml", """apiVersion: v1
kind: ConfigMap
metadata:
  name: venture-studio-config
  namespace: venture-studio
data:
  ENVIRONMENT: production
  LOG_LEVEL: INFO
  BACKEND_URL: http://backend:8020
  AUTH_SERVICE_URL: http://auth-service:8010
  AGENT_ORCHESTRATOR_URL: http://agent-orchestrator:8001
  MARKET_INTEL_URL: http://market-intel:8002
  OPPORTUNITY_ENGINE_URL: http://opportunity-engine:8003
  PRODUCT_FACTORY_URL: http://product-factory:8004
  STARTUP_GENERATOR_URL: http://startup-generator:8005
  INVESTMENT_PIPELINE_URL: http://investment-pipeline:8006
  GROWTH_ENGINE_URL: http://growth-engine:8007
  FOUNDER_COPILOT_URL: http://founder-copilot:8008
""")

w("deploy/k8s/base/ingress.yaml", """apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: venture-studio-ingress
  namespace: venture-studio
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: 1m
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - api.venture-studio.ai
      secretName: venture-studio-tls
  rules:
    - host: api.venture-studio.ai
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: api-gateway
                port:
                  number: 8000
""")

w("deploy/k8s/base/secrets.example.yaml", """# NEVER commit actual values.
# Apply with:
#   kubectl create secret generic venture-studio-secrets \\
#     --from-literal=ANTHROPIC_API_KEY=sk-ant-... \\
#     --from-literal=NOTION_TOKEN=secret_... \\
#     --from-literal=SECRET_KEY=$(openssl rand -hex 32) \\
#     -n venture-studio
apiVersion: v1
kind: Secret
metadata:
  name: venture-studio-secrets
  namespace: venture-studio
type: Opaque
data:
  ANTHROPIC_API_KEY: CHANGE_ME_BASE64
  NOTION_TOKEN: CHANGE_ME_BASE64
  SECRET_KEY: CHANGE_ME_BASE64
  STRIPE_SECRET_KEY: CHANGE_ME_BASE64
  DATABASE_URL: CHANGE_ME_BASE64
  REDIS_URL: CHANGE_ME_BASE64
""")

# One K8s deployment template per main service
SERVICES = [
    ("api-gateway",         8000, 2),
    ("backend",             8020, 2),
    ("agent-orchestrator",  8001, 3),
    ("auth-service",        8010, 2),
    ("market-intel",        8002, 1),
    ("opportunity-engine",  8003, 1),
    ("product-factory",     8004, 1),
    ("startup-generator",   8005, 1),
    ("investment-pipeline", 8006, 1),
    ("growth-engine",       8007, 1),
    ("founder-copilot",     8008, 2),
    ("org-service",         8011, 1),
    ("billing-service",     8012, 1),
]

for name, port, replicas in SERVICES:
    safe = name.replace("-", "_")
    w(f"deploy/k8s/base/{name}.yaml", f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {name}
  namespace: venture-studio
  labels:
    app: {name}
spec:
  replicas: {replicas}
  selector:
    matchLabels:
      app: {name}
  template:
    metadata:
      labels:
        app: {name}
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "{port}"
    spec:
      containers:
        - name: {name}
          image: ghcr.io/aegalindezarraiz/{name}:latest
          ports:
            - containerPort: {port}
          envFrom:
            - configMapRef:
                name: venture-studio-config
            - secretRef:
                name: venture-studio-secrets
          env:
            - name: PORT
              value: "{port}"
          resources:
            requests:
              cpu: 100m
              memory: 256Mi
            limits:
              cpu: 1000m
              memory: 1Gi
          livenessProbe:
            httpGet:
              path: /health
              port: {port}
            initialDelaySeconds: 15
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: /health
              port: {port}
            initialDelaySeconds: 5
            periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: {name}
  namespace: venture-studio
spec:
  selector:
    app: {name}
  ports:
    - port: {port}
      targetPort: {port}
  type: ClusterIP
""")

# ── Helm deployment template ───────────────────────────────────────────────────
w("deploy/helm/venture-studio/templates/deployment.yaml", """{{- range $name, $svc := .Values.services }}
{{- if $svc.enabled }}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ $name }}
  namespace: {{ $.Release.Namespace }}
  labels:
    app: {{ $name }}
    chart: {{ $.Chart.Name }}-{{ $.Chart.Version }}
    release: {{ $.Release.Name }}
spec:
  replicas: {{ $svc.replicaCount | default 1 }}
  selector:
    matchLabels:
      app: {{ $name }}
  template:
    metadata:
      labels:
        app: {{ $name }}
    spec:
      containers:
        - name: {{ $name }}
          image: "{{ $.Values.global.imageRegistry }}/{{ $svc.image }}:{{ $.Values.global.imageTag }}"
          imagePullPolicy: {{ $.Values.global.imagePullPolicy }}
          ports:
            - containerPort: {{ $svc.port }}
          envFrom:
            - configMapRef:
                name: venture-studio-config
            - secretRef:
                name: venture-studio-secrets
          env:
            - name: PORT
              value: "{{ $svc.port }}"
          resources:
            {{- toYaml ($svc.resources | default dict) | nindent 12 }}
          livenessProbe:
            httpGet:
              path: /health
              port: {{ $svc.port }}
            initialDelaySeconds: 15
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: /health
              port: {{ $svc.port }}
            initialDelaySeconds: 5
            periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: {{ $name }}
  namespace: {{ $.Release.Namespace }}
spec:
  selector:
    app: {{ $name }}
  ports:
    - port: {{ $svc.port }}
      targetPort: {{ $svc.port }}
  type: ClusterIP
---
{{- end }}
{{- end }}
""")

# ── Agents structure ──────────────────────────────────────────────────────────
for cat in ["executive", "product", "engineering", "growth", "data", "security", "osint"]:
    w(f"agents/{cat}-agents/__init__.py", f'"""Agentes de categoría {cat} del AI Venture Studio OS."""\n')
    w(f"agents/{cat}-agents/README.md", f"# {cat.title()} Agents\n\nAgentes especializados de la categoria `{cat}`.\nVer definiciones completas en `packages/agents/definitions.py`.\n")

# ── Docs structure ─────────────────────────────────────────────────────────────
w("docs/architecture/README.md", """# Architecture

## System Overview

```
                    Internet
                       |
                  [API Gateway :8000]
                       |
        ┌──────────────┼───────────────┐
        |              |               |
  [Auth :8010]   [Backend :8020]  [Orchestrator :8001]
                       |
        ┌──────────────┼───────────────────────────────┐
        |              |               |               |
  [Market :8002] [Product :8004] [Startup :8005] [Growth :8007]
        |              |               |               |
  [Opportunity]  [Investment]   [Copilot :8008] [Org :8011]
   [:8003]        [:8006]

Infrastructure: PostgreSQL | Redis | Qdrant | NATS | Prometheus | Grafana
```

## Service Ports

| Service              | Port  | Description                          |
|---------------------|-------|--------------------------------------|
| api-gateway          | 8000  | Single entry point, routing          |
| agent-orchestrator   | 8001  | Coordinates agent execution          |
| market-intel         | 8002  | Market analysis & competitive intel  |
| opportunity-engine   | 8003  | Opportunity discovery & validation   |
| product-factory      | 8004  | PRDs, roadmaps, user stories         |
| startup-generator    | 8005  | Full startup concept generation      |
| investment-pipeline  | 8006  | Due diligence & portfolio analysis   |
| growth-engine        | 8007  | Growth strategy & content            |
| founder-copilot      | 8008  | Personal AI for founders             |
| auth-service         | 8010  | JWT authentication                   |
| org-service          | 8011  | Organizations & teams                |
| billing-service      | 8012  | Subscriptions & payments             |
| backend              | 8020  | Core APIs, Notion sync, agents       |

## Data Flow

1. Client → API Gateway (auth check)
2. API Gateway → appropriate microservice
3. Microservice → Claude API (LLM)
4. Microservice → Notion (sync state)
5. Microservice → Redis (cache/queue)
6. Microservice → Qdrant (memory search)
""")

w("docs/devops/README.md", """# DevOps Guide

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
helm upgrade --install venture-studio deploy/helm/venture-studio/ \\
  --namespace venture-studio \\
  --create-namespace \\
  --set secrets.anthropicApiKey=sk-ant-... \\
  --set secrets.notionToken=secret_...
```

### Terraform (Railway)
```bash
cd deploy/terraform/railway
terraform init
terraform plan -var="railway_token=..."
terraform apply
```
""")

w("docs/sre/README.md", """# SRE Guide

## Health Endpoints

Every service exposes `GET /health` returning:
```json
{"status": "ok", "service": "service-name"}
```

## Platform Status

```bash
# Full status
curl http://localhost:8000/status

# Summary
curl http://localhost:8000/status/summary

# Specific service
curl http://localhost:8002/health
```

## SLOs

| Service            | Availability | Latency p99 |
|-------------------|--------------|-------------|
| api-gateway        | 99.9%        | < 200ms     |
| agent-orchestrator | 99.5%        | < 5s        |
| founder-copilot    | 99.5%        | < 10s       |
| market-intel       | 99.0%        | < 15s       |

## Alerting Rules

- Service down for > 1 minute → PagerDuty
- Error rate > 5% for > 5 minutes → Slack #alerts
- LLM latency p99 > 30s → Slack #alerts
- Notion API failures > 10 in 5 minutes → Slack #alerts

## Runbooks

- [Service restart](runbooks/service-restart.md)
- [Database recovery](runbooks/db-recovery.md)
- [LLM fallback](runbooks/llm-fallback.md)
""")

w("docs/api/README.md", """# API Reference

## Base URL

- Local: `http://localhost:8000`
- Production: `https://api.venture-studio.ai`

## Authentication

All endpoints (except /health) require JWT:
```
Authorization: Bearer <token>
```

Get token: `POST /auth/token`

## Interactive Docs

Each service exposes Swagger UI at `/docs`:
- API Gateway: http://localhost:8000/docs
- Backend: http://localhost:8020/docs
- Market Intel: http://localhost:8002/docs
- All others follow same pattern

## Key Endpoints

### Intelligence
```
POST /intel/analyze              Market analysis
POST /intel/competitor-signal    Competitor signal analysis
GET  /intel/trends/{sector}     Sector trends
```

### Opportunities
```
POST /opportunities/discover    Find business opportunities
POST /opportunities/validate    Validation plan
```

### Products
```
POST /products/prd              Generate PRD
POST /products/roadmap          Generate roadmap
POST /products/user-stories     Generate user stories
```

### Startups
```
POST /startups/generate         Full startup concept
POST /startups/pitch-deck       Pitch deck content
POST /startups/name-generator   Name ideas
```

### Investments
```
POST /investments/due-diligence Due diligence report
POST /investments/portfolio-analysis Portfolio health
```

### Growth
```
POST /growth/strategy           Growth strategy
POST /growth/content-strategy   Content plan
POST /growth/experiment         A/B test design
```

### Copilot
```
POST /copilot/chat              Direct conversation
POST /copilot/decision-framework Decision analysis
POST /copilot/weekly-planning   Weekly plan
```

### Agents Monitor
```
GET  /agents                    List 500 agents
GET  /agents/summary            Stats by category
GET  /agents/{id}               Agent details
POST /monitor/seed              Populate Notion Monitor
GET  /monitor/overview          Monitor status
```
""")

print("All infra/docs/agents files written!")
