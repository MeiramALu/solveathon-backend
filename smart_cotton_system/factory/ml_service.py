"""
ML Service for Cotton Quality Analysis
Integrates HVI Classification, Computer Vision, and Seed Recommendation
"""

import os
import joblib
import numpy as np
import cv2
from PIL import Image
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Model paths
MODELS_DIR = os.path.join(settings.BASE_DIR, 'models')

class HVIClassifier:
    """HVI Laboratory - Quality Classification from fiber parameters"""
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.color_encoder = None
        self.load_models()
    
    def load_models(self):
        try:
            self.model = joblib.load(os.path.join(MODELS_DIR, 'cotton_xgboost_model.pkl'))
            self.scaler = joblib.load(os.path.join(MODELS_DIR, 'cotton_scaler.pkl'))
            self.color_encoder = joblib.load(os.path.join(MODELS_DIR, 'color_encoder.pkl'))
            logger.info("HVI models loaded successfully")
        except Exception as e:
            logger.error(f"Error loading HVI models: {e}")
    
    def predict(self, data):
        """
        Predict quality class from HVI parameters
        
        Args:
            data (dict): {
                'micronaire': float,
                'strength': float,
                'length': float,
                'uniformity': float,
                'trash_grade': int,
                'trash_cnt': int,
                'trash_area': float,
                'sfi': float,
                'sci': float,
                'color_grade': str
            }
        
        Returns:
            dict: {
                'quality_class': str,
                'confidence': float,
                'probabilities': dict
            }
        """
        if not self.model:
            raise Exception("HVI models not loaded")
        
        try:
            import pandas as pd
            
            # Prepare input data
            input_df = pd.DataFrame([{
                'Micronaire': data['micronaire'],
                'Strength': data['strength'],
                'Length': data['length'],
                'Uniformity': data['uniformity'],
                'Trash_Grade': data['trash_grade'],
                'Trash_Cnt': data['trash_cnt'],
                'Trash_Area': data['trash_area'],
                'SFI': data['sfi'],
                'SCI': data['sci'],
                'Color_Grade': data['color_grade']
            }])
            
            # Encode color grade - handle unknown labels
            try:
                input_df['Color_Grade'] = self.color_encoder.transform(input_df['Color_Grade'])
            except ValueError:
                # If color grade not in encoder, use the most common class (0 or mode)
                logger.warning(f"Unknown color grade: {data['color_grade']}. Using default encoding.")
                # Get available classes
                available_classes = list(self.color_encoder.classes_)
                logger.info(f"Available color grades: {available_classes}")
                # Use first class as default or raise informative error
                raise ValueError(f"Color grade '{data['color_grade']}' not recognized. Available options: {', '.join(available_classes)}")
            
            # Scale features
            input_scaled = self.scaler.transform(input_df)
            
            # Predict
            prediction = self.model.predict(input_scaled)[0]
            probabilities = self.model.predict_proba(input_scaled)[0]
            
            # Map classes
            classes = {0: 'Low Grade', 1: 'Premium', 2: 'Standard'}
            
            return {
                'quality_class': classes[prediction],
                'confidence': float(probabilities[prediction]),
                'probabilities': {
                    'low_grade': float(probabilities[0]),
                    'premium': float(probabilities[1]),
                    'standard': float(probabilities[2])
                }
            }
        except Exception as e:
            logger.error(f"Error in HVI prediction: {e}")
            raise


class CottonVisionClassifier:
    """Computer Vision - Clean/Dirty classification from images"""
    
    def __init__(self):
        self.model = None
        self.load_model()
    
    def load_model(self):
        try:
            import tensorflow as tf
            self.model = tf.keras.models.load_model(os.path.join(MODELS_DIR, 'cotton_model.keras'))
            logger.info("Computer Vision model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading CV model: {e}")
    
    def predict(self, image_path):
        """
        Predict if cotton is clean or dirty from image
        
        Args:
            image_path (str): Path to cotton image
        
        Returns:
            dict: {
                'label': str ('Clean' or 'Dirty'),
                'confidence': float,
                'score': float
            }
        """
        if not self.model:
            raise Exception("Computer Vision model not loaded")
        
        try:
            # Load and preprocess image
            image = Image.open(image_path).convert('RGB')
            img_array = np.array(image)
            img_resized = cv2.resize(img_array, (224, 224))
            img_batch = np.expand_dims(img_resized, 0)
            
            # Predict
            prediction = self.model.predict(img_batch)
            score = float(prediction[0][0])
            
            # Interpret results (0=Clean, 1=Dirty)
            if score > 0.5:
                label = "Dirty"
                confidence = score
            else:
                label = "Clean"
                confidence = 1 - score
            
            return {
                'label': label,
                'confidence': confidence,
                'score': score
            }
        except Exception as e:
            logger.error(f"Error in CV prediction: {e}")
            raise


