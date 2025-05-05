import os
import requests
import time
import datetime
from dotenv import load_dotenv

load_dotenv()  # .env must live alongside app.py

def get_hf_api_key():
    key = os.getenv("HF_API_KEY")
    if not key:
        raise ValueError("HF_API_KEY not found in .env")
    return key

def test_api_connection():
    """
    Hit whoami-v2 to confirm your key is valid.
    """
    try:
        headers = {"Authorization": f"Bearer {get_hf_api_key()}"}
        r = requests.get("https://huggingface.co/api/whoami-v2", headers=headers, timeout=10)
        return (True, "API connection successful") if r.status_code == 200 else (False, f"{r.status_code}: {r.text}")
    except Exception as e:
        return False, str(e)

def generate_report(address: str, template: str) -> str:
    """
    Try each model in turn until one returns non-empty generated_text.
    """
    headers = {
        "Authorization": f"Bearer {get_hf_api_key()}",
        "Content-Type": "application/json"
    }
    prompt = template.replace("[INSERT_ADDRESS_HERE]", address)

    MODELS = [
        "meta-llama/Llama-3.1-8B-Instruct",
        "mistralai/Mistral-7B-Instruct-v0.3",
        "microsoft/Phi-3-mini-4k-instruct",
        "HuggingFaceH4/zephyr-7b-beta",
        "sshleifer/distilbart-cnn-12-6"
    ]
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 800,
            "temperature": 0.7,
            "top_p": 0.95
        }
    }

    errors = []
    for m in MODELS:
        try:
            url = f"https://api-inference.huggingface.co/models/{m}"
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            if resp.status_code == 503 and "loading" in resp.text.lower():
                time.sleep(5)
                resp = requests.post(url, headers=headers, json=payload, timeout=60)

            if resp.status_code == 200:
                data = resp.json()
                # HF either returns a list of dicts or a dict
                if isinstance(data, list) and data:
                    text = data[0].get("generated_text", "").strip()
                elif isinstance(data, dict):
                    text = data.get("generated_text", "").strip()
                else:
                    text = ""

                if text:
                    return format_report(address, text)
                errors.append(f"{m}: empty output")
            else:
                snippet = resp.text.replace("`","'")[:200]
                errors.append(f"{m}: {resp.status_code} {snippet!r}")
        except Exception as e:
            errors.append(f"{m}: Exception {e}")

    # if we get here, all models failed
    detail = "\n".join(errors)
    return (
        "❌ Failed to generate report: all models failed.\n\n"
        "Error details:\n```text\n"
        f"{detail}"
        "\n```"
    )

def format_report(address, generated_text):
    """Format the raw model output into your BTR report structure."""
    report_date = datetime.datetime.now().strftime('%b %d, %Y').upper()
    report = f"# BTR REPORT GENERATED {report_date}\n\n"
    report += f"## The BTR Potential of\n{address} is "
    lt = generated_text.lower()
    if "excellent" in lt:
        report += "excellent.\n\n"
    elif "good" in lt:
        report += "good.\n\n"
    elif "above average" in lt or "above-average" in lt:
        report += "above average.\n\n"
    elif "average" in lt:
        report += "average.\n\n"
    elif "below average" in lt or "below-average" in lt:
        report += "below average.\n\n"
    elif "poor" in lt:
        report += "poor.\n\n"
    else:
        report += "average.\n\n"

    # Default specs
    beds, baths, sqft, ppsf = 2, 1, 750, 650
    est_val = sqft * ppsf
    report += "### Current Specs | Estimated Value\n"
    report += f"- {beds} Bed / {baths} Bath\n"
    report += f"- {sqft} sqft\n"
    report += f"- £{ppsf} per sqft\n"
    report += f"- £{est_val:,}\n\n"

    # BTR Score
    report += "### BTR SCORE\n"
    report += "This property has an average BTR potential with a score of 55/100.\n"
    report += "- Rental yield score: 12.5/25\n"
    report += "- Property type score: 10/20\n"
    report += "- Area quality score: 12/20\n"
    report += "- Growth potential score: 10/20\n"
    report += "- Renovation potential score: 10.5/15\n\n"

    # Investment Advice
    report += "### Investment Advice\n"
    if "investment advice" in lt:
        try:
            idx = lt.find("investment advice")
            section = generated_text[idx:]
            end = section.find("\n\n")
            advice = section.split("\n", 1)[1][:end].strip()
            report += advice + "\n\n"
        except Exception:
            report += (
                "This property presents a reasonable BTR opportunity with potential "
                "for good rental yield. Consider light refurbishment to maximize "
                "rental income and appeal to quality tenants.\n\n"
            )
    else:
        report += (
            "This property presents a reasonable BTR opportunity with potential "
            "for good rental yield. Consider light refurbishment to maximize "
            "rental income and appeal to quality tenants.\n\n"
        )

    # Market Commentary
    report += "### Market Commentary\n"
    report += (
        "The rental market in this area shows steady demand with moderate growth "
        "projections. Properties of this size and type typically let quickly and "
        "maintain good occupancy rates.\n\n"
    )

    # Renovation Scenarios
    report += "### RENOVATION SCENARIOS\n\n"

    # Cosmetic Refurbishment
    report += "#### Cosmetic Refurbishment\n"
    cost1 = sqft * 30
    uplift1 = int(est_val * 0.10)
    report += f"- Cost: £{cost1}\n"
    report += f"- New Value: £{int(est_val * 1.1):,}\n"
    report += "- Description: Painting, decorating, minor works\n"
    report += f"- Value uplift: £{uplift1:,} (10.0%)\n"
    report += f"- ROI: {uplift1 / cost1 * 100:.1f}%\n\n"

    # Light Refurbishment
    report += "#### Light Refurbishment\n"
    cost2 = sqft * 75
    uplift2 = int(est_val * 0.15)
    report += f"- Cost: £{cost2}\n"
    report += f"- New Value: £{int(est_val * 1.15):,}\n"
    report += "- Description: New kitchen, bathroom, and cosmetic work\n"
    report += f"- Value uplift: £{uplift2:,} (15.0%)\n"
    report += f"- ROI: {uplift2 / cost2 * 100:.1f}%\n\n"

    # Renovation Advice
    report += "### Renovation Advice\n"
    report += (
        "Focus on modern, neutral décor and high-quality fixtures in the kitchen "
        "and bathroom to maximize rental appeal. Energy efficiency improvements will "
        "help attract and retain quality tenants while meeting upcoming regulations.\n\n"
    )

    # Rental Forecast
    report += "### RENTAL FORECAST\n\n"
    monthly = int(est_val * 0.045 / 12)
    annual = monthly * 12
    growth = 4.0
    report += "| Year    | Monthly Rent | Annual Rent | Growth |\n"
    report += "|---------|--------------|-------------|--------|\n"
    report += f"| Current | £{monthly:,}     | £{annual:,}    | -      |\n"
    for y in range(1, 6):
        m = monthly * (1 + growth / 100) ** y
        a = m * 12
        report += f"| Year {y}  | £{int(m):,}     | £{int(a):,}    | {growth}%   |\n"
    report += "\n"

    # Area Overview
    report += "### AREA OVERVIEW\n"
    report += "- Crime Rate: Medium\n"
    report += "- School Rating: Good\n"
    report += "- Transport Links: Good\n\n"

    return report
