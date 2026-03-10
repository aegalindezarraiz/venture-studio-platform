# SRE Guide

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
