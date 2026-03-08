import requests
import json
import pandas as pd
from datetime import datetime
import os
from visualizer import plot_portfolio

def load_portfolio(file_path='portfolio.json'):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {file_path} not found!")
        return {}
    except json.JSONDecodeError:
        print("Error: Invalid JSON in portfolio.json")
        return {}

def fetch_latest_nav(scheme_code):
    url = f"https://api.mfapi.in/mf/{scheme_code}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get('data'):
            latest = data['data'][0]
            return float(latest['nav']), latest['date']
        return None, None
    except Exception as e:
        print(f"Error fetching {scheme_code}: {e}")
        return None, None

def log_to_csv(report, filename='data/historical.csv'):
    os.makedirs('data', exist_ok=True)
    today = datetime.now().strftime('%Y-%m-%d')
    row = {'date': today}
    row.update({f"{fund}_value": value for fund, value in report.items()})
    
    df_new = pd.DataFrame([row])
    
    if os.path.exists(filename):
        df_old = pd.read_csv(filename)
        df = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df = df_new
    
    df.to_csv(filename, index=False)
    print(f"Logged to {filename}")

def simple_forecast(current_value, annual_rate=0.12, months=24):
    """Project value assuming constant annual return"""
    monthly_rate = (1 + annual_rate) ** (1/12) - 1
    future_values = []
    dates = []
    value = current_value
    today = datetime.now()
    
    for m in range(1, months + 1):
        value *= (1 + monthly_rate)
        future_date = today + pd.DateOffset(months=m)
        dates.append(future_date.strftime('%Y-%m'))
        future_values.append(value)
    
    df = pd.DataFrame({'Month': dates, 'Projected Value': future_values})
    print("\n24-Month Projection (12% CAGR assumed):")
    print(df.round(2))
    return df

def generate_report():
    portfolio = load_portfolio()
    if not portfolio:
        print("No portfolio loaded. Check portfolio.json")
        return
    
    print(f"{'Fund Name':<30} | {'NAV':<10} | {'Value (₹)':<15} | {'Units':<10}")
    print("-" * 70)
    
    report = {}
    total_value = 0.0
    
    for code, info in portfolio.items():
        nav, date = fetch_latest_nav(code)
        if nav is not None:
            value = nav * info['units']
            total_value += value
            report[info['name']] = value
            
            print(f"{info['name']:<30} | {nav:<10.2f} | {value:>12,.2f} | {info['units']:<10}")
        else:
            print(f"{info.get('name', code):<30} | FAILED TO FETCH NAV")
    
    print("-" * 70)
    print(f"{'TOTAL PORTFOLIO':<30} | {' ':<10} | {total_value:>12,.2f}")
    # After printing total
    if total_value > 0:
        simple_forecast(total_value)
    
    log_to_csv(report)
    plot_portfolio(report)

if __name__ == "__main__":
    generate_report()