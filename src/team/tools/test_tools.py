import os
import subprocess
import json
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

class PytestRunnerSchema(BaseModel):
    test_target: str = Field(
        default="tests/backend", 
        description="The directory or specific file path to run tests on (e.g., 'tests/backend/test_auth.py')."
    )
    extra_flags: str = Field(
        default="", 
        description="Optional flags to pass to pytest (e.g., '-v', '-k test_login', '--lf')."
    )

class PytestRunnerTool(BaseTool):
    name: str = "pytest_runner"
    description: str = "Runs Python unit and integration tests using pytest and returns the execution results."
    args_schema: type[BaseModel] = PytestRunnerSchema

    def _run(self, test_target: str = "tests/backend", extra_flags: str = "") -> str:
        try:
            command = f"pytest {test_target} {extra_flags}".strip()
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=45)
            return f"COMMAND EXECUTED: {command}\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
        except subprocess.TimeoutExpired:
            return "Execution timed out. The test suite took longer than 45 seconds to finish."
        except Exception as e:
            return f"Failed to run pytest. Error: {str(e)}"

class JestRunnerSchema(BaseModel):
    test_target: str = Field(
        default="src", 
        description="The directory, file pattern, or npm script name to target for frontend tests (e.g., 'npm test' or 'jest src/components')."
    )

class JestRunnerTool(BaseTool):
    name: str = "jest_runner"
    description: str = "Runs frontend JavaScript/TypeScript tests using Jest or npm/yarn test runners."
    args_schema: type[BaseModel] = JestRunnerSchema

    def _run(self, test_target: str = "src") -> str:
        try:
            # Check if it looks like an npm command or direct jest command
            if test_target.startswith(("npm", "yarn", "pnpm")):
                command = test_target
            else:
                command = f"npx jest {test_target} --watchAll=false"
            
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
            return f"COMMAND EXECUTED: {command}\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
        except subprocess.TimeoutExpired:
            return "Execution timed out. The Jest test suite took longer than 60 seconds to finish."
        except Exception as e:
            return f"Failed to run Jest. Error: {str(e)}"

class CoverageAnalysisSchema(BaseModel):
    environment: str = Field(
        ..., 
        description="Specify 'backend' (to run coverage.py/pytest-cov) or 'frontend' (to run jest --coverage)."
    )

class CoverageAnalysisTool(BaseTool):
    name: str = "coverage_analyzer"
    description: str = "Generates and analyzes test coverage metrics for either backend or frontend systems."
    args_schema: type[BaseModel] = CoverageAnalysisSchema

    def _run(self, environment: str) -> str:
        try:
            if environment.lower() == "backend":
                # Ensure code has been run with coverage tracking, or invoke via pytest-cov
                command = "pytest --cov=. --cov-report=term-missing"
                result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=45)
                return f"BACKEND COVERAGE RESULTS:\n\n{result.stdout}"
                
            elif environment.lower() == "frontend":
                command = "npx jest --coverage --watchAll=false"
                result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
                return f"FRONTEND COVERAGE RESULTS:\n\n{result.stdout}"
            else:
                return "Error: Invalid environment specified. Must be 'backend' or 'frontend'."
        except Exception as e:
            return f"Coverage metrics collection failed. Error: {str(e)}"