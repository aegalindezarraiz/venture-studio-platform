"""
definitions.py — Catálogo completo de los 500 agentes del AI Venture Studio OS.

Estructura por categoría:
  EXECUTIVE   (50)  · CEO, CFO, COO, CMO, CTO, Legal, M&A, HR…
  PRODUCT     (80)  · PM, UX, Design, Roadmap, Analytics…
  ENGINEERING (100) · Frontend, Backend, DevOps, QA, ML, DB…
  GROWTH      (80)  · SEO, Content, Paid, Email, Social, CRO…
  DATA        (70)  · Analytics, ETL, BI, ML, Reporting…
  SECURITY    (60)  · AppSec, SIEM, Compliance, IAM, Pentest…
  OSINT       (60)  · Competitive, Social, Web, Dark Web, Brand…
"""

from dataclasses import dataclass, field
from typing import Literal

AgentCategory = Literal[
    "executive", "product", "engineering",
    "growth", "data", "security", "osint"
]

DEFAULT_MODELS = {
    "executive":   "claude-opus-4-6",
    "product":     "claude-sonnet-4-6",
    "engineering": "claude-sonnet-4-6",
    "growth":      "claude-sonnet-4-6",
    "data":        "claude-sonnet-4-6",
    "security":    "claude-opus-4-6",
    "osint":       "claude-sonnet-4-6",
}


@dataclass
class AgentDef:
    id: str                   # slug único: "exec-ceo-001"
    name: str                 # nombre legible
    category: AgentCategory
    role: str                 # rol corto
    description: str          # qué hace
    capabilities: list[str]   # lista de capacidades
    model: str                # modelo LLM asignado
    system_prompt: str        # prompt base del sistema
    tools: list[str] = field(default_factory=list)   # herramientas disponibles
    priority: int = 2         # 1=crítico 2=normal 3=soporte


# ─────────────────────────────────────────────────────────────────────────────
# Utilidad para generar agentes en bloque
# ─────────────────────────────────────────────────────────────────────────────

