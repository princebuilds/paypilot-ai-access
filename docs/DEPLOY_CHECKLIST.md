# docs/DEPLOY_CHECKLIST.md: Render Blueprint Deployment Guide

Follow this click-by-click guide to deploy PayPilot AI ACCESS to Render using the Blueprint.

---

## Pre-Deployment Notes
- **Blueprint File:** [`render.yaml`](../render.yaml) is pre-configured with Python 3.13, health check path `/api/health`, and generous rate limits (`RATE_LIMIT_PER_HOUR=120`) for hackathon judges.
- **Secrets Needed:** You will need your 4 existing API keys from your local `.env` file:
  1. `CHANNEL3_API_KEY`
  2. `GEMINI_API_KEY`
  3. `PAYPAL_CLIENT_ID`
  4. `PAYPAL_CLIENT_SECRET`

---

## Step 1: Safely Copying Keys from `.env`
To avoid accidental trailing spaces or copying key names:
1. Open your local `.env` file in **Notepad** (or your text editor).
2. For each key:
   - Carefully highlight **only the characters AFTER the `=` sign**.
   - Do NOT select quotes (if any) or leading/trailing whitespace.
   - Press `Ctrl + C` to copy.

---

## Step 2: Click-by-Click Render Blueprint Deployment
1. Log in to your [Render Dashboard](https://dashboard.render.com).
2. In the top-right corner, click **New +** and select **Blueprint**.
3. Under **Connect a repository**, find and select:
   ```text
   princebuilds/paypilot-ai-access
   ```
4. Render will inspect `render.yaml` and display the **paypilot-ai-access** web service.
5. In the **Environment Variables** section, Render will prompt for the 4 un-synced secrets:
   - **`CHANNEL3_API_KEY`**: Paste your Channel3 API key.
   - **`GEMINI_API_KEY`**: Paste your Google Gemini API key.
   - **`PAYPAL_CLIENT_ID`**: Paste your PayPal Sandbox Client ID.
   - **`PAYPAL_CLIENT_SECRET`**: Paste your PayPal Sandbox Secret.
6. Verify non-secret values pre-populated by `render.yaml`:
   - `PYTHON_VERSION`: `3.13.0`
   - `PAYPAL_ENV`: `sandbox`
   - `GEMINI_MODEL`: `gemini-3.5-flash-lite`
   - `RATE_LIMIT_PER_HOUR`: `120`
   - `DAILY_SEARCH_CAP`: `1500`
   - `OFFLINE_TESTS`: `0`
7. Click **Apply** at the bottom of the page.
8. Render will initiate the build:
   - Runs `pip install -r requirements.txt`.
   - Starts `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
   - Verifies the health check at `/api/health`.

---

## Step 3: Retrieve Hosted URL
1. Once deployment shows **Live** (green checkmark), copy the public URL at the top of the service page (e.g., `https://paypilot-ai-access.onrender.com` or `https://paypilot-ai-access-xxxx.onrender.com`).
2. Provide this URL to start Phase 2 automated checks.
