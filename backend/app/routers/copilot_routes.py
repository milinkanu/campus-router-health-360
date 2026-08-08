from fastapi import APIRouter, HTTPException, status
from app.evidence import build_evidence
from app.copilot import ask_copilot
from app.schemas import CopilotRequest, CopilotResponse

router = APIRouter()


@router.post("/copilot/ask", response_model=CopilotResponse)
def handle_copilot_ask(payload: CopilotRequest):
    try:
        evidence = build_evidence(payload.router_id)
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"router_id '{payload.router_id}' not found",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error building evidence: {str(e)}",
        ) from e

    try:
        response_dict = ask_copilot(evidence, payload.question, payload.api_key)
        return CopilotResponse(**response_dict)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI Copilot response generation failed: {str(e)}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error contacting AI Copilot service: {str(e)}",
        ) from e
