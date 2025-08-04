#!/usr/bin/env python3
import sqlite3

def analyze_database():
    conn = sqlite3.connect('app/araba_verileri.db')
    cursor = conn.cursor()
    
    print("=== ANALYZING CAR DATABASE ===\n")
    
    # Get total count
    cursor.execute('SELECT COUNT(*) FROM araba_ilanlari')
    total_cars = cursor.fetchone()[0]
    print(f"Total cars in database: {total_cars}\n")
    
    print("=== KASA_TIPI (Body Types) ===")
    cursor.execute('SELECT DISTINCT kasa_tipi, COUNT(*) as count FROM araba_ilanlari GROUP BY kasa_tipi ORDER BY count DESC')
    kasa_types = cursor.fetchall()
    for kasa, count in kasa_types:
        percentage = (count/total_cars)*100
        print(f"'{kasa}': {count} ({percentage:.1f}%)")
    
    print("\n=== YAKIT (Fuel Types) ===")
    cursor.execute('SELECT DISTINCT yakit, COUNT(*) as count FROM araba_ilanlari GROUP BY yakit ORDER BY count DESC')
    fuel_types = cursor.fetchall()
    for fuel, count in fuel_types:
        percentage = (count/total_cars)*100
        print(f"'{fuel}': {count} ({percentage:.1f}%)")
    
    print("\n=== VITES (Transmission Types) ===")
    cursor.execute('SELECT DISTINCT vites, COUNT(*) as count FROM araba_ilanlari GROUP BY vites ORDER BY count DESC')
    trans_types = cursor.fetchall()
    for trans, count in trans_types:
        percentage = (count/total_cars)*100
        print(f"'{trans}': {count} ({percentage:.1f}%)")
    
    print("\n=== MILEAGE ANALYSIS ===")
    cursor.execute('SELECT MIN(km), MAX(km), AVG(km) FROM araba_ilanlari WHERE km IS NOT NULL')
    km_stats = cursor.fetchone()
    print(f"Mileage range: {km_stats[0]:,.0f} - {km_stats[1]:,.0f} km")
    print(f"Average mileage: {km_stats[2]:,.0f} km")
    
    # Mileage thresholds
    thresholds = [30000, 50000, 80000, 100000, 150000, 200000]
    for threshold in thresholds:
        cursor.execute('SELECT COUNT(*) FROM araba_ilanlari WHERE km <= ? AND km IS NOT NULL', (threshold,))
        count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM araba_ilanlari WHERE km IS NOT NULL')
        total_with_km = cursor.fetchone()[0]
        percentage = (count/total_with_km)*100
        print(f"Cars with ≤{threshold:,} km: {count} ({percentage:.1f}%)")
    
    print("\n=== YEAR ANALYSIS ===")
    cursor.execute('SELECT MIN(yil), MAX(yil), AVG(yil) FROM araba_ilanlari WHERE yil IS NOT NULL')
    year_stats = cursor.fetchone()
    print(f"Year range: {year_stats[0]} - {year_stats[1]}")
    print(f"Average year: {year_stats[2]:.0f}")
    
    # Age analysis (assuming current year is 2025)
    current_year = 2025
    age_thresholds = [1, 2, 3, 5, 7, 10]
    for age in age_thresholds:
        min_year = current_year - age
        cursor.execute('SELECT COUNT(*) FROM araba_ilanlari WHERE yil >= ? AND yil IS NOT NULL', (min_year,))
        count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM araba_ilanlari WHERE yil IS NOT NULL')
        total_with_year = cursor.fetchone()[0]
        percentage = (count/total_with_year)*100
        print(f"Cars ≤{age} years old ({min_year}+): {count} ({percentage:.1f}%)")
    
    print("\n=== TOP BRANDS ===")
    cursor.execute('SELECT DISTINCT marka, COUNT(*) as count FROM araba_ilanlari GROUP BY marka ORDER BY count DESC LIMIT 15')
    brands = cursor.fetchall()
    for brand, count in brands:
        percentage = (count/total_cars)*100
        print(f"'{brand}': {count} ({percentage:.1f}%)")
    
    conn.close()

if __name__ == "__main__":
    analyze_database()
