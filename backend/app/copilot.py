import os
import sys
import json
import logging
from pathlib import Path
from pydantic import ValidationError

backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.config import GEMINI_API_KEY, LLM_MODEL
from app.schemas import CopilotResponse

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a network diagnostics assistant for a campus IT team. You will be given a JSON evidence bundle for exactly one router: its health score, aggregated metric summary, and recent complaint texts. This evidence is the ONLY information you have about this router.

Rules:
- Base your diagnosis strictly on the numbers and complaint text provided. Never invent metrics, dates, or complaints not present in the evidence.
- If the metrics are healthy (health_score >= 80) and there are no complaints, say so plainly — do not manufacture a problem.
- If there are complaints but metrics are healthy, treat it as a likely user-education or environmental issue, not a hardware fault.
- Cite the specific numbers you used to reach your conclusion inside the "evidence" list.
- Choose exactly one recommended_fix from this fixed set:
  ["firmware_update", "relocate", "replace", "user_education", "none"]
- Respond with ONLY a single valid JSON object, no markdown fences, no prose outside the JSON, matching exactly this schema:
{
  "diagnosis": "<2-4 sentence plain-English diagnosis>",
  "evidence": ["<short bullet citing a specific number>", "..."],
  "recommended_fix": "<one of the fixed set above>",
  "confidence": "<low|medium|high>"
}"""


def _clean_json_text(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()


def _generate_rule_based_fallback(evidence: dict, question: str) -> dict:
    """
    Deterministically generates a valid Copilot response based on evidence rules
    when no API key is available or for offline testing.
    """
    router_id = evidence.get("router_id", "R-0000")
    h_score = evidence.get("health_score", 100.0)
    top_issue = evidence.get("top_issue", "Healthy")
    complaints = evidence.get("recent_complaints", [])
    metrics = evidence.get("metric_summary", {})

    disconnects = metrics.get("avg_disconnects_per_hour", 0.0)
    pkt_loss = metrics.get("avg_packet_loss_pct", 0.0)
    latency = metrics.get("avg_latency_ms", 0.0)
    weak_sig_pct = metrics.get("weak_signal_hours_pct", 0.0)
    low_spd_pct = metrics.get("low_speed_hours_pct", 0.0)

    # Rule 1: Healthy router & no complaints
    if h_score >= 80.0 and not complaints:
        return {
            "router_id": router_id,
            "diagnosis": f"Router {router_id} is operating in excellent health with a health score of {h_score}. Latency average is {latency}ms and packet loss is {pkt_loss}%. No user complaints have been reported.",
            "evidence": [
                f"Health score: {h_score}/100",
                f"Average latency: {latency} ms",
                f"Packet loss: {pkt_loss}%",
                f"Disconnects per hour: {disconnects}"
            ],
            "recommended_fix": "none",
            "confidence": "high"
        }

    # Rule 2: Healthy metrics but complaints exist
    if h_score >= 80.0 and complaints:
        c_sample = complaints[0] if complaints else "User report"
        return {
            "router_id": router_id,
            "diagnosis": f"Router {router_id} has healthy telemetry metrics (Health score: {h_score}), but complaints exist ({c_sample}). The issue is likely local environment or user device setup rather than a router hardware failure.",
            "evidence": [
                f"Health score: {h_score}/100",
                f"Recent complaint: '{c_sample}'",
                f"Packet loss is low at {pkt_loss}%"
            ],
            "recommended_fix": "user_education",
            "confidence": "high"
        }

    # Rule 3: Weak signal coverage dominant
    if top_issue == "Weak signal coverage" or weak_sig_pct > 0.3:
        return {
            "router_id": router_id,
            "diagnosis": f"Router {router_id} suffers from poor Wi-Fi signal coverage, operating under weak signal for {round(weak_sig_pct*100, 1)}% of observed hours. Physical placement or wall obstruction is impeding transmission.",
            "evidence": [
                f"Weak signal hours: {round(weak_sig_pct*100, 1)}%",
                f"Health score: {h_score}/100",
                f"Average disconnects per hour: {disconnects}"
            ],
            "recommended_fix": "relocate",
            "confidence": "high"
        }

    # Rule 4: Frequent disconnects or heavy hardware degradation
    if top_issue == "Frequent disconnects" or disconnects > 3.0 or h_score < 30.0:
        rec_fix = "replace" if disconnects > 4.0 or h_score < 20.0 else "firmware_update"
        return {
            "router_id": router_id,
            "diagnosis": f"Router {router_id} shows severe instability with {disconnects} disconnects per hour, high latency of {latency}ms, and packet loss of {pkt_loss}%. Health score is critically low at {h_score}.",
            "evidence": [
                f"Disconnects per hour: {disconnects}",
                f"Average latency: {latency} ms",
                f"Packet loss: {pkt_loss}%",
                f"Low speed hours: {round(low_spd_pct*100, 1)}%"
            ],
            "recommended_fix": rec_fix,
            "confidence": "high"
        }

    # Default fallback
    return {
        "router_id": router_id,
        "diagnosis": f"Router {router_id} is exhibiting degraded performance with top issue '{top_issue}' and health score {h_score}.",
        "evidence": [
            f"Health score: {h_score}",
            f"Top issue: {top_issue}",
            f"Latency: {latency} ms"
        ],
        "recommended_fix": "firmware_update",
        "confidence": "medium"
    }


def ask_copilot(evidence: dict, question: str) -> dict:
    """
    Calls Google Gemini LLM API with evidence bundle and question.
    Parses JSON and validates against CopilotResponse model.
    Falls back to deterministic rule-based output if GEMINI_API_KEY is not configured.
    Retries once with strict prompt on JSON parse failure.
    """
    clean_key = (GEMINI_API_KEY or "").strip().lower()
    if not clean_key or any(placeholder in clean_key for placeholder in ["your_gemini_api_key_here", "your_api_key_here", "sk-dummy", "placeholder", "xxx"]):
        logger.info("GEMINI_API_KEY not set or placeholder. Using rule-based copilot engine.")
        raw_res = _generate_rule_based_fallback(evidence, question)
        validated = CopilotResponse(**raw_res)
        return validated.model_dump()

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=GEMINI_API_KEY)
        user_prompt = f"Evidence: {json.dumps(evidence)}\nQuestion: {question}"

        def call_api(prompt_text: str) -> str:
            config = types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.2,
                response_mime_type="application/json",
            )
            response = client.models.generate_content(
                model=LLM_MODEL,
                contents=prompt_text,
                config=config,
            )
            return response.text

        response_text = call_api(user_prompt)
        cleaned_text = _clean_json_text(response_text)
        data = json.loads(cleaned_text)
        data["router_id"] = evidence["router_id"]
        validated = CopilotResponse(**data)
        return validated.model_dump()

    except (json.JSONDecodeError, ValidationError) as err:
        logger.warning("First Gemini API call failed parse/validation (%s). Retrying once with strict instructions.", err)
        retry_prompt = user_prompt + "\n\nCRITICAL: Output ONLY raw valid JSON adhering exactly to the specified JSON schema. No additional words."
        try:
            retry_text = call_api(retry_prompt)
            cleaned_text = _clean_json_text(retry_text)
            data = json.loads(cleaned_text)
            data["router_id"] = evidence["router_id"]
            validated = CopilotResponse(**data)
            return validated.model_dump()
        except Exception as retry_err:
            logger.error("Retry Gemini LLM call failed: %s. Falling back to rule-based response.", retry_err)
            raw_res = _generate_rule_based_fallback(evidence, question)
            return CopilotResponse(**raw_res).model_dump()
    except Exception as e:
        logger.error("Error calling Gemini API (%s). Falling back to rule-based copilot engine.", e)
        raw_res = _generate_rule_based_fallback(evidence, question)
        return CopilotResponse(**raw_res).model_dump()
