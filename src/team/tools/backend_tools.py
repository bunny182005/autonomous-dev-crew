"""
tools/backend_tools.py

FileWriteTool  — safe file writer (blocks path traversal and generated_project/)
TerminalTool   — safe command executor (allowlist-based)
DockerTool     — Docker command runner (10-min timeout for builds)
GithubTool     — safe git executor
"""

import subprocess

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import ClassVar

from tools.workspace import PROJECT_DIR


# =========================================================
# SAFE FILE WRITE TOOL
# =========================================================

class FileWriteSchema(BaseModel):
    filepath: str = Field(
        ...,
        description=(
            "Relative path inside the workspace (e.g., 'backend/app/main.py', "
            "'frontend/src/App.tsx'). Never use 'generated_project/' in paths."
        ),
    )
    content: str = Field(..., description="Complete file content to write.")


class FileWriteTool(BaseTool):
    name: str = "file_writer"
    description: str = (
        "Safely writes files ONLY inside the workspace. "
        "Use relative paths like 'backend/app/main.py'. "
        "Never prefix paths with 'generated_project/'."
    )
    args_schema: type[BaseModel] = FileWriteSchema

    def _run(self, filepath: str, content: str) -> str:
        try:
            safe_filepath = filepath.strip().lstrip("/\\")

            # Reject forbidden path segments
            forbidden = ["generated_project", "../", "..\\"]
            for item in forbidden:
                if item in safe_filepath:
                    return (
                        f"BLOCKED: Path contains forbidden segment '{item}'. "
                        f"Use a direct relative path instead (e.g., 'backend/app/main.py')."
                    )

            full_path = (PROJECT_DIR / safe_filepath).resolve()

            # Guard against traversal outside workspace
            if not str(full_path).startswith(str(PROJECT_DIR.resolve())):
                return "BLOCKED: Path traversal outside workspace detected."

            full_path.parent.mkdir(parents=True, exist_ok=True)

            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

            return f"SUCCESS: {full_path}"

        except Exception as e:
            return f"FileWriteTool failed: {str(e)}"


# =========================================================
# SAFE TERMINAL TOOL
# =========================================================

class TerminalExecuteSchema(BaseModel):
    command: str = Field(
        ...,
        description=(
            "Shell command to run inside the workspace. "
            "Must start with an allowed prefix: pytest, pip, uvicorn, npm, "
            "python, alembic, docker compose, docker-compose, npx, node."
        ),
    )


class TerminalTool(BaseTool):
    name: str = "terminal_executor"
    description: str = (
        "Executes safe shell commands inside the workspace. "
        "Allowed: pytest, pip install, uvicorn, npm, npx, python, alembic, docker compose."
    )
    args_schema: type[BaseModel] = TerminalExecuteSchema

    ALLOWED_COMMANDS: ClassVar[list[str]] = [
        "pytest",
        "pip",
        "uvicorn",
        "npm",
        "npx",
        "node",
        "python",
        "alembic",
        "docker compose",
        "docker-compose",
    ]

    BLOCKED_COMMANDS: ClassVar[list[str]] = [
        "rm -rf",
        "sudo",
        "shutdown",
        "reboot",
        "mkfs",
        "dd if=",
        "chmod 777",
        "curl | sh",
        "wget | sh",
    ]

    def _run(self, command: str) -> str:
        try:
            command = command.strip()

            for blocked in self.BLOCKED_COMMANDS:
                if blocked in command:
                    return f"BLOCKED: Dangerous pattern '{blocked}' detected."

            if not any(command.startswith(cmd) for cmd in self.ALLOWED_COMMANDS):
                return (
                    f"BLOCKED: Command not in allowlist.\n"
                    f"Received: {command}\n"
                    f"Allowed prefixes: {', '.join(self.ALLOWED_COMMANDS)}"
                )

            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=PROJECT_DIR,
                timeout=120,  # 2 min — enough for pip install
            )

            return (
                f"COMMAND: {command}\n\n"
                f"STDOUT:\n{result.stdout}\n\n"
                f"STDERR:\n{result.stderr}\n\n"
                f"RETURN CODE: {result.returncode}"
            )

        except subprocess.TimeoutExpired:
            return f"TIMEOUT: '{command}' exceeded 120 seconds."
        except Exception as e:
            return f"TerminalTool failed: {str(e)}"


# =========================================================
# SAFE DOCKER TOOL
# =========================================================

class DockerCommandSchema(BaseModel):
    action: str = Field(
        ...,
        description=(
            "Docker command to run (e.g., 'docker compose up --build -d', "
            "'docker compose build --no-cache', 'docker compose logs backend'). "
            "Must start with 'docker' or 'docker-compose'."
        ),
    )


class DockerTool(BaseTool):
    name: str = "docker_manager"
    description: str = (
        "Runs Docker and Docker Compose commands inside the workspace. "
        "Use for building images, starting/stopping services, and viewing logs."
    )
    args_schema: type[BaseModel] = DockerCommandSchema

    def _run(self, action: str) -> str:
        try:
            action = action.strip()

            if not action.startswith(("docker", "docker-compose")):
                return "BLOCKED: Only 'docker' or 'docker-compose' commands are allowed."

            result = subprocess.run(
                action,
                shell=True,
                capture_output=True,
                text=True,
                cwd=PROJECT_DIR,
                timeout=600,  # ← FIXED: 10 minutes for docker build (was 60s/120s)
            )

            return (
                f"STDOUT:\n{result.stdout}\n\n"
                f"STDERR:\n{result.stderr}\n\n"
                f"RETURN CODE: {result.returncode}"
            )

        except subprocess.TimeoutExpired:
            return (
                "TIMEOUT: Docker operation exceeded 10 minutes. "
                "Consider splitting the build into smaller stages or using --no-cache."
            )
        except Exception as e:
            return f"DockerTool failed: {str(e)}"


# =========================================================
# SAFE GIT TOOL
# =========================================================

class GithubCommandSchema(BaseModel):
    git_command: str = Field(
        ...,
        description=(
            "Git command to run. Allowed: git init, git status, git add, "
            "git commit, git branch, git log."
        ),
    )


class GithubTool(BaseTool):
    name: str = "github_workflow_tool"
    description: str = (
        "Runs safe, read-only or initialization Git commands inside the workspace."
    )
    args_schema: type[BaseModel] = GithubCommandSchema

    ALLOWED_GIT: ClassVar[list[str]] = [
        "git init",
        "git status",
        "git add",
        "git commit",
        "git branch",
        "git log",
    ]

    def _run(self, git_command: str) -> str:
        try:
            git_command = git_command.strip()

            if not any(git_command.startswith(cmd) for cmd in self.ALLOWED_GIT):
                return (
                    f"BLOCKED: Git command not in allowlist.\n"
                    f"Allowed: {', '.join(self.ALLOWED_GIT)}"
                )

            result = subprocess.run(
                git_command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=PROJECT_DIR,
                timeout=30,
            )

            return (
                f"STDOUT:\n{result.stdout}\n\n"
                f"STDERR:\n{result.stderr}"
            )

        except Exception as e:
            return f"GithubTool failed: {str(e)}"