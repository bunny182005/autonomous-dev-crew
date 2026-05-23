"""
tools/devops_tools.py — FIXED

Key fix: DockerManagerTool timeout raised from 60s → 600s (10 min).
A multi-stage Python + React Docker build reliably exceeds 60 seconds.
"""

import os
import subprocess
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from tools.workspace import PROJECT_DIR


class DockerCommandSchema(BaseModel):
    command: str = Field(
        ...,
        description=(
            "The exact docker or docker-compose command to run "
            "(e.g., 'docker compose up --build -d', "
            "'docker compose build --no-cache backend', "
            "'docker compose logs -f'). Must start with 'docker'."
        ),
    )


class DockerManagerTool(BaseTool):
    name: str = "docker_orchestrator"
    description: str = (
        "Manages application containerization, image builds, and service orchestration. "
        "Use for: docker compose build, up, down, logs, ps, exec."
    )
    args_schema: type[BaseModel] = DockerCommandSchema

    def _run(self, command: str) -> str:
        if not command.strip().startswith(("docker", "docker-compose")):
            return "Error: Only 'docker' or 'docker-compose' commands are accepted."
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=600,  # ← FIXED: was 60s. Docker builds need up to 10 min.
                cwd=PROJECT_DIR,
            )
            output = f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}\nRETURN CODE: {result.returncode}"
            return output if output.strip() else "Command executed with no output."
        except subprocess.TimeoutExpired:
            return (
                "Timeout: Docker operation exceeded 10 minutes. "
                "Try 'docker compose build --no-cache' for a clean build, "
                "or check that base images are accessible."
            )
        except Exception as e:
            return f"DockerManagerTool failed: {str(e)}"


class GABlueprintSchema(BaseModel):
    filepath: str = Field(
        ...,
        description="Relative path to the GitHub Actions YAML file (e.g., '.github/workflows/ci.yml').",
    )


class GitHubActionsValidatorTool(BaseTool):
    name: str = "github_actions_validator"
    description: str = (
        "Validates a GitHub Actions YAML workflow file for structural correctness "
        "(has 'on' trigger and 'jobs' block)."
    )
    args_schema: type[BaseModel] = GABlueprintSchema

    def _run(self, filepath: str) -> str:
        try:
            import yaml

            full_path = (PROJECT_DIR / filepath).resolve()
            if not str(full_path).startswith(str(PROJECT_DIR.resolve())):
                return "Blocked: Path outside workspace."
            if not full_path.exists():
                return f"Validation Failed: File not found at {filepath}"

            with open(full_path, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)

            if not config_data or not isinstance(config_data, dict):
                return "Validation Failed: Empty or non-dict YAML."
            if "on" not in config_data or "jobs" not in config_data:
                return (
                    "Validation Failed: Missing 'on' trigger or 'jobs' block. "
                    "Both are required for a valid GitHub Actions workflow."
                )

            job_names = list(config_data["jobs"].keys())
            return (
                f"Validation Passed: {filepath}\n"
                f"Jobs defined: {', '.join(job_names)}"
            )
        except Exception as e:
            return f"Validation error: {str(e)}"


class K8sManifestSchema(BaseModel):
    manifest_path: str = Field(
        ...,
        description="Path to the Kubernetes manifest file (e.g., 'k8s/deployment.yaml').",
    )


class KubernetesManifestTool(BaseTool):
    name: str = "kubernetes_manifest_analyzer"
    description: str = (
        "Analyzes Kubernetes manifest files for structural correctness and "
        "missing health/readiness probes."
    )
    args_schema: type[BaseModel] = K8sManifestSchema

    def _run(self, manifest_path: str) -> str:
        try:
            import yaml

            full_path = (PROJECT_DIR / manifest_path).resolve()
            if not str(full_path).startswith(str(PROJECT_DIR.resolve())):
                return "Blocked: Path outside workspace."
            if not full_path.exists():
                return f"File not found: {manifest_path}"

            with open(full_path, "r", encoding="utf-8") as f:
                manifests = list(yaml.safe_load_all(f))

            summary = []
            for idx, doc in enumerate(manifests):
                if not doc:
                    continue
                kind = doc.get("kind", "Unknown")
                name = doc.get("metadata", {}).get("name", "unnamed")
                probe_status = "OK"

                if kind.lower() == "deployment":
                    containers = (
                        doc.get("spec", {})
                        .get("template", {})
                        .get("spec", {})
                        .get("containers", [])
                    )
                    for c in containers:
                        if not c.get("livenessProbe") or not c.get("readinessProbe"):
                            probe_status = "WARNING: Missing liveness/readiness probes"

                summary.append(f"[{idx+1}] {kind}/{name} — probes: {probe_status}")

            return "MANIFEST ANALYSIS:\n" + "\n".join(summary)
        except Exception as e:
            return f"KubernetesManifestTool failed: {str(e)}"