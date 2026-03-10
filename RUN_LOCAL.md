# Run Local

```bash
cp .env.example .env
docker compose up --build
```

## URLs
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- OpenAPI: http://localhost:8000/docs
- Metrics: http://localhost:8000/metrics
- Qdrant: http://localhost:6333/dashboard

## Smoke Test
```bash
bash scripts/smoke_test.sh
```
