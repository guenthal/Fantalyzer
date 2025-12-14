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
    
    import json
    from pathlib import Path

    # Load token data manually to ensure it's passed correctly
    token_path = Path("token.json")
    token_data = None
    if token_path.exists():
        try:
            with open(token_path, "r") as f:
                token_data = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read token.json: {e}")

    # Inject missing fields required by yfpy when passing dict
    if token_data:
        if 'consumer_key' not in token_data:
            token_data['consumer_key'] = client_id
        if 'consumer_secret' not in token_data:
            token_data['consumer_secret'] = client_secret
        
        # Ensure 'guid' exists (yfpy validation requires the key, even if None)
        if 'guid' not in token_data:
            token_data['guid'] = token_data.get('xoauth_yahoo_guid', None)

    # Explicitly pass token data and disable browser callback
    query = YahooFantasySportsQuery(
        league_id=league_id,
        game_code=game_code,
        yahoo_consumer_key=client_id,
        yahoo_consumer_secret=client_secret,
        yahoo_access_token_json=token_data, 
        browser_callback=False
    )
    
    return query
