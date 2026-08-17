"""Build trial lifecycle metadata without deleting historical county observations."""

from pathlib import Path

import pandas as pd


OUTPUT_PATH = Path(__file__).parents[1] / "data" / "trial" / "county_lifecycle.parquet"


lifecycle = pd.DataFrame(
    [
        {
            "playthrough_id": "trial_dead_run",
            "county_id": "c_annaba",
            "lifecycle_state": "archived",
            "active_in_editor": False,
            "reason": "Held as historical evidence; complete Constantine proof is the active UI slice.",
        },
        {
            "playthrough_id": "trial_dead_run",
            "county_id": "c_constantine",
            "lifecycle_state": "active",
            "active_in_editor": True,
            "reason": "Current screenshot-complete proof slice.",
        },
    ]
)

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
lifecycle.to_parquet(OUTPUT_PATH, index=False)
print(f"Wrote {OUTPUT_PATH}")
