import os
import subprocess
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

class DockerCommandSchema(BaseModel):
    command: str = Field(..., description="The exact docker or docker-compose execution string (e.g., 'docker build -t app:latest .', 'docker compose up -d').")

class DockerManagerTool(BaseTool):
    name: str = "docker_orchestrator"
    description: str = "Manages application containerization, local image building, multi-stage orchestration, and verification testing."
    args_schema: type[BaseModel] = DockerCommandSchema

    def _run(self, command: str) -> str:
        # Strict enforcement block to prevent unintended escape queries
        if not command.strip().startswith(("docker", "docker-compose")):
            return "Error: Protection boundary tripped. This tool only accepts valid 'docker' or 'docker-compose' commands."
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
            output = f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            return output if output.strip() else "Container command executed successfully with no trailing terminal output."
        except subprocess.TimeoutExpired:
            return "Execution Error: Container operation timed out after 60 seconds."
        except Exception as e:
            return f"System Failure executing container commands. Details: {str(e)}"

class GABlueprintSchema(BaseModel):
    filepath: str = Field(..., description="Relative file path to the target CI/CD workflow file (e.g., '.github/workflows/ci.yml').")

class GitHubActionsValidatorTool(BaseTool):
    name: str = "github_actions_validator"
    description: str = "Inspects and validates local GitHub Actions YAML files for structural correctness and structural pipeline configurations."
    args_schema: type[BaseModel] = GABlueprintSchema

    def _run(self, filepath: str) -> str:
        try:
            import yaml  # Leverages PyYAML (guaranteed core dependency in CrewAI ecosystems)
            full_path = os.path.abspath(filepath)
            if not os.path.exists(full_path):
                return f"Validation Failed: Configuration file not found at location: {filepath}"
                
            with open(full_path, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)
                
            # Basic schema rule execution for quick validation mapping
            if not config_data or not isinstance(config_data, dict):
                return "Validation Failed: Document is empty or not formatted as a standard dictionary payload."
            if "on" not in config_data or "jobs" not in config_data:
                return "Validation Failed: Invalid GitHub Actions structure. Missing foundational root structural blocks ('on' trigger matrix or 'jobs' execution matrix)."
                
            return f"Validation Success: YAML layout schema for workflow target [{filepath}] structural blocks are correct."
        except yaml.YAMLError as exc:
            return f"Validation Failed: Invalid YAML syntax block configuration parsed.\nDetails: {str(exc)}"
        except Exception as e:
            return f"Validation Error running structural asset assessment. Details: {str(e)}"

class K8sManifestSchema(BaseModel):
    manifest_path: str = Field(..., description="Target path pointing to the local Kubernetes deployment manifest file (e.g., 'k8s/deployment.yml').")

class KubernetesManifestTool(BaseTool):
    name: str = "kubernetes_manifest_analyzer"
    description: str = "Analyzes, verifies structural design conventions, and runs dry-run evaluations on Kubernetes resource files."
    args_schema: type[BaseModel] = K8sManifestSchema

    def _run(self, manifest_path: str) -> str:
        try:
            import yaml
            full_path = os.path.abspath(manifest_path)
            if not os.path.exists(full_path):
                return f"Analysis Failed: Kubernetes asset target missing at path: {manifest_path}"
                
            with open(full_path, "r", encoding="utf-8") as f:
                manifests = list(yaml.safe_load_all(f))
                
            summary = []
            for idx, doc in enumerate(manifests):
                if not doc: continue
                kind = doc.get("kind", "Unknown Kind")
                api_version = doc.get("apiVersion", "Unknown Version")
                metadata = doc.get("metadata", {})
                name = metadata.get("name", "Unnamed Resource")
                
                # Check for standard liveness/readiness probes on deployments
                probe_status = "Checked"
                if kind.lower() == "deployment":
                    containers = doc.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [])
                    for c in containers:
                        if not c.get("livenessProbe") or not c.get("readinessProbe"):
                            probe_status = "WARNING: Missing production health/readiness probe arrays on container block."
                
                summary.append(f"Document [{idx+1}] -> Kind: {kind} | Name: {name} | API: {api_version} | Probes: {probe_status}")
            
            # Subprocess validation check fallback option if user environment runs local kubectl engines
            try:
                cli_check = subprocess.run(f"kubectl apply --dry-run=client -f {manifest_path}", shell=True, capture_output=True, text=True, timeout=10)
                if cli_check.returncode == 0:
                    summary.append("\nLocal Engine Check: kubectl client validation confirms structural integrity.")
                elif "not found" not in cli_check.stderr.lower():
                    summary.append(f"\nLocal Engine Warning: kubectl flags compilation failure.\n{cli_check.stderr}")
            except Exception:
                pass # Gracefully skip if local system environment lacks a global kubectl binary
                
            return "MANIFEST PERFORMANCE READOUT:\n" + "\n".join(summary)
        except yaml.YAMLError as exc:
            return f"Analysis Failed: Broken multi-document YAML syntax mapped inside manifest path.\nDetails: {str(exc)}"
        except Exception as e:
            return f"Analysis aborted unexpectedly. Details: {str(e)}"