import time
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Optional, Dict, Any
from api import get
from dotenv import load_dotenv 


load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_game_data(data: Any) -> bool:
    return isinstance(data, dict) and 'away' in data and 'home' in data

def extract_odds_line(game_odds: Optional[Dict[str, Any]], key: str, label: str, preferred_book: Optional[str] = None) -> str:
    if not game_odds or not isinstance(game_odds, dict):
        return f"{label}: N/A"
    for book in game_odds.get("sportsBooks", []):
        if not isinstance(book, dict):
            continue
        if preferred_book and book.get("sportsBook") != preferred_book:
            continue
        val = book.get("odds", {}).get(key)
        if val is not None:
            return f"{label}: {val}"
    return f"{label}: N/A"

extract_ou_line = lambda odds, pb=None: extract_odds_line(odds, "totalOver", "O/U", pb)
extract_ml_line = lambda odds, pb=None: extract_odds_line(odds, "homeTeamMLOdds", "ML", pb)

def get_api_data(endpoint: str, params: dict, expected_type: type, default):
    try:
        resp = get(endpoint, params)
        body = resp.get("body", default)
        if not isinstance(body, expected_type):
            """logger.warning(f"Unexpected {endpoint} response body format")"""
            return default
        return body
    except Exception as e:
        logger.error(f"Error fetching {endpoint}: {e}")
        return default

def get_live_scores(date: Optional[str] = None) -> Dict[str, Any]:
    if not date:
        date = datetime.now(ZoneInfo("America/Chicago")).strftime("%Y%m%d")
    return get_api_data("getNFLScoresOnly", {"gameDate": date, "topPerformers": "true"}, dict, {})

def get_betting_odds(date: Optional[str] = None) -> list:
    if not date:
        date = datetime.now(ZoneInfo("America/Chicago")).strftime("%Y%m%d")
    return get_api_data("getNFLBettingOdds", {"gameDate": date, "playerProps": "true", "itemFormat": "list"}, list, [])

def get_team_data(date: Optional[str] = None) -> list:
    if not date:
        date = datetime.now(ZoneInfo("America/Chicago")).strftime("%Y%m%d")
    return get_api_data("getNFLBoxScore", {"gameDate": date}, list, [])

def get_game_venue(game_id: str) -> dict:
    return get_api_data("getNFLGameInfo", {"gameID": game_id}, dict, {"venue":"N/A", "away":"???", "home":"???", "gameTime":""})
    


def get_box_score(game_id: str) -> dict:
    return get_api_data("getNFLBoxScore", {"gameID": game_id, "playerStatsFormat": "list", "startingLineups": "true", "fantasyPoints": "true"}, dict, {})

def get_team_record(team_abv: str, team_data: list) -> str:
    for team in team_data:
        if isinstance(team, dict) and team.get("teamAbv") == team_abv:
            try:
                return f"{int(team.get('wins',0))} - {int(team.get('loss',0))}"
            except Exception:
                break
    return "N/A"

def print_game_status(game: Dict[str, Any]) -> None:
    away, home = game["away"], game["home"]
    ar, hr = game.get("away_record", "N/A"), game.get("home_record", "N/A")
    ascore, hscore = game.get("away_score", 0), game.get("home_score", 0)
    status = game.get("display_status", "")
    ou = game.get("ou_string", "O/U: N/A")
    ml = game.get("ml_string", "ML: N/A")
    sched = game.get("scheduled_time", "Unknown")
    venue = game.get("venue", "N/A")  # <- pull venue

    ingame = any(k in status.lower() for k in ["halftime", "timeout", "period", "final", "completed", "win!"])

    if not ingame:
        print(f"Pre-Season: {away} ({ar}) @ {home} ({hr})")
        print(f"Venue: {venue}")  # <- show it
        print(f"Start Time: {sched} | {ou} | {ml}")
    else:
        print(f"Live {away} {ascore} @ {home} {hscore}")
        print(f"Venue: {venue}")  # <- show it
        print(f"Status: {status} | {ou} | {ml}")

def find_next_game_date(start_date: datetime, max_days=7):
    for offset in range(1, max_days + 1):
        next_date = start_date + timedelta(days=offset)
        date_str = next_date.strftime("%Y%m%d")
        games = get_live_scores(date_str)
        if games:
            return date_str, games
    return None, None

def process_scores() -> None:
    today = datetime.now(ZoneInfo("America/Chicago"))
    date_str = today.strftime("%Y%m%d")
    games = get_live_scores(date_str)

    if not games:
        logger.info(f"No games found for {date_str}, searching next 7 days...")
        date_str, games = find_next_game_date(today) or (None, None)
        if not games:
            logger.info("No upcoming games found in next 7 days.")
            return
        logger.info(f"Next games found on {date_str}")

    odds_list = get_betting_odds(date_str)
    odds_by_game = {item["gameID"]: item for item in odds_list if isinstance(item, dict) and "gameID" in item}
    team_data_cache = get_team_data(date_str)

    logger.info(f"\nNFL Games for {datetime.strptime(date_str, '%Y%m%d').strftime('%Y-%m-%d')}:\n")

    for game_id, game_info in games.items():
        if not validate_game_data(game_info):
            logger.warning(f"Skipping invalid game data for {game_id}")
            continue

        try:
            time.sleep(0.5)  # API rate limiting

            boxscore = get_box_score(game_id)
            venue_info = get_game_venue(game_id)
            venue = venue_info.get("venue", "N/A")
            away = venue_info.get("away", "???")
            home = venue_info.get("home", "???")
            scheduled_time = venue_info.get("gameTime", "")

            away_score = int(boxscore.get("awayPts", 0) or 0)
            home_score = int(boxscore.get("homePts", 0) or 0)

            status = boxscore.get("gameStatus", "gameTime")
            period = boxscore.get("currentPeriod", "")

            away_record = get_team_record(away, team_data_cache)
            home_record = get_team_record(home, team_data_cache)

            if status.lower().startswith("live"):
                display_status = period or "In Progress"
            elif status == "gameTime":
                display_status = scheduled_time or "Scheduled"
            elif status.lower() in ("final", "completed"):
                if away_score > home_score:
                    display_status = f"{away} win!"
                elif home_score > away_score:
                    display_status = f"{home} win!"
                else:
                    display_status = "Game ended in a tie"
            else:
                display_status = status

            game_odds = odds_by_game.get(game_id, {})
            ou_string = extract_ou_line(game_odds)
            ml_string = extract_ml_line(game_odds)

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

            print_game_status(game_data)

        except Exception as e:
            logger.error(f"Error processing game {game_id}: {e}", exc_info=True)

if __name__ == "__main__":
    process_scores()
