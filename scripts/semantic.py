"""Optional server-side semantic review adapter contract; intentionally disabled.

Implement review_batch(records, budget) in an independent integration. Call ONLY
from the collector/Actions environment, never from browser code. Persist model
reviews separately from source metadata, keyed by (DOI, abstract hash, model,
prompt version). Stop at max_records/max_cost_usd; use Secrets for credentials.
Do not replace source title/abstract or describe model claims as verified facts.
The built-in keyword engine requires no provider or API key.
"""
from typing import Protocol
class SemanticReviewer(Protocol):
    def review_batch(self, records: list[dict], *, max_records: int, max_cost_usd: float) -> list[dict]: ...
