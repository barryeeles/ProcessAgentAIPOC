"""Loads and validates config.yaml into a typed dataclass."""

import hashlib
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ScopeConfig:
    epic_key_prefixes: list[str]
    capability_key_prefixes: list[str]
    epic_terminal_statuses: list[str] = field(default_factory=lambda: ["Done", "Cancelled", "On Hold", "Portfolio Funnel"])


@dataclass
class ThresholdConfig:
    stagnation_scoping_warning: int
    stagnation_scoping_priority: int
    stagnation_delivery_warning1: int
    stagnation_delivery_warning2: int
    stagnation_delivery_alert: int
    scoping_budget_days: int
    kpi_full_cycle_time_sla: int
    kpi_delivery_predictability_sla: int
    kpi_delivery_cycle_time_sla: int
    kpi_amber_zone_pct: float
    rag_green_threshold: float
    rag_amber_threshold: float
    delivery_at_risk_horizon_days: int
    low_confidence_threshold: float
    ageing_backlog_days: int
    rekey_phantom_weeks: int
    high_risk_grace_calendar_months: int
    high_risk_penalty_pct: float


@dataclass
class WeightConfig:
    data_quality: float
    flow_throughput: float
    kpis: float


@dataclass
class AppConfig:
    scope: ScopeConfig
    fiscal_calendar: dict[str, Any]
    thresholds: ThresholdConfig
    weights: WeightConfig
    dq_severity_weights: dict[str, int]
    blocked_penalties: dict[str, float]
    flow_scores: dict[str, int]
    kpi_scores: dict[str, int]
    snapshot_history_weeks: int
    feature_workflow_ordinal: list[str]
    legacy_statuses: list[str]
    status_normalisation: dict[str, Any]
    excel_columns: dict[str, str]
    # Derived
    ruleset_version: str = ""
    feature_ordinal_map: dict[str, int] = field(default_factory=dict)


_config: AppConfig | None = None
_config_path: Path | None = None


def load_config(path: Path | None = None) -> AppConfig:
    global _config, _config_path

    if path is None:
        # Walk up from this file to find config.yaml at project root
        here = Path(__file__).parent
        path = here.parent / "config.yaml"

    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    config = AppConfig(
        scope=ScopeConfig(**raw["scope"]),
        fiscal_calendar=raw["fiscal_calendar"],
        thresholds=ThresholdConfig(**raw["thresholds"]),
        weights=WeightConfig(**raw["weights"]),
        dq_severity_weights=raw["dq_severity_weights"],
        blocked_penalties=raw["blocked_penalties"],
        flow_scores=raw["flow_scores"],
        kpi_scores=raw["kpi_scores"],
        snapshot_history_weeks=raw["snapshot_history_weeks"],
        feature_workflow_ordinal=raw["feature_workflow_ordinal"],
        legacy_statuses=raw["legacy_statuses"],
        status_normalisation=raw["status_normalisation"],
        excel_columns=raw["excel_columns"],
    )

    # Stable hash of the config file — stored on every snapshot for reproducibility
    with open(path, "rb") as f:
        config.ruleset_version = hashlib.sha256(f.read()).hexdigest()[:12]

    # Build ordinal lookup: status → integer position (1-indexed)
    config.feature_ordinal_map = {
        status: idx + 1
        for idx, status in enumerate(config.feature_workflow_ordinal)
    }

    _config = config
    _config_path = path
    return config


def get_config() -> AppConfig:
    if _config is None:
        return load_config()
    return _config
