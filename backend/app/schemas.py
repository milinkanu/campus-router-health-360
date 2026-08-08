from pydantic import BaseModel, Field
from typing import Literal


class RouterRankingItem(BaseModel):
    router_id: str
    health_score: float
    building: str
    model: str
    firmware_version: str
    user_type: str
    top_issue: str
    disconnects_per_hour: float
    avg_packet_loss_pct: float
    avg_latency_ms: float


class RankingsResponse(BaseModel):
    total_routers: int
    routers: list[RouterRankingItem]


class HourlyMetric(BaseModel):
    hour: str
    avg_speed_mbps: float
    latency_ms: float
    packet_loss_pct: float
    disconnects: int
    connected_devices: int
    signal_dbm: float


class Complaint(BaseModel):
    ticket_id: str
    date: str
    complaint_text: str


class RouterDetailResponse(BaseModel):
    router_id: str
    model: str
    firmware_version: str
    building: str
    room: str
    user_type: str
    issue_date: str
    health_score: float
    top_issue: str
    metrics: list[HourlyMetric]
    complaints: list[Complaint]


class CopilotRequest(BaseModel):
    router_id: str
    question: str


class CopilotResponse(BaseModel):
    router_id: str
    diagnosis: str
    evidence: list[str]
    recommended_fix: Literal["firmware_update", "relocate", "replace", "user_education", "none"]
    confidence: Literal["low", "medium", "high"]


class FiltersResponse(BaseModel):
    buildings: list[str]
    firmware_versions: list[str]
    models: list[str]


class HealthCheckResponse(BaseModel):
    status: str = "ok"
