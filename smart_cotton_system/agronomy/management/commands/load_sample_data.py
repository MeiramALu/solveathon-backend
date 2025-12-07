from django.core.management.base import BaseCommand
from agronomy.models import Field, SensorReading
from django.contrib.auth import get_user_model
from datetime import date, timedelta
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Load sample sensor data for testing'

    def handle(self, *args, **options):
        self.stdout.write('Loading sample sensor data...')
        
        # Create or get a test user
        user, user_created = User.objects.get_or_create(
            username='test_farmer',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'Farmer'
            }
        )
        
        if user_created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Created test user: {user.username}'))
        else:
            self.stdout.write(f'Using existing user: {user.username}')
        
        # Create or get a test field
        field, created = Field.objects.get_or_create(
            name='Test Field 1',
            owner=user,
            defaults={
                # Add other fields if needed based on your Field model
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created new field: {field.name}'))
        else:
            self.stdout.write(f'Using existing field: {field.name}')
        
        # Create sample sensor readings for last 7 days
        base_date = date.today() - timedelta(days=7)
        
        # Multiple sensor locations
        locations = [
            (87.6234, 43.2156),
            (87.6235, 43.2157),
            (87.6236, 43.2158),
            (87.6237, 43.2159),
            (87.6238, 43.2160),
        ]
        
        readings_created = 0
        readings_existing = 0
        
        for loc_x, loc_y in locations:
            for day in range(8):
                reading_date = base_date + timedelta(days=day)
                
                reading, created_reading = SensorReading.objects.get_or_create(
                    field=field,
                    date=reading_date,
                    location_x=loc_x,
                    location_y=loc_y,
                    defaults={
                        'soil_humidity': round(random.uniform(20, 40), 2),
                        'soil_temperature': round(random.uniform(18, 28), 2),
                        'rain': round(random.choice([0, 0, 0, random.uniform(0, 10)]), 2),
                        'daily_mean_temperature': round(random.uniform(25, 35), 2),
                        'irrigation_amount': round(random.choice([0, 0, 0, random.uniform(20, 40)]), 2),
                        'days_since_irrigation': random.randint(0, 7),
                    }
                )
                
                if created_reading:
                    readings_created += 1
                else:
                    readings_existing += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'\nSample data loaded successfully!\n'
            f'  - User: {user.username}\n'
            f'  - Field: {field.name} (ID: {field.id})\n'
            f'  - New readings: {readings_created}\n'
            f'  - Existing readings: {readings_existing}\n'
            f'  - Locations: {len(locations)}\n'
            f'  - Date range: {base_date} to {base_date + timedelta(days=7)}\n'
            f'\nYou can now test the API with field_id={field.id}'
        ))