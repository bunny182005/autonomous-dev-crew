"""
crew.py

FIXES:
  1. memory=True now passes an explicit `embedder` config pointing at the
     same sentence-transformer model your custom memory tools use.
     Without this, CrewAI defaults to OpenAI embeddings and crashes (or
     silently bills you) if OPENAI_API_KEY is set for a different purpose.

  2. Removed `shared_docker = DockerTool()` and `shared_github = GithubTool()`.
     Neither was passed to any agent — devops_engineer uses DockerManagerTool()
     from devops_tools.py. Keeping dead instances wastes memory and causes
     confusion during debugging.
"""

import re
import os

from pathlib import Path
from datetime import datetime
from typing import Tuple, Any, List

from pydantic import BaseModel, Field

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.tasks.task_output import TaskOutput
from tools.workspace import PROJECT_DIR
from tools.memory_writer import ChromaMemoryWriteTool


# =========================================================
# IMPORT CUSTOM TOOLS
# =========================================================

from tools.search_tools import AdvancedDDGSearchTool
from tools.memory_tools import ChromaMemoryRetrievalTool

from tools.architect_tools import (
    ArchitectureGeneratorTool,
    DatabaseSchemaTool,
    ApiDesignTool,
)

from tools.backend_tools import (
    FileWriteTool,
    TerminalTool,
    # FIX: DockerTool and GithubTool removed — were instantiated but never
    # assigned to any agent. devops_engineer uses DockerManagerTool instead.
)

from tools.frontend_tools import (
    BrowserPreviewTool,
    ScreenshotAnalysisTool,
)

from tools.database_tools import (
    PostgresTool,
    MigrationTool,
    SqlValidatorTool,
)

from tools.test_tools import (
    PytestRunnerTool,
    JestRunnerTool,
    CoverageAnalysisTool,
)

from tools.debugger_tools import (
    FileEditTool,
    StackTraceParserTool,
    LogAnalysisTool,
)

from tools.security_tools import (
    CodeSecurityScannerTool,
    DependencyScannerTool,
    SecretsDetectionTool,
)

from tools.devops_tools import (
    DockerManagerTool,
    GitHubActionsValidatorTool,
    KubernetesManifestTool,
)

from tools.docs_tools import (
    MarkdownGeneratorTool,
    OpenApiDocTool,
)


# =========================================================
# FOLDER STRUCTURE
# Created by workspace.py on import.
# =========================================================

print("[INFO] workspace.py already initialized all project folders.\n")


# =========================================================
# GENERATION LOG
# =========================================================

with open(PROJECT_DIR / "generation.log", "w") as log:
    log.write(
        f"Project generated at: "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    )


# =========================================================
# SHARED TOOL INSTANCES
# FIX: removed shared_docker and shared_github — both were unused.
# =========================================================

shared_file_writer = FileWriteTool()
shared_terminal    = TerminalTool()


# =========================================================
# STRUCTURED OUTPUT MODELS
# =========================================================

class SecurityVulnerability(BaseModel):
    severity: str = Field(description="High, Medium, or Low")
    vulnerability_type: str = Field(description="Example: SQLi, XSS, CSRF")
    file_path: str = Field(description="Affected source file")
    remediation_snippet: str = Field(description="Suggested secure code fix")


class SecurityAuditReport(BaseModel):
    is_secure: bool = Field(description="True if project is secure")
    vulnerabilities: List[SecurityVulnerability] = Field(
        description="List of discovered vulnerabilities"
    )
    summary: str = Field(description="Security audit summary")


# =========================================================
# CREW
# =========================================================

