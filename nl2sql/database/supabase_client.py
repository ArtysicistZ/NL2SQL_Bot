from __future__ import annotations

from supabase import Client, create_client

from ..config import load_config, require_supabase_config

_CLIENT: Client | None = None


def get_supabase_client() -> Client:
    global _CLIENT
    if _CLIENT is None:
        config = load_config()
        supabase_url, supabase_key = require_supabase_config(config)
        _CLIENT = create_client(supabase_url, supabase_key)
    return _CLIENT
