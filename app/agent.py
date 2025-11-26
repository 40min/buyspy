from google.adk.apps.app import App

from app.subagents.orchestrator.agent import root_agent

# Create and export the app instance
app = App(root_agent=root_agent, name="app")
