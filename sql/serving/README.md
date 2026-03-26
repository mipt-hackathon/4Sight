# Serving Schema SQL

Use this folder for tables and refresh logic that expose scored outputs in the `serving` schema.

- Serving outputs should be application- and BI-friendly.
- Store prediction results, recommendations, and segments here after batch jobs are implemented.
- Avoid embedding heavy business logic directly inside API handlers.
