import psycopg
import os
from dotenv import load_dotenv

load_dotenv()

def connect_db():
    return psycopg.connect(
        dbname=os.getenv("NFL_DB_NAME"),
        user=os.getenv("NFL_DB_USER"),
        password=os.getenv("NFL_DB_PASSWORD"),
        host=os.getenv("NFL_DB_HOST"),
        port=os.getenv("NFL_DB_PORT")
    )

def save_game_and_score(game_id, venue, away_team, home_team, away_record, home_record, ou_string, ml_string, start_time, status, away_score, home_score, period):
    with connect_db() as conn:
        with conn.cursor() as cur:
            # Insert/update games table with start_time and status
            cur.execute("""
                INSERT INTO games (game_id, venue, away_team, home_team, away_record, home_record, ou_string, ml_string, start_time, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (game_id) DO UPDATE SET
                    away_team = EXCLUDED.away_team,
                    home_team = EXCLUDED.home_team,
                    start_time = EXCLUDED.start_time,
                    status = EXCLUDED.status;
            """, (game_id, venue, away_team, home_team, away_record, home_record, ou_string, ml_string, start_time, status))
            
            # Insert/update scores table WITHOUT start_time
            cur.execute("""
                INSERT INTO scores (game_id, away_score, home_score, period)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (game_id) DO UPDATE SET
                    away_score = EXCLUDED.away_score,
                    home_score = EXCLUDED.home_score,
                    period = EXCLUDED.period;
            """, (game_id, away_score, home_score, period))

        conn.commit()

