-- PostgreSQL migration target for Crew Availability.
CREATE TABLE sync_runs (
  id BIGSERIAL PRIMARY KEY,
  source TEXT NOT NULL,
  started_at TIMESTAMPTZ NOT NULL,
  finished_at TIMESTAMPTZ,
  status TEXT NOT NULL,
  records_read INTEGER NOT NULL DEFAULT 0,
  error TEXT
);
CREATE TABLE raw_board_snapshots (
  id BIGSERIAL PRIMARY KEY,
  sync_run_id BIGINT NOT NULL REFERENCES sync_runs(id),
  board_id TEXT NOT NULL,
  captured_at TIMESTAMPTZ NOT NULL,
  payload_json JSONB NOT NULL
);
CREATE TABLE crew_members (
  id BIGSERIAL PRIMARY KEY,
  source_person_id TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  active BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE TABLE crew_availability_daily (
  id BIGSERIAL PRIMARY KEY,
  date DATE NOT NULL,
  crew_member_id BIGINT NOT NULL REFERENCES crew_members(id),
  status TEXT NOT NULL,
  source_parent_id TEXT,
  source_subitem_id TEXT,
  source_updated_at TIMESTAMPTZ,
  sync_run_id BIGINT NOT NULL REFERENCES sync_runs(id),
  data_state TEXT NOT NULL DEFAULT 'current',
  validation_errors JSONB,
  UNIQUE(date, crew_member_id)
);
CREATE INDEX crew_availability_daily_date_idx ON crew_availability_daily(date);
