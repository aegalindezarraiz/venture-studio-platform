# Database Schema

## users
Usuarios autenticables.

## organizations
Tenants principales de la plataforma.

## memberships
Relación usuario-organización con rol.

## startups
Registro de iniciativas y compañías incubadas.

## agents
Catálogo de agentes configurados por organización.

## prompts
Biblioteca de prompts por organización.

## workflows
Ejecuciones en cola y su resultado.

## memory_entries
Memoria durable textual, con proyección vectorial en Qdrant.

La migración fuente es `apps/backend/alembic/versions/0001_init.py`.
