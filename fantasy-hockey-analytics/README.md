# Fantasy Hockey Analytics

This project connects to the Yahoo Fantasy API to retrieve and display NHL fantasy league data.

## Prerequisites

- Python 3.12+
- Yahoo Developer Credentials (Client ID and Client Secret)

## Setup

1.  **Create a Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Credentials**:
    - Copy `.env.template` to `.env`.
    - Open `.env` and paste your Yahoo Client ID and Secret.
    ```
    YAHOO_CLIENT_ID=...
    YAHOO_CLIENT_SECRET=...
    ```

## Usage

1.  **First Run (Authentication)**:
    ```bash
    python main.py
    ```
    - The browser will open to Yahoo's authorization page.
    - Click "Agree".
    - Copy the verification code displayed.
    - Paste the code into the terminal when prompted.

2.  **Subsequent Runs**:
    ```bash
    python main.py
    ```
    Authentication will be automatic using the saved token.

## Project Structure

- `src/auth.py`: Handles OAuth flow using `yfpy`.
- `src/data_fetcher.py`: Logic for discovering game IDs and fetching matchups.
- `src/models.py`: Data structures for teams and matchups.
- `src/display.py`: Console output formatting.
