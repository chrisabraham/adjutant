"""Model calls: one model per job, effort per job, refusal fallback, and a cost ledger.

Pattern 7. A model per job, with fallbacks and a cost ledger.

The Anthropic SDK is optional. Without it (or without a key) everything deterministic
still works, and the parts that need writing or judgment say so plainly.

  key:     ~/.config/adjutant/anthropic-api-key
  routes:  ~/.config/adjutant/models.json   {"chat": "claude-sonnet-5-5", ...}
  tests:   ADJUTANT_ANTHROPIC_URL points the SDK at a fake server
"""

import json
import os

from . import clock, store

SCHEMA = """
CREATE TABLE IF NOT EXISTS usage (
    id INTEGER PRIMARY KEY,
    time TEXT NOT NULL,
    job TEXT NOT NULL,
    model TEXT NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    cost REAL
);
"""

JOBS = {
    "chat": "questions and conversation",
    "brief": "good morning, good night, week in review",
    "extract": "short structured reading of loose sentences",
}
DEFAULT_ROUTES = {"chat": "claude-opus-5-5", "brief": "claude-opus-5-5", "extract": "claude-haiku-5-5"}
# How hard the model thinks. Opus 5.5 and Haiku 5.5 default to medium, so it is always set.
EFFORT = {"chat": "low", "brief": "medium", "extract": "low"}
ALIASES = {"opus": "claude-opus-5-5", "sonnet": "claude-sonnet-5-5", "haiku": "claude-haiku-5-5",
           "fable": "claude-fable-5-1"}
# Dollars per million tokens, input and output. Check current prices before relying on these.
PRICES = {"claude-opus-5-5": (4.00, 20.00), "claude-sonnet-5-5": (2.00, 10.00),
          "claude-haiku-5-5": (0.10, 0.50), "claude-fable-5-1": (10.00, 50.00)}
# If a safety classifier declines, Anthropic retries on the model it recommends, in the same request.
FALLBACK_MODELS = {"claude-opus-5-5", "claude-sonnet-5-5", "claude-fable-5-1"}


class Unavailable(Exception):
    pass


def routes():
    current = dict(DEFAULT_ROUTES)
    try:
        saved = json.loads((store.config_dir() / "models.json").read_text(encoding="utf-8"))
        current.update({k: v for k, v in saved.items() if k in JOBS})
    except (OSError, ValueError):
        pass
    return current


def set_route(job, alias):
    model = ALIASES.get(alias.lower(), alias)
    jobs = list(JOBS) if job == "everything" else [job]
    if any(j not in JOBS for j in jobs):
        return "Jobs are: " + ", ".join(JOBS) + " (or everything)."
    current = routes()
    current.update({j: model for j in jobs})
    path = store.config_dir() / "models.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
    return f"{', '.join(jobs)} → {model}"


def cost(model, tokens_in, tokens_out):
    rates = PRICES.get(model)
    return None if rates is None else tokens_in / 1e6 * rates[0] + tokens_out / 1e6 * rates[1]


def available():
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return False
    return bool(store.secret("anthropic-api-key"))


def call(connection, job, system, messages, schema=None):
    """One model call for one job. Returns the text. Raises Unavailable with a plain reason."""
    try:
        import anthropic
    except ImportError:
        raise Unavailable("the Anthropic SDK isn't installed (pip install -r requirements.txt)") from None
    key = store.secret("anthropic-api-key")
    if not key:
        raise Unavailable("no key at ~/.config/adjutant/anthropic-api-key")
    model = routes()[job]
    client = anthropic.Anthropic(api_key=key, base_url=os.environ.get("ADJUTANT_ANTHROPIC_URL") or None,
                                 timeout=180.0, max_retries=2)
    params = {
        "model": model, "max_tokens": 16000, "messages": messages,
        # Stable instructions first and marked cacheable: repeats read them at a fraction of the price.
        "system": [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        "output_config": {"effort": EFFORT[job]},
    }
    if schema:
        params["output_config"]["format"] = {"type": "json_schema", "schema": schema}
    try:
        if model in FALLBACK_MODELS:
            response = client.beta.messages.create(betas=["server-side-fallback-2026-07-01"],
                                                   fallbacks="default", **params)
        else:
            response = client.messages.create(**params)
    except (anthropic.AuthenticationError, anthropic.PermissionDeniedError):
        raise Unavailable("Anthropic refused the key") from None
    except anthropic.RateLimitError:
        raise Unavailable("Anthropic rate limit; try again in a minute") from None
    except anthropic.APIConnectionError:
        raise Unavailable("couldn't reach Anthropic") from None
    except anthropic.APIStatusError as error:
        raise Unavailable(f"Anthropic error {error.status_code}") from None
    if response.stop_reason == "refusal":
        raise Unavailable("the model declined this one")
    usage = response.usage
    tokens_in = (usage.input_tokens or 0) + (getattr(usage, "cache_creation_input_tokens", 0) or 0) \
        + (getattr(usage, "cache_read_input_tokens", 0) or 0)
    tokens_out = usage.output_tokens or 0
    with connection:
        connection.execute(
            "INSERT INTO usage(time, job, model, input_tokens, output_tokens, cost) VALUES (?, ?, ?, ?, ?, ?)",
            (clock.now(), job, response.model, tokens_in, tokens_out, cost(model, tokens_in, tokens_out)))
    return "".join(block.text for block in response.content if block.type == "text").strip()


def spend_report(connection):
    rows = connection.execute("SELECT job, model, COUNT(*) n, SUM(input_tokens) i, SUM(output_tokens) o, "
                              "SUM(cost) c FROM usage GROUP BY job, model ORDER BY job").fetchall()
    if not rows:
        return "No model calls recorded yet."
    lines = [f"{r['job']:8} {r['model']:20} {r['n']:>5} calls  {r['i']:>9} in  {r['o']:>8} out  "
             + (f"${r['c']:.4f}" if r["c"] is not None else "(no price on file)") for r in rows]
    total = sum(r["c"] or 0 for r in rows)
    return "\n".join(lines + [f"Estimated total: ${total:.4f}"])