class SeedRecommender:
    """Seed Recommendation - Yield and quality prediction"""
    
    def __init__(self):
        self.yield_model = None
        self.quality_model = None
        self.location_encoder = None
        self.variety_encoder = None
        self.load_models()
    
    def load_models(self):
        try:
            self.yield_model = joblib.load(os.path.join(MODELS_DIR, 'yield_model.pkl'))
            self.quality_model = joblib.load(os.path.join(MODELS_DIR, 'quality_model.pkl'))
            self.location_encoder = joblib.load(os.path.join(MODELS_DIR, 'loc_encoder.pkl'))
            self.variety_encoder = joblib.load(os.path.join(MODELS_DIR, 'var_encoder.pkl'))
            logger.info("Seed recommendation models loaded successfully")
        except Exception as e:
            logger.error(f"Error loading seed models: {e}")
    
    def get_recommendations(self, location):
        """
        Get top seed variety recommendations for a location
        
        Args:
            location (str): Farm location/region
        
        Returns:
            list: Top 3 recommendations with yield and quality predictions
        """
        if not self.yield_model:
            raise Exception("Seed models not loaded")
        
        try:
            # Variety information
            varieties_info = {
                'PHY 485WRF': {'type': 'Upland', 'brand': 'PhytoGen (Corteva)'},
                'DP 555 R/R': {'type': 'Upland', 'brand': 'DeltaPine (Monsanto)'},
                'FM 960B2R': {'type': 'Upland', 'brand': 'FiberMax (Bayer)'},
                'STV 4892 BR': {'type': 'Upland', 'brand': 'Stoneville'},
                'DPL 445BR': {'type': 'Upland', 'brand': 'DeltaPine'},
                'TAMCOT 22': {'type': 'Upland', 'brand': 'Tamcot (Texas A&M)'},
                'COBALT': {'type': 'Pima', 'brand': 'Cobalt Pima (Premium)'},
                'DP 340': {'type': 'Pima', 'brand': 'DeltaPine Pima'},
                'PHY 800': {'type': 'Pima', 'brand': 'PhytoGen Pima'}
            }
            
            # Encode location
            loc_code = self.location_encoder.transform([location])[0]
            
            # Get all varieties
            all_varieties = self.variety_encoder.classes_
            
            results = []
            for variety in all_varieties:
                var_code = self.variety_encoder.transform([variety])[0]
                
                # Predict
                pred_yield = self.yield_model.predict([[loc_code, var_code]])[0]
                pred_quality = self.quality_model.predict([[loc_code, var_code]])[0]
                
                # Get variety info
                info = varieties_info.get(variety, {'type': 'Other', 'brand': 'Local'})
                
                # Calculate score
                price_multiplier = 1.3 if info['type'] == 'Pima' else 1.0
                score = (pred_yield * price_multiplier) + (pred_quality * 5)
                
                results.append({
                    'variety': variety,
                    'type': info['type'],
                    'brand': info['brand'],
                    'predicted_yield': int(pred_yield),
                    'predicted_quality': round(pred_quality, 1),
                    'score': score
                })
            
            # Sort by score and return top 3
            results.sort(key=lambda x: x['score'], reverse=True)
            return results[:3]
            
        except Exception as e:
            logger.error(f"Error in seed recommendation: {e}")
            raise


# Singleton instances
hvi_classifier = HVIClassifier()
vision_classifier = CottonVisionClassifier()
seed_recommender = SeedRecommender()
