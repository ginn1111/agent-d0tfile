"""
Capture user prompt from the most recent session message.
Runs via post_user_message hook.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

PROFILE_DIR = Path(__file__).parent.parent.parent
DAILY_DIR = PROFILE_DIR / "english-tutor" / "daily_prompts"
DAILY_DIR.mkdir(parents=True, exist_ok=True)

DAILY_FILE = DAILY_DIR / f"prompts_{datetime.now().strftime('%Y-%m-%d')}.jsonl"


def _capture_user_prompt(session_id, content):
    if not content or not content.strip():
        return 0

    # Skip very short messages, commands, or system messages
    content = content.strip()
    if len(content) < 5:
        return 0
    if content.startswith(('/', '!', '@', '#')):
        return 0

    record = {
        "timestamp": datetime.now().isoformat(),
        "prompt": content,
        "length": len(content)
    }

    try:
        with open(DAILY_FILE, 'a') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    except Exception as e:
        print(f"Write error: {e}", file=sys.stderr)
        return 1
    return 0


def register(ctx):
    ctx.register_hook("pre_llm_call", _capture_user_prompt)
