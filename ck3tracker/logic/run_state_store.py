"""Transactional DuckDB store for mutable playthrough state."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd


TRIAL_DIR = Path(__file__).parents[1] / "data" / "trial"
DB_PATH = TRIAL_DIR / "run_state.duckdb"
STATE_TABLES = (
    "county_lifecycle",
    "acquisition_events",
    "barony_state",
    "transaction_events",
    "barony_observations",
)


def connect() -> duckdb.DuckDBPyConnection:
    """Open the run-state database and migrate existing Parquet state once."""
    TRIAL_DIR.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(str(DB_PATH))
    for table_name in STATE_TABLES:
        exists = connection.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",
            [table_name],
        ).fetchone()[0]
        if not exists:
            source_path = TRIAL_DIR / f"{table_name}.parquet"
            if source_path.exists():
                connection.execute(
                    f"CREATE TABLE {table_name} AS SELECT * FROM read_parquet(?)",
                    [str(source_path)],
                )
            elif table_name == "transaction_events":
                connection.execute(
                    """
                    CREATE TABLE transaction_events (
                        transaction_id VARCHAR,
                        playthrough_id VARCHAR,
                        event_type VARCHAR,
                        scope VARCHAR,
                        target_id VARCHAR,
                        observed_at VARCHAR,
                        recorded_at_utc VARCHAR,
                        source VARCHAR,
                        note VARCHAR
                    )
                    """
                )
            elif table_name == "barony_observations":
                connection.execute(
                    """
                    CREATE TABLE barony_observations (
                        observation_id VARCHAR,
                        transaction_id VARCHAR,
                        playthrough_id VARCHAR,
                        barony_id VARCHAR,
                        county_id VARCHAR,
                        duchy_id VARCHAR,
                        barony_name VARCHAR,
                        holding_type VARCHAR,
                        holder_type VARCHAR,
                        tax DOUBLE,
                        levies DOUBLE,
                        plague_resistance DOUBLE,
                        note VARCHAR,
                        observed_at VARCHAR,
                        source VARCHAR
                    )
                    """
                )
    return connection


def load_table(table_name: str) -> pd.DataFrame:
    """Load one mutable run-state table from DuckDB."""
    if table_name not in STATE_TABLES:
        raise ValueError(f"Unsupported run-state table: {table_name}")
    connection = connect()
    try:
        return connection.execute(f"SELECT * FROM {table_name}").fetchdf()
    finally:
        connection.close()


def replace_rows(
    table_name: str,
    frame: pd.DataFrame,
    key_columns: list[str],
) -> None:
    """Replace rows by stable key inside one DuckDB transaction."""
    if frame.empty:
        return
    connection = connect()
    try:
        connection.register("incoming_rows", frame)
        connection.execute("BEGIN TRANSACTION")
        for _, row in frame.iterrows():
            predicates = " AND ".join(f"{column} = ?" for column in key_columns)
            connection.execute(
                f"DELETE FROM {table_name} WHERE {predicates}",
                [row[column] for column in key_columns],
            )
        connection.execute(f"INSERT INTO {table_name} SELECT * FROM incoming_rows")
        connection.execute("COMMIT")
    except Exception:
        connection.execute("ROLLBACK")
        raise
    finally:
        connection.close()


def update_county_lifecycle(
    playthrough_id: str,
    county_id: str,
    lifecycle_state: str,
    active_in_editor: bool,
    reason: str,
) -> None:
    """Upsert one sparse lifecycle row transactionally."""
    connection = connect()
    try:
        connection.execute("BEGIN TRANSACTION")
        connection.execute(
            "DELETE FROM county_lifecycle WHERE playthrough_id = ? AND county_id = ?",
            [playthrough_id, county_id],
        )
        connection.execute(
            "INSERT INTO county_lifecycle VALUES (?, ?, ?, ?, ?)",
            [playthrough_id, county_id, lifecycle_state, active_in_editor, reason],
        )
        connection.execute("COMMIT")
    except Exception:
        connection.execute("ROLLBACK")
        raise
    finally:
        connection.close()
