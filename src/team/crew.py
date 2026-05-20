from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

# Import Custom Tools 
from .tools.search_tools import AdvancedDDGSearchTool
from .tools.memory_tools import ChromaMemoryRetrievalTool
from .tools.architect_tools import ArchitectureGeneratorTool, DatabaseSchemaTool, ApiDesignTool
from .tools.backend_tools import FileWriteTool, TerminalTool, DockerTool, GithubTool
from .tools.frontend_tools import BrowserPreviewTool, ScreenshotAnalysisTool
from .tools.database_tools import PostgresTool, MigrationTool, SqlValidatorTool
from .tools.test_tools import PytestRunnerTool, JestRunnerTool, CoverageAnalysisTool
from .tools.debugger_tools import FileEditTool, StackTraceParserTool, LogAnalysisTool
from .tools.security_tools import CodeSecurityScannerTool, DependencyScannerTool, SecretsDetectionTool
from .tools.devops_tools import DockerManagerTool, GitHubActionsValidatorTool, KubernetesManifestTool
from .tools.docs_tools import MarkdownGeneratorTool, OpenApiDocTool

@CrewBase
class SoftwareDevelopmentCrew():
    """Autonomous Software Development AI Crew"""
    
    # Path to your YAML configuration files
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    # ==========================================
    # AGENTS
    # ==========================================

    @agent
    def product_manager(self) -> Agent:
        return Agent(
            config=self.agents_config['product_manager'],
            tools=[AdvancedDDGSearchTool(), ChromaMemoryRetrievalTool()]
        )

    @agent
    def system_architect(self) -> Agent:
        return Agent(
            config=self.agents_config['system_architect'],
            tools=[ArchitectureGeneratorTool(), DatabaseSchemaTool(), ApiDesignTool()]
        )

    @agent
    def database_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['database_engineer'],
            tools=[PostgresTool(), MigrationTool(), SqlValidatorTool()]
        )

    @agent
    def backend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['backend_engineer'],
            tools=[FileWriteTool(), TerminalTool(), DockerTool(), GithubTool()]
        )

    @agent
    def frontend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['frontend_engineer'],
            tools=[FileWriteTool(), BrowserPreviewTool(), ScreenshotAnalysisTool()]
        )

    @agent
    def test_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['test_engineer'],
            tools=[PytestRunnerTool(), JestRunnerTool(), CoverageAnalysisTool()]
        )

    @agent
    def debugging_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['debugging_agent'],
            tools=[TerminalTool(), FileEditTool(), StackTraceParserTool(), LogAnalysisTool()]
        )

    @agent
    def security_auditor(self) -> Agent:
        return Agent(
            config=self.agents_config['security_auditor'],
            tools=[CodeSecurityScannerTool(), DependencyScannerTool(), SecretsDetectionTool()]
        )

    @agent
    def devops_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['devops_engineer'],
            tools=[DockerManagerTool(), GitHubActionsValidatorTool(), KubernetesManifestTool()]
        )

    @agent
    def documentation_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['documentation_agent'],
            tools=[MarkdownGeneratorTool(), OpenApiDocTool()]
        )

    # ==========================================
    # TASKS
    # ==========================================

    @task
    def requirement_analysis_task(self) -> Task:
        return Task(config=self.tasks_config['requirement_analysis_task'])

    @task
    def system_design_task(self) -> Task:
        return Task(config=self.tasks_config['system_design_task'])

    @task
    def database_design_task(self) -> Task:
        return Task(config=self.tasks_config['database_design_task'])

    @task
    def backend_development_task(self) -> Task:
        return Task(config=self.tasks_config['backend_development_task'])

    @task
    def frontend_development_task(self) -> Task:
        return Task(config=self.tasks_config['frontend_development_task'])

    @task
    def testing_task(self) -> Task:
        return Task(config=self.tasks_config['testing_task'])

    @task
    def debugging_task(self) -> Task:
        return Task(config=self.tasks_config['debugging_task'])

    @task
    def security_audit_task(self) -> Task:
        return Task(config=self.tasks_config['security_audit_task'])

    @task
    def deployment_task(self) -> Task:
        return Task(config=self.tasks_config['deployment_task'])

    @task
    def documentation_task(self) -> Task:
        return Task(config=self.tasks_config['documentation_task'])

    # ==========================================
    # CREW ORCHESTRATION
    # ==========================================
    
    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents, 
            tasks=self.tasks,   
            process=Process.sequential, 
            verbose=True,
        )