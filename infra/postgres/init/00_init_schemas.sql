-- Bootstrap only foundational PostgreSQL namespaces used by the project.
-- Raw CSV files remain on the filesystem and are not materialized here as raw replica tables.

CREATE SCHEMA IF NOT EXISTS clean;
CREATE SCHEMA IF NOT EXISTS mart;
CREATE SCHEMA IF NOT EXISTS feature;
CREATE SCHEMA IF NOT EXISTS serving;
