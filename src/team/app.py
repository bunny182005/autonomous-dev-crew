import os
import sys
import re
import time
import logging
import traceback

from datetime import datetime
from pathlib import Path

import streamlit as st

from dotenv import load_dotenv

# =========================================================
# LOAD ENV VARIABLES
# =========================================================

load_dotenv()

# =========================================================
# IMPORT CREW
# FIX: class is named Team, not SoftwareDevelopmentCrew
# =========================================================

from crew import Team

# =========================================================
# IMPORT WORKSPACE
# =========================================================

from tools.workspace import PROJECT_DIR


# =========================================================
# STREAMLIT CONFIG
# =========================================================

st.set_page_config(
    page_title="Neural Matrix | AI Factory",
    page_icon="🌌",
    layout="wide"
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown("""
<style>

.stCodeBlock code {
    font-family: 'Fira Code', monospace !important;
    color: #00ff66 !important;
    background-color: #0d1117 !important;
}

.stCodeBlock {
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
}

h1 {
    font-weight: 800 !important;
    letter-spacing: -1px;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# HEADER
# =========================================================

st.title("🌌 Neural Matrix: Autonomous Agent Cluster")

st.markdown("""
Supply the initial product constraints.
The autonomous AI engineering crew will:
- Architect
- Develop
- Test
- Secure
- Deploy
- Document
your software system.
""")

st.caption(f"📁 Workspace: {PROJECT_DIR}")


# =========================================================
# ENV VALIDATION
# =========================================================

if not os.getenv("OPENAI_API_KEY"):
    st.error("OPENAI_API_KEY missing in .env file")
    st.stop()


# =========================================================
# PIPELINE STEPS
# FIX: task IDs now match tasks.yaml exactly.
#      - Removed backend_development_task  (doesn't exist)
#      - Removed frontend_development_task (doesn't exist)
#      - Added dependency_setup_task       (was missing)
#      - Added auth_task, service_layer_task, api_routes_task
#      - Added component_task, page_task, integration_task
# =========================================================

PIPELINE_STEPS = [
    {
        "id": "requirement_analysis_task",
        "label": "Product Management",
        "agent": "product_manager",
        "icon": "📊"
    },
    {
        "id": "system_design_task",
        "label": "System Architecture",
        "agent": "system_architect",
        "icon": "📐"
    },
    {
        "id": "dependency_setup_task",
        "label": "Dependency Setup",
        "agent": "dependency_engineer",
        "icon": "📦"
    },
    {
        "id": "database_design_task",
        "label": "Database Engineering",
        "agent": "database_engineer",
        "icon": "💾"
    },
    {
        "id": "auth_task",
        "label": "Auth & Security Backend",
        "agent": "auth_engineer",
        "icon": "🔐"
    },
    {
        "id": "service_layer_task",
        "label": "Service Layer",
        "agent": "service_engineer",
        "icon": "⚙️"
    },
    {
        "id": "api_routes_task",
        "label": "API Routes",
        "agent": "api_routes_engineer",
        "icon": "⚡"
    },
    {
        "id": "component_task",
        "label": "UI Components",
        "agent": "component_engineer",
        "icon": "🧩"
    },
    {
        "id": "page_task",
        "label": "Page Views & Routing",
        "agent": "page_engineer",
        "icon": "🎨"
    },
    {
        "id": "integration_task",
        "label": "Frontend Integration",
        "agent": "integration_engineer",
        "icon": "🔗"
    },
    {
        "id": "testing_task",
        "label": "QA Automation",
        "agent": "test_engineer",
        "icon": "🧪"
    },
    {
        "id": "debugging_task",
        "label": "Autonomous Debugging",
        "agent": "debugging_agent",
        "icon": "🩺"
    },
    {
        "id": "security_audit_task",
        "label": "Security Audit",
        "agent": "security_auditor",
        "icon": "🛡️"
    },
    {
        "id": "deployment_task",
        "label": "DevOps Infrastructure",
        "agent": "devops_engineer",
        "icon": "🚀"
    },
    {
        "id": "documentation_task",
        "label": "Technical Documentation",
        "agent": "documentation_agent",
        "icon": "📝"
    }
]


# =========================================================
# SESSION STATE
# =========================================================

if "current_step_index" not in st.session_state:
    st.session_state.current_step_index = -1

if "logs" not in st.session_state:
    st.session_state.logs = ""


# =========================================================
# LIVE TERMINAL STREAMER
# FIX: also captures Python logging output (crewai uses logging,
#      not print — redirecting only sys.stdout missed everything)
# =========================================================

class StreamlitTerminal:

    def __init__(self, terminal_placeholder, roadmap_placeholder):
        self.terminal_placeholder = terminal_placeholder
        self.roadmap_placeholder  = roadmap_placeholder
        self.text = ""

    def write(self, data):
        if not data:
            return

        # Remove noisy telemetry
        if "missing ScriptRunContext" in data or "CrewAISyncHandler" in data:
            return

        # Remove ANSI escape codes
        cleaned_data = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', data)
        self.text += cleaned_data

        # Prevent UI lag on very long runs
        if len(self.text) > 25000:
            self.text = self.text[-25000:]

        # =================================================
        # STEP DETECTION ENGINE
        # =================================================
        search_text = cleaned_data.lower()

        for idx, step in enumerate(PIPELINE_STEPS):
            patterns = [
                f"working on '{step['id'].lower()}'",
                step["id"].lower(),
                step["label"].lower(),
                step["agent"].lower(),
                step["agent"].replace("_", " ").lower(),
            ]
            if any(p in search_text for p in patterns):
                # Only advance — never go backward
                if idx > st.session_state.current_step_index:
                    st.session_state.current_step_index = idx
                    self.render_roadmap()
                    break

        # =================================================
        # LIVE TERMINAL
        # =================================================
        display_text = self.text[-4000:] if len(self.text) > 4000 else self.text
        self.terminal_placeholder.code(display_text, language="text")

    def flush(self):
        pass

    def render_roadmap(self):
        with self.roadmap_placeholder.container():
            st.markdown("## 🗺️ Execution Roadmap")

            current_idx  = st.session_state.current_step_index
            progress_pct = 0.0

            if 0 <= current_idx < len(PIPELINE_STEPS):
                progress_pct = (current_idx + 1) / len(PIPELINE_STEPS)
            elif current_idx >= len(PIPELINE_STEPS):
                progress_pct = 1.0

            st.progress(
                progress_pct,
                text=f"Pipeline Completion: {int(progress_pct * 100)}%"
            )
            st.divider()

            for idx, step in enumerate(PIPELINE_STEPS):
                if idx < current_idx:
                    st.success(
                        f"{step['icon']} **{step['label']}**\n\n"
                        f"Completed by `{step['agent']}`"
                    )
                elif idx == current_idx:
                    st.info(
                        f"{step['icon']} **{step['label']}** *(ACTIVE)*\n\n"
                        f"`{step['agent']}` currently processing..."
                    )
                else:
                    st.markdown(
                        f"> ⚪ **{step['label']}**\n"
                        f">\n"
                        f"> Waiting for `{step['agent']}`"
                    )
            st.divider()


# =========================================================
# LOGGING HANDLER
# FIX: CrewAI writes via Python logging, not print().
#      Without this, the terminal widget shows nothing and
#      step detection never fires.
# =========================================================

class StreamlitLoggingHandler(logging.Handler):

    def __init__(self, terminal: StreamlitTerminal):
        super().__init__()
        self.terminal = terminal

    def emit(self, record: logging.LogRecord):
        try:
            msg = self.format(record)
            self.terminal.write(msg + "\n")
        except Exception:
            pass


# =========================================================
# UI LAYOUT
# =========================================================

left_col, right_col = st.columns([0.7, 0.3])


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    st.header("⚙️ Ignition Parameters")

    project_topic = st.text_area(
        "Project Architecture Vision",
        value="A local-first markdown note-taking app with real-time collaborative syncing.",
        height=200,
        max_chars=5000
    )

    st.markdown("---")

    start_button = st.button(
        "🚀 Initialize Hive",
        use_container_width=True,
        type="primary"
    )


# =========================================================
# INITIAL ROADMAP
# =========================================================

with right_col:
    roadmap_slot = st.empty()

    with roadmap_slot.container():
        st.markdown("## 🗺️ Execution Roadmap")
        st.progress(0.0, text="System Idle")
        st.divider()

        for step in PIPELINE_STEPS:
            st.markdown(
                f"> ⚪ **{step['label']}**\n"
                f">\n"
                f"> Waiting for `{step['agent']}`"
            )
        st.divider()


# =========================================================
# EXECUTION
# =========================================================

with left_col:

    if start_button:

        # FIX: validate input BEFORE updating session state
        # so the roadmap doesn't show "step 1 active" on empty submit
        if not project_topic.strip():
            st.warning("Please provide a project vision.")
            st.stop()

        st.session_state.current_step_index = 0

        st.subheader("🛰️ Live Agent Telemetry")

        with st.status(
            "Initializing AI agent cluster...",
            expanded=True
        ) as status_box:

            terminal_placeholder = st.empty()

            terminal_handler = StreamlitTerminal(
                terminal_placeholder,
                roadmap_slot
            )

            # Redirect stdout (for any print() calls)
            old_stdout = sys.stdout
            sys.stdout  = terminal_handler

            # FIX: also attach to Python logging so CrewAI output is captured
            log_handler = StreamlitLoggingHandler(terminal_handler)
            log_handler.setFormatter(logging.Formatter("%(levelname)s | %(name)s | %(message)s"))
            root_logger = logging.getLogger()
            old_log_level = root_logger.level
            root_logger.setLevel(logging.DEBUG)
            root_logger.addHandler(log_handler)

            try:
                start_time = time.time()

                terminal_handler.render_roadmap()

                inputs = {
                    "project_idea": project_topic,
                    "current_year": str(datetime.now().year)
                }

                # =========================================
                # RUN CREW
                # FIX: class is Team(), not SoftwareDevelopmentCrew()
                # =========================================

                crew_instance = Team()
                crew_runner   = crew_instance.crew()
                result        = crew_runner.kickoff(inputs=inputs)

                # =========================================
                # COMPLETE
                # =========================================

                st.session_state.current_step_index = len(PIPELINE_STEPS)
                terminal_handler.render_roadmap()

                execution_time = round(time.time() - start_time, 2)

                status_box.update(
                    label=f"✅ Execution Complete ({execution_time}s)",
                    state="complete",
                    expanded=False
                )

            except Exception as e:
                error_trace = traceback.format_exc()

                status_box.update(
                    label="❌ System Failure",
                    state="error",
                    expanded=True
                )

                st.error(str(e))
                st.code(error_trace)
                result = None

            finally:
                # Restore stdout
                sys.stdout = old_stdout

                # FIX: remove our log handler and restore original log level
                # (don't touch sys.stderr — we never redirected it)
                root_logger.removeHandler(log_handler)
                root_logger.setLevel(old_log_level)


        # =====================================================
        # FINAL OUTPUT
        # =====================================================

        if result:
            st.divider()
            st.subheader("🎯 Final Synthesis Output")

            try:
                if hasattr(result, "raw"):
                    st.markdown(result.raw)
                elif hasattr(result, "tasks_output"):
                    for task_output in result.tasks_output:
                        with st.expander(task_output.description, expanded=False):
                            st.markdown(task_output.raw)
                else:
                    st.markdown(str(result))
            except Exception as render_error:
                st.error(f"Render Error: {render_error}")
                st.code(str(result))


        # =====================================================
        # GENERATED FILES
        # =====================================================

        st.divider()
        st.subheader("📂 Generated Project Files")

        files_found = False

        for path in PROJECT_DIR.rglob("*"):
            if path.is_file():
                files_found = True
                relative_path = path.relative_to(PROJECT_DIR)
                st.text(str(relative_path))

        if not files_found:
            st.warning("No generated files detected.")