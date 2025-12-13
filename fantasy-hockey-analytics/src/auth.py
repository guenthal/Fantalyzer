import os
import logging
from yfpy.query import YahooFantasySportsQuery
from dotenv import load_dotenv

# Load env vars
load_dotenv()

logger = logging.getLogger(__name__)

def get_yahoo_query(league_id: str, game_code: str = "nhl") -> YahooFantasySportsQuery:
    """
    Initializes the YahooFantasySportsQuery object.
    YFPY handles the OAuth flow automatically.
    """
    client_id = os.getenv("YAHOO_CLIENT_ID")
    client_secret = os.getenv("YAHOO_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        raise ValueError("Missing YAHOO_CLIENT_ID or YAHOO_CLIENT_SECRET in .env file.")

    # YFPY automatically uses 'token.json' (or .yfpy_token.json) for persistence
    # We pass the directory where we want to store it, usually current dir.
    # relative_key_path defaults to .
    
    # We need to construct the query object.
    # We can perform an initial query to trigger auth if needed.
    
    query = YahooFantasySportsQuery(
        league_id=league_id,
        game_code=game_code,
        yahoo_consumer_key=client_id,
        yahoo_consumer_secret=client_secret
    )
    
    return query
