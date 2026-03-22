from relationship_os.infrastructure.db.tables import event_records


def test_event_records_table_has_expected_uniqueness_contract() -> None:
    unique_constraints = {
        tuple(column.name for column in constraint.columns)
        for constraint in event_records.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    }

    assert ("stream_id", "version") in unique_constraints


def test_event_records_table_contains_projection_fields() -> None:
    assert {
        "event_id",
        "stream_id",
        "version",
        "event_type",
        "payload",
        "metadata",
        "occurred_at",
    } <= {column.name for column in event_records.columns}
