"""Gmail integration via OAuth2.

First-time setup:
  1. Create a project at https://console.cloud.google.com
  2. Enable the Gmail API
  3. Create OAuth 2.0 credentials (Desktop App) and download as credentials.json
  4. Place credentials.json in the dashboard/ folder
  5. Run: python gmail_utils.py
     A browser window will open asking for permission — approve it.
     A token.json file is saved and reused automatically.
"""

import os
from datetime import datetime, timezone
import email.utils

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "credentials.json")
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "token.json")


def _get_service():
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
    except ImportError:
        return None, "Bibliotecas Google não instaladas. Execute: pip install google-api-python-client google-auth-oauthlib"

    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None

        if not creds:
            if not os.path.exists(CREDENTIALS_FILE):
                return None, (
                    "credentials.json não encontrado.\n"
                    "Siga as instruções em gmail_utils.py para configurar o Gmail."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as fh:
            fh.write(creds.to_json())

    try:
        service = build("gmail", "v1", credentials=creds)
        return service, None
    except Exception as exc:
        return None, str(exc)


def _parse_date(date_str: str) -> str:
    try:
        dt = email.utils.parsedate_to_datetime(date_str)
        now = datetime.now(timezone.utc)
        diff = (now - dt.astimezone(timezone.utc)).total_seconds()
        if diff < 3600:
            return f"{int(diff // 60)}min atrás"
        if diff < 86400:
            return f"{int(diff // 3600)}h atrás"
        return f"{int(diff // 86400)}d atrás"
    except Exception:
        return date_str[:16]


def _clean_sender(from_str: str) -> str:
    if "<" in from_str:
        name = from_str.split("<")[0].strip().strip('"')
        return name if name else from_str.split("<")[1].rstrip(">")
    return from_str


def fetch_todos(max_items: int = 12) -> tuple[list[dict], str | None]:
    """Fetch important unread emails. Returns (todos, error_message)."""
    service, err = _get_service()
    if err:
        return [], err

    try:
        result = service.users().messages().list(
            userId="me",
            q="in:inbox -category:promotions -category:social",
            maxResults=max_items,
        ).execute()

        messages = result.get("messages", [])
        todos = []

        for msg in messages:
            data = service.users().messages().get(
                userId="me",
                id=msg["id"],
                format="metadata",
                metadataHeaders=["Subject", "From", "Date"],
            ).execute()

            headers = {h["name"]: h["value"] for h in data["payload"]["headers"]}
            todos.append({
                "id": msg["id"],
                "subject": headers.get("Subject", "(Sem assunto)"),
                "from": _clean_sender(headers.get("From", "Desconhecido")),
                "date": _parse_date(headers.get("Date", "")),
            })

        return todos, None

    except Exception as exc:
        return [], str(exc)


def archive_email(message_id: str) -> bool:
    """Remove email from inbox (mark as done)."""
    service, err = _get_service()
    if err:
        return False
    try:
        service.users().messages().modify(
            userId="me",
            id=message_id,
            body={"removeLabelIds": ["INBOX", "UNREAD"]},
        ).execute()
        return True
    except Exception:
        return False


if __name__ == "__main__":
    print("Iniciando autenticação Gmail...")
    todos, err = fetch_todos(max_items=3)
    if err:
        print(f"Erro: {err}")
    else:
        print(f"Autenticado! {len(todos)} e-mails importantes encontrados.")
        for t in todos:
            print(f"  - [{t['date']}] {t['from']}: {t['subject']}")
