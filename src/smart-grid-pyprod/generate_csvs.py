import csv, os, random
from datetime import datetime, timedelta

out_dir = os.path.join(os.path.dirname(__file__), 'input')
os.makedirs(out_dir, exist_ok=True)
random.seed(42)
regions = ['North','South','East','West','Central']
feeder_types = ['residential','commercial','industrial','mixed']
start = datetime(2026, 6, 1)

for file_no in range(1, 5):
    path = os.path.join(out_dir, f'smart_meter_batch_{file_no}.csv')
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'meter_id','reading_timestamp','region','feeder_type',
            'kwh_consumed','voltage_avg','temperature_c','outage_minutes'
        ])
        for i in range(30):
            meter_seq = (file_no - 1) * 30 + i + 1
            ts = start + timedelta(hours=i + (file_no - 1) * 30)
            feeder = random.choice(feeder_types)
            base = {'residential': 2.8, 'commercial': 8.5, 'industrial': 18.0, 'mixed': 6.2}[feeder]
            temp = round(random.uniform(14.0, 35.5), 1)
            temp_adj = max(temp - 22, 0) * random.uniform(0.08, 0.25)
            kwh = round(base + temp_adj + random.uniform(-1.0, 2.5), 2)
            voltage = round(random.uniform(216.0, 244.0), 1)
            outage = random.choices([0,0,0,0,5,10,15,20,30], weights=[45,15,10,8,7,5,4,3,3])[0]
            writer.writerow([
                f'MTR-{meter_seq:05d}', ts.strftime('%Y-%m-%d %H:%M:%S'),
                random.choice(regions), feeder, kwh, voltage, temp, outage
            ])
