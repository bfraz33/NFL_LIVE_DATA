# team_venues.py

team_venues = {
    "ARI": "State Farm Stadium",
    "ATL": "Mercedes-Benz Stadium",
    "BAL": "M&T Bank Stadium",
    "BUF": "Highmark Stadium",
    "CAR": "Bank of America Stadium",
    "CHI": "Soldier Field",
    "CIN": "Paycor Stadium",
    "CLE": "FirstEnergy Stadium",
    "DAL": "AT&T Stadium",
    "DEN": "Empower Field at Mile High",
    "DET": "Ford Field",
    "GB": "Lambeau Field",
    "HOU": "NRG Stadium",
    "IND": "Lucas Oil Stadium",
    "JAX": "TIAA Bank Field",
    "KC": "GEHA Field at Arrowhead Stadium",
    "LV": "Allegiant Stadium",
    "LAC": "SoFi Stadium",
    "LAR": "SoFi Stadium",
    "MIA": "Hard Rock Stadium",
    "MIN": "U.S. Bank Stadium",
    "NE": "Gillette Stadium",
    "NO": "Caesars Superdome",
    "NYG": "MetLife Stadium",
    "NYJ": "MetLife Stadium",
    "PHI": "Lincoln Financial Field",
    "PIT": "Acrisure Stadium",
    "SF": "Levi's Stadium",
    "SEA": "Lumen Field",
    "TB": "Raymond James Stadium",
    "TEN": "Nissan Stadium",
    "WAS": "FedExField",
}

def get_venue_for_team(team_abbr: str) -> str:
    return team_venues.get(team_abbr.upper(), "Unknown Venue")