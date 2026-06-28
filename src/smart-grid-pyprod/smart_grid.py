import csv
import os
import shutil
from datetime import datetime
from typing import Dict, List, Tuple

import iris
from intersystems_pyprod import (    
    BusinessProcess,
    BusinessService,
    Column,
    InboundAdapter,
    BusinessOperation,
    IRISLog,
    IRISParameter,
    IRISProperty,
    JsonSerialize,
    OperationItem,
    ProcessItem,
    Production,
    ServiceItem,
    Status,
)

iris_package_name = "EnergyOps"

FILE_WATCHER_ROOT = "/home/irisowner/dev/Data"


class SmartMeterFileMessage(JsonSerialize):
    file_path: str = Column()
    source_file: str = Column()
    headers: list = Column()


class SmartMeterAnalysisMessage(JsonSerialize):
    file_path: str = Column()
    source_file: str = Column()
    headers: list = Column()
    file_total_kwh: float = Column()
    file_avg_kwh: float = Column()
    peak_meter_id: str = Column()
    peak_kwh: float = Column()


class CSVFileInboundAdapter(InboundAdapter):
    inbound_file_dir: str = IRISProperty(
        description="Directory to poll for inbound smart-meter CSV files",
        settings="Adapter Settings"
    )
    processed_file_dir: str = IRISProperty(
        description="Directory where files are moved while being processed",
        settings="Adapter Settings"
    )

    def on_task(self):
        os.makedirs(self.inbound_file_dir, exist_ok=True)
        os.makedirs(self.processed_file_dir, exist_ok=True)

        for name in sorted(os.listdir(self.inbound_file_dir)):
            if not name.lower().endswith(".csv"):
                continue

            src = os.path.join(self.inbound_file_dir, name)
            dst = os.path.join(self.processed_file_dir, name)
            if not os.path.isfile(src):
                continue

            shutil.move(src, dst)
            IRISLog.Info(f"Moved inbound CSV to working directory: {dst}")
            self.business_host_process_input(dst)
            break

        return Status.OK()


class SmartMeterFileService(BusinessService):
    ADAPTER: str = IRISParameter(
        value="EnergyOps.CSVFileInboundAdapter",
        description="Pure Python CSV polling adapter"
    )
    process_target: str = IRISProperty(
        description="Business process target",
        settings="Target Settings"
    )

    def on_process_input(self, input):
        file_path = str(input)
        with open(file_path, newline="") as f:
            reader = csv.reader(f)
            headers = next(reader)

        msg = SmartMeterFileMessage(
            file_path=file_path,
            source_file=os.path.basename(file_path),
            headers=headers
        )
        return self.send_request_async(self.process_target, msg)


class SmartMeterAnalysisProcess(BusinessProcess):
    operation_target: str = IRISProperty(
        description="Operation that persists rows and analysis results",
        settings="Target Settings"
    )

    def on_request(self, request):
        required = {
            "meter_id", "reading_timestamp", "region", "feeder_type",
            "kwh_consumed", "voltage_avg", "temperature_c", "outage_minutes"
        }

        missing = required.difference(set(request.headers))
        if missing:
            IRISLog.Error(f"CSV {request.source_file} is missing columns: {sorted(missing)}")
            return Status.Error()

        total_kwh = 0.0
        count = 0
        peak_meter_id = ""
        peak_kwh = -1.0

        with open(request.file_path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                kwh = float(row["kwh_consumed"])
                total_kwh += kwh
                count += 1
                if kwh > peak_kwh:
                    peak_kwh = kwh
                    peak_meter_id = row["meter_id"]

        avg_kwh = round(total_kwh / count, 2) if count else 0.0
        analysis = SmartMeterAnalysisMessage(
            file_path=request.file_path,
            source_file=request.source_file,
            headers=request.headers,
            file_total_kwh=round(total_kwh, 2),
            file_avg_kwh=avg_kwh,
            peak_meter_id=peak_meter_id,
            peak_kwh=round(peak_kwh, 2)
        )

        return self.send_request_async(self.operation_target, analysis, response_required=0)


class SmartMeterDBOperation(BusinessOperation):
    archive_file_dir: str = IRISProperty(
        description="Directory where successfully loaded files are archived",
        settings="Operation Settings"
    )

    message_map = {
        f"{iris_package_name}.SmartMeterAnalysisMessage": "save_readings"
    }

    def _ensure_table(self):
        ddl = """
        CREATE TABLE IF NOT EXISTS EnergyOps.SmartMeterReadings (
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
        )
        """
        iris.sql.prepare(ddl).execute()

    def save_readings(self, request):
        self._ensure_table()
        insert_sql = """
        INSERT INTO EnergyOps.SmartMeterReadings (
            source_file, meter_id, reading_timestamp, region, feeder_type,
            kwh_consumed, voltage_avg, temperature_c, outage_minutes,
            file_total_kwh, file_avg_kwh, peak_meter_id, peak_kwh
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        stmt = iris.sql.prepare(insert_sql)
        rows_inserted = 0

        with open(request.file_path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                stmt.execute(
                    request.source_file,
                    row["meter_id"],
                    row["reading_timestamp"],
                    row["region"],
                    row["feeder_type"],
                    float(row["kwh_consumed"]),
                    float(row["voltage_avg"]),
                    float(row["temperature_c"]),
                    int(row["outage_minutes"]),
                    float(request.file_total_kwh),
                    float(request.file_avg_kwh),
                    request.peak_meter_id,
                    float(request.peak_kwh)
                )
                rows_inserted += 1

        os.makedirs(self.archive_file_dir, exist_ok=True)
        archive_path = os.path.join(self.archive_file_dir, request.source_file)
        shutil.move(request.file_path, archive_path)
        IRISLog.Info(
            f"Loaded {rows_inserted} rows from {request.source_file}; "
            f"total_kwh={request.file_total_kwh}, avg_kwh={request.file_avg_kwh}, "
            f"peak_meter={request.peak_meter_id}, peak_kwh={request.peak_kwh}"
        )
        return Status.OK()


class SmartGridProduction(Production):
    services = [
        ServiceItem(
            "SmartMeterCSVService",
            "EnergyOps.SmartMeterFileService",
            host_settings={"process_target": "SmartMeterAnalysisProcess"},
            adapter_settings={
                "inbound_file_dir": f"{FILE_WATCHER_ROOT}/input",
                "processed_file_dir": f"{FILE_WATCHER_ROOT}/processing"
            }
        )
    ]
    processes = [
        ProcessItem(
            "SmartMeterAnalysisProcess",
            "EnergyOps.SmartMeterAnalysisProcess",
            host_settings={"operation_target": "SmartMeterDBOperation"}
        )
    ]
    operations = [
        OperationItem(
            "SmartMeterDBOperation",
            "EnergyOps.SmartMeterDBOperation",
            host_settings={"archive_file_dir": f"{FILE_WATCHER_ROOT}/archive"}
        )
    ]