def _make(category: AgentCategory, idx: int, role: str, description: str,
          capabilities: list[str], tools: list[str] = None,
          priority: int = 2, extra_prompt: str = "") -> AgentDef:
    cat_prefix = category[:4].upper()
    slug = f"{cat_prefix.lower()}-{role.lower().replace(' ', '-')[:20]}-{idx:03d}"
    model = DEFAULT_MODELS[category]
    system_prompt = (
        f"Eres el {role} del AI Venture Studio. "
        f"Tu misión: {description}. "
        "Responde siempre en español, con precisión técnica y orientado a resultados. "
        "Cuando detectes un problema, propón una solución concreta. "
        + extra_prompt
    )
    return AgentDef(
        id=slug, name=f"{role} Agent", category=category,
        role=role, description=description, capabilities=capabilities,
        model=model, system_prompt=system_prompt,
        tools=tools or [], priority=priority,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 1. EXECUTIVE AGENTS  (50)
# ─────────────────────────────────────────────────────────────────────────────

EXECUTIVE_AGENTS: list[AgentDef] = [
    _make("executive", 1,  "CEO Estratégico",           "Visión, dirección y toma de decisiones de alto nivel",                                ["strategic_planning","okr_alignment","stakeholder_management"], ["notion","slack"], 1),
    _make("executive", 2,  "CFO Financiero",            "Planificación financiera, fundraising y control de costos",                           ["financial_modeling","burn_rate","runway_analysis"],            ["notion","sheets"], 1),
    _make("executive", 3,  "COO Operaciones",           "Eficiencia operativa, procesos y escalabilidad",                                      ["process_optimization","kpi_tracking","resource_allocation"],  ["notion","jira"],  1),
    _make("executive", 4,  "CMO Marketing",             "Estrategia de marketing, branding y go-to-market",                                    ["brand_strategy","gtm","budget_allocation"],                   ["notion","hubspot"],1),
    _make("executive", 5,  "CTO Tecnología",            "Arquitectura tecnológica, roadmap técnico y equipo de ingeniería",                     ["tech_strategy","architecture_review","team_scaling"],          ["github","notion"], 1),
    _make("executive", 6,  "CPO Producto",              "Visión de producto, priorización y experiencia de usuario",                           ["product_vision","prioritization","user_research"],             ["notion","figma"],  1),
    _make("executive", 7,  "CHRO Talento",              "Cultura, contratación y desarrollo del equipo",                                       ["hiring","culture","performance_management"],                   ["notion"],          2),
    _make("executive", 8,  "CLO Legal",                 "Compliance, contratos y protección de IP",                                            ["contract_review","ip_protection","regulatory_compliance"],     ["notion"],          2),
    _make("executive", 9,  "CSO Seguridad Corp",        "Seguridad corporativa, riesgos y continuidad del negocio",                            ["risk_assessment","business_continuity","crisis_management"],   ["notion"],          2),
    _make("executive", 10, "Board Relations",           "Comunicación con el board e inversores",                                              ["investor_relations","board_reporting","cap_table"],            ["notion","sheets"], 2),
    _make("executive", 11, "M&A Strategy",              "Identificación y análisis de adquisiciones estratégicas",                             ["deal_sourcing","valuation","due_diligence"],                   ["notion"],          2),
    _make("executive", 12, "Investor Relations",        "Gestión de inversores actuales y prospección de nuevos",                              ["deck_preparation","investor_updates","term_sheets"],           ["notion"],          2),
    _make("executive", 13, "Strategy Planner",          "Planificación estratégica trimestral y anual",                                        ["scenario_planning","competitive_analysis","roadmapping"],      ["notion"],          2),
    _make("executive", 14, "OKR Manager",               "Definición, seguimiento y alineación de OKRs en toda la organización",                ["okr_setting","progress_tracking","cross_team_alignment"],      ["notion"],          2),
    _make("executive", 15, "Crisis Manager",            "Detección temprana y gestión de crisis organizacionales",                             ["crisis_detection","communication","damage_control"],           ["notion","slack"], 1),
    _make("executive", 16, "Culture Architect",         "Diseño y mantenimiento de la cultura organizacional",                                 ["culture_design","values_alignment","ritual_creation"],         ["notion"],          3),
    _make("executive", 17, "Fundraising Advisor",       "Estrategia y ejecución de rondas de financiamiento",                                  ["pitch_coaching","investor_targeting","data_room"],             ["notion"],          1),
    _make("executive", 18, "Revenue Operations",        "Alineación entre ventas, marketing y éxito del cliente",                              ["pipeline_management","forecasting","revenue_alignment"],       ["hubspot","notion"],2),
    _make("executive", 19, "Partnership Director",      "Identificación y gestión de alianzas estratégicas",                                   ["partner_identification","negotiation","alliance_management"],  ["notion"],          2),
    _make("executive", 20, "Competitive Intelligence",  "Monitoreo de competidores y análisis del mercado",                                    ["competitor_tracking","market_analysis","positioning"],         ["notion"],          2),
    # 21-50: agentes ejecutivos de soporte y especialización
    *[_make("executive", i, f"Exec Specialist {i}", f"Especialización ejecutiva en área {i}", ["executive_support","decision_making","reporting"], ["notion"], 3) for i in range(21, 51)],
]

# ─────────────────────────────────────────────────────────────────────────────
# 2. PRODUCT AGENTS  (80)
# ─────────────────────────────────────────────────────────────────────────────

PRODUCT_AGENTS: list[AgentDef] = [
    _make("product", 1,  "Product Manager Core",       "Gestión del ciclo de vida del producto y priorización del backlog",                    ["backlog_management","sprint_planning","stakeholder_alignment"],["jira","notion"],   1),
    _make("product", 2,  "UX Researcher",              "Investigación de usuarios, entrevistas y síntesis de insights",                        ["user_interviews","usability_testing","persona_creation"],      ["figma","notion"],  1),
    _make("product", 3,  "UI Designer",                "Diseño de interfaces y sistemas de diseño",                                            ["ui_design","design_system","prototyping"],                     ["figma"],           1),
    _make("product", 4,  "Product Analytics",          "Análisis de métricas de producto y funnel",                                            ["funnel_analysis","retention","cohort_analysis"],               ["mixpanel","sheets"],1),
    _make("product", 5,  "Feature Prioritizer",        "Scoring y priorización de features usando frameworks (RICE, ICE)",                     ["rice_scoring","roadmap","stakeholder_negotiation"],            ["notion","jira"],   2),
    _make("product", 6,  "Roadmap Planner",            "Construcción y mantenimiento del roadmap de producto",                                 ["roadmap_creation","dependency_mapping","quarterly_planning"],  ["notion"],          1),
    _make("product", 7,  "Customer Journey Mapper",    "Mapeo de la experiencia del cliente end-to-end",                                       ["journey_mapping","touchpoint_analysis","pain_point_id"],       ["figma","notion"],  2),
    _make("product", 8,  "A/B Test Designer",          "Diseño y análisis de experimentos de producto",                                        ["hypothesis_design","statistical_analysis","experiment_mgmt"],  ["notion"],          2),
    _make("product", 9,  "Onboarding Specialist",      "Optimización del flujo de onboarding y activación de usuarios",                        ["onboarding_flow","activation_rate","aha_moment"],              ["notion"],          2),
    _make("product", 10, "Retention Strategist",       "Estrategias de retención y reducción de churn",                                        ["churn_analysis","engagement","lifecycle_emails"],              ["notion","hubspot"],2),
    _make("product", 11, "Pricing Strategist",         "Estrategia de precios, modelos y experimentos de pricing",                             ["pricing_models","willingness_to_pay","packaging"],             ["notion","sheets"], 2),
    _make("product", 12, "Monetization Advisor",       "Identificación y optimización de flujos de monetización",                              ["revenue_streams","upsell","expansion_revenue"],                ["notion"],          2),
    _make("product", 13, "API Product Manager",        "Gestión de productos API y developer experience",                                      ["api_design","developer_docs","sdk_management"],               ["notion","github"], 2),
    _make("product", 14, "Mobile PM",                  "Gestión de producto para plataformas móviles iOS/Android",                             ["app_store_optimization","mobile_metrics","release_management"],["notion"],          2),
    _make("product", 15, "B2B Product Specialist",     "Producto para segmentos enterprise y B2B",                                             ["enterprise_features","integration","sla_management"],          ["notion"],          2),
    _make("product", 16, "Voice of Customer",          "Captura y síntesis de feedback de clientes",                                           ["nps_analysis","feedback_synthesis","customer_interviews"],     ["notion","hubspot"],2),
    _make("product", 17, "Competitive Product Analyst","Benchmarking de producto vs competidores",                                             ["feature_comparison","gap_analysis","positioning"],             ["notion"],          2),
    _make("product", 18, "PLG Strategist",             "Estrategia de Product-Led Growth",                                                    ["viral_loops","self_serve","product_qualified_leads"],          ["notion"],          2),
    _make("product", 19, "Accessibility Specialist",   "Accesibilidad e inclusión en el diseño de producto",                                   ["wcag_compliance","screen_reader","inclusive_design"],          ["figma","notion"],  3),
    _make("product", 20, "Localization PM",            "Gestión de localización e internacionalización del producto",                          ["i18n","l10n","market_adaptation"],                             ["notion"],          3),
    # 21-80: especialistas adicionales de producto
    *[_make("product", i, f"Product Specialist {i}", f"Especialización de producto en área {i}", ["product_management","feature_delivery","user_feedback"], ["notion","jira"], 3) for i in range(21, 81)],
]

# ─────────────────────────────────────────────────────────────────────────────
# 3. ENGINEERING AGENTS  (100)
# ─────────────────────────────────────────────────────────────────────────────

ENGINEERING_AGENTS: list[AgentDef] = [
    _make("engineering", 1,  "Frontend Architect",      "Arquitectura de frontend, frameworks y performance",                                   ["react","typescript","performance_optimization"],               ["github"],          1),
    _make("engineering", 2,  "Backend Architect",       "Diseño de APIs, microservicios y arquitecturas escalables",                           ["api_design","microservices","database_design"],               ["github"],          1),
    _make("engineering", 3,  "DevOps Engineer",         "CI/CD, infraestructura como código y automatización",                                 ["kubernetes","terraform","github_actions"],                     ["github"],          1),
    _make("engineering", 4,  "ML Engineer",             "Desarrollo e implementación de modelos de Machine Learning",                          ["model_training","mlops","feature_engineering"],               ["github"],          1),
    _make("engineering", 5,  "Database Architect",      "Diseño de esquemas, optimización de queries y estrategia de datos",                   ["sql_optimization","schema_design","indexing"],                 ["github"],          1),
    _make("engineering", 6,  "QA Automation",           "Testing automatizado, estrategias de QA y coverage",                                  ["pytest","selenium","ci_testing"],                             ["github"],          1),
    _make("engineering", 7,  "Security Engineer",       "Implementación de seguridad en el código y la infraestructura",                       ["sast","dependency_scanning","secrets_management"],             ["github"],          1),
    _make("engineering", 8,  "API Gateway Specialist",  "Gestión de gateways de API, rate limiting y autenticación",                           ["api_gateway","oauth2","rate_limiting"],                        ["github"],          2),
    _make("engineering", 9,  "Cloud Architect",         "Arquitectura cloud multi-proveedor y optimización de costos",                         ["aws","gcp","azure","cost_optimization"],                       ["github"],          1),
    _make("engineering", 10, "Data Engineer",           "Pipelines de datos, ETL y data lakes",                                               ["spark","airflow","dbt","data_pipelines"],                      ["github"],          1),
    _make("engineering", 11, "Mobile Engineer iOS",     "Desarrollo nativo iOS con Swift y SwiftUI",                                           ["swift","swiftui","xcode","app_store"],                         ["github"],          2),
    _make("engineering", 12, "Mobile Engineer Android", "Desarrollo nativo Android con Kotlin y Jetpack",                                     ["kotlin","jetpack","gradle"],                                   ["github"],          2),
    _make("engineering", 13, "Platform Engineer",       "Infraestructura de plataforma interna para desarrolladores",                          ["internal_tools","developer_portal","sdks"],                   ["github"],          2),
    _make("engineering", 14, "SRE Reliability",         "Disponibilidad, SLOs, incident response y postmortems",                               ["slo_management","incident_response","chaos_engineering"],      ["github","notion"], 1),
    _make("engineering", 15, "Performance Engineer",    "Optimización de rendimiento backend y frontend",                                      ["profiling","load_testing","caching"],                          ["github"],          2),
    _make("engineering", 16, "Blockchain Developer",    "Smart contracts, DeFi y protocolos Web3",                                             ["solidity","ethers_js","hardhat"],                              ["github"],          3),
    _make("engineering", 17, "AI Integration Engineer", "Integración de LLMs y APIs de IA en productos",                                      ["langchain","anthropic_api","rag"],                             ["github"],          1),
    _make("engineering", 18, "WebSocket Specialist",    "Tiempo real, WebSockets y arquitecturas event-driven",                                ["websockets","redis_pubsub","sse"],                             ["github"],          2),
    _make("engineering", 19, "Search Engineer",         "Motores de búsqueda, Elasticsearch y búsqueda vectorial",                             ["elasticsearch","vector_search","ranking"],                     ["github"],          2),
    _make("engineering", 20, "Observability Engineer",  "Logs, métricas, trazas y alertas",                                                   ["opentelemetry","prometheus","grafana"],                        ["github"],          2),
    # 21-100: ingenieros especializados
    *[_make("engineering", i, f"Engineering Specialist {i}", f"Especialización de ingeniería en dominio {i}", ["coding","architecture","code_review","testing"], ["github"], 3) for i in range(21, 101)],
]

# ─────────────────────────────────────────────────────────────────────────────
# 4. GROWTH AGENTS  (80)
# ─────────────────────────────────────────────────────────────────────────────

GROWTH_AGENTS: list[AgentDef] = [
    _make("growth", 1,  "SEO Strategist",             "Estrategia SEO on-page, off-page y técnica",                                          ["keyword_research","link_building","technical_seo"],            ["notion"],          1),
    _make("growth", 2,  "Content Marketer",           "Creación de contenido, blog y thought leadership",                                     ["content_creation","editorial_calendar","copywriting"],         ["notion"],          1),
    _make("growth", 3,  "Paid Acquisition",           "Google Ads, Meta Ads y SEM en general",                                               ["google_ads","meta_ads","roas_optimization"],                   ["notion","sheets"], 1),
    _make("growth", 4,  "Email Marketing",            "Secuencias de email, nurturing y automatización",                                      ["email_sequences","segmentation","deliverability"],             ["notion","hubspot"],1),
    _make("growth", 5,  "Social Media Manager",       "Gestión de redes sociales y comunidad",                                               ["social_strategy","community_mgmt","content_calendar"],         ["notion"],          2),
    _make("growth", 6,  "CRO Specialist",             "Optimización de conversión, landing pages y funnels",                                  ["ab_testing","heatmaps","funnel_optimization"],                 ["notion"],          1),
    _make("growth", 7,  "Viral Growth Hacker",        "Mecánicas virales, referral y loops de crecimiento",                                   ["viral_loops","referral_programs","k_factor"],                  ["notion"],          2),
    _make("growth", 8,  "Community Builder",          "Construcción y gestión de comunidades",                                               ["discord","slack_communities","events"],                        ["notion"],          2),
    _make("growth", 9,  "Influencer Marketer",        "Identificación y gestión de influencers y KOLs",                                       ["influencer_identification","campaign_mgmt","roi_tracking"],    ["notion"],          2),
    _make("growth", 10, "Partnership Growth",         "Crecimiento a través de alianzas y co-marketing",                                      ["co_marketing","integration_partners","affiliate"],             ["notion"],          2),
    _make("growth", 11, "Product Marketing",          "Posicionamiento, messaging y lanzamiento de features",                                 ["positioning","messaging","launch_playbook"],                   ["notion"],          1),
    _make("growth", 12, "Sales Enablement",           "Habilitación de ventas, decks y materiales",                                          ["sales_deck","battlecards","objection_handling"],               ["notion"],          2),
    _make("growth", 13, "Account Based Marketing",    "ABM para cuentas enterprise estratégicas",                                             ["account_targeting","personalization","multi_touch"],           ["hubspot","notion"],2),
    _make("growth", 14, "Podcast Strategist",         "Estrategia de podcast y audio marketing",                                             ["podcast_strategy","distribution","sponsorships"],              ["notion"],          3),
    _make("growth", 15, "Video Marketing",            "Estrategia de video, YouTube y video ads",                                            ["youtube_seo","video_production","tiktok"],                     ["notion"],          2),
    _make("growth", 16, "PR Specialist",              "Relaciones públicas, prensa y comunicación",                                           ["press_releases","journalist_outreach","media_coverage"],       ["notion"],          2),
    _make("growth", 17, "Event Marketing",            "Webinars, conferencias y eventos de growth",                                           ["event_planning","webinar_strategy","sponsorships"],            ["notion"],          3),
    _make("growth", 18, "Retention Growth",           "Programas de retención y expansión de ingresos",                                       ["lifecycle_marketing","expansion_revenue","churn_prevention"],  ["notion","hubspot"],2),
    _make("growth", 19, "Growth Analyst",             "Análisis de métricas de crecimiento y experimentos",                                   ["growth_metrics","experiment_analysis","funnel_data"],          ["notion","sheets"], 2),
    _make("growth", 20, "Demand Generation",          "Generación de demanda y pipeline B2B",                                                ["demand_gen","pipeline_creation","mql_optimization"],           ["hubspot","notion"],1),
    # 21-80: growth specialists adicionales
    *[_make("growth", i, f"Growth Specialist {i}", f"Especialización de growth en canal {i}", ["growth_marketing","channel_optimization","experiment_design"], ["notion"], 3) for i in range(21, 81)],
]

# ─────────────────────────────────────────────────────────────────────────────
# 5. DATA AGENTS  (70)
# ─────────────────────────────────────────────────────────────────────────────

DATA_AGENTS: list[AgentDef] = [
    _make("data", 1,  "Data Analyst Core",          "Análisis exploratorio, dashboards y reportes de negocio",                              ["sql","tableau","python_pandas"],                               ["sheets","notion"],  1),
    _make("data", 2,  "BI Developer",               "Business Intelligence, modelos dimensionales y data warehouse",                        ["dbt","snowflake","looker"],                                    ["notion"],           1),
    _make("data", 3,  "ML Scientist",               "Investigación y desarrollo de modelos de ML avanzados",                               ["scikit_learn","pytorch","feature_stores"],                     ["github"],           1),
    _make("data", 4,  "ETL Pipeline Engineer",      "Construcción y mantenimiento de pipelines de datos",                                  ["airflow","spark","kafka"],                                     ["github"],           1),
    _make("data", 5,  "Product Analytics",          "Análisis de comportamiento de usuario y métricas de producto",                        ["mixpanel","amplitude","sql"],                                  ["notion","sheets"],  1),
    _make("data", 6,  "Revenue Analytics",          "Análisis financiero, MRR, ARR y métricas SaaS",                                      ["saas_metrics","cohort_analysis","ltv_cac"],                    ["sheets","notion"],  1),
    _make("data", 7,  "NLP Engineer",               "Procesamiento de lenguaje natural y text analytics",                                  ["transformers","spacy","text_classification"],                  ["github"],           2),
    _make("data", 8,  "Computer Vision Engineer",   "Visión computacional e image analytics",                                             ["opencv","pytorch","object_detection"],                         ["github"],           2),
    _make("data", 9,  "Forecasting Specialist",     "Modelos de forecasting y series temporales",                                          ["prophet","arima","lstm"],                                      ["github","sheets"],  2),
    _make("data", 10, "A/B Testing Analyst",        "Diseño estadístico de experimentos y análisis de resultados",                         ["statistical_testing","bayesian","power_analysis"],             ["notion","sheets"],  2),
    _make("data", 11, "Data Governance Officer",    "Calidad, catálogo y gobierno de datos",                                              ["data_catalog","data_quality","lineage"],                       ["notion"],           2),
    _make("data", 12, "Real-time Analytics",        "Analytics en streaming y procesamiento en tiempo real",                               ["kafka_streams","flink","clickhouse"],                          ["github"],           2),
    _make("data", 13, "Customer Analytics",         "Segmentación de clientes, RFM y CLV",                                                ["rfm_analysis","customer_segmentation","clv"],                  ["sheets","notion"],  2),
    _make("data", 14, "Market Intelligence",        "Datos de mercado, trends y análisis sectorial",                                       ["market_data","trend_analysis","benchmarking"],                 ["notion"],           2),
    _make("data", 15, "Data Storyteller",           "Comunicación de datos e insights a stakeholders no técnicos",                         ["data_visualization","narrative","executive_reporting"],        ["notion","sheets"],  2),
    # 16-70: data specialists adicionales
    *[_make("data", i, f"Data Specialist {i}", f"Especialización de datos en dominio {i}", ["data_analysis","modeling","reporting","sql"], ["notion","sheets"], 3) for i in range(16, 71)],
]

# ─────────────────────────────────────────────────────────────────────────────
# 6. SECURITY AGENTS  (60)
# ─────────────────────────────────────────────────────────────────────────────

SECURITY_AGENTS: list[AgentDef] = [
    _make("security", 1,  "AppSec Engineer",          "Seguridad en el ciclo de desarrollo (SSDLC)",                                         ["sast","dast","code_review","owasp"],                           ["github"],           1),
    _make("security", 2,  "Threat Intelligence",      "Inteligencia de amenazas y análisis de adversarios",                                   ["threat_modeling","ioc_analysis","mitre_attack"],               ["notion"],           1),
    _make("security", 3,  "SIEM Analyst",             "Análisis de logs, correlación de eventos y detección de amenazas",                     ["splunk","elastic_siem","alert_triage"],                        ["notion"],           1),
    _make("security", 4,  "Pentest Engineer",         "Pruebas de penetración y red teaming",                                                ["kali","burpsuite","metasploit","web_pentesting"],              ["notion"],           1),
    _make("security", 5,  "Cloud Security",           "Seguridad en entornos cloud (AWS, GCP, Azure)",                                        ["cspm","iam_hardening","cloud_config"],                         ["notion","github"],  1),
    _make("security", 6,  "Compliance Officer",       "GDPR, SOC2, ISO27001 y otros frameworks regulatorios",                                ["compliance_audits","policy_writing","risk_assessment"],        ["notion"],           1),
    _make("security", 7,  "IAM Specialist",           "Gestión de identidades, privilegios y acceso",                                         ["zero_trust","pam","sso_mfa"],                                  ["notion"],           2),
    _make("security", 8,  "Incident Responder",       "Respuesta a incidentes de seguridad y forense digital",                               ["incident_playbook","forensics","eradication"],                 ["notion"],           1),
    _make("security", 9,  "Vulnerability Manager",    "Gestión de vulnerabilidades y patch management",                                       ["cve_tracking","patch_prioritization","vuln_scanning"],         ["notion","github"],  2),
    _make("security", 10, "Crypto & PKI Specialist",  "Criptografía, PKI y gestión de certificados",                                          ["tls","pki","secrets_management","hsm"],                        ["notion","github"],  2),
    _make("security", 11, "DLP Officer",              "Prevención de pérdida de datos y política de datos",                                   ["dlp_policies","data_classification","exfil_detection"],       ["notion"],           2),
    _make("security", 12, "API Security Specialist",  "Seguridad de APIs, autenticación y autorización",                                     ["api_security","oauth2","jwt_hardening"],                       ["github","notion"],  2),
    _make("security", 13, "Security Awareness",       "Formación en seguridad, phishing y cultura de seguridad",                             ["security_training","phishing_simulation","awareness"],         ["notion"],           3),
    _make("security", 14, "Container Security",       "Seguridad en contenedores Docker y Kubernetes",                                       ["image_scanning","pod_security","runtime_protection"],          ["github","notion"],  2),
    _make("security", 15, "Red Team Lead",            "Simulaciones de ataque y ejercicios de red team",                                      ["adversarial_simulation","attack_paths","purple_team"],         ["notion"],           1),
    # 16-60: security specialists adicionales
    *[_make("security", i, f"Security Specialist {i}", f"Especialización de seguridad en dominio {i}", ["security_assessment","threat_detection","incident_response","compliance"], ["notion"], 3, "Prioriza siempre la seguridad defensiva y el cumplimiento normativo.") for i in range(16, 61)],
]

# ─────────────────────────────────────────────────────────────────────────────
# 7. OSINT AGENTS  (60)
# ─────────────────────────────────────────────────────────────────────────────

OSINT_AGENTS: list[AgentDef] = [
    _make("osint", 1,  "Competitive OSINT",         "Monitoreo continuo de competidores: precios, features, contrataciones",                ["web_scraping","competitor_tracking","price_monitoring"],        ["notion"],           1),
    _make("osint", 2,  "Social Listening",          "Análisis de sentimiento y menciones en redes sociales",                               ["twitter_api","reddit_api","sentiment_analysis"],               ["notion"],           1),
    _make("osint", 3,  "Brand Monitor",             "Monitoreo de marca, reputación y menciones online",                                   ["brand_alerts","review_monitoring","pr_tracking"],              ["notion"],           1),
    _make("osint", 4,  "Tech Stack Investigator",   "Identificación del stack tecnológico de competidores",                                ["builtwith","wappalyzer","job_posting_analysis"],               ["notion"],           2),
    _make("osint", 5,  "Funding Tracker",           "Seguimiento de rondas de financiamiento y movimientos de VCs",                        ["crunchbase","pitchbook","funding_alerts"],                     ["notion"],           2),
    _make("osint", 6,  "Talent Intelligence",       "Análisis de contrataciones y movimientos de talento en competidores",                  ["linkedin_osint","job_postings","team_growth_analysis"],        ["notion"],           2),
    _make("osint", 7,  "Patent Analyst",            "Vigilancia tecnológica de patentes y propiedad intelectual",                           ["patent_search","ip_landscape","freedom_to_operate"],          ["notion"],           3),
    _make("osint", 8,  "Domain & Infra OSINT",      "Análisis de infraestructura web y dominios de competidores",                           ["shodan","censys","dns_analysis","whois"],                      ["notion"],           2),
    _make("osint", 9,  "Dark Web Monitor",          "Monitoreo de amenazas en dark web y foros de hacking",                                ["dark_web_monitoring","credential_leaks","threat_feeds"],       ["notion"],           1),
    _make("osint", 10, "Regulatory Intelligence",   "Seguimiento de cambios regulatorios y compliance en el sector",                       ["regulatory_tracking","legal_changes","compliance_alerts"],     ["notion"],           2),
    _make("osint", 11, "Market Signal Detector",    "Detección de señales tempranas de cambios de mercado",                                ["trend_analysis","google_trends","news_aggregation"],           ["notion"],           1),
    _make("osint", 12, "Executive Profiler",        "Perfiles públicos de ejecutivos de empresas objetivo",                                ["linkedin_analysis","public_records","press_coverage"],         ["notion"],           3),
    _make("osint", 13, "Partnership OSINT",         "Identificación de partnerships y alianzas de competidores",                           ["press_release_monitoring","partnership_tracking"],             ["notion"],           2),
    _make("osint", 14, "SEO Competitive Intel",     "Análisis SEO competitivo, keywords y autoridad de dominio",                           ["semrush_analysis","keyword_gaps","backlink_analysis"],         ["notion"],           1),
    _make("osint", 15, "Customer Review Analyst",   "Análisis de reviews de clientes de competidores (G2, Capterra)",                      ["review_scraping","sentiment","feature_gap_analysis"],          ["notion"],           2),
    # 16-60: OSINT specialists adicionales
    *[_make("osint", i, f"OSINT Specialist {i}", f"Inteligencia de fuentes abiertas en dominio {i}", ["web_research","data_collection","analysis","reporting"], ["notion"], 3) for i in range(16, 61)],
]

# ─────────────────────────────────────────────────────────────────────────────
# Registro maestro
# ─────────────────────────────────────────────────────────────────────────────

ALL_AGENTS: list[AgentDef] = (
    EXECUTIVE_AGENTS +   # 50
    PRODUCT_AGENTS +     # 80
    ENGINEERING_AGENTS + # 100
    GROWTH_AGENTS +      # 80
    DATA_AGENTS +        # 70
    SECURITY_AGENTS +    # 60
    OSINT_AGENTS         # 60
)                        # = 500

AGENTS_BY_CATEGORY: dict[str, list[AgentDef]] = {
    "executive":   EXECUTIVE_AGENTS,
    "product":     PRODUCT_AGENTS,
    "engineering": ENGINEERING_AGENTS,
    "growth":      GROWTH_AGENTS,
    "data":        DATA_AGENTS,
    "security":    SECURITY_AGENTS,
    "osint":       OSINT_AGENTS,
}

AGENTS_BY_ID: dict[str, AgentDef] = {a.id: a for a in ALL_AGENTS}

assert len(ALL_AGENTS) == 500, f"Se esperaban 500 agentes, hay {len(ALL_AGENTS)}"
