import os

def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes"}

DB_PATH = os.getenv("DLH_DB_PATH", "deadlink.db")
CORS_ORIGINS = list(dict.fromkeys([
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://deadlink-hunter.vercel.app",
    *(o.strip() for o in os.getenv("DLH_CORS_ORIGINS", "").split(",") if o.strip()),
]))
MAX_CONCURRENT_SCANS = int(os.getenv("DLH_MAX_CONCURRENT_SCANS", "2"))
ALLOW_PRIVATE_HOSTS = _bool("DLH_ALLOW_PRIVATE_HOSTS")

USER_AGENT = "DeadLinkHunter/0.2 (+https://github.com/deadlink-hunter; link checker)"
MAX_REDIRECTS = 5
MAX_PAGE_BYTES = 2_000_000
PAGE_CONCURRENCY = 5
LINK_CONCURRENCY = 12
HARD_MAX_PAGES = 200
