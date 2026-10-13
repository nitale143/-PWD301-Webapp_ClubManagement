"""Opt-in real provider connectivity check; no member data or real database."""
from pathlib import Path
from dotenv import load_dotenv


def main():
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    from app import create_app
    from app.services.assistant import RulesProvider, get_provider
    from app.services.common import DomainError

    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                      "MAIL_ENABLED": False})
    with app.app_context():
        provider = get_provider()
        if isinstance(provider, RulesProvider):
            print("No model provider configured; rules-only mode.")
            return 1
        try:
            reply = provider.complete("Connectivity check. No tools or private data.",
                                      "Reply only OK.", max_tokens=64, purpose="connection_check")
        except DomainError as error:
            print("Provider check failed:", str(error))
            return 1
        print("Provider check passed:", type(provider).__name__, "nonempty response:", bool(reply))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
