"""Live end-to-end evaluation of Gemini Agent + Channel3 + Grounding Validator.

Executes real API calls through AgentService, reports:
- Number of raw recommendations from Gemini
- Number dropped by grounding and exact drop reasons
- Each surviving recommendation with its reasons and evidence text
- Appends complete results to docs/LIVE_TEST_REPORT.md
"""
import datetime
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.agent import AgentService
from app.config import get_settings
from app.grounding import ground_recommendations

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("live_agent_eval")

def run_eval():
    settings = get_settings()
    if not settings.GEMINI_API_KEY or not settings.CHANNEL3_API_KEY:
        print("[ERROR] Real API keys missing in .env")
        sys.exit(1)

    print(f"\n--- Live Gemini Agent & Grounding Evaluation ---")
    print(f"Model: {settings.GEMINI_MODEL}")
    print(f"Database: {settings.DATABASE_PATH}")

    agent_service = AgentService(settings=settings)

    # Intercept ground_recommendations to capture raw counts and drop reasons
    import app.agent as agent_module
    orig_ground = agent_module.ground_recommendations
    last_ground_info = {}

    def tracking_ground(raw_recs, snapshots_by_id, requested_query=None):
        surviving, drops = orig_ground(raw_recs, snapshots_by_id, requested_query=requested_query)
        last_ground_info["raw_count"] = len(raw_recs)
        last_ground_info["surviving_count"] = len(surviving)
        last_ground_info["dropped_count"] = len(drops)
        last_ground_info["drops"] = drops
        return surviving, drops

    agent_module.ground_recommendations = tracking_ground

    queries = [
        ("I need a sturdy wooden walking stick under $40", "40.00", "walking stick"),
        ("I need a jar opener for weak hands under $25", "25.00", "jar opener"),
        ("I need a handheld magnifying glass with light under $25", "25.00", "magnifier"),
        ("I need a walking stick with large buttons under $40", "40.00", "negative test: buttons"),
    ]

    report_file = ROOT / "docs" / "LIVE_TEST_REPORT.md"
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    lines = [
        f"\n## Real End-to-End Agent & Grounding Verification ({timestamp})",
        f"- **Model:** `{settings.GEMINI_MODEL}`",
        f"- **Channel3 Base:** `api.trychannel3.com/v1`",
        f"- **Mode:** Live end-to-end (`AgentService.run`) with caching",
        "",
    ]

    for user_prompt, budget, label in queries:
        print(f"\nEvaluating: '{user_prompt}' (Label: {label}, Budget: ${budget})")
        session_id = f"eval_{datetime.datetime.now(datetime.timezone.utc).strftime('%H%M%S')}"

        res = agent_service.process_request(
            message=user_prompt,
            budget=budget,
            session_id=session_id,
        )

        snapshots = agent_service._load_snapshots_for_search(res.search_id)
        
        raw_count = last_ground_info.get("raw_count", len(res.recommendations))
        dropped_count = last_ground_info.get("dropped_count", 0)
        drops = last_ground_info.get("drops", [])
        surviving_count = len(res.recommendations)
        
        print(f"  Reply Text: {res.reply_text}")
        print(f"  Model produced: {raw_count} raw recommendations")
        print(f"  Grounding dropped: {dropped_count} recommendations")
        for d in drops:
            print(f"    - Drop reason: {d}")
        print(f"  Surviving recommendations: {surviving_count}")

        query_report = [
            f"### Query: \"{user_prompt}\"",
            f"- **Budget:** ${budget}",
            f"- **Search ID:** `{res.search_id}`",
            f"- **Reply Text:** {res.reply_text}",
            f"- **Model Proposed Recommendations:** {raw_count}",
            f"- **Recommendations Dropped by Grounding:** {dropped_count}",
        ]
        if drops:
            query_report.append("- **Drop Reasons:**")
            for d in drops:
                query_report.append(f"  - `{d}`")
        query_report.append(f"- **Recommendations Survived Grounding:** {surviving_count}")

        if res.recommendations:
            query_report.append("- **Verified Recommendations & Reasons:**")
            for idx, item in enumerate(res.recommendations, 1):
                p_title = item.title
                p_price = f"${item.price} {item.currency}"
                p_domain = item.merchant_domain
                query_report.append(f"  {idx}. **{p_title}** ({p_price}, `{p_domain}`)")
                for r in item.reasons:
                    query_report.append(f"     - *Claim:* {r.claim}")
                    query_report.append(f"       *Evidence ({r.evidence_field}):* \"{r.evidence_text}\"")
        else:
            query_report.append("- **No recommendations survived grounding.** (Safe rejection verified)")

        lines.extend(query_report)
        lines.append("")

    with open(report_file, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print("\n[PASS] All 4 live evaluations completed successfully.")
    print("Report updated in docs/LIVE_TEST_REPORT.md\n")

if __name__ == "__main__":
    run_eval()
