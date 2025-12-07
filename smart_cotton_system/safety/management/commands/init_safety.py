"""
Management command to initialize safety monitoring system with sample data
"""
from django.core.management.base import BaseCommand
from safety.models import Worker, Zone


class Command(BaseCommand):
    help = 'Initialize safety monitoring system with workers and zones'

    def handle(self, *args, **options):
        self.stdout.write('Initializing Safety Monitoring System...')
        
        # Create Zones
        zones_data = [
            {
                'name': 'Chemical Storage',
                'zone_type': 'CHEMICAL',
                'lat_min': 20, 'lat_max': 55,
                'lon_min': 20, 'lon_max': 55,
                'description': 'Hazardous chemical storage area'
            },
            {
                'name': 'Assembly Line',
                'zone_type': 'ASSEMBLY',
                'lat_min': 25, 'lat_max': 55,
                'lon_min': 65, 'lon_max': 95,
                'description': 'High-noise assembly operations'
            },
            {
                'name': 'Loading Dock',
                'zone_type': 'LOADING',
                'lat_min': 55, 'lat_max': 85,
                'lon_min': 5, 'lon_max': 35,
                'description': 'Heavy machinery and vehicle traffic'
            }
        ]
        
        for zone_data in zones_data:
            zone, created = Zone.objects.get_or_create(
                name=zone_data['name'],
                defaults=zone_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created zone: {zone.name}'))
            else:
                self.stdout.write(f'Zone already exists: {zone.name}')
        
        # Create Workers
        workers_data = [
            {
                'worker_id': 101,
                'name': 'Alex Chen',
                'role': 'Operator',
                'latitude': 20.0,
                'longitude': 30.0,
                'heart_rate': 75.0,
                'steps': 1000,
                'activity_level': 2,
            },
            {
                'worker_id': 102,
                'name': 'Sarah Jones',
                'role': 'Supervisor',
                'latitude': 50.0,
                'longitude': 50.0,
                'heart_rate': 80.0,
                'steps': 1200,
                'activity_level': 2,
            },
            {
                'worker_id': 103,
                'name': 'Mike Ross',
                'role': 'Technician',
                'latitude': 70.0,
                'longitude': 20.0,
                'heart_rate': 72.0,
                'steps': 1100,
                'activity_level': 2,
            },
            {
                'worker_id': 104,
                'name': 'David Kim',
                'role': 'Welder',
                'latitude': 40.0,
                'longitude': 80.0,
                'heart_rate': 68.0,
                'steps': 900,
                'activity_level': 2,
                'altitude': 5.0,
            },
            {
                'worker_id': 999,
                'name': 'Nurdaulet Izmailov',
                'role': 'Site Manager',
                'latitude': 25.0,
                'longitude': 25.0,
                'heart_rate': 75.0,
                'steps': 0,
                'activity_level': 0,
            }
        ]
        
        for worker_data in workers_data:
            worker, created = Worker.objects.get_or_create(
                worker_id=worker_data['worker_id'],
                defaults=worker_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created worker: {worker.name}'))
            else:
                self.stdout.write(f'Worker already exists: {worker.name}')
        
        self.stdout.write(self.style.SUCCESS('\n✅ Safety system initialized successfully!'))
        self.stdout.write(f'Total Workers: {Worker.objects.count()}')
        self.stdout.write(f'Total Zones: {Zone.objects.count()}')
