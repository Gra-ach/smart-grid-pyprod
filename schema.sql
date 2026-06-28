CREATE TABLE EnergyOps.SmartMeterReadings (
    id INTEGER IDENTITY PRIMARY KEY,
    source_file VARCHAR(255) NOT NULL,
    meter_id VARCHAR(20) NOT NULL,
    reading_timestamp TIMESTAMP NOT NULL,
    region VARCHAR(40) NOT NULL,
    feeder_type VARCHAR(40) NOT NULL,
    kwh_consumed NUMERIC(10,2) NOT NULL,
    voltage_avg NUMERIC(6,1) NOT NULL,
    temperature_c NUMERIC(5,1) NOT NULL,
    outage_minutes INTEGER NOT NULL,
    file_total_kwh NUMERIC(12,2) NOT NULL,
    file_avg_kwh NUMERIC(10,2) NOT NULL,
    peak_meter_id VARCHAR(20) NOT NULL,
    peak_kwh NUMERIC(10,2) NOT NULL,
    inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
