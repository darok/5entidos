import os
import types


def _patch_supabase_key_regex():
    """Allow new Supabase sb_ key format rejected by supabase-py 2.15.2 JWT validator."""
    import re
    _old = r"^[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*$"
    _new = r"^(sb_[a-zA-Z0-9_-]+|[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*)$"

    def _match(pattern, string, *a, **kw):
        return re.match(_new if pattern == _old else pattern, string, *a, **kw)

    def _re_wrapper():
        w = types.SimpleNamespace(**{k: getattr(re, k) for k in dir(re) if not k.startswith("__")})
        w.match = _match
        return w

    try:
        import supabase._sync.client as m
        m.re = _re_wrapper()
    except ImportError:
        pass
    try:
        import supabase._async.client as m
        m.re = _re_wrapper()
    except ImportError:
        pass


_patch_supabase_key_regex()

try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            try:
                import streamlit as st
                url = url or st.secrets.get("SUPABASE_URL")
                key = key or st.secrets.get("SUPABASE_KEY")
            except Exception:
                pass
        _client = create_client(url, key)
    return _client
