import os
import subprocess
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

class FileWriteSchema(BaseModel):
    filepath: str = Field(..., description="Target relative file path (e.g., 'app/models/user.py').")
    content: str = Field(..., description="The complete source code or file text content.")

class FileWriteTool(BaseTool):
    name: str = "file_writer"
    description: str = "Writes or updates source code files in the local workspace directory structure."
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

class TerminalExecuteSchema(BaseModel):
    command: str = Field(..., description="The shell command to execute (e.g., 'pytest', 'alembic upgrade head').")

class TerminalTool(BaseTool):
    name: str = "terminal_executor"
    description: str = "Executes arbitrary shell commands locally within the project workspace environment and returns stdout/stderr."
    args_schema: type[BaseModel] = TerminalExecuteSchema

    def _run(self, command: str) -> str:
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            output = f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            return output if output.strip() else "Command executed successfully with no output."
        except subprocess.TimeoutExpired:
            return "Command execution timed out after 30 seconds."
        except Exception as e:
            return f"Execution failed. Error: {str(e)}"

class DockerCommandSchema(BaseModel):
    action: str = Field(..., description="The exact docker or docker-compose command sequence (e.g., 'docker build -t backend .').")

class DockerTool(BaseTool):
    name: str = "docker_manager"
    description: str = "Handles containerization tasks, container building, orchestration steps, and status checks."
    args_schema: type[BaseModel] = DockerCommandSchema

    def _run(self, action: str) -> str:
        if not action.strip().startswith(("docker", "docker-compose")):
            return "Error: This tool only accepts commands beginning with 'docker' or 'docker-compose'."
        try:
            result = subprocess.run(action, shell=True, capture_output=True, text=True, timeout=60)
            return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        except Exception as e:
            return f"Docker operation failed. Error: {str(e)}"

class GithubCommandSchema(BaseModel):
    git_command: str = Field(..., description="The precise local git subcommand string (e.g., 'git add .', 'git commit -m \"feat: backend authentication\"').")

class GithubTool(BaseTool):
    name: str = "github_workflow_tool"
    description: str = "Manages source control pipelines, local staging, commits, and branch transitions."
    args_schema: type[BaseModel] = GithubCommandSchema

    def _run(self, git_command: str) -> str:
        if not git_command.strip().startswith("git"):
            return "Error: This tool only executes valid 'git' command inputs."
        try:
            result = subprocess.run(git_command, shell=True, capture_output=True, text=True, timeout=20)
            return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        except Exception as e:
            return f"Git operation failed. Error: {str(e)}"