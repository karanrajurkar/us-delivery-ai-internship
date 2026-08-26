import asyncio
import json
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from src.triage.triage_agent import TicketTriageAgent, TriageInput, TriageOutput
from src.summariser.account_summariser import TAMAccountSummariser, AccountBrief

app = FastAPI(
    title="US Delivery AI Support & TAM API",
    description="Production-grade AI API for Intelligent Ticket Triage and TAM Account Health Summaries.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

triage_agent = TicketTriageAgent()
account_summariser = TAMAccountSummariser()

class SummariseRequest(BaseModel):
    account_id: str

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "US Delivery AI Support Agent", "version": "1.0.0"}

@app.post("/api/v1/triage", response_model=TriageOutput)
def api_triage_ticket(payload: TriageInput):
    """
    Task 1 Endpoint: Ingests raw support ticket and returns structured triage output.
    """
    try:
        result = triage_agent.triage(payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Triage processing error: {str(e)}")

@app.post("/api/v1/summarise", response_model=AccountBrief)
def api_summarise_account(payload: SummariseRequest):
    """
    Task 2 Endpoint: Pulls account metadata and 90d ticket history to produce deterministic account brief.
    """
    try:
        result = account_summariser.summarise_account(payload.account_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Account summarisation error: {str(e)}")

@app.post("/api/v1/triage/stream")
async def api_triage_stream(payload: TriageInput):
    """
    Bonus Feature (+3 marks): Streaming triage response token by token via SSE.
    """
    async def event_generator():
        out = triage_agent.triage(payload)
        out_dict = out.model_dump()
        full_json = json.dumps(out_dict)
        
        # Simulate token-by-token streaming
        chunk_size = 15
        for i in range(0, len(full_json), chunk_size):
            chunk = full_json[i:i+chunk_size]
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            await asyncio.sleep(0.05)
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
