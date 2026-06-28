# Smart Grid PyProd Production

Domain: electric utility smart-meter telemetry.

Files:
- `input/smart_meter_batch_1.csv` through `input/smart_meter_batch_4.csv`: four sample CSV files, 30 records each.
- `schema.sql`: SQL DDL for `EnergyOps.SmartMeterReadings`.
- `smart_grid_production.py`: complete PyProd production with inbound adapter, business service, business process, and business operation.
- `generate_csvs.py`: deterministic generator for the four sample CSV files.

The business process computes per-file total kWh, average kWh, peak meter id, and peak kWh, then the operation persists every CSV row with those calculation results.