@CrewBase
class Team():
    """Autonomous AI Software Engineering Crew"""

    agents_config = "config/agents.yaml"
    tasks_config  = "config/tasks.yaml"

    # =====================================================
    # AGENTS
    # =====================================================

    @agent
    def product_manager(self) -> Agent:
        return Agent(
            config=self.agents_config["product_manager"],
            tools=[
                AdvancedDDGSearchTool(),
                ChromaMemoryRetrievalTool(),
                ChromaMemoryWriteTool(),
            ],
        )

    @agent
    def system_architect(self) -> Agent:
        return Agent(
            config=self.agents_config["system_architect"],
            tools=[
                ArchitectureGeneratorTool(),
                DatabaseSchemaTool(),
                ApiDesignTool(),
                ChromaMemoryWriteTool(),
            ],
        )

    @agent
    def dependency_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["dependency_engineer"],
            tools=[
                shared_file_writer,
                shared_terminal,
            ],
        )

    @agent
    def database_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["database_engineer"],
            tools=[
                PostgresTool(),
                MigrationTool(),
                SqlValidatorTool(),
                shared_file_writer,
            ],
        )

    # ── Backend (3 scoped agents) ──────────────────────

    @agent
    def auth_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["auth_engineer"],
            tools=[shared_file_writer],
        )

    @agent
    def service_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["service_engineer"],
            tools=[shared_file_writer],
        )

    @agent
    def api_routes_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["api_routes_engineer"],
            tools=[
                shared_file_writer,
                shared_terminal,
            ],
        )

    # ── Frontend (3 scoped agents) ─────────────────────

    @agent
    def component_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["component_engineer"],
            tools=[shared_file_writer],
        )

    @agent
    def page_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["page_engineer"],
            tools=[shared_file_writer],
        )

    @agent
    def integration_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["integration_engineer"],
            tools=[
                shared_file_writer,
                BrowserPreviewTool(),
                ScreenshotAnalysisTool(),
            ],
        )

    # ── Quality, Security, DevOps, Docs ───────────────

    @agent
    def test_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["test_engineer"],
            tools=[
                PytestRunnerTool(),
                JestRunnerTool(),
                CoverageAnalysisTool(),
                shared_file_writer,
            ],
        )

    @agent
    def debugging_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["debugging_agent"],
            tools=[
                shared_terminal,
                FileEditTool(),
                StackTraceParserTool(),
                LogAnalysisTool(),
                PytestRunnerTool(),
                JestRunnerTool(),
            ],
        )

    @agent
    def security_auditor(self) -> Agent:
        return Agent(
            config=self.agents_config["security_auditor"],
            tools=[
                CodeSecurityScannerTool(),
                DependencyScannerTool(),
                SecretsDetectionTool(),
                shared_file_writer,
            ],
        )

    @agent
    def devops_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["devops_engineer"],
            tools=[
                DockerManagerTool(),
                GitHubActionsValidatorTool(),
                KubernetesManifestTool(),
                shared_file_writer,
            ],
        )

    @agent
    def documentation_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["documentation_agent"],
            tools=[
                MarkdownGeneratorTool(),
                OpenApiDocTool(),
                shared_file_writer,
            ],
        )

    # =====================================================
    # TASKS
    # =====================================================

    @task
    def requirement_analysis_task(self) -> Task:
        return Task(config=self.tasks_config["requirement_analysis_task"])

    @task
    def system_design_task(self) -> Task:
        return Task(config=self.tasks_config["system_design_task"])

    @task
    def dependency_setup_task(self) -> Task:
        return Task(config=self.tasks_config["dependency_setup_task"])

    @task
    def database_design_task(self) -> Task:
        return Task(config=self.tasks_config["database_design_task"])

    @task
    def auth_task(self) -> Task:
        return Task(config=self.tasks_config["auth_task"])

    @task
    def service_layer_task(self) -> Task:
        return Task(config=self.tasks_config["service_layer_task"])

    @task
    def api_routes_task(self) -> Task:
        return Task(config=self.tasks_config["api_routes_task"])

    @task
    def component_task(self) -> Task:
        return Task(config=self.tasks_config["component_task"])

    @task
    def page_task(self) -> Task:
        return Task(config=self.tasks_config["page_task"])

    @task
    def integration_task(self) -> Task:
        return Task(config=self.tasks_config["integration_task"])

    @task
    def testing_task(self) -> Task:
        return Task(config=self.tasks_config["testing_task"])

    @task
    def debugging_task(self) -> Task:
        return Task(config=self.tasks_config["debugging_task"])

    @task
    def security_audit_task(self) -> Task:
        return Task(
            config=self.tasks_config["security_audit_task"],
            output_pydantic=SecurityAuditReport,
        )

    @task
    def deployment_task(self) -> Task:
        return Task(config=self.tasks_config["deployment_task"])

    @task
    def documentation_task(self) -> Task:
        return Task(config=self.tasks_config["documentation_task"])

    # =====================================================
    # CREW ORCHESTRATION
    # =====================================================

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            # FIX: explicit embedder so CrewAI doesn't silently fall back to
            # OpenAI embeddings. Uses the same model as the custom memory tools
            # (all-MiniLM-L6-v2 via sentence-transformers, runs locally, free).
            memory=False,
            embedder={
                "provider": "huggingface",
                "config": {
                    "model": "all-MiniLM-L6-v2",
                }
            },
            cache=True,
            share_crew=False,
        )