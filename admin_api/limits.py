"""A small limit on how often one person can use the chat, so a free AI key is not used up."""
import time

WINDOW_SECONDS = 600
MAX_MESSAGES = 20

_recent = {}


def allow(user_id, now=None):
    """True if this person may send another message. Counts messages in the last ten minutes."""
    now = time.time() if now is None else now
    recent = [moment for moment in _recent.get(user_id, []) if now - moment < WINDOW_SECONDS]
    if len(recent) >= MAX_MESSAGES:
        _recent[user_id] = recent
        return False
    recent.append(now)
    _recent[user_id] = recent
    return True
