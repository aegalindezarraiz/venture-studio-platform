-- Extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Base de datos ya creada por POSTGRES_DB en docker-compose.
-- Este script inicializa extensiones y configuración inicial.

-- Collation para búsqueda en español
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_collation WHERE collname = 'es_ES') THEN
    CREATE COLLATION es_ES (LOCALE = 'es_ES.UTF-8');
  END IF;
EXCEPTION WHEN OTHERS THEN
  NULL; -- Ignorar si el locale no está disponible
END;
$$;
