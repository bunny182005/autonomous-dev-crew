#!/usr/bin/env python
import sys
import warnings

from datetime import datetime
from team.crew import Team

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def run():
    """
    Run the crew.

    Usage:
        # Option A — edit PROJECT_IDEA below and run: crewai run
        # Option B — pass idea as argument: python -m team.main "your project idea"
    """

    # ── Edit this to describe your project ────────────────
    PROJECT_IDEA = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "A task management web app where users can create projects, assign tasks, set deadlines, and track progress with a Kanban board."
    )
    # ──────────────────────────────────────────────────────

    inputs = {
        "project_idea": PROJECT_IDEA,          # ← matches {project_idea} in tasks.yaml
        "current_year": str(datetime.now().year),
    }

    print("\n" + "=" * 60)
    print("PROJECT IDEA:")
    print(PROJECT_IDEA)
    print("=" * 60 + "\n")

    try:
        Team().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    inputs = {
        "project_idea": "A task management web app",
        "current_year": str(datetime.now().year),
    }
    try:
        Team().crew().train(
            n_iterations=int(sys.argv[1]),
            filename=sys.argv[2],
            inputs=inputs,
        )
    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    try:
        Team().crew().replay(task_id=sys.argv[1])
    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test():
    inputs = {
        "project_idea": "A task management web app",
        "current_year": str(datetime.now().year),
    }
    try:
        Team().crew().test(
            n_iterations=int(sys.argv[1]),
            eval_llm=sys.argv[2],
            inputs=inputs,
        )
    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")