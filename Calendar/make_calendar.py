import pandas as pd
import numpy as np
from datetime import date
import holidays

dates = pd.date_range(start="2020-01-01", end="2025-12-31", freq="D")
df = pd.DataFrame({"date": dates})

# Základní časové atributy
df["year"] = df["date"].dt.year
df["month"] = df["date"].dt.month
df["day"] = df["date"].dt.day
df["weekday"] = df["date"].dt.day_name()
df["weekend"] = df["weekday"].isin(["Saturday", "Sunday"]).astype(int)

# České státní svátky
cz_holidays = holidays.Czechia(years=range(2020, 2026))
df["holiday"] = df["date"].isin(cz_holidays).astype(int)

# Školní prázdniny
def is_school_holiday(d):
    m, day = d.month, d.day
    # Letní prázdniny
    if m in [7, 8]:
        return True
    # Podzimní prázdniny
    if date(2020, 10, 29) <= d.date() <= date(2020, 10, 30) or \
       date(2021, 10, 27) <= d.date() <= date(2021, 10, 29) or \
       date(2022, 10, 26) <= d.date() <= date(2022, 10, 27) or \
       date(2023, 10, 26) <= d.date() <= date(2023, 10, 27) or \
       date(2024, 10, 29) <= d.date() <= date(2024, 10, 30) or \
       date(2025, 10, 27) <= d.date() <= date(2025, 10, 29):
        return True
    # Vánoční prázdniny
    if (m == 12 and day >= 23) or (m == 1 and day <= 2):
        return True
    # Pololetní prázdniny
    if d.date in [date(2020, 1, 31), date(2021, 1, 29),
                  date(2022, 2, 4), date(2023, 2, 3),
                  date(2024, 2, 2), date(2025, 1, 31)]:
        return True
    # Jarní prázdniny – přibližně únor–březen (různé týdny v Praze)
    if date(2020, 2, 3) <= d.date() <= date(2020, 2, 9) or \
        date(2020, 3, 2) <= d.date() <= date(2020, 3, 8) or \
        date(2021, 2, 22) <= d.date() <= date(2021, 2, 28) or \
        date(2021, 3, 1) <= d.date() <= date(2021, 3, 7) or \
        date(2022, 3, 7) <= d.date() <= date(2022, 3, 13) or \
        date(2022, 3, 14) <= d.date() <= date(2022, 3, 20) or \
        date(2023, 2, 6) <= d.date() <= date(2023, 2, 12) or \
        date(2023, 2, 13) <= d.date() <= date(2023, 2, 19) or \
        date(2024, 2, 5) <= d.date() <= date(2024, 2, 11) or \
        date(2024, 2, 12) <= d.date() <= date(2024, 2, 18) or \
        date(2025, 2, 10) <= d.date() <= date(2025, 2, 16) or \
        date(2025, 2, 17) <= d.date() <= date(2025, 2, 23):
        return True
    # Velikonoční prázdniny
    if d.date() in [date(2020, 4, 9), date(2021, 4, 1),
                    date(2022, 4, 14), date(2023, 4, 6),
                    date(2024, 3, 28), date(2025, 4, 17)]:
        return True
       
    return False

df["school_holiday"] = df["date"].apply(is_school_holiday).astype(int)

# 5. Sezóna
def get_season(month):
    if month in [12, 1, 2]:
        return "winter"
    elif month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    else:
        return "autumn"

df["season"] = df["month"].apply(get_season)

# 6. Covid lockdown úrovně (ručně zhruba podle reality v ČR)
def lockdown_level(d):
    if date(2020, 3, 11) <= d.date() <= date(2020, 5, 10):
        return 3
    if date(2020, 10, 5) <= d.date() <= date(2020, 12, 3):
        return 2
    if date(2021, 2, 27) <= d.date() <= date(2021, 4, 11):
        return 3
    if date(2021, 11, 20) <= d.date() <= date(2021, 12, 31):
        return 1
    return 0

df["lockdown_level"] = df["date"].apply(lockdown_level)

# 7. Běžný pracovní den
df["is_workday"] = ((df["weekend"] == 0) & (df["holiday"] == 0)).astype(int)

# 8. Ulož
df.to_csv("Calendar/calendar_features.csv", index=False)
