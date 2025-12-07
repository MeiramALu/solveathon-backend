from django.core.management.base import BaseCommand
from agronomy.ml_models.water_prediction import WaterAISuite

class Command(BaseCommand):
    help = 'Train the water management prediction model'

    def handle(self, *args, **options):
        self.stdout.write('Training water management model...')
        
        suite = WaterAISuite()
        suite.load_and_process_data()
        suite.train()
        suite.evaluate_and_plot()
        suite.save_model()
        
        self.stdout.write(self.style.SUCCESS('Model trained successfully!'))
