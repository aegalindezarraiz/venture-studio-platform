# Architecture

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
