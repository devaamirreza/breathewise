from pathlib import Path


# Locate the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Agent instruction file
INSTRUCTIONS_FILE = PROJECT_ROOT / "breathewise_agent_instructions.md"


def load_agent_instructions():
    """
    Loads BreatheWise persona and behavioural instructions.
    """

    if not INSTRUCTIONS_FILE.exists():
        raise FileNotFoundError(
            "BreatheWise agent instructions file not found."
        )

    return INSTRUCTIONS_FILE.read_text(encoding="utf-8")