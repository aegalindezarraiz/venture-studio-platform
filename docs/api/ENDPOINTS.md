# Referencia de API — AI Venture Studio OS

La documentación interactiva completa está en http://localhost:8000/docs (Swagger UI).

## Autenticación

Todas las rutas protegidas requieren header:
```
Authorization: Bearer <token>
```

### Obtener token
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password"
}
```
→ Responde `{ "access_token": "...", "token_type": "bearer" }`

---

## Organizaciones

| Método | Ruta                      | Descripción                    |
|--------|---------------------------|--------------------------------|
| GET    | /organizations            | Listar organizaciones          |
| POST   | /organizations            | Crear organización             |
| GET    | /organizations/{id}       | Detalle                        |
| PUT    | /organizations/{id}       | Actualizar                     |
| DELETE | /organizations/{id}       | Eliminar                       |

## Startups

| Método | Ruta              | Descripción          |
|--------|-------------------|----------------------|
| GET    | /startups         | Listar               |
| POST   | /startups         | Crear                |
| GET    | /startups/{id}    | Detalle              |
| PUT    | /startups/{id}    | Actualizar           |
| DELETE | /startups/{id}    | Eliminar             |

## Agentes

| Método | Ruta             | Descripción          |
|--------|------------------|----------------------|
| GET    | /agents          | Listar               |
| POST   | /agents          | Crear                |
| GET    | /agents/{id}     | Detalle              |
| PUT    | /agents/{id}     | Actualizar           |

## Workflows

| Método | Ruta                   | Descripción              |
|--------|------------------------|--------------------------|
| GET    | /workflows             | Listar                   |
| POST   | /workflows             | Crear y encolar          |
| GET    | /workflows/{id}        | Estado actual            |
| DELETE | /workflows/{id}        | Cancelar                 |

## Memoria vectorial

| Método | Ruta              | Descripción                        |
|--------|-------------------|------------------------------------|
| GET    | /memory           | Buscar por texto (vector search)   |
| POST   | /memory           | Indexar nueva entrada              |
| DELETE | /memory/{id}      | Eliminar entrada                   |

## Health

```http
GET /health
→ { "status": "ok", "version": "0.1.0", "db": "ok", "redis": "ok" }
```
