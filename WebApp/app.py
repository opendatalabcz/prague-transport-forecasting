from flask import Flask, render_template, request, jsonify
from processor import DataProcessor
from catboost import CatBoostRegressor
import numpy as np
import pandas as pd
import shap
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

# 1. Inicializace procesoru (načte kalendář do paměti)
# Uprav cestu ke kalendáři a start_date podle tvého notebooku
processor = DataProcessor(start_date_str='2025-01-01')

# 2. Načtení modelu
# Pokud používáš jiný formát (joblib/pickle), uprav načítání
model_cars = CatBoostRegressor()
model_cars.load_model("models/car_model.cbm")
explainer_cars = shap.TreeExplainer(model_cars)

model_cyclo = CatBoostRegressor()
model_cyclo.load_model("models/bike_model.cbm")
explainer_cyclo = shap.TreeExplainer(model_cyclo)

model_mhd = CatBoostRegressor()
model_mhd.load_model("models/mhd_model.cbm")
explainer_mhd = shap.TreeExplainer(model_mhd)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        
        # Auta ----------------------------------
        df_cars = processor.transform(data, mode='cars')
        prediction_car = model_cars.predict(df_cars)[0]
        car_bins = np.load('models/car_bins.npy')
        final_car_val = pd.cut(
                            pd.Series([prediction_car]),
                            bins=car_bins,
                            labels=[1, 2, 3, 4, 5]
                        ).iloc[0]
        final_car_val = int(str(final_car_val))

        # Vytvoření grafu
        shap_values = explainer_cars(df_cars)
        
        plt.figure(figsize=(8, 4))
        shap.plots.waterfall(shap_values[0], show=False)
        plt.tight_layout()
        
        # Převod grafu na obrázek (base64)
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        car_img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close() # uvolnění paměťi
        
        # MHD ----------------------------------
        df_mhd = processor.transform(data, mode='mhd')
        prediction_mhd = model_mhd.predict(df_mhd)[0]
        mhd_bins = np.load('models/mhd_bins.npy')
        final_mhd_val = pd.cut(
                            pd.Series([prediction_mhd]),
                            bins=mhd_bins,
                            labels=[1, 2, 3, 4, 5]
                        ).iloc[0]
        final_mhd_val = int(str(final_mhd_val))

        # Vytvoření grafu
        shap_values = explainer_mhd(df_mhd)
        
        plt.figure(figsize=(8, 4))
        shap.plots.waterfall(shap_values[0], show=False)
        plt.tight_layout()
        
        # Převod grafu na obrázek (base64)
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        mhd_img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close() # uvolnění paměťi

        # Kola ----------------------------------
        df_cyclo = processor.transform(data, mode='bike')
        prediction_cyclo = model_cyclo.predict(df_cyclo)[0]
        cyclo_bins = np.load('models/cyclo_bins.npy')
        final_cyclo_val = pd.cut(
                            pd.Series([prediction_cyclo]),
                            bins=cyclo_bins,
                            labels=[1, 2, 3, 4, 5]
                        ).iloc[0]
        final_cyclo_val = int(str(final_cyclo_val))

        # Vytvoření grafu
        shap_values = explainer_cyclo(df_cyclo)
        
        plt.figure(figsize=(8, 4))
        shap.plots.waterfall(shap_values[0], show=False)
        plt.tight_layout()
        
        # Převod grafu na obrázek (base64)
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        cyclo_img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close() # uvolnění paměťi

        return jsonify({
            'success': True,
            'car_value': final_car_val,
            'car_shap': car_img_base64,
            'cyclo_value': final_cyclo_val,
            'cyclo_shap': cyclo_img_base64,
            'mhd_value': final_mhd_val,
            'mhd_shap': mhd_img_base64
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)