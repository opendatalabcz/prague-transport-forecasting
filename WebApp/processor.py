import pandas as pd
import numpy as np
import datetime
import holidays

class DataProcessor:
    def __init__(self, calendar_path="static/calendar_features.csv", start_date_str='2021-01-01'):
        self.cz_holidays = holidays.CZ()
        self.start_date = pd.to_datetime(start_date_str)
        
        # Definice mapování
        self.mappings = {
            'temp': {'mrazivo': -3, 'chladno': 6, 'mirne': 15, 'horko': 25},
            'sun': {'0': 0, '2': 2, '4': 4, '6': 6, '8': 8, '10': 10, '12': 12, '14': 14},
            'wind': {'slaby': 1.0, 'stredni': 2.6, 'silny': 5.0},
            'rain': {'zadny': 0.0, 'slaby': 3.0, 'stredni': 9.0, 'silny': 15.0},
            'snow': {'zadny': 0.0, 'poprasek': 2.0, 'závěj': 12.0}
        }


        # Definice seznamu features pro jednotlivé modely
        # POZOR: Pořadí musí přesně odpovídat tomu, jak byly modely trénovány!
        self.feature_lists = {
            'cars': [
                'weekday', 'school_impact_scale', 'doy_sin','workday_vacation',
                'month_sin', 'weekday_cos', 'holiday','weekday_sin', 'month_cos',
                'is_workday', 'workday_rain', 'lockdown_level', 'exodus_pressure',
                'nonwork_block_size', 'school_holiday', 'TEMP', 'TEMP_sq',
                'return_pressure'
            ],
            'bike': [
                'SUN_TEMP_inter', 'doy_cos', 'is_workday', 'weekday', 'WIND', 
                'month', 'RAIN', 'TEMP_sq', 'holiday_proximity', 'school_holiday', 
                'rain_intensity_interaction', 'lockdown_level', 'month_cos', 'early_sun_joy'

            ],
            'mhd': [
                'weekday_sin', 'SNOW', 'workday_rain', 'doy_sin', 'RAIN', 
                'workday_vacation', 'holiday', 'time_idx', 'WIND_RAIN_inter', 
                'SUN', 'month', 'doy_cos', 'lockdown_level', 'weekday_cos'
            ]
        }

        # 4. Načtení a příprava kalendáře
        df_cal = pd.read_csv(calendar_path)
        df_cal['date'] = pd.to_datetime(df_cal['date'])
        df_cal = self._prepare_calendar(df_cal)
        self.calendar_data = df_cal.set_index('date')

    def _prepare_calendar(self, df):
        """Spustí tvou logiku výpočtu tlaků a proximity na celém kalendáři."""
        df = df.sort_values('date').copy()
        
        # 1. IDENTIFIKACE BLOKŮ VOLNA (Víkendy + Svátky)
        # work_free: 1 pro den volna, 0 pro pracovní den
        df['work_free'] = (df['is_workday'] == 0).astype(int)
        
        # Seskupení po sobě jdoucích stejných typů dní (volno vs. práce)
        df['work_block_id'] = (df['work_free'] != df['work_free'].shift()).cumsum()
        
        # nonwork_block_size: Velikost aktuálního bloku volna. 
        # Pro pracovní dny bude 0, pro dny volna to bude délka celého bloku (např. 3 pro prodloužený víkend)
        df['nonwork_block_size'] = df.groupby('work_block_id')['work_free'].transform('sum')
        
        # 2. IDENTIFIKACE BLOKŮ ŠKOLNÍCH PRÁZDNIN
        df['school_block_id'] = (df['school_holiday'] != df['school_holiday'].shift()).cumsum()
        school_block_len = df.groupby('school_block_id')['school_holiday'].transform('sum')
        
        # 3. EXODUS & RETURN (Tlak na odjezd a návrat)
        # Využíváme nonwork_block_size k určení síly tlaku
        df['work_exodus'] = 0.0
        # Den před začátkem bloku volna (poslední pracovní den)
        w_exo_mask = (df['work_free'] == 0) & (df['work_free'].shift(-1) == 1)
        df.loc[w_exo_mask, 'work_exodus'] = df['nonwork_block_size'].shift(-1)
        
        df['work_return'] = 0.0
        # Poslední den bloku volna (před návratem do práce)
        w_ret_mask = (df['work_free'] == 1) & (df['work_free'].shift(-1) == 0)
        df.loc[w_ret_mask, 'work_return'] = df['nonwork_block_size']
        
        # Finální tlaky (zastropované na 9, jak jsi chtěla)
        df['exodus_pressure'] = (df['work_exodus'] * 1.0).clip(upper=9.0)
        df['return_pressure'] = (df['work_return'] * 1.0).clip(upper=9.0)
        
        # 4. SCHOOL IMPACT SCALE
        df['school_impact_scale'] = 0
        mask_h = df['school_holiday'] == 1
        # Délka konkrétního bloku prázdnin
        h_lengths = df[mask_h].groupby('school_block_id')['date'].transform('count')
        
        df.loc[mask_h, 'school_impact_scale'] = np.where(h_lengths <= 1, 1,
                                                np.where(h_lengths <= 4, 2,
                                                np.where(h_lengths <= 9, 3, 5)))

        # 5. ČASOVÉ A CYKLICKÉ FEATURES
        df['time_idx'] = (df['date'] - self.start_date).dt.days
        df['month'] = df['date'].dt.month
        df['weekday'] = df['date'].dt.weekday
        
        # Goniometrické funkce pro zachování cykličnosti času
        df['month_sin'] = np.sin(2 * np.pi * (df['month'] - 1) / 12)
        df['month_cos'] = np.cos(2 * np.pi * (df['month'] - 1) / 12)
        df['weekday_sin'] = np.sin(2 * np.pi * df['weekday'] / 7)
        df['weekday_cos'] = np.cos(2 * np.pi * df['weekday'] / 7)
        
        doy = df['date'].dt.dayofyear
        df['doy_sin'] = np.sin(2 * np.pi * doy / 365.25)
        df['doy_cos'] = np.cos(2 * np.pi * doy / 365.25)

        # 6. PROXIMITY A OSTATNÍ
        df['is_workday_shifted_prev'] = df['is_workday'].shift(1)
        df['is_workday_shifted_next'] = df['is_workday'].shift(-1)
        
        # Holiday proximity (Den sousedící s volnem)
        df['holiday_proximity'] = ((df['is_workday'] == 1) & 
                                   ((df['is_workday_shifted_prev'] == 0) | 
                                    (df['is_workday_shifted_next'] == 0))).astype(int)
        
        # Bridge day (Osamocený pracovní den mezi dny volna)
        df['bridge_day'] = ((df['is_workday'] == 1) & 
                            (df['is_workday_shifted_prev'] == 0) & 
                            (df['is_workday_shifted_next'] == 0)).astype(int)
        
        df['workday_vacation'] = df['is_workday'] * df['school_holiday']

        return df

    def transform(self, data, mode='cars'):
        """Univerzální transformace pro jakýkoliv mód."""
        target_date = pd.to_datetime(data['date'])
        if target_date not in self.calendar_data.index:
            raise ValueError("Datum mimo rozsah kalendáře.")

        # Základ z kalendáře
        row = self.calendar_data.loc[target_date].to_dict()
        
        # Hodnoty z webu (převedené na čísla)
        T = self.mappings['temp'].get(data.get('temp'), 15)
        S = self.mappings['sun'].get(data.get('sun'), 8)
        W = self.mappings['wind'].get(data.get('wind'), 2.0)
        R = self.mappings['rain'].get(data.get('rain'), 0.0)
        SN = self.mappings['snow'].get(data.get('snow'), 0.0)

        # Výpočet společných interakcí
        row['TEMP'] = T
        row['RAIN'] = R
        row['SNOW'] = SN
        row['WIND'] = W
        row['SUN'] = S
        row['TEMP_sq'] = T ** 2
        row['temp_deviation'] = abs(T - 20)
        row['bad_weather'] = 1 if (R > 0 or SN > 0 or W > 3) else 0
        row['workday_rain'] = row['is_workday'] * (1 if R > 0.5 else 0)
        
        # Specifické pro BIKE
        row['SUN_TEMP_inter'] = S * T
        row['WIND_RAIN_inter'] = R * W
        row['rain_intensity_interaction'] = R * row['month_sin']
        row['early_sun_joy'] = row['SUN'] * int(row['month'] <= 4)

        # Vytvoření DataFrame se správným pořadím sloupců
        return pd.DataFrame([row])[self.feature_lists[mode]]