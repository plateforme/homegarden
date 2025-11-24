#!/usr/bin/env python3
"""
Script de diagnostic pour le capteur d'humidité du sol
Affiche les valeurs brutes pour comprendre le problème
"""
import sys
import os
import time

# Ajouter le chemin des modules locaux
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib/python3.11/site-packages'))

import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

def diagnostic_humidite():
    """Effectue un diagnostic du capteur d'humidité"""
    print("=" * 60)
    print("DIAGNOSTIC DU CAPTEUR D'HUMIDITÉ DU SOL")
    print("=" * 60)
    
    try:
        # Initialisation
        print("\n1. Initialisation de l'ADS1115...")
        i2c = busio.I2C(board.SCL, board.SDA)
        ads = ADS.ADS1115(i2c)
        chan = AnalogIn(ads, ADS.P0)
        print("   ✓ ADS1115 initialisé")
        
        print("\n2. Lecture des valeurs (10 mesures)...")
        print("-" * 60)
        
        voltages = []
        values = []
        moisture_current = []  # Formule actuelle
        moisture_inverted = []  # Formule inversée
        
        for i in range(10):
            voltage = chan.voltage
            value = chan.value
            
            # Formule actuelle (tension basse = humide)
            moisture_curr = (1 - (voltage / 3.3)) * 100
            moisture_curr = max(0, min(100, moisture_curr))
            
            # Formule inversée (tension basse = sec)
            moisture_inv = (voltage / 3.3) * 100
            moisture_inv = max(0, min(100, moisture_inv))
            
            voltages.append(voltage)
            values.append(value)
            moisture_current.append(moisture_curr)
            moisture_inverted.append(moisture_inv)
            
            print(f"Lecture {i+1:2d}: Tension={voltage:6.3f}V | "
                  f"Valeur brute={value:5d} | "
                  f"Formule actuelle={moisture_curr:6.2f}% | "
                  f"Formule inversée={moisture_inv:6.2f}%")
            
            time.sleep(0.5)
        
        # Statistiques
        print("\n" + "-" * 60)
        print("3. STATISTIQUES")
        print("-" * 60)
        print(f"Tension moyenne: {sum(voltages)/len(voltages):.3f} V")
        print(f"Tension min:     {min(voltages):.3f} V")
        print(f"Tension max:     {max(voltages):.3f} V")
        print(f"Plage:           {max(voltages) - min(voltages):.3f} V")
        print()
        print(f"Humidité (formule actuelle) - Moyenne: {sum(moisture_current)/len(moisture_current):.2f}%")
        print(f"Humidité (formule inversée) - Moyenne: {sum(moisture_inverted)/len(moisture_inverted):.2f}%")
        
        # Analyse
        print("\n" + "-" * 60)
        print("4. ANALYSE")
        print("-" * 60)
        avg_voltage = sum(voltages) / len(voltages)
        
        if avg_voltage < 0.1:
            print("⚠ Tension très basse (< 0.1V)")
            print("  → Cela indique soit:")
            print("    1. Le sol est très humide (si la formule actuelle est correcte)")
            print("    2. Le sol est très sec (si la formule doit être inversée)")
            print("    3. Problème de connexion ou capteur défectueux")
        elif avg_voltage > 3.0:
            print("⚠ Tension très élevée (> 3.0V)")
            print("  → Cela indique soit:")
            print("    1. Le sol est très sec (si la formule actuelle est correcte)")
            print("    2. Le sol est très humide (si la formule doit être inversée)")
            print("    3. Problème de connexion ou capteur défectueux")
        else:
            print("✓ Tension dans une plage normale")
        
        print("\n" + "=" * 60)
        print("RECOMMANDATION:")
        print("=" * 60)
        print("Si la terre est SÈCHE mais le capteur indique une humidité élevée")
        print("(comme 98.63%), alors la formule est probablement INVERSÉE.")
        print()
        print("Solution: Remplacer dans app.py ligne 66:")
        print("  AVANT: moisture_percentage = (1 - (voltage / 3.3)) * 100")
        print("  APRÈS: moisture_percentage = (voltage / 3.3) * 100")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    success = diagnostic_humidite()
    sys.exit(0 if success else 1)


