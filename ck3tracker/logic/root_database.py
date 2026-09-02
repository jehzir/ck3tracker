"""Connection and schema bootstrap for the production CK3 Tracker database."""

from __future__ import annotations

from pathlib import Path

import duckdb


DB_PATH = Path(__file__).parents[1] / "ck3tracker_v2.duckdb"


def connect(database_path: str | Path | None = None) -> duckdb.DuckDBPyConnection:
    """Open the root database and ensure the baseline foundation exists."""
    path = Path(database_path) if database_path is not None else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(str(path))
    _bootstrap(connection)
    return connection


def _bootstrap(connection: duckdb.DuckDBPyConnection) -> None:
    connection.execute("CREATE SCHEMA IF NOT EXISTS source")
    connection.execute("CREATE SCHEMA IF NOT EXISTS reference")
    connection.execute("CREATE SCHEMA IF NOT EXISTS journal")
    connection.execute("CREATE SCHEMA IF NOT EXISTS app")

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS source.reference_snapshots (
            reference_snapshot_id VARCHAR PRIMARY KEY,
            game_version VARCHAR NOT NULL,
            steam_build_id VARCHAR,
            map_profile VARCHAR NOT NULL,
            review_status VARCHAR NOT NULL,
            created_at_utc TIMESTAMP NOT NULL DEFAULT current_timestamp
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS source.source_files (
            reference_snapshot_id VARCHAR NOT NULL,
            relative_path VARCHAR NOT NULL,
            source_group VARCHAR NOT NULL,
            byte_size BIGINT NOT NULL,
            modified_at_utc TIMESTAMP NOT NULL,
            sha256 VARCHAR NOT NULL,
            PRIMARY KEY (reference_snapshot_id, relative_path)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS source.parser_runs (
            parser_run_id VARCHAR PRIMARY KEY,
            reference_snapshot_id VARCHAR NOT NULL,
            parser_name VARCHAR NOT NULL,
            parser_version VARCHAR NOT NULL,
            status VARCHAR NOT NULL,
            started_at_utc TIMESTAMP NOT NULL,
            completed_at_utc TIMESTAMP,
            row_count BIGINT,
            warning_count BIGINT,
            error_text VARCHAR
        )
        """
    )
    connection.execute(
        "ALTER TABLE source.source_files ADD COLUMN IF NOT EXISTS parser_run_id VARCHAR"
    )
    connection.execute(
        """
        UPDATE source.source_files AS source_file
        SET parser_run_id = latest.parser_run_id
        FROM (
            SELECT reference_snapshot_id, parser_name, parser_run_id
            FROM (
                SELECT reference_snapshot_id, parser_name, parser_run_id,
                       row_number() OVER (
                           PARTITION BY reference_snapshot_id, parser_name
                           ORDER BY started_at_utc DESC, parser_run_id DESC
                       ) AS run_order
                FROM source.parser_runs
                WHERE status = 'completed'
            ) completed_runs
            WHERE run_order = 1
        ) latest
        WHERE source_file.parser_run_id IS NULL
          AND source_file.reference_snapshot_id = latest.reference_snapshot_id
          AND source_file.source_group = latest.parser_name
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS source.wiki_pages (
            reference_snapshot_id VARCHAR NOT NULL,
            page_key VARCHAR NOT NULL,
            canonical_url VARCHAR NOT NULL,
            permanent_url VARCHAR NOT NULL,
            revision_id VARCHAR NOT NULL,
            retrieved_at_utc TIMESTAMP NOT NULL,
            stated_game_version VARCHAR,
            review_status VARCHAR NOT NULL,
            PRIMARY KEY (reference_snapshot_id, page_key)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS source.wiki_page_links (
            reference_snapshot_id VARCHAR NOT NULL,
            from_page_key VARCHAR NOT NULL,
            to_page_key VARCHAR NOT NULL,
            link_text VARCHAR NOT NULL,
            link_url VARCHAR NOT NULL,
            PRIMARY KEY (reference_snapshot_id, from_page_key, to_page_key)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS source.localization_declarations (
            reference_snapshot_id VARCHAR NOT NULL,
            language VARCHAR NOT NULL,
            localization_key VARCHAR NOT NULL,
            value_version INTEGER,
            display_value VARCHAR NOT NULL,
            relative_path VARCHAR NOT NULL,
            source_line INTEGER NOT NULL,
            declaration_order BIGINT NOT NULL,
            is_winner BOOLEAN NOT NULL,
            resolution_status VARCHAR NOT NULL,
            PRIMARY KEY (reference_snapshot_id, language, declaration_order)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS source.title_history_declarations (
            reference_snapshot_id VARCHAR NOT NULL,
            declaration_order BIGINT NOT NULL,
            title_id VARCHAR NOT NULL,
            effective_date VARCHAR NOT NULL,
            operation_order INTEGER NOT NULL,
            operation_key VARCHAR NOT NULL,
            value_kind VARCHAR NOT NULL,
            scalar_value VARCHAR,
            raw_script VARCHAR NOT NULL,
            source_path VARCHAR NOT NULL,
            source_line_start INTEGER NOT NULL,
            source_line_end INTEGER NOT NULL,
            encoding_name VARCHAR NOT NULL,
            parser_version VARCHAR NOT NULL,
            resolution_status VARCHAR NOT NULL,
            PRIMARY KEY (reference_snapshot_id, declaration_order)
        )
        """
    )
    connection.execute(
        "ALTER TABLE source.title_history_declarations ADD COLUMN IF NOT EXISTS source_block_order BIGINT"
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS source.title_history_blocks (
            reference_snapshot_id VARCHAR NOT NULL,
            source_block_order BIGINT NOT NULL,
            title_id VARCHAR NOT NULL,
            source_path VARCHAR NOT NULL,
            source_line_start INTEGER NOT NULL,
            source_line_end INTEGER NOT NULL,
            raw_script VARCHAR NOT NULL,
            raw_sha256 VARCHAR NOT NULL,
            semantic_sha256 VARCHAR NOT NULL,
            duplicate_classification VARCHAR NOT NULL,
            baseline_conflict_fields VARCHAR,
            PRIMARY KEY (reference_snapshot_id, source_block_order)
        )
        """
    )
    connection.execute(
        "ALTER TABLE source.title_history_blocks ADD COLUMN IF NOT EXISTS resolution_status VARCHAR"
    )
    connection.execute(
        "ALTER TABLE source.title_history_blocks ADD COLUMN IF NOT EXISTS is_winner BOOLEAN"
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS source.character_history_declarations (
            reference_snapshot_id VARCHAR NOT NULL,
            declaration_order BIGINT NOT NULL,
            character_id VARCHAR NOT NULL,
            effective_date VARCHAR,
            operation_order INTEGER NOT NULL,
            operation_key VARCHAR NOT NULL,
            value_kind VARCHAR NOT NULL,
            scalar_value VARCHAR,
            raw_script VARCHAR NOT NULL,
            source_path VARCHAR NOT NULL,
            source_line_start INTEGER NOT NULL,
            source_line_end INTEGER NOT NULL,
            encoding_name VARCHAR NOT NULL,
            parser_version VARCHAR NOT NULL,
            resolution_status VARCHAR NOT NULL,
            PRIMARY KEY (reference_snapshot_id, declaration_order)
        )
        """
    )
    connection.execute(
        "ALTER TABLE source.character_history_declarations ADD COLUMN IF NOT EXISTS source_block_order BIGINT"
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS source.character_history_blocks (
            reference_snapshot_id VARCHAR NOT NULL,
            source_block_order BIGINT NOT NULL,
            character_id VARCHAR NOT NULL,
            source_path VARCHAR NOT NULL,
            source_line_start INTEGER NOT NULL,
            source_line_end INTEGER NOT NULL,
            raw_script VARCHAR NOT NULL,
            raw_sha256 VARCHAR NOT NULL,
            semantic_sha256 VARCHAR NOT NULL,
            duplicate_classification VARCHAR NOT NULL,
            baseline_conflict_fields VARCHAR,
            PRIMARY KEY (reference_snapshot_id, source_block_order)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS source.bookmark_declarations (
            reference_snapshot_id VARCHAR NOT NULL,
            declaration_order BIGINT NOT NULL,
            entity_kind VARCHAR NOT NULL,
            entity_id VARCHAR NOT NULL,
            raw_script VARCHAR NOT NULL,
            source_path VARCHAR NOT NULL,
            source_line_start INTEGER NOT NULL,
            source_line_end INTEGER NOT NULL,
            encoding_name VARCHAR NOT NULL,
            parser_version VARCHAR NOT NULL,
            resolution_status VARCHAR NOT NULL,
            PRIMARY KEY (reference_snapshot_id, declaration_order)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reference.baselines (
            baseline_id VARCHAR PRIMARY KEY,
            reference_snapshot_id VARCHAR NOT NULL,
            bookmark_id VARCHAR,
            baseline_date DATE NOT NULL,
            label VARCHAR NOT NULL,
            support_status VARCHAR NOT NULL,
            historical_state_complete BOOLEAN NOT NULL DEFAULT false,
            UNIQUE (reference_snapshot_id, baseline_date)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reference.titles (
            baseline_id VARCHAR NOT NULL,
            title_id VARCHAR NOT NULL,
            title_rank VARCHAR NOT NULL,
            parent_title_id VARCHAR,
            de_jure_liege_id VARCHAR,
            localization_key VARCHAR,
            display_name VARCHAR NOT NULL,
            selectable BOOLEAN NOT NULL DEFAULT true,
            PRIMARY KEY (baseline_id, title_id)
        )
        """
    )
    connection.execute(
        "ALTER TABLE reference.titles ADD COLUMN IF NOT EXISTS source_path VARCHAR"
    )
    connection.execute(
        "ALTER TABLE reference.titles ADD COLUMN IF NOT EXISTS source_line INTEGER"
    )
    connection.execute(
        "ALTER TABLE reference.titles ADD COLUMN IF NOT EXISTS parser_version VARCHAR"
    )
    connection.execute(
        "ALTER TABLE reference.titles ADD COLUMN IF NOT EXISTS validation_status VARCHAR"
    )
    connection.execute(
        "ALTER TABLE reference.titles ADD COLUMN IF NOT EXISTS validation_note VARCHAR"
    )
    connection.execute(
        "ALTER TABLE reference.titles ADD COLUMN IF NOT EXISTS source_order BIGINT"
    )
    connection.execute(
        "ALTER TABLE reference.titles ADD COLUMN IF NOT EXISTS declared_capital_title_id VARCHAR"
    )
    connection.execute(
        "ALTER TABLE reference.titles ADD COLUMN IF NOT EXISTS static_capital_title_id VARCHAR"
    )
    connection.execute(
        "ALTER TABLE reference.titles ADD COLUMN IF NOT EXISTS static_capital_status VARCHAR"
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reference.localizations (
            reference_snapshot_id VARCHAR NOT NULL,
            language VARCHAR NOT NULL,
            localization_key VARCHAR NOT NULL,
            value_version INTEGER,
            display_value VARCHAR NOT NULL,
            source_path VARCHAR NOT NULL,
            source_line INTEGER NOT NULL,
            parser_version VARCHAR NOT NULL,
            resolution_status VARCHAR NOT NULL,
            PRIMARY KEY (reference_snapshot_id, language, localization_key)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reference.governments (
            reference_snapshot_id VARCHAR NOT NULL,
            government_id VARCHAR NOT NULL,
            source_path VARCHAR NOT NULL,
            source_line_start INTEGER NOT NULL,
            source_line_end INTEGER NOT NULL,
            source_order BIGINT NOT NULL,
            raw_script VARCHAR NOT NULL,
            parser_version VARCHAR NOT NULL,
            wiki_page_key VARCHAR NOT NULL,
            validation_status VARCHAR NOT NULL,
            validation_note VARCHAR,
            PRIMARY KEY (reference_snapshot_id, government_id)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reference.cultures (
            reference_snapshot_id VARCHAR NOT NULL,
            culture_id VARCHAR NOT NULL,
            source_path VARCHAR NOT NULL,
            source_line_start INTEGER NOT NULL,
            source_line_end INTEGER NOT NULL,
            source_order BIGINT NOT NULL,
            raw_script VARCHAR NOT NULL,
            parser_version VARCHAR NOT NULL,
            wiki_page_key VARCHAR NOT NULL,
            validation_status VARCHAR NOT NULL,
            validation_note VARCHAR,
            PRIMARY KEY (reference_snapshot_id, culture_id)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reference.languages (
            reference_snapshot_id VARCHAR NOT NULL,
            language_id VARCHAR NOT NULL,
            source_path VARCHAR NOT NULL,
            source_line_start INTEGER NOT NULL,
            source_line_end INTEGER NOT NULL,
            source_order BIGINT NOT NULL,
            raw_script VARCHAR NOT NULL,
            parser_version VARCHAR NOT NULL,
            validation_status VARCHAR NOT NULL,
            validation_note VARCHAR,
            PRIMARY KEY (reference_snapshot_id, language_id)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reference.culture_native_languages (
            reference_snapshot_id VARCHAR NOT NULL,
            culture_id VARCHAR NOT NULL,
            language_id VARCHAR NOT NULL,
            source_path VARCHAR NOT NULL,
            source_line_start INTEGER NOT NULL,
            source_line_end INTEGER NOT NULL,
            source_declaration_order BIGINT NOT NULL,
            parser_version VARCHAR NOT NULL,
            validation_status VARCHAR NOT NULL,
            validation_note VARCHAR,
            PRIMARY KEY (reference_snapshot_id, culture_id)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reference.faiths (
            reference_snapshot_id VARCHAR NOT NULL,
            faith_id VARCHAR NOT NULL,
            religion_id VARCHAR NOT NULL,
            source_path VARCHAR NOT NULL,
            source_line_start INTEGER NOT NULL,
            source_line_end INTEGER NOT NULL,
            source_order BIGINT NOT NULL,
            raw_script VARCHAR NOT NULL,
            parser_version VARCHAR NOT NULL,
            wiki_page_key VARCHAR NOT NULL,
            validation_status VARCHAR NOT NULL,
            validation_note VARCHAR,
            PRIMARY KEY (reference_snapshot_id, faith_id)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reference.title_baseline_state_faiths (
            baseline_id VARCHAR NOT NULL,
            title_id VARCHAR NOT NULL,
            reference_snapshot_id VARCHAR NOT NULL,
            faith_id VARCHAR NOT NULL,
            effective_date DATE NOT NULL,
            source_group VARCHAR NOT NULL,
            source_declaration_order BIGINT NOT NULL,
            validation_status VARCHAR NOT NULL,
            validation_note VARCHAR,
            PRIMARY KEY (baseline_id, title_id),
            FOREIGN KEY (baseline_id, title_id)
                REFERENCES reference.titles (baseline_id, title_id),
            FOREIGN KEY (reference_snapshot_id, faith_id)
                REFERENCES reference.faiths (reference_snapshot_id, faith_id)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reference.dynasties (
            reference_snapshot_id VARCHAR NOT NULL,
            dynasty_id VARCHAR NOT NULL,
            source_path VARCHAR NOT NULL,
            source_line_start INTEGER NOT NULL,
            source_line_end INTEGER NOT NULL,
            source_order BIGINT NOT NULL,
            raw_script VARCHAR NOT NULL,
            parser_version VARCHAR NOT NULL,
            wiki_page_key VARCHAR NOT NULL,
            validation_status VARCHAR NOT NULL,
            validation_note VARCHAR,
            PRIMARY KEY (reference_snapshot_id, dynasty_id)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reference.dynasty_houses (
            reference_snapshot_id VARCHAR NOT NULL,
            dynasty_house_id VARCHAR NOT NULL,
            dynasty_id VARCHAR NOT NULL,
            source_path VARCHAR NOT NULL,
            source_line_start INTEGER NOT NULL,
            source_line_end INTEGER NOT NULL,
            source_order BIGINT NOT NULL,
            raw_script VARCHAR NOT NULL,
            parser_version VARCHAR NOT NULL,
            wiki_page_key VARCHAR NOT NULL,
            validation_status VARCHAR NOT NULL,
            validation_note VARCHAR,
            PRIMARY KEY (reference_snapshot_id, dynasty_house_id)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reference.title_history_events (
            reference_snapshot_id VARCHAR NOT NULL,
            title_id VARCHAR NOT NULL,
            effective_date VARCHAR NOT NULL,
            event_sequence BIGINT NOT NULL,
            event_type VARCHAR NOT NULL,
            text_value VARCHAR,
            integer_value INTEGER,
            source_declaration_order BIGINT NOT NULL,
            validation_status VARCHAR NOT NULL,
            validation_note VARCHAR,
            PRIMARY KEY (reference_snapshot_id, event_sequence)
        )
        """
    )
    connection.execute(
        "ALTER TABLE reference.title_history_events ADD COLUMN IF NOT EXISTS required_game_start_date VARCHAR"
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reference.law_definitions (
            reference_snapshot_id VARCHAR NOT NULL,
            law_id VARCHAR NOT NULL,
            law_group_id VARCHAR NOT NULL,
            source_path VARCHAR NOT NULL,
            source_line_start INTEGER NOT NULL,
            source_line_end INTEGER NOT NULL,
            source_order BIGINT NOT NULL,
            raw_script VARCHAR NOT NULL,
            raw_sha256 VARCHAR NOT NULL,
            parser_version VARCHAR NOT NULL,
            validation_status VARCHAR NOT NULL,
            validation_note VARCHAR,
            PRIMARY KEY (reference_snapshot_id, law_id)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reference.title_baseline_laws (
            baseline_id VARCHAR NOT NULL,
            title_id VARCHAR NOT NULL,
            law_order INTEGER NOT NULL,
            law_id VARCHAR NOT NULL,
            effective_date DATE NOT NULL,
            source_declaration_order BIGINT NOT NULL,
            validation_status VARCHAR NOT NULL,
            validation_note VARCHAR,
            PRIMARY KEY (baseline_id, title_id, law_order)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reference.title_baseline_de_jure_lieges (
            baseline_id VARCHAR NOT NULL,
            title_id VARCHAR NOT NULL,
            de_jure_liege_title_id VARCHAR,
            de_jure_liege_status VARCHAR NOT NULL,
            effective_date DATE NOT NULL,
            source_declaration_order BIGINT NOT NULL,
            validation_status VARCHAR NOT NULL,
            validation_note VARCHAR,
            PRIMARY KEY (baseline_id, title_id)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reference.subject_contract_group_definitions (
            reference_snapshot_id VARCHAR NOT NULL,
            contract_group_id VARCHAR NOT NULL,
            is_tributary BOOLEAN NOT NULL,
            source_path VARCHAR NOT NULL,
            source_line_start INTEGER NOT NULL,
            source_line_end INTEGER NOT NULL,
            raw_script VARCHAR NOT NULL,
            raw_sha256 VARCHAR NOT NULL,
            parser_version VARCHAR NOT NULL,
            validation_status VARCHAR NOT NULL,
            validation_note VARCHAR,
            PRIMARY KEY (reference_snapshot_id, contract_group_id)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reference.title_baseline_tributaries (
            baseline_id VARCHAR NOT NULL,
            title_id VARCHAR NOT NULL,
            suzerain_title_id VARCHAR NOT NULL,
            contract_group_id VARCHAR NOT NULL,
            effective_date DATE NOT NULL,
            source_declaration_order BIGINT NOT NULL,
            validation_status VARCHAR NOT NULL,
            validation_note VARCHAR,
            PRIMARY KEY (baseline_id, title_id)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reference.title_baseline_variables (
            baseline_id VARCHAR NOT NULL,
            title_id VARCHAR NOT NULL,
            variable_name VARCHAR NOT NULL,
            value_kind VARCHAR NOT NULL,
            text_value VARCHAR NOT NULL,
            effective_date DATE NOT NULL,
            source_declaration_order BIGINT NOT NULL,
            validation_status VARCHAR NOT NULL,
            validation_note VARCHAR,
            PRIMARY KEY (baseline_id, title_id, variable_name)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reference.dynasty_baseline_prestige_constraints (
            baseline_id VARCHAR NOT NULL,
            dynasty_id VARCHAR NOT NULL,
            minimum_prestige_level INTEGER NOT NULL,
            value_status VARCHAR NOT NULL,
            effective_date DATE NOT NULL,
            source_title_id VARCHAR NOT NULL,
            source_holder_character_id VARCHAR NOT NULL,
            source_declaration_order BIGINT NOT NULL,
            helper_source_path VARCHAR NOT NULL,
            helper_raw_sha256 VARCHAR,
            validation_status VARCHAR NOT NULL,
            validation_note VARCHAR,
            PRIMARY KEY (baseline_id, source_declaration_order)
        )
        """
    )
    connection.execute(
        """
        ALTER TABLE reference.dynasty_baseline_prestige_constraints
        ALTER COLUMN helper_raw_sha256 DROP NOT NULL
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reference.title_baseline_name_overrides (
            baseline_id VARCHAR NOT NULL,
            title_id VARCHAR NOT NULL,
            localization_key VARCHAR,
            display_name VARCHAR,
            name_status VARCHAR NOT NULL,
            effective_date DATE NOT NULL,
            source_declaration_order BIGINT NOT NULL,
            validation_status VARCHAR NOT NULL,
            validation_note VARCHAR,
            PRIMARY KEY (baseline_id, title_id)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reference.title_baseline_states (
            baseline_id VARCHAR NOT NULL,
            title_id VARCHAR NOT NULL,
            holder_character_id VARCHAR,
            holder_status VARCHAR NOT NULL,
            liege_title_id VARCHAR,
            liege_status VARCHAR NOT NULL,
            government_id VARCHAR,
            government_status VARCHAR NOT NULL,
            development_level INTEGER,
            development_status VARCHAR NOT NULL,
            capital_title_id VARCHAR,
            capital_status VARCHAR NOT NULL,
            validation_status VARCHAR NOT NULL,
            validation_note VARCHAR,
            PRIMARY KEY (baseline_id, title_id)
        )
        """
    )
    connection.execute(
        "ALTER TABLE reference.title_baseline_states ADD COLUMN IF NOT EXISTS capital_source_event_sequence BIGINT"
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reference.character_history_events (
            reference_snapshot_id VARCHAR NOT NULL,
            character_id VARCHAR NOT NULL,
            effective_date VARCHAR NOT NULL,
            event_sequence BIGINT NOT NULL,
            event_type VARCHAR NOT NULL,
            text_value VARCHAR,
            source_declaration_order BIGINT NOT NULL,
            validation_status VARCHAR NOT NULL,
            validation_note VARCHAR,
            PRIMARY KEY (reference_snapshot_id, event_sequence)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reference.nicknames (
            reference_snapshot_id VARCHAR NOT NULL,
            nickname_id VARCHAR NOT NULL,
            is_bad BOOLEAN NOT NULL,
            is_prefix BOOLEAN NOT NULL,
            localization_language VARCHAR NOT NULL,
            localization_key VARCHAR NOT NULL,
            display_name VARCHAR NOT NULL,
            definition_source_path VARCHAR NOT NULL,
            definition_source_line_start INTEGER NOT NULL,
            definition_source_line_end INTEGER NOT NULL,
            definition_source_order BIGINT NOT NULL,
            raw_script VARCHAR NOT NULL,
            localization_source_path VARCHAR NOT NULL,
            localization_source_line INTEGER NOT NULL,
            parser_version VARCHAR NOT NULL,
            validation_status VARCHAR NOT NULL,
            validation_note VARCHAR,
            PRIMARY KEY (reference_snapshot_id, nickname_id),
            FOREIGN KEY (
                reference_snapshot_id,
                localization_language,
                localization_key
            ) REFERENCES reference.localizations (
                reference_snapshot_id,
                language,
                localization_key
            )
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reference.character_nickname_events (
            reference_snapshot_id VARCHAR NOT NULL,
            character_id VARCHAR NOT NULL,
            source_group VARCHAR NOT NULL,
            source_declaration_order BIGINT NOT NULL,
            source_operation_order INTEGER NOT NULL,
            effective_date VARCHAR NOT NULL,
            event_kind VARCHAR NOT NULL,
            nickname_id VARCHAR,
            source_path VARCHAR NOT NULL,
            source_line_start INTEGER NOT NULL,
            source_line_end INTEGER NOT NULL,
            validation_status VARCHAR NOT NULL,
            validation_note VARCHAR,
            PRIMARY KEY (
                reference_snapshot_id,
                character_id,
                source_group,
                source_declaration_order,
                source_operation_order
            ),
            FOREIGN KEY (reference_snapshot_id, nickname_id)
                REFERENCES reference.nicknames
                    (reference_snapshot_id, nickname_id),
            CHECK (
                (event_kind = 'set' AND nickname_id IS NOT NULL)
                OR (event_kind = 'clear' AND nickname_id IS NULL)
            )
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reference.character_baseline_states (
            baseline_id VARCHAR NOT NULL,
            character_id VARCHAR NOT NULL,
            display_name VARCHAR,
            sex VARCHAR NOT NULL,
            sex_status VARCHAR NOT NULL,
            culture_id VARCHAR,
            faith_id VARCHAR,
            faith_source_key VARCHAR,
            dynasty_id VARCHAR,
            dynasty_house_id VARCHAR,
            birth_date VARCHAR,
            death_date VARCHAR,
            lifecycle_status VARCHAR NOT NULL,
            validation_status VARCHAR NOT NULL,
            validation_note VARCHAR,
            PRIMARY KEY (baseline_id, character_id)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reference.character_baseline_nickname_states (
            baseline_id VARCHAR NOT NULL,
            character_id VARCHAR NOT NULL,
            reference_snapshot_id VARCHAR NOT NULL,
            active_nickname_id VARCHAR,
            last_event_kind VARCHAR NOT NULL,
            effective_date VARCHAR NOT NULL,
            source_group VARCHAR NOT NULL,
            source_declaration_order BIGINT NOT NULL,
            source_operation_order INTEGER NOT NULL,
            validation_status VARCHAR NOT NULL,
            validation_note VARCHAR,
            PRIMARY KEY (baseline_id, character_id),
            FOREIGN KEY (baseline_id, character_id)
                REFERENCES reference.character_baseline_states
                    (baseline_id, character_id),
            FOREIGN KEY (
                reference_snapshot_id,
                character_id,
                source_group,
                source_declaration_order,
                source_operation_order
            ) REFERENCES reference.character_nickname_events (
                reference_snapshot_id,
                character_id,
                source_group,
                source_declaration_order,
                source_operation_order
            ),
            FOREIGN KEY (reference_snapshot_id, active_nickname_id)
                REFERENCES reference.nicknames
                    (reference_snapshot_id, nickname_id),
            CHECK (
                (last_event_kind = 'set' AND active_nickname_id IS NOT NULL)
                OR (last_event_kind = 'clear' AND active_nickname_id IS NULL)
            )
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reference.character_baseline_court_states (
            baseline_id VARCHAR NOT NULL,
            character_id VARCHAR NOT NULL,
            court_language_id VARCHAR,
            court_language_effective_date DATE,
            court_language_source_declaration_order BIGINT,
            court_type_id VARCHAR,
            court_type_effective_date DATE,
            court_type_source_declaration_order BIGINT,
            validation_status VARCHAR NOT NULL,
            validation_note VARCHAR,
            PRIMARY KEY (baseline_id, character_id)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reference.character_baseline_languages (
            baseline_id VARCHAR NOT NULL,
            character_id VARCHAR NOT NULL,
            language_id VARCHAR NOT NULL,
            knowledge_kind VARCHAR NOT NULL,
            effective_date DATE,
            source_group VARCHAR NOT NULL,
            source_declaration_order BIGINT,
            validation_status VARCHAR NOT NULL,
            validation_note VARCHAR,
            PRIMARY KEY (baseline_id, character_id, language_id)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reference.title_holder_adjudications (
            baseline_id VARCHAR NOT NULL,
            title_id VARCHAR NOT NULL,
            declared_holder_character_id VARCHAR NOT NULL,
            adjudicated_holder_character_id VARCHAR NOT NULL,
            evidence_kind VARCHAR NOT NULL,
            evidence_path VARCHAR NOT NULL,
            evidence_sha256 VARCHAR NOT NULL,
            evidence_game_version VARCHAR NOT NULL,
            evidence_date DATE NOT NULL,
            save_player_character_id BIGINT,
            review_status VARCHAR NOT NULL,
            review_note VARCHAR NOT NULL,
            created_at_utc TIMESTAMP NOT NULL DEFAULT current_timestamp,
            PRIMARY KEY (baseline_id, title_id)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reference.title_holder_validations (
            baseline_id VARCHAR NOT NULL,
            title_id VARCHAR NOT NULL,
            holder_character_id VARCHAR NOT NULL,
            declaration_status VARCHAR NOT NULL,
            uniqueness_status VARCHAR NOT NULL,
            lifecycle_status VARCHAR NOT NULL,
            validation_status VARCHAR NOT NULL,
            validation_note VARCHAR,
            PRIMARY KEY (baseline_id, title_id)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reference.bookmark_groups (
            reference_snapshot_id VARCHAR NOT NULL,
            bookmark_group_id VARCHAR NOT NULL,
            default_start_date VARCHAR NOT NULL,
            localization_key VARCHAR NOT NULL,
            validation_status VARCHAR NOT NULL,
            validation_note VARCHAR,
            PRIMARY KEY (reference_snapshot_id, bookmark_group_id)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reference.bookmarks (
            reference_snapshot_id VARCHAR NOT NULL,
            bookmark_id VARCHAR NOT NULL,
            bookmark_group_id VARCHAR NOT NULL,
            explicit_start_date VARCHAR,
            effective_start_date VARCHAR NOT NULL,
            is_playable BOOLEAN NOT NULL,
            is_recommended BOOLEAN NOT NULL,
            weight_script VARCHAR,
            localization_key VARCHAR NOT NULL,
            description_localization_key VARCHAR NOT NULL,
            validation_status VARCHAR NOT NULL,
            validation_note VARCHAR,
            PRIMARY KEY (reference_snapshot_id, bookmark_id)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reference.baseline_bookmarks (
            baseline_id VARCHAR NOT NULL,
            bookmark_id VARCHAR NOT NULL,
            validation_status VARCHAR NOT NULL,
            validation_note VARCHAR,
            PRIMARY KEY (baseline_id, bookmark_id)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reference.bookmark_featured_characters (
            reference_snapshot_id VARCHAR NOT NULL,
            bookmark_id VARCHAR NOT NULL,
            character_ordinal INTEGER NOT NULL,
            parent_character_ordinal INTEGER,
            character_kind VARCHAR NOT NULL,
            history_character_id VARCHAR,
            title_id VARCHAR,
            name_localization_key VARCHAR,
            relation_localization_key VARCHAR,
            character_type VARCHAR,
            difficulty_localization_key VARCHAR,
            position_script VARCHAR,
            validation_status VARCHAR NOT NULL,
            validation_note VARCHAR,
            PRIMARY KEY (reference_snapshot_id, bookmark_id, character_ordinal)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reference.dlc_packages (
            reference_snapshot_id VARCHAR NOT NULL,
            package_id VARCHAR NOT NULL,
            display_name VARCHAR NOT NULL,
            steam_id VARCHAR,
            pops_id VARCHAR,
            msgr_id VARCHAR,
            source_path VARCHAR NOT NULL,
            source_sha256 VARCHAR NOT NULL,
            wiki_permanent_url VARCHAR NOT NULL,
            wiki_revision_id VARCHAR NOT NULL,
            validation_status VARCHAR NOT NULL,
            validation_note VARCHAR,
            PRIMARY KEY (reference_snapshot_id, package_id)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reference.dlc_feature_mappings (
            reference_snapshot_id VARCHAR NOT NULL,
            feature_flag VARCHAR NOT NULL,
            package_id VARCHAR NOT NULL,
            review_status VARCHAR NOT NULL,
            evidence_note VARCHAR NOT NULL,
            PRIMARY KEY (reference_snapshot_id, feature_flag)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reference.bookmark_dlc_requirements (
            reference_snapshot_id VARCHAR NOT NULL,
            bookmark_id VARCHAR NOT NULL,
            requirement_kind VARCHAR NOT NULL,
            requirement_value VARCHAR NOT NULL,
            resolution_status VARCHAR NOT NULL,
            validation_note VARCHAR,
            PRIMARY KEY (reference_snapshot_id, bookmark_id, requirement_kind, requirement_value)
        )
        """
    )
    connection.execute(
        "ALTER TABLE reference.bookmark_dlc_requirements ADD COLUMN IF NOT EXISTS resolved_package_id VARCHAR"
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reference.promotion_readiness_reports (
            report_id VARCHAR PRIMARY KEY,
            baseline_id VARCHAR NOT NULL,
            reference_snapshot_id VARCHAR NOT NULL,
            generated_at_utc TIMESTAMP NOT NULL,
            overall_status VARCHAR NOT NULL,
            blocking_count INTEGER NOT NULL,
            accepted_exception_count INTEGER NOT NULL,
            informational_count INTEGER NOT NULL,
            passed_count INTEGER NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reference.promotion_readiness_findings (
            report_id VARCHAR NOT NULL,
            finding_order INTEGER NOT NULL,
            finding_code VARCHAR NOT NULL,
            classification VARCHAR NOT NULL,
            subject_count BIGINT NOT NULL,
            summary VARCHAR NOT NULL,
            detail VARCHAR NOT NULL,
            PRIMARY KEY (report_id, finding_order)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reference.promotion_readiness_evidence (
            report_id VARCHAR NOT NULL,
            parser_name VARCHAR NOT NULL,
            parser_run_id VARCHAR,
            parser_version VARCHAR,
            parser_status VARCHAR NOT NULL,
            manifest_count BIGINT NOT NULL,
            manifest_digest VARCHAR NOT NULL,
            PRIMARY KEY (report_id, parser_name)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS journal.playthroughs (
            playthrough_id VARCHAR PRIMARY KEY,
            reference_snapshot_id VARCHAR NOT NULL,
            baseline_id VARCHAR NOT NULL,
            ruler_character_id VARCHAR,
            ruler_name VARCHAR NOT NULL,
            lifecycle_state VARCHAR NOT NULL,
            created_at_utc TIMESTAMP NOT NULL DEFAULT current_timestamp
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS journal.playthrough_baselines (
            playthrough_id VARCHAR PRIMARY KEY,
            transaction_id VARCHAR NOT NULL UNIQUE,
            baseline_date DATE NOT NULL,
            starting_title_id VARCHAR NOT NULL,
            starting_empire_id VARCHAR,
            starting_kingdom_id VARCHAR,
            starting_duchy_id VARCHAR,
            starting_county_id VARCHAR,
            starting_barony_id VARCHAR,
            source VARCHAR NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS journal.transaction_events (
            transaction_id VARCHAR PRIMARY KEY,
            playthrough_id VARCHAR NOT NULL,
            event_type VARCHAR NOT NULL,
            scope VARCHAR NOT NULL,
            target_id VARCHAR NOT NULL,
            observed_at DATE NOT NULL,
            recorded_at_utc TIMESTAMP NOT NULL DEFAULT current_timestamp,
            source VARCHAR NOT NULL,
            note VARCHAR
        )
        """
    )

    connection.execute(
        """
        CREATE OR REPLACE VIEW app.supported_baselines AS
        SELECT
            baseline.baseline_id,
            baseline.reference_snapshot_id,
            baseline.bookmark_id,
            baseline.baseline_date,
            baseline.label,
            snapshot.game_version,
            snapshot.map_profile
        FROM reference.baselines AS baseline
        JOIN source.reference_snapshots AS snapshot USING (reference_snapshot_id)
        WHERE baseline.support_status = 'promoted'
          AND baseline.historical_state_complete
          AND snapshot.review_status = 'promoted'
        """
    )
    connection.execute(
        """
        CREATE OR REPLACE VIEW app.reference_location_options AS
        SELECT
            title.baseline_id,
            title.title_id,
            title.title_rank,
            title.parent_title_id,
            title.display_name
        FROM reference.titles AS title
        JOIN app.supported_baselines AS baseline USING (baseline_id)
        WHERE title.selectable
        """
    )
    connection.execute(
        """
        CREATE OR REPLACE VIEW app.playthrough_context AS
        SELECT
            playthrough.playthrough_id,
            playthrough.reference_snapshot_id,
            playthrough.baseline_id,
            baseline.baseline_date,
            playthrough.ruler_character_id,
            playthrough.ruler_name,
            playthrough.lifecycle_state,
            selection.starting_title_id,
            selection.starting_empire_id,
            selection.starting_kingdom_id,
            selection.starting_duchy_id,
            selection.starting_county_id,
            selection.starting_barony_id
        FROM journal.playthroughs AS playthrough
        JOIN reference.baselines AS baseline USING (baseline_id)
        JOIN journal.playthrough_baselines AS selection USING (playthrough_id)
        """
    )