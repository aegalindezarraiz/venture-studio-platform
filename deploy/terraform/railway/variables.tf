variable "railway_token" {
  description = "Railway API token"
  type        = string
  sensitive   = true
}

variable "github_repo" {
  description = "GitHub repository owner/repo"
  type        = string
  default     = "aegalindezarraiz/venture-studio-platform"
}

variable "anthropic_api_key" {
  type      = string
  sensitive = true
}

variable "notion_token" {
  type      = string
  sensitive = true
}

variable "secret_key" {
  type      = string
  sensitive = true
}
