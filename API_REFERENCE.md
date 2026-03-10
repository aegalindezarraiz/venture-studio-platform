# API Reference

## Auth
- `POST /auth/register`
- `POST /auth/login`

## Organizations
- `GET /organizations/`
- `POST /organizations/`

## Startups
- `GET /startups/?organization_id=<uuid>`
- `POST /startups/`

## Agents
- `GET /agents/?organization_id=<uuid>`
- `POST /agents/`

## Prompts
- `GET /prompts/?organization_id=<uuid>`
- `POST /prompts/`

## Workflows
- `GET /workflows/?organization_id=<uuid>`
- `POST /workflows/`

## Memory
- `GET /memory/?organization_id=<uuid>`
- `POST /memory/`

## Health and Metrics
- `GET /health`
- `GET /metrics`
