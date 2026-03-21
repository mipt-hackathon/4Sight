/*
Purpose:
  Build cleaned order-item level records for downstream sales and recommendation analytics.

Expected inputs:
  - Parsed transaction rows derived from the wide transactional CSV.
  - ETL-produced intermediate load tables or staging objects.

Expected outputs:
  - clean.order_items or equivalent curated grain table.

TODO:
  - Enforce one row per order-item grain.
  - Validate quantities, prices, discounts, and warehouse references.
*/

-- TODO: implement clean order item transformation logic.
