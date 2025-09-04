import time
from datetime import datetime
from zoneinfo import ZoneInfo
from livescores import process_scores
from logger import get_logger
from cache import save_to_cache, load_from_cache, GAME_CACHE_FILE, LOGO_CACHE_FILE

logger = get_logger(__name__)
POLL_INTERVAL = 180  # seconds (3 minutes)


def should_poll(now=None):
    """Return True if current time is within polling hours (8 AM to midnight Chicago)."""
    if now is None:
        now = datetime.now(ZoneInfo("America/Chicago"))
    return 8 <= now.hour < 24


def run_once():
    """
    Run the livescores + any other scripts ONCE and return the results.
    This is what publisher.py will call.
    """
    now = datetime.now(ZoneInfo("America/Chicago"))
    data = {
        "timestamp": now.isoformat(),
        "within_polling_hours": should_poll(now),
        "scores": None,
    }

    if should_poll(now):
        logger.info("Polling API (single run)...")
        data["scores"] = process_scores()
    else:
        logger.info("Outside polling hours. Skipping API call.")

    return data


def main_loop():
    """Main polling loop to run livescores process periodically."""
    while True:
        run_once()
        logger.info(f"Waiting {POLL_INTERVAL // 60} minutes before next poll...\n")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main_loop()
