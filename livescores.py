import time
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Optional, Dict, Any

from api import get
from dotenv import load_dotenv
from paneldisplay import render_game_to_image
from odds import odds_by_game

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# ---------------------- API WRAPPERS ---------------------- #

def get_api_data(endpoint: str, params: dict, expected_type: type, default):
    """Generic wrapper for API calls."""
    try:
        resp = get(endpoint, params)
        body = resp.get("body", default)
        return body if isinstance(body, expected_type) else default
    except Exception as e:
        logger.error(f"Error fetching {endpoint}: {e}")
        return default


def get_live_scores(date: Optional[str] = None) -> Dict[str, Any]:
    """Primary scoreboard endpoint."""
    if not date:
        date = datetime.now(ZoneInfo("America/Chicago")).strftime("%Y%m%d")
    return get_api_data(
        "getNFLScoresOnly",
        {"gameDate": date, "topPerformers": "true"},
        dict,
        {},
    )


def get_team_data() -> list:
    """Proper source for records — DO NOT USE getNFLBoxScore."""
    return get_api_data(
        "getNFLTeams",
        {
            "sortBy": "standings",
            "rosters": "false",
            "schedules": "false",
            "topPerformers": "false",
            "teamStats": "false",
            "teamStatsSeason": "2024"
        },
        list,
        [],
    )


def get_game_venue(game_id: str) -> dict:
    """Used only for venue + scheduled kickoff."""
    return get_api_data(
        "getNFLGameInfo",
        {"gameID": game_id},
        dict,
        {"venue": "N/A", "away": "???", "home": "???", "gameTime": "", "gameTime_epoch": None},
    )


# ---------------------- DATA PROCESSING ---------------------- #

def validate_game_data(data: Any) -> bool:
    return isinstance(data, dict) and "away" in data and "home" in data


def get_team_record(team_abv: str, team_data: list) -> str:
    for team in team_data:
        if team.get("teamAbv") == team_abv:
            w = team.get("wins", 0)
            l = team.get("loss", 0)
            t = team.get("tie", 0)
            return f"{w}-{l}-{t}" if t else f"{w}-{l}"
    return "N/A"


def format_kickoff_ct(game_info: dict, venue_info: dict) -> str:
    """Convert UTC epoch → Central time."""
    epoch = venue_info.get("gameTime_epoch") or game_info.get("gameTime_epoch")
    try:
        if epoch:
            dt_utc = datetime.fromtimestamp(int(epoch), tz=ZoneInfo("UTC"))
            dt_ct = dt_utc.astimezone(ZoneInfo("America/Chicago"))
            return dt_ct.strftime("%-I:%M%p").lower().replace("pm", "p").replace("am", "a")
    except Exception:
        pass

    # fallback raw
    return venue_info.get("gameTime") or game_info.get("gameTime") or "TBD"


def build_display_status(raw_status, period, clock, away, home, away_score, home_score):
    """Turn random Tank01 statuses into clean statuses."""
    s = (raw_status or "").lower().strip()

    if s in ("scheduled", "pre-game", "pregame", "gametime", "game time", ""):
        return "Scheduled"

    if "final" in s or "completed" in s:
        if away_score > home_score:
            return f"{away} win!"
        if home_score > away_score:
            return f"{home} win!"
        return "Final (tied)"

    # Live conditions
    if "live" in s or "in progress" in s or "quarter" in s or "qtr" in s:
        parts = []
        if period:
            parts.append(f"Q{period}")
        if clock:
            parts.append(clock)
        return ("Live " + " ".join(parts)).strip()

    return raw_status or "In Progress"


# ---------------------- PRINTING ---------------------- #

def print_game_status(game: Dict[str, Any]) -> None:
    """Cleaner console output for debugging."""
    away, home = game["away"], game["home"]
    ar, hr = game["away_record"], game["home_record"]
    ascore, hscore = game["away_score"], game["home_score"]
    venue = game["venue"]
    status = game["display_status"]
    sched = game["scheduled_time"]
    ou = game["ou_string"]
    ml = game["ml_string"]

    if "live" in status.lower() or "q" in status.lower() or "win!" in status.lower():
        print(f"{away} {ascore} @ {home} {hscore}")
        print(f"Venue: {venue}")
        print(f"Status: {status} | {ou} | {ml}")
    else:
        print(f"Upcoming: {away} ({ar}) @ {home} ({hr})")
        print(f"Venue: {venue}")
        print(f"Kickoff: {sched} | {ou} | {ml}")


# ---------------------- MAIN ENGINE ---------------------- #

def find_next_game_date(start_date: datetime, max_days=7):
    for offset in range(1, max_days + 1):
        next_date = start_date + timedelta(days=offset)
        date_str = next_date.strftime("%Y%m%d")
        games = get_live_scores(date_str)
        if games:
            return date_str, games
    return None, None


def process_scores() -> None:
    """Main entry point for your IoT publisher."""
    today = datetime.now(ZoneInfo("America/Chicago"))
    date_str = today.strftime("%Y%m%d")
    games = get_live_scores(date_str)

    if not games:
        logger.info("No games today. Searching next 7 days…")
        date_str, games = find_next_game_date(today) or (None, None)
        if not games:
            logger.info("No upcoming games at all.")
            return
        logger.info(f"Next games on {date_str}")

    odds_data = odds_by_game(date_str)
    team_data_cache = get_team_data()

    logger.info(f"\nNFL Games for {date_str}:\n")

    for game_id, game_info in games.items():
        if not validate_game_data(game_info):
            logger.warning(f"Skipping invalid game {game_id}")
            continue

        try:
            time.sleep(0.5)

            away = game_info["away"]
            home = game_info["home"]

            # Scores
            away_score = int(game_info.get("awayScore") or 0)
            home_score = int(game_info.get("homeScore") or 0)

            raw_status = game_info.get("gameStatus") or ""
            period = game_info.get("currentPeriod") or game_info.get("quarter") or ""
            clock = game_info.get("gameClock") or game_info.get("clock") or ""

            venue_info = get_game_venue(game_id)
            venue = venue_info.get("venue", "N/A")
            scheduled_time = format_kickoff_ct(game_info, venue_info)

            away_record = get_team_record(away, team_data_cache)
            home_record = get_team_record(home, team_data_cache)

            display_status = build_display_status(
                raw_status, period, clock,
                away, home, away_score, home_score
            )

            # Odds
            game_odds = odds_data.get(game_id, {"ML": "ML: N/A", "O/U": "O/U: N/A"})
            ou_string = game_odds["O/U"]
            ml_string = game_odds["ML"]

            game_data = {
                "venue": venue,
                "away": away,
                "home": home,
                "away_score": away_score,
                "home_score": home_score,
                "display_status": display_status,
                "ou_string": ou_string,
                "ml_string": ml_string,
                "scheduled_time": scheduled_time,
                "away_record": away_record,
                "home_record": home_record,
            }

            render_game_to_image(game_data)
            print_game_status(game_data)

        except Exception as e:
            logger.error(f"Error processing game {game_id}: {e}", exc_info=True)


if __name__ == "__main__":
    process_scores()
