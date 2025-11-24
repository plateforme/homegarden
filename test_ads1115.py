#!/usr/bin/env python3
"""
Script de test pour vérifier la connexion du capteur ADS1115
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

def test_i2c_bus():
    """Teste si le bus I2C est disponible"""
    print("=" * 50)
    print("Test de connexion ADS1115")
    print("=" * 50)
    
    try:
        print("\n1. Vérification du bus I2C...")
        i2c = busio.I2C(board.SCL, board.SDA)
        print("   ✓ Bus I2C initialisé avec succès")
        
        # Scanner le bus I2C pour détecter les périphériques
        print("\n2. Scan du bus I2C pour détecter les périphériques...")
        while not i2c.try_lock():
            pass
        
        try:
            devices = i2c.scan()
            if devices:
                print(f"   ✓ Périphériques I2C détectés aux adresses: {[hex(addr) for addr in devices]}")
                # L'ADS1115 a généralement l'adresse 0x48 (par défaut)
                if 0x48 in devices:
                    print("   ✓ ADS1115 détecté à l'adresse 0x48")
                else:
                    print("   ⚠ ADS1115 non détecté à l'adresse 0x48")
                    print("   ⚠ Vérifiez les connexions I2C (SDA, SCL)")
            else:
                print("   ✗ Aucun périphérique I2C détecté")
                print("   ✗ Vérifiez les connexions I2C (SDA, SCL)")
                return False
        finally:
            i2c.unlock()
        
        print("\n3. Initialisation de l'ADS1115...")
        ads = ADS.ADS1115(i2c)
        print("   ✓ ADS1115 initialisé avec succès")
        
        print("\n4. Configuration du canal P0 (capteur d'humidité du sol)...")
        chan = AnalogIn(ads, ADS.P0)
        print("   ✓ Canal P0 configuré")
        
        print("\n5. Test de lecture du capteur...")
        print("   Effectuation de 5 lectures pour vérifier la stabilité...")
        
        readings = []
        for i in range(5):
            try:
                voltage = chan.voltage
                value = chan.value
                # Calcul du pourcentage d'humidité (inversé car tension basse = sol humide)
                moisture_percentage = (1 - (voltage / 3.3)) * 100
                moisture_percentage = max(0, min(100, moisture_percentage))
                
                readings.append({
                    'voltage': voltage,
                    'value': value,
                    'moisture': moisture_percentage
                })
                
                print(f"   Lecture {i+1}:")
                print(f"      - Tension: {voltage:.3f} V")
                print(f"      - Valeur brute: {value}")
                print(f"      - Humidité du sol: {moisture_percentage:.2f}%")
                
                time.sleep(0.5)
            except Exception as e:
                print(f"   ✗ Erreur lors de la lecture {i+1}: {e}")
                return False
        
        # Vérifier la cohérence des lectures
        voltages = [r['voltage'] for r in readings]
        avg_voltage = sum(voltages) / len(voltages)
        voltage_range = max(voltages) - min(voltages)
        
        print(f"\n6. Analyse des résultats...")
        print(f"   - Tension moyenne: {avg_voltage:.3f} V")
        print(f"   - Plage de variation: {voltage_range:.3f} V")
        
        if voltage_range < 0.1:
            print("   ✓ Lectures stables")
        else:
            print("   ⚠ Variations importantes détectées")
        
        if 0 <= avg_voltage <= 3.3:
            print("   ✓ Tension dans la plage valide (0-3.3V)")
        else:
            print("   ✗ Tension hors plage normale")
            return False
        
        print("\n" + "=" * 50)
        print("✓ TEST RÉUSSI - Le capteur ADS1115 est bien connecté")
        print("=" * 50)
        return True
        
    except ValueError as e:
        print(f"\n✗ Erreur de valeur: {e}")
        print("   Vérifiez que le bus I2C est activé sur le Raspberry Pi")
        print("   Utilisez: sudo raspi-config -> Interface Options -> I2C -> Enable")
        return False
    except OSError as e:
        print(f"\n✗ Erreur d'accès: {e}")
        print("   Vérifiez les connexions physiques:")
        print("   - SDA connecté au GPIO 2 (pin 3)")
        print("   - SCL connecté au GPIO 3 (pin 5)")
        print("   - VCC connecté au 3.3V")
        print("   - GND connecté à la masse")
        return False
    except Exception as e:
        print(f"\n✗ Erreur inattendue: {e}")
        print(f"   Type d'erreur: {type(e).__name__}")
        return False

if __name__ == '__main__':
    success = test_i2c_bus()
    sys.exit(0 if success else 1)

