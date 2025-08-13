import logging
from api import get
from datetime import datetime
from zoneinfo import ZoneInfo

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def test_venue_api(game_id: str):
    try:
        response = get("getNFLGameInfo", {"gameID": game_id})
        logging.debug(f"Raw API response for game {game_id}: {response}")
        body = response.get("body", {})
        print("Raw 'body' content:", body)

        # Try extracting venue info if available
        venue = body.get("venue", "N/A")
        away = body.get("away", "???")
        home = body.get("home", "???")
        game_time = body.get("gameTime", "")

        print(f"Venue: {venue}")
        print(f"Away Team: {away}")
        print(f"Home Team: {home}")
        print(f"Game Time: {game_time}")

    except Exception as e:
        logging.error(f"Error fetching game info for {game_id}: {e}")

if __name__ == "__main__":
    # Replace with an actual game ID from your data
    example_game_id = "20250815_TEN@ATL"
    test_venue_api(example_game_id)
