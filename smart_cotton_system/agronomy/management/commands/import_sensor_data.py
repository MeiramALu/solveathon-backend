"""
Django management command to import sensor data from task_1_dataset into database
Usage: python manage.py import_sensor_data --field-id=1
"""
from django.core.management.base import BaseCommand
from agronomy.models import Field, SensorReading, IrrigationEvent
from pathlib import Path
from django.conf import settings
import pandas as pd
from datetime import datetime


class Command(BaseCommand):
    help = 'Import sensor data from task_1_dataset CSV files into database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--field-id',
            type=int,
            required=True,
            help='Field ID to associate readings with',
        )
        parser.add_argument(
            '--data-dir',
            type=str,
            help='Path to dataset directory (default: task_1_dataset/dataset)',
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Clear existing readings for this field before importing',
        )

    def handle(self, *args, **options):
        field_id = options['field_id']
        
        # Verify field exists
        try:
            field = Field.objects.get(id=field_id)
        except Field.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Field with ID {field_id} does not exist'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'📍 Importing data for field: {field.name}'))
        
        # Set data directory
        data_dir = options.get('data_dir')
        if not data_dir:
            data_dir = Path(settings.BASE_DIR).parent / 'task_1_dataset' / 'dataset'
        else:
            data_dir = Path(data_dir)
        
        # Clear existing data if requested
        if options['clear_existing']:
            count = SensorReading.objects.filter(field=field).count()
            if count > 0:
                self.stdout.write(f'🗑️  Clearing {count} existing readings...')
                SensorReading.objects.filter(field=field).delete()
        
        try:
            # Load CSV files
            self.stdout.write('\n📂 Loading CSV files...')
            hum = pd.read_csv(data_dir / "CottonSensor" / "HumiditySensor.csv")
            tem = pd.read_csv(data_dir / "CottonSensor" / "TemSensor.csv")
            weather = pd.read_csv(data_dir / "Weather" / "Weather.csv")
            mgmt = pd.read_csv(data_dir / "ManagementInfo.csv")
            
            self.stdout.write(self.style.SUCCESS(f'✅ Loaded {len(hum)} humidity readings'))
            self.stdout.write(self.style.SUCCESS(f'✅ Loaded {len(tem)} temperature readings'))
            self.stdout.write(self.style.SUCCESS(f'✅ Loaded {len(weather)} weather records'))
            self.stdout.write(self.style.SUCCESS(f'✅ Loaded {len(mgmt)} irrigation events'))
            
            # Process data (similar to WaterAISuite)
            self.stdout.write('\n🔄 Processing data...')
            
            def parse_time(s):
                return pd.to_datetime(s.astype(str), format="%Y%m%d%H%M", errors="coerce")

            def parse_date(s):
                return pd.to_datetime(s.astype(str), format="%Y%m%d", errors="coerce")
            
            # Process humidity
            hum["ts"] = parse_time(hum["collect_time"])
            hum["date"] = hum["ts"].dt.date
            hum["loc_x"] = hum["location_info_x"].round(4)
            hum["loc_y"] = hum["location_info_y"].round(4)
            hum_agg = (
                hum.groupby(["date", "loc_x", "loc_y"])["soil_humidity(%)"]
                .mean()
                .reset_index()
            )
            
            # Process temperature
            tem["ts"] = parse_time(tem["collect_time"])
            tem["date"] = tem["ts"].dt.date
            tem["loc_x"] = tem["location_info_x"].round(4)
            tem["loc_y"] = tem["location_info_y"].round(4)
            tem_agg = (
                tem.groupby(["date", "loc_x", "loc_y"])["soil_temperature(°C)"]
                .mean()
                .reset_index()
            )
            
            # Merge sensors
            df = pd.merge(hum_agg, tem_agg, on=["date", "loc_x", "loc_y"], how="left")
            df["date"] = pd.to_datetime(df["date"])
            
            # Process weather
            weather["date"] = parse_date(weather["date"])
            w_cols = [
                "date",
                "rain(mm/day)",
                "daily_mean_temperature(°C)",
            ]
            
            # Process irrigation
            mgmt["date"] = parse_date(mgmt["irrigation_time"])
            irr_agg = mgmt.groupby("date")["irrigation_amount(m3/mu)"].sum().reset_index()
            
            # Merge all data
            df = pd.merge(df, weather[w_cols], on="date", how="left")
            df = pd.merge(df, irr_agg, on="date", how="left")
            
            # Clean data
            df["irrigation_amount(m3/mu)"] = df["irrigation_amount(m3/mu)"].fillna(0)
            df = df.ffill().bfill()
            
            # Calculate days since irrigation
            irr_dates = irr_agg[irr_agg["irrigation_amount(m3/mu)"] > 0]["date"]
            
            def calc_days_since(d):
                past = irr_dates[irr_dates < d]
                return (d - past.max()).days if not past.empty else -1
            
            unique_dates = pd.DataFrame({"date": df["date"].unique()})
            unique_dates["days_since_irrigation"] = unique_dates["date"].apply(calc_days_since)
            df = pd.merge(df, unique_dates, on="date", how="left")
            
            df = df.dropna()
            
            self.stdout.write(self.style.SUCCESS(f'✅ Processed {len(df)} records'))
            
            # Import into database
            self.stdout.write('\n💾 Importing into database...')
            
            sensor_readings = []
            irrigation_events = []
            irrigation_dates_processed = set()
            
            for idx, row in df.iterrows():
                # Create sensor reading
                reading = SensorReading(
                    field=field,
                    date=row['date'].date(),
                    location_x=row['loc_x'],
                    location_y=row['loc_y'],
                    soil_humidity=row['soil_humidity(%)'],
                    soil_temperature=row['soil_temperature(°C)'],
                    rain=row['rain(mm/day)'],
                    daily_mean_temperature=row['daily_mean_temperature(°C)'],
                    irrigation_amount=row['irrigation_amount(m3/mu)'],
                    days_since_irrigation=int(row['days_since_irrigation']),
                )
                sensor_readings.append(reading)
                
                # Create irrigation event if there was irrigation
                if row['irrigation_amount(m3/mu)'] > 0:
                    date_key = row['date'].date()
                    if date_key not in irrigation_dates_processed:
                        irrigation_dates_processed.add(date_key)
                        event = IrrigationEvent(
                            field=field,
                            date=date_key,
                            amount=row['irrigation_amount(m3/mu)'],
                            notes='Imported from historical data'
                        )
                        irrigation_events.append(event)
                
                # Bulk create in batches
                if len(sensor_readings) >= 1000:
                    SensorReading.objects.bulk_create(sensor_readings, ignore_conflicts=True)
                    sensor_readings = []
                    self.stdout.write('.', ending='')
            
            # Create remaining records
            if sensor_readings:
                SensorReading.objects.bulk_create(sensor_readings, ignore_conflicts=True)
            
            if irrigation_events:
                IrrigationEvent.objects.bulk_create(irrigation_events, ignore_conflicts=True)
            
            total_readings = SensorReading.objects.filter(field=field).count()
            total_events = IrrigationEvent.objects.filter(field=field).count()
            
            self.stdout.write(self.style.SUCCESS(f'\n\n✅ Import complete!'))
            self.stdout.write(self.style.SUCCESS(f'   - {total_readings} sensor readings'))
            self.stdout.write(self.style.SUCCESS(f'   - {total_events} irrigation events'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Error during import: {str(e)}'))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
