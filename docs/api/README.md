# API Reference

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
