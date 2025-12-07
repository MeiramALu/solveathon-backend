"""
Django management command to train the irrigation prediction model
Usage: python manage.py train_irrigation_model
"""
from django.core.management.base import BaseCommand
from agronomy.ml_models.water_prediction_suite import WaterAISuite
from pathlib import Path
from django.conf import settings


class Command(BaseCommand):
    help = 'Train the irrigation prediction model using task_1_dataset'

    def add_arguments(self, parser):
        parser.add_argument(
            '--data-dir',
            type=str,
            help='Path to dataset directory (default: task_1_dataset/dataset)',
        )
        parser.add_argument(
            '--dry-threshold',
            type=float,
            default=30.0,
            help='Humidity threshold for dry risk (default: 30.0)',
        )
        parser.add_argument(
            '--target-humidity',
            type=float,
            default=35.0,
            help='Target humidity level (default: 35.0)',
        )
        parser.add_argument(
            '--max-irrigation',
            type=float,
            default=40.0,
            help='Maximum daily irrigation in m3/mu (default: 40.0)',
        )
        parser.add_argument(
            '--skip-plots',
            action='store_true',
            help='Skip generating evaluation plots',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('  SMART COTTON IRRIGATION MODEL TRAINING'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        
        # Initialize suite
        data_dir = options.get('data_dir')
        if not data_dir:
            data_dir = Path(settings.BASE_DIR).parent / 'task_1_dataset' / 'dataset'
        
        suite = WaterAISuite(
            dry_threshold=options['dry_threshold'],
            target_humidity=options['target_humidity'],
            max_daily_m3_mu=options['max_irrigation'],
            data_dir=data_dir
        )
        
        try:
            # Load and process data
            self.stdout.write('\n📊 Loading and processing data...')
            suite.load_and_process_data()
            
            if suite.data is None:
                self.stdout.write(self.style.ERROR('❌ Failed to load data'))
                return
            
            self.stdout.write(self.style.SUCCESS(f'✅ Dataset loaded: {suite.data.shape[0]} samples'))
            
            # Train model
            self.stdout.write('\n🤖 Training Random Forest model...')
            suite.train()
            self.stdout.write(self.style.SUCCESS('✅ Model trained successfully'))
            
            # Generate evaluation plots
            if not options['skip_plots']:
                self.stdout.write('\n📈 Generating evaluation plots...')
                suite.evaluate_and_plot()
                self.stdout.write(self.style.SUCCESS('✅ Plots generated'))
            
            # Save model
            self.stdout.write('\n💾 Saving model...')
            suite.save_model()
            self.stdout.write(self.style.SUCCESS('✅ Model saved'))
            
            self.stdout.write(self.style.SUCCESS('\n' + '=' * 70))
            self.stdout.write(self.style.SUCCESS('  TRAINING COMPLETE'))
            self.stdout.write(self.style.SUCCESS('=' * 70))
            self.stdout.write(self.style.SUCCESS('\n✨ Model is ready for predictions!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Error during training: {str(e)}'))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
