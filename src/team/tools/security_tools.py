import os
import re
import subprocess
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

class CodeSecurityScannerSchema(BaseModel):
    target_dir: str = Field(
        default=".", 
        description="The directory containing the Python source code to scan (e.g., 'app' or 'src')."
    )

class CodeSecurityScannerTool(BaseTool):
    name: str = "owasp_code_scanner"
    description: str = "Runs a Static Application Security Testing (SAST) scan using Bandit to find common OWASP vulnerabilities in Python code."
    args_schema: type[BaseModel] = CodeSecurityScannerSchema

    def _run(self, target_dir: str = ".") -> str:
        try:
            # -ll means report only Medium and High severity issues (saves tokens)
            # -i means ignore tests with nosec
            command = f"bandit -r {target_dir} -ll -i"
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
            
            output = result.stdout if result.stdout.strip() else result.stderr
            
            # Truncate if output is massively long to save LLM context
            if len(output) > 3000:
                output = output[:3000] + "\n...[TRUNCATED due to length. Focus on these top issues first]."
                
            return f"SAST SCAN RESULTS:\n{output}"
        except Exception as e:
            return f"Code security scan failed. Error: {str(e)}"

class DependencyScannerSchema(BaseModel):
    ecosystem: str = Field(
        ..., 
        description="Specify 'python' to audit requirements.txt or 'node' to audit package.json."
    )

class DependencyScannerTool(BaseTool):
    name: str = "dependency_vulnerability_scanner"
    description: str = "Audits project dependencies against known CVE databases to find vulnerable libraries."
    args_schema: type[BaseModel] = DependencyScannerSchema

    def _run(self, ecosystem: str) -> str:
        try:
            if ecosystem.lower() == "python":
                command = "pip-audit"
            elif ecosystem.lower() == "node":
                command = "npm audit --audit-level=high"
            else:
                return "Error: Unsupported ecosystem. Use 'python' or 'node'."

            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
            output = result.stdout if result.stdout.strip() else result.stderr
            
            if len(output) > 3000:
                output = output[:3000] + "\n...[TRUNCATED]."
                
            return f"DEPENDENCY AUDIT RESULTS:\n{output}"
        except Exception as e:
            return f"Dependency scan failed. Error: {str(e)}"

class SecretsDetectionSchema(BaseModel):
    target_dir: str = Field(default=".", description="The directory to recursively scan for hardcoded secrets.")

class SecretsDetectionTool(BaseTool):
    name: str = "secrets_detection_tool"
    description: str = "Scans codebase files for exposed API keys, JWT secrets, AWS credentials, and hardcoded passwords."
    args_schema: type[BaseModel] = SecretsDetectionSchema

    def _run(self, target_dir: str = ".") -> str:
        # High-signal Regex patterns for common secrets
        patterns = {
            "AWS Access Key": r"AKIA[0-9A-Z]{16}",
            "RSA Private Key": r"-----BEGIN RSA PRIVATE KEY-----",
            "Generic API Key / Secret": r"(?i)(secret|password|token|api[_-]?key).{0,5}[:=].{0,5}[\"'][a-zA-Z0-9\-_]{16,}[\"']"
        }
        
        ignore_dirs = {".git", "node_modules", "venv", "__pycache__", ".env"}
        findings = []

        try:
            for root, dirs, files in os.walk(target_dir):
                dirs[:] = [d for d in dirs if d not in ignore_dirs]
                
                for file in files:
                    # Skip common binary/asset files
                    if file.endswith(('.png', '.jpg', '.pyc', '.pdf')):
                        continue
                        
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            lines = f.readlines()
                            
                        for line_num, line in enumerate(lines, 1):
                            for secret_type, pattern in patterns.items():
                                if re.search(pattern, line):
                                    # We don't print the actual secret, just the fact it exists, to keep logs safe
                                    findings.append(f"- Found potential {secret_type} in {filepath} (Line {line_num})")
                    except Exception:
                        pass # Ignore encoding errors for non-text files
                        
            if not findings:
                return "SECRETS SCAN: No hardcoded secrets detected in the codebase."
                
            return "SECRETS SCAN RESULTS:\n" + "\n".join(findings)
        except Exception as e:
            return f"Secrets detection failed. Error: {str(e)}"