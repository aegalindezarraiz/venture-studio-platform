"""Definición de entornos y sus valores por defecto."""
import os
from enum import Enum


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


ENVIRONMENT = Environment(os.environ.get("ENVIRONMENT", "development"))

IS_DEV = ENVIRONMENT == Environment.DEVELOPMENT
IS_PROD = ENVIRONMENT == Environment.PRODUCTION
