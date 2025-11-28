from google.adk.apps.app import App, EventsCompactionConfig

from app.subagents.orchestrator.agent import root_agent

# Create and export the app instance
app = App(
    root_agent=root_agent,
    name="app",
    events_compaction_config=EventsCompactionConfig(
        compaction_interval=3,  # Trigger compaction every 3 invocations
        overlap_size=1,  # Keep 1 previous turn for context
    ),
)
