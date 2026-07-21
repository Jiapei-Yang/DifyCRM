from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from . import crm_service as crm
from .command_parser import HELP_TEXT, handle_command
from .config import get_settings
from .db import fetch_one


settings = get_settings()
app = FastAPI(title=settings.app_name, version="1.0.0")


class CommandRequest(BaseModel):
    message: str = Field(..., description="Feishu/LangBot/Dify user message")
    sender_id: str = Field(default="demo_sales", description="Feishu user id or demo user")
    conversation_id: str | None = None


class DictRequest(BaseModel):
    data: dict[str, Any] = Field(default_factory=dict)
    sender_id: str = "demo_sales"


@app.get("/health")
def health() -> dict[str, Any]:
    db = fetch_one("SELECT DATABASE() AS db, VERSION() AS version")
    return {"ok": True, "service": settings.app_name, "database": db}


@app.get("/")
def root() -> dict[str, Any]:
    return {"ok": True, "message": "DifyCRM API is running", "help": "/help"}


@app.post("/assistant/command")
def assistant_command(req: CommandRequest) -> dict[str, Any]:
    return handle_command(req.message, req.sender_id)


@app.get("/assistant/help")
def assistant_help() -> dict[str, Any]:
    return {"ok": True, "reply": HELP_TEXT}


@app.post("/channels")
def create_channel(req: DictRequest) -> dict[str, Any]:
    return {"ok": True, "data": crm.create_channel(req.data, req.sender_id)}


@app.post("/campaigns")
def create_campaign(req: DictRequest) -> dict[str, Any]:
    return {"ok": True, "data": crm.create_campaign(req.data, req.sender_id)}


@app.post("/leads")
def create_lead(req: DictRequest) -> dict[str, Any]:
    return {"ok": True, "data": crm.create_lead(req.data, req.sender_id)}


@app.get("/leads")
def list_leads(status: str | None = None, mine: bool = False, sender_id: str = "demo_sales") -> dict[str, Any]:
    return {"ok": True, "data": crm.list_leads({"status": status, "mine": mine}, sender_id)}


@app.post("/leads/{lead_id}/score")
def score_lead(lead_id: int) -> dict[str, Any]:
    return {"ok": True, "data": crm.rescore_lead(lead_id)}


@app.post("/leads/{lead_id}/convert")
def convert_lead(lead_id: int, sender_id: str = "demo_sales") -> dict[str, Any]:
    return {"ok": True, "data": crm.convert_lead(lead_id, sender_id)}


@app.post("/customers")
def create_customer(req: DictRequest) -> dict[str, Any]:
    return {"ok": True, "data": crm.create_customer(req.data, req.sender_id)}


@app.get("/customers/mine")
def my_customers(sender_id: str = "demo_sales") -> dict[str, Any]:
    return {"ok": True, "data": crm.list_customers(sender_id)}


@app.post("/followups")
def add_followup(req: DictRequest) -> dict[str, Any]:
    return {"ok": True, "data": crm.add_followup(req.data, req.sender_id)}


@app.get("/stats/source")
def stats_source() -> dict[str, Any]:
    return {"ok": True, "data": crm.source_stats()}


@app.get("/stats/acquisition")
def stats_acquisition() -> dict[str, Any]:
    return {"ok": True, "data": crm.acquisition_stats()}


@app.get("/stats/funnel")
def stats_funnel() -> dict[str, Any]:
    return {"ok": True, "data": crm.funnel_stats()}


@app.get("/dashboard")
def dashboard(sender_id: str = "demo_sales") -> dict[str, Any]:
    return {"ok": True, "data": crm.dashboard(sender_id)}
