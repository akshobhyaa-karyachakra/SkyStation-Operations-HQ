-- Shared PostgreSQL foundation for every portal domain.
-- Domain tables (crew_availability_daily, flight_execution, etc.) reference sync_runs.
CREATE TABLE sync_runs (
  id BIGSERIAL PRIMARY KEY,
  domain TEXT NOT NULL,
  source_provider TEXT NOT NULL,
  started_at TIMESTAMPTZ NOT NULL,
  finished_at TIMESTAMPTZ,
  status TEXT NOT NULL CHECK (status IN ('running','published','failed')),
  records_read INTEGER NOT NULL DEFAULT 0,
  error TEXT
);
CREATE INDEX sync_runs_domain_started_idx ON sync_runs(domain, started_at DESC);

CREATE TABLE raw_snapshots (
  id BIGSERIAL PRIMARY KEY,
  sync_run_id BIGINT NOT NULL REFERENCES sync_runs(id),
  source_board_id TEXT,
  source_name TEXT,
  captured_at TIMESTAMPTZ NOT NULL,
  payload JSONB NOT NULL
);
CREATE INDEX raw_snapshots_run_idx ON raw_snapshots(sync_run_id);

CREATE TABLE quality_issues (
  id BIGSERIAL PRIMARY KEY,
  sync_run_id BIGINT NOT NULL REFERENCES sync_runs(id),
  domain TEXT NOT NULL,
  severity TEXT NOT NULL CHECK (severity IN ('info','warning','error')),
  code TEXT NOT NULL,
  message TEXT NOT NULL,
  source_record_id TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX quality_issues_run_idx ON quality_issues(sync_run_id);

CREATE TABLE snapshot_manifests (
  id BIGSERIAL PRIMARY KEY,
  domain TEXT NOT NULL,
  snapshot_version TEXT NOT NULL,
  sync_run_id BIGINT NOT NULL REFERENCES sync_runs(id),
  state TEXT NOT NULL CHECK (state IN ('current','stale','unavailable','needs_review','partial')),
  record_count INTEGER NOT NULL DEFAULT 0,
  published_at TIMESTAMPTZ,
  UNIQUE(domain, snapshot_version)
);
CREATE INDEX snapshot_manifests_latest_idx ON snapshot_manifests(domain, published_at DESC);

CREATE TABLE published_projections (
  id BIGSERIAL PRIMARY KEY,
  manifest_id BIGINT NOT NULL REFERENCES snapshot_manifests(id),
  audience TEXT NOT NULL CHECK (audience IN ('public','protected')),
  route TEXT NOT NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX published_projections_route_idx ON published_projections(route, audience, created_at DESC);
