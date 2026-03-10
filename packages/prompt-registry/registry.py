"""Centralized prompt registry with versioning and org overrides."""
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class PromptTemplate:
    id: str
    name: str
    template: str
    category: str
    version: int = 1
    variables: list[str] = field(default_factory=list)

    def render(self, **kwargs) -> str:
        result = self.template
        for k, v in kwargs.items():
            result = result.replace(f"{{{k}}}", str(v))
        return result

_registry: dict[str, PromptTemplate] = {}

def register_prompt(p: PromptTemplate) -> None:
    _registry[p.id] = p

def get_prompt(prompt_id: str, org_id: Optional[str] = None) -> Optional[PromptTemplate]:
    if org_id and f"{org_id}:{prompt_id}" in _registry:
        return _registry[f"{org_id}:{prompt_id}"]
    return _registry.get(prompt_id)

class PromptRegistry:
    def __init__(self, org_id: Optional[str] = None):
        self.org_id = org_id

    def get(self, prompt_id: str, **kwargs) -> str:
        p = get_prompt(prompt_id, self.org_id)
        if not p:
            raise KeyError(f"Prompt '{prompt_id}' not found")
        return p.render(**kwargs) if kwargs else p.template

    def register(self, p: PromptTemplate) -> None:
        register_prompt(p)

    def list(self, category: Optional[str] = None) -> list[PromptTemplate]:
        items = list(_registry.values())
        return [i for i in items if i.category == category] if category else items

# Pre-load system prompts
for _p in [
    PromptTemplate("market_analysis", "Market Analysis", "Analyze {sector} market for {target_market}. TAM/SAM/SOM, trends, opportunities. JSON.", "intel", variables=["sector", "target_market"]),
    PromptTemplate("startup_brief", "Startup Brief", "Executive brief for {startup_name} in {sector}. Problem: {problem}. Solution: {solution}. Markdown.", "product", variables=["startup_name", "sector", "problem", "solution"]),
    PromptTemplate("okr_generator", "OKR Generator", "Generate OKRs for Q{quarter} {year} for {startup_name}. Focus: {focus_area}. 3 objectives x 3 KRs. JSON.", "executive", variables=["quarter", "year", "startup_name", "focus_area"]),
    PromptTemplate("due_diligence", "Due Diligence", "Due diligence for {startup_name} ({sector}, {stage}). Investment: ${investment_usd}. {description}. INVEST/PASS/NEGOTIATE. JSON.", "investment", variables=["startup_name", "sector", "stage", "investment_usd", "description"]),
]:
    register_prompt(_p)
