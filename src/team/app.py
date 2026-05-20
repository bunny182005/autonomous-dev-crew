import streamlit as st
import sys
import re
from datetime import datetime

# Import your CrewAI class (adjust 'team.crew' to 'src.crew' if your folder is named src)
from team.crew import SoftwareDevelopmentCrew

# ==========================================
# UI Configuration
# ==========================================
st.set_page_config(page_title="CrewAI Studio", page_icon="🤖", layout="wide")

st.title("🤖 Autonomous Software Development Crew")
st.markdown("Enter your project requirements and watch the 10 AI agents collaborate in real-time.")

# ==========================================
# Real-Time Terminal Capture
# ==========================================
class StreamlitTerminal:
    """Captures terminal output, removes ANSI color codes, and streams it to the UI."""
    def __init__(self, placeholder):
        self.placeholder = placeholder
        self.text = ""

    def write(self, data):
        # Clean ANSI escape codes (colors) from the terminal output
        cleaned_data = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', data)
        self.text += cleaned_data
        
        # Display the last 4000 characters to prevent the UI from lagging
        display_text = self.text[-4000:] if len(self.text) > 4000 else self.text
        
        # FIXED: Using triple quotes to prevent multi-line string errors
        self.placeholder.markdown(f"""```text\n{display_text}\n```""")

    def flush(self):
        pass

# ==========================================
# Sidebar Input Panel
# ==========================================
with st.sidebar:
    st.header("⚙️ Execution Settings")
    
    project_topic = st.text_area(
        "Project Topic / Idea:", 
        value="A local-first markdown note-taking app with real-time collaborative syncing.",
        height=150
    )
    
    start_button = st.button("🚀 Kickoff Crew", use_container_width=True, type="primary")

# ==========================================
# Main Execution Logic
# ==========================================
if start_button:
    if not project_topic.strip():
        st.warning("Please enter a project topic before starting.")
    else:
        st.divider()
        st.subheader("🕵️‍♂️ Live Agent Execution Logs")

        # Create an expanding status box for the logs
        with st.status("Agents are analyzing requirements and writing code...", expanded=True) as status_box:
            
            # Create an empty placeholder inside the status box for our live terminal
            terminal_placeholder = st.empty()
            
            # Redirect standard output to our Streamlit UI
            old_stdout = sys.stdout
            sys.stdout = StreamlitTerminal(terminal_placeholder)

            try:
                # Define the inputs matching exactly what tasks.yaml expects
                inputs = {
                    'project_idea': project_topic,
                    'current_year': str(datetime.now().year)
                }
                
                # Execute the crew using the correct class name
                result = SoftwareDevelopmentCrew().crew().kickoff(inputs=inputs)
                
                # Update status box on success
                status_box.update(label="✅ Crew Execution Complete!", state="complete", expanded=False)
                
            except Exception as e:
                # Update status box on failure
                status_box.update(label=f"❌ Execution Failed: {str(e)}", state="error", expanded=True)
                result = None
            finally:
                # ALWAYS restore standard output back to the real terminal
                sys.stdout = old_stdout

        # ==========================================
        # Display Final Output
        # ==========================================
        if result:
            st.divider()
            st.subheader("🎯 Final Output")
            
            # Display the final output in a nice, formatted markdown block
            st.markdown(result)