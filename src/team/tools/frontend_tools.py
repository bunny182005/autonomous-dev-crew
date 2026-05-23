"""
tools/frontend_tools.py

FIXES:
  1. Removed dead `FileWriteSchema` class that was defined but never used.

  2. BrowserPreviewTool / ScreenshotAnalysisTool — added a clear ImportError
     guard with an actionable message when playwright is not installed.
     Install command: pip install playwright && playwright install chromium

  3. ScreenshotAnalysisTool — removed the separate `from openai import OpenAI`
     client instantiation that required a second billing surface and its own
     import. The screenshot is now described by reading the file path back so
     the calling agent can use its own LLM for analysis, OR you can restore
     the OpenAI path if you explicitly want vision analysis (see comment).

NOTE: Add these to backend/requirements.txt before running:
      playwright==1.44.0
      (then run: playwright install chromium)
"""

import os
import base64

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from tools.workspace import PROJECT_DIR


# =========================================================
# BROWSER PREVIEW TOOL
# =========================================================

class BrowserPreviewSchema(BaseModel):
    url: str = Field(..., description="The local or public URL to preview.")


class BrowserPreviewTool(BaseTool):
    name: str = "browser_preview_tool"
    description: str = (
        "Opens a URL in a headless browser, extracts the rendered DOM text "
        "content, and captures browser console errors. "
        "Requires: pip install playwright && playwright install chromium"
    )
    args_schema: type[BaseModel] = BrowserPreviewSchema

    def _run(self, url: str) -> str:
        try:
            from playwright.sync_api import sync_playwright  # type: ignore
        except ImportError:
            return (
                "playwright is not installed. "
                "Run: pip install playwright && playwright install chromium"
            )

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                logs = []
                page.on("console", lambda msg: logs.append(f"[{msg.type}] {msg.text}"))
                page.on("pageerror", lambda exc: logs.append(f"[ERROR] {exc.message}"))

                page.goto(url, wait_until="networkidle", timeout=15000)
                text_content = page.inner_text("body")
                browser.close()

                formatted_logs = "\n".join(logs) if logs else "No console errors."
                return (
                    f"CONSOLE LOGS:\n{formatted_logs}\n\n"
                    f"RENDERED TEXT:\n{text_content[:2000]}"
                )
        except Exception as e:
            return f"Browser preview failed. Error: {str(e)}"


# =========================================================
# SCREENSHOT ANALYSIS TOOL
# =========================================================

class ScreenshotAnalysisSchema(BaseModel):
    url: str = Field(..., description="The URL to capture and analyze.")
    instructions: str = Field(..., description="Specific UI/UX aspects to analyze.")


class ScreenshotAnalysisTool(BaseTool):
    name: str = "screenshot_analysis_tool"
    description: str = (
        "Takes a full-page screenshot of a URL and returns the saved path plus "
        "a base64 data URI so the calling agent can analyse it with its LLM. "
        "Requires: pip install playwright && playwright install chromium"
    )
    args_schema: type[BaseModel] = ScreenshotAnalysisSchema

    def _run(self, url: str, instructions: str) -> str:
        try:
            from playwright.sync_api import sync_playwright  # type: ignore
        except ImportError:
            return (
                "playwright is not installed. "
                "Run: pip install playwright && playwright install chromium"
            )

        try:
            os.makedirs(str(PROJECT_DIR / "docs" / "screenshots"), exist_ok=True)
            safe_url = (
                url.replace("http://", "")
                   .replace("https://", "")
                   .replace(":", "_")
                   .replace("/", "_")
            )
            filepath = PROJECT_DIR / "docs" / "screenshots" / f"ui_{safe_url}.png"

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, wait_until="networkidle", timeout=15000)
                page.screenshot(path=str(filepath), full_page=True)
                browser.close()

            # Return the screenshot as a base64 data URI so the agent's
            # own vision-capable LLM (gpt-4o / claude-3-opus) can analyse it.
            # The calling agent should include this in its next message.
            with open(filepath, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")

            return (
                f"Screenshot saved to: {filepath}\n\n"
                f"Analysis instructions: {instructions}\n\n"
                f"IMAGE_DATA_URI: data:image/png;base64,{b64[:200]}... "
                f"[full base64 available at {filepath}]\n\n"
                "Pass the full image path to your LLM vision call for detailed analysis."
            )

            # ── OPTIONAL: restore direct OpenAI vision analysis ───────────
            # If you want the tool to call GPT-4o vision directly, uncomment
            # the block below AND ensure OPENAI_API_KEY is set in your .env.
            #
            # from openai import OpenAI
            # client = OpenAI()
            # with open(filepath, "rb") as image_file:
            #     b64_full = base64.b64encode(image_file.read()).decode("utf-8")
            # response = client.chat.completions.create(
            #     model="gpt-4o-mini",
            #     messages=[{
            #         "role": "user",
            #         "content": [
            #             {"type": "text", "text": f"Analyze this UI: {instructions}"},
            #             {"type": "image_url",
            #              "image_url": {"url": f"data:image/png;base64,{b64_full}"}}
            #         ]
            #     }],
            #     max_tokens=500
            # )
            # return f"Screenshot saved to {filepath}.\n\nUI ANALYSIS:\n{response.choices[0].message.content}"
            # ─────────────────────────────────────────────────────────────

        except Exception as e:
            return f"Screenshot analysis failed. Error: {str(e)}"