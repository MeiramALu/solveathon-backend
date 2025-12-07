# ML Models Directory

Place your trained models here:

## Required Models for Quality Control:

### HVI Classification (Tab 1):

- `cotton_xgboost_model.pkl` - XGBoost model for quality classification
- `cotton_scaler.pkl` - StandardScaler for feature normalization
- `color_encoder.pkl` - LabelEncoder for color grade encoding

### Computer Vision (Tab 2):

- `cotton_model.keras` - CNN model for clean/dirty classification

### Seed Recommendation (Tab 3):

- `yield_model.pkl` - Model for yield prediction
- `quality_model.pkl` - Model for quality prediction
- `loc_encoder.pkl` - LabelEncoder for location
- `var_encoder.pkl` - LabelEncoder for variety

## Note:

Copy these files from your training directory to this location.
