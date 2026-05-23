"""
tools/debugger_tools.py

FIXES:
  1. StackTraceParserTool — logic was INVERTED. The old condition skipped all
     absolute project paths and kept nothing. Now correctly skips site-packages
     and node_modules and keeps everything else.

  2. TerminalTool renamed to UnrestrictedTerminalTool to avoid a name clash with
     backend_tools.TerminalTool (both had tool name "terminal_executor"). The
     debugging_agent uses shared_terminal from backend_tools (allowlisted), so
     this class is only here for reference — it is NOT wired into crew.py.
"""

import re
import os

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from tools.workspace import PROJECT_DIR


# =========================================================
# UNRESTRICTED TERMINAL (debugging only — NOT used in crew.py)
# Kept for completeness; crew.py uses backend_tools.TerminalTool
# which has a command allowlist.
# =========================================================

class UnrestrictedTerminalSchema(BaseModel):
    command: str = Field(
        ...,
        description="The shell command to execute (e.g., 'pytest', 'npm start').",
    )


class UnrestrictedTerminalTool(BaseTool):
    name: str = "unrestricted_terminal_executor"
    description: str = (
        "Executes arbitrary shell commands locally to reproduce errors or test fixes. "
        "WARNING: no allowlist — only use when backend_tools.TerminalTool is insufficient."
    )
    args_schema: type[BaseModel] = UnrestrictedTerminalSchema

    def _run(self, command: str) -> str:
        try:
            import subprocess
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=PROJECT_DIR,
            )
            output = f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            return output if output.strip() else "Command executed successfully with no output."
        except Exception as e:
            return f"Execution failed. Error: {str(e)}"


# =========================================================
# SURGICAL FILE EDITOR
# =========================================================

class FileEditSchema(BaseModel):
    filepath: str = Field(..., description="Target relative file path.")
    search_string: str = Field(
        ...,
        description=(
            "The EXACT existing string block to replace. "
            "Must match the file's content perfectly, including indentation."
        ),
    )
    replace_string: str = Field(..., description="The new string block to insert.")


class FileEditTool(BaseTool):
    name: str = "surgical_file_editor"
    description: str = (
        "Replaces a specific block of code in a file without rewriting the whole file. "
        "Use this for surgical bug fixes."
    )
    args_schema: type[BaseModel] = FileEditSchema

    def _run(self, filepath: str, search_string: str, replace_string: str) -> str:
        try:
            full_path = (PROJECT_DIR / filepath).resolve()
            if not str(full_path).startswith(str(PROJECT_DIR.resolve())):
                return "Blocked: Outside workspace."
            if not os.path.exists(full_path):
                return f"Error: File {filepath} does not exist."

            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()

            if search_string not in content:
                return (
                    "Error: `search_string` not found in the file. "
                    "Check for exact indentation and line breaks."
                )

            updated_content = content.replace(search_string, replace_string, 1)

            with open(full_path, "w", encoding="utf-8") as f:
                f.write(updated_content)

            return f"Successfully updated {filepath}."
        except Exception as e:
            return f"File edit failed. Error: {str(e)}"


# =========================================================
# STACK TRACE PARSER
# FIX: old condition was inverted — it skipped project files and kept
#      nothing useful. Correct logic: skip library paths, keep everything else.
# =========================================================

class StackTraceSchema(BaseModel):
    trace_text: str = Field(..., description="The raw stack trace or error log output.")


class StackTraceParserTool(BaseTool):
    name: str = "stack_trace_parser"
    description: str = (
        "Parses a raw stack trace, extracts referenced files and line numbers, "
        "and returns the surrounding code context."
    )
    args_schema: type[BaseModel] = StackTraceSchema

    def _run(self, trace_text: str) -> str:
        py_pattern = re.compile(r'File "([^"]+)", line (\d+)')
        node_pattern = re.compile(r'at .*? \(([^)]+):(\d+):\d+\)')

        matches = py_pattern.findall(trace_text) + node_pattern.findall(trace_text)

        if not matches:
            return (
                "No local file references found in the stack trace. "
                "The bug might be in a third-party library or standard output."
            )

        context = []
        for filepath, line_num in matches:
            try:
                line_num = int(line_num)

                # FIX: OLD (inverted) logic was:
                #   if filepath.startswith("/") and "site-packages" not in filepath
                #      and "node_modules" not in filepath: continue
                # That skipped ALL project files. Correct: skip library paths only.
                if "site-packages" in filepath or "node_modules" in filepath:
                    continue

                if not os.path.exists(filepath):
                    continue

                with open(filepath, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                start = max(0, line_num - 5)
                end = min(len(lines), line_num + 5)
                snippet = "".join(lines[start:end])

                context.append(
                    f"--- Code Context: {filepath} "
                    f"(Lines {start + 1}-{end}) ---\n{snippet}"
                )
            except Exception:
                continue

        if not context:
            return "Parsed files were inaccessible or out of workspace bounds."

        return "\n\n".join(context)


# =========================================================
# LOG ANALYSIS TOOL
# =========================================================

class LogAnalysisSchema(BaseModel):
    filepath: str = Field(
        default="logs/app.log",
        description="Path to the log file.",
    )
    keyword: str = Field(
        default="ERROR",
        description="Keyword to search for (e.g., 'ERROR', 'CRITICAL', 'Exception').",
    )
    lines: int = Field(
        default=50,
        description="Number of recent lines to extract.",
    )


class LogAnalysisTool(BaseTool):
    name: str = "log_analyzer"
    description: str = (
        "Scans a log file for specific error keywords and returns the most recent matching lines."
    )
    args_schema: type[BaseModel] = LogAnalysisSchema

    def _run(self, filepath: str, keyword: str = "ERROR", lines: int = 50) -> str:
        try:
            # Resolve relative to PROJECT_DIR for safety
            full_path = (PROJECT_DIR / filepath).resolve()
            if not str(full_path).startswith(str(PROJECT_DIR.resolve())):
                return "Blocked: Path outside workspace."
            if not os.path.exists(full_path):
                return f"Error: Log file {filepath} not found."

            with open(full_path, "r", encoding="utf-8") as f:
                all_lines = f.readlines()

            matched_lines = [line for line in all_lines if keyword.lower() in line.lower()]
            recent_matches = matched_lines[-lines:]

            if not recent_matches:
                return f"No logs found containing the keyword '{keyword}'."

            return "".join(recent_matches)
        except Exception as e:
            return f"Log analysis failed. Error: {str(e)}"