terraform {
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
