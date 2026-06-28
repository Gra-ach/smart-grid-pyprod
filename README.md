
# Smart Grid PyProd Production

A Pure Python InterSystems IRIS Interoperability production built based on **PyProd**.

This project demonstrates how to build a complete InterSystems IRIS production entirely in Python that ingests CSV smart-meter readings, validates the file structure, performs analytics, and stores the results in an IRIS SQL table.

The implementation is based on the PyProd framework and follows the same architectural style as the https://github.com/gabriel-ing/csvgen-pyprod sample.

## Architecture

```
CSV Files
     │
     ▼
CSVFileInboundAdapter
     │
     ▼
SmartMeterFileService
     │
     ▼
SmartMeterAnalysisProcess
     │
     ▼
SmartMeterDBOperation
     │
     ▼
EnergyOps.SmartMeterReadings
```

The production performs the following steps:

1. Polls an input directory for CSV files.
2. Moves the file to a processing directory.
3. Validates the CSV structure.
4. Calculates:
   * Total kWh consumed in the file
   * Average kWh consumed
   * Peak meter ID
   * Peak kWh reading
5. Inserts every CSV row into an IRIS SQL table together with the calculated file statistics.
6. Archives the processed CSV.

# Build

Clone the repository

```bash
git clone https://github.com/Gra-ach/smart-grid-pyprod.git
cd smart-grid-pyprod
```

Start up the Docker container:

```bash
docker-compose up --build -d
```

---

# Run

Open the Management Portal
http://localhost:62773/csp/ensemble/EnsPortal.ProductionConfig.zen?PRODUCTION=EnergyOps.SmartGridProduction
and start the production.
---

# Input Files

Copy CSV files into

```
Data/input
```

---

# Processing

When a file is detected:

* it is moved to `Data/processing`
* validated
* analysed
* inserted into SQL
* moved to `Data/archive`

---

# SQL Table

The production automatically creates

```
EnergyOps.SmartMeterReadings
```

if it does not already exist.

Each inserted row contains

* original meter reading
* source filename
* file total kWh
* file average kWh
* peak meter
* peak kWh

---

# View Results

Using SQL

```sql
SELECT *
  FROM EnergyOps.SmartMeterReadings;
```

---

# Interoperability Components

## Inbound Adapter

* Polls an input directory
* Detects CSV files
* Moves files to the processing directory

## Business Service

* Reads CSV headers
* Creates a SmartMeterFileMessage

## Business Process

* Validates the CSV schema
* Calculates

    * total consumption
    * average consumption
    * peak meter

## Business Operation

* Creates the SQL table if required
* Inserts every CSV record
* Archives processed files

---

# References

* PyProd
  https://github.com/intersystems/pyprod

* CSVGen PyProd
  https://github.com/gabriel-ing/csvgen-pyprod

* InterSystems Developer Community article
  https://community.intersystems.com/post/45-second-production-testing-chatgpt%E2%80%99s-limits-intersystems-iris-and-pyprod