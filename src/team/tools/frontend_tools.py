import os
import base64
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

class FileWriteSchema(BaseModel):
    filepath: str = Field(..., description="Target relative file path.")
    content: str = Field(..., description="The complete source code or file text content.")

class FileWriteTool(BaseTool):
    name: str = "file_writer"
    description: str = "Writes or updates source code files in the frontend workspace."
    args_schema: type[BaseModel] = FileWriteSchema

    def _run(self, filepath: str, content: str) -> str:
        try:
            full_path = os.path.abspath(filepath)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Successfully wrote file at {filepath}"
        except Exception as e:
            return f"Failed to write file. Error: {str(e)}"

class BrowserPreviewSchema(BaseModel):
    url: str = Field(..., description="The local or public URL to preview.")

class BrowserPreviewTool(BaseTool):
    name: str = "browser_preview_tool"
    description: str = "Opens a URL in a headless browser, extracts the rendered DOM, text content, and captures browser console errors."
    args_schema: type[BaseModel] = BrowserPreviewSchema

    def _run(self, url: str) -> str:
        try:
            from playwright.sync_api import sync_playwright
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
                return f"CONSOLE LOGS:\n{formatted_logs}\n\nRENDERED TEXT:\n{text_content[:2000]}"
        except Exception as e:
            return f"Browser preview failed. Error: {str(e)}"

class ScreenshotAnalysisSchema(BaseModel):
    url: str = Field(..., description="The URL to capture and analyze.")
    instructions: str = Field(..., description="Specific UI/UX aspects to analyze.")

class ScreenshotAnalysisTool(BaseTool):
    name: str = "screenshot_analysis_tool"
    description: str = "Takes a screenshot of the UI and uses Vision AI to analyze layout, styling, and accessibility."
    args_schema: type[BaseModel] = ScreenshotAnalysisSchema

    def _run(self, url: str, instructions: str) -> str:
        try:
            from playwright.sync_api import sync_playwright
            from openai import OpenAI
            
            os.makedirs("./docs/screenshots", exist_ok=True)
            safe_url = url.replace("http://", "").replace("https://", "").replace(":", "_").replace("/", "_")
            filepath = f"./docs/screenshots/ui_{safe_url}.png"
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, wait_until="networkidle", timeout=15000)
                page.screenshot(path=filepath, full_page=True)
                browser.close()
            
            client = OpenAI()
            
            with open(filepath, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": f"Analyze this UI screenshot: {instructions}"},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                        ]
                    }
                ],
                max_tokens=500
            )
            
            analysis = response.choices[0].message.content
            return f"Screenshot saved to {filepath}.\n\nUI ANALYSIS:\n{analysis}"
            
        except Exception as e:
            return f"Screenshot analysis failed. Error: {str(e)}"