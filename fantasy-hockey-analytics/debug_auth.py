import os
import requests
from dotenv import load_dotenv
import base64

load_dotenv()

CLIENT_ID = os.getenv("YAHOO_CLIENT_ID")
CLIENT_SECRET = os.getenv("YAHOO_CLIENT_SECRET")

if not CLIENT_ID or not CLIENT_SECRET:
    print("Error: Missing credentials in .env")
    exit(1)

print(f"Client ID: {CLIENT_ID[:5]}...{CLIENT_ID[-5:]}")
print(f"Client Secret (len): {len(CLIENT_SECRET)}")

# 1. Get Auth URL
# Note: Using 'oob' as yahoo_oauth does.
redirect_uri = "oob"
auth_url = (
    f"https://api.login.yahoo.com/oauth2/request_auth?"
    f"redirect_uri={redirect_uri}&response_type=code&client_id={CLIENT_ID}"
)

print("\nPlease copy this URL and open it in your browser:")
print(f"{auth_url}\n")

code = input("Enter the verification code: ").strip()

# 2. Exchange for Token
token_url = "https://api.login.yahoo.com/oauth2/get_token"

# Basic Auth header (ClientID:ClientSecret base64 encoded)
# yahoo_oauth might send it in body or header. Standard is usually Header or Body.
# Let's try standard body first (grant_type, redirect_uri, code) + Authorization header.

auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
b64_auth = base64.b64encode(auth_str.encode()).decode()
headers = {
    "Authorization": f"Basic {b64_auth}",
    "Content-Type": "application/x-www-form-urlencoded"
}
data = {
    "grant_type": "authorization_code",
    "redirect_uri": redirect_uri,
    "code": code
}

print(f"\nSending POST to {token_url}...")
response = requests.post(token_url, headers=headers, data=data)

print(f"Status Code: {response.status_code}")
print("Response Body:")
print(response.text)
