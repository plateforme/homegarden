from flask import Flask, render_template, jsonify, request
import adafruit_dht
import board
import RPi.GPIO as GPIO
import threading
import time
import datetime
import os
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import json
from nodes_api import (
    register_node, get_node, get_all_nodes, 
    record_node_data, get_node_history
)

app = Flask(__name__)

# Configuration des GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.OUT)  # Pompe

# Configuration I2C pour ADS1115
i2c = busio.I2C(board.SCL, board.SDA)

# Configuration ADS1115
ads = ADS.ADS1115(i2c)
chan = AnalogIn(ads, ADS.P0)

# Configuration du GPIO pour DHT11
dht_device = adafruit_dht.DHT11(board.D4)  # Utiliser le bon pin, D4 pour GPIO4

# Fichier pour enregistrer l'historique des arrosages et des lectures
log_file = "arrosage_log.csv"
temp_humidity_log_file = "temp_humidity_log.csv"
soil_moisture_log_file = "soil_moisture_log.csv"
data_file = "data.json"

# Variables globales pour le contrôle de la pompe
pump_on_time = None
watering_duration_minutes = None
last_watering_time = None  # Dernier arrosage pour protection anti-excès
maintenance_mode = False  # Mode maintenance
vacation_mode = False  # Mode vacances
scheduled_waterings = []  # Planification d'arrosage

# Cache de configuration pour optimiser les performances
_config_cache = None
_config_cache_time = None
_config_cache_ttl = 5  # Temps de cache en secondes

def load_config():
    if os.path.exists(data_file):
        with open(data_file, 'r') as file:
            config = json.load(file)
            print(f"Configuration chargée : {config}")
    else:
        save_config()

def save_config():
    # Cette fonction n'est plus utilisée car la config est dans data.json
    # Gardée pour compatibilité
    pass

load_config()

def get_soil_moisture():
    """Lit l'humidité du sol depuis l'ADS1115
    
    Returns:
        float: Pourcentage d'humidité du sol (0-100)
        None: En cas d'erreur de lecture
    """
    try:
        voltage = chan.voltage
        # Gérer les tensions négatives (problème de connexion ou capteur)
        if voltage < 0:
            voltage = 0
        # Calcul du pourcentage d'humidité
        # Pour ce capteur : tension BASSE = sol HUMIDE, tension HAUTE = sol SEC
        # Formule : inverser car plus la tension est basse, plus le sol est humide
        moisture_percentage = (1 - (voltage / 3.3)) * 100
        # S'assurer que le résultat est entre 0 et 100
        moisture_percentage = max(0, min(100, moisture_percentage))
        return round(moisture_percentage, 2)
    except Exception as e:
        print(f"Erreur lors de la lecture de l'humidité du sol : {e}")
        return None

def check_scheduled_watering():
    """Vérifie si un arrosage programmé doit être déclenché"""
    global scheduled_waterings, last_watering_time
    global _config_cache
    
    # Utiliser le cache si disponible
    if _config_cache:
        scheduled_waterings = _config_cache.get('scheduled_waterings', [])
    else:
        try:
            with open(data_file, 'r') as file:
                config = json.load(file)
            scheduled_waterings = config.get('scheduled_waterings', [])
        except:
            scheduled_waterings = []
    
    if not scheduled_waterings:
        return False
    
    now = datetime.datetime.now()
    current_time = now.strftime("%H:%M")
    current_day = now.strftime("%A").lower()  # jour de la semaine en anglais
    
    for schedule in scheduled_waterings:
        if not schedule.get('enabled', True):
            continue
        
        schedule_time = schedule.get('time', '')
        schedule_days = schedule.get('days', [])
        schedule_duration = schedule.get('duration', 1)  # minutes
        
        # Vérifier si c'est le bon jour
        if current_day not in schedule_days:
            continue
        
        # Vérifier si c'est l'heure (avec une marge de 1 minute)
        schedule_hour, schedule_min = map(int, schedule_time.split(':'))
        current_hour, current_min = map(int, current_time.split(':'))
        
        time_diff = abs((current_hour * 60 + current_min) - (schedule_hour * 60 + schedule_min))
        
        if time_diff <= 1:  # Dans la fenêtre de 1 minute
            # Vérifier qu'on n'a pas déjà arrosé récemment (protection)
            if last_watering_time:
                minutes_since_last = (now - last_watering_time).total_seconds() / 60
                if minutes_since_last < 5:  # Au moins 5 minutes entre arrosages
                    continue
            
            # Déclencher l'arrosage programmé
            is_pump_on = GPIO.input(18) == 0
            if not is_pump_on:
                GPIO.output(18, GPIO.LOW)
                global pump_on_time, watering_duration_minutes
                pump_on_time = datetime.datetime.now()
                watering_duration_minutes = schedule_duration
                last_watering_time = pump_on_time
                print(f"Arrosage programmé déclenché à {current_time} pour {schedule_duration} minutes")
                return True
    
    return False

def monitor_humidity():
    global pump_on_time, watering_duration_minutes, last_watering_time, maintenance_mode, vacation_mode
    global _config_cache, _config_cache_time
    pump_on_time = None  # Réinitialiser pump_on_time
    watering_duration_minutes = None  # Durée d'arrosage prévue en minutes

    while True:
        try:
            # Charger les paramètres depuis le cache
            global _config_cache
            if _config_cache:
                config = _config_cache
            else:
                try:
                    with open(data_file, 'r') as file:
                        config = json.load(file)
                except:
                    time.sleep(5)
                    continue
            
            maintenance_mode = config.get('maintenance_mode', False)
            vacation_mode = config.get('vacation_mode', False)
            
            # Si mode maintenance, ne rien faire
            if maintenance_mode:
                time.sleep(30)  # Attendre plus longtemps en mode maintenance
                continue
            
            soil_moisture = get_soil_moisture()
            
            # Lire température et humidité avec gestion des erreurs
            try:
                air_temperature = dht_device.temperature
                air_humidity = dht_device.humidity
            except RuntimeError:
                air_temperature = None
                air_humidity = None
                print("Erreur lors de la lecture du DHT11")
            
            print(f"Humidité du sol : {soil_moisture}%, Température de l'air : {air_temperature}°C, Humidité de l'air : {air_humidity}%")
            
            if soil_moisture is not None:
                record_soil_moisture(soil_moisture)

            # Vérifier si la pompe doit être arrêtée après la durée prévue
            if pump_on_time is not None and watering_duration_minutes is not None:
                elapsed_minutes = (datetime.datetime.now() - pump_on_time).total_seconds() / 60
                max_duration = watering_duration_minutes * 1.5  # 50% de marge pour détecter les fuites
                
                # Détection de fuite : si la pompe tourne trop longtemps
                if elapsed_minutes > max_duration:
                    print(f"⚠️ ALERTE FUITE : La pompe tourne depuis {elapsed_minutes:.1f} minutes (max prévu: {max_duration:.1f} min)")
                    GPIO.output(18, GPIO.HIGH)  # Arrêt d'urgence
                    pump_off_time = datetime.datetime.now()
                    duration_seconds = (pump_off_time - pump_on_time).total_seconds()
                    print(f"Pompe arrêtée d'urgence à {pump_off_time}")
                    record_arrosage(pump_on_time, duration_seconds)
                    last_watering_time = pump_off_time
                    pump_on_time = None
                    watering_duration_minutes = None
                elif elapsed_minutes >= watering_duration_minutes:
                    # Arrêter la pompe après la durée prévue
                    GPIO.output(18, GPIO.HIGH)
                    pump_off_time = datetime.datetime.now()
                    duration_seconds = (pump_off_time - pump_on_time).total_seconds()
                    print(f"Pompe éteinte à {pump_off_time} (durée prévue atteinte)")
                    print(f"Durée d'arrosage : {duration_seconds} secondes")
                    record_arrosage(pump_on_time, duration_seconds)
                    last_watering_time = pump_off_time
                    pump_on_time = None
                    watering_duration_minutes = None

            # Vérifier les arrosages programmés
            check_scheduled_watering()

            # Charger la configuration avec cache pour optimiser
            now = datetime.datetime.now()
            
            # Vérifier si le cache est valide
            if _config_cache is None or _config_cache_time is None or \
               (now - _config_cache_time).total_seconds() > _config_cache_ttl:
                try:
                    with open(data_file, 'r') as file:
                        config_data = json.load(file)
                    _config_cache = config_data
                    _config_cache_time = now
                except Exception as e:
                    print(f"Erreur lors du chargement de la configuration: {e}")
                    time.sleep(5)
                    continue
            
            config = _config_cache
            scenarios = config['scenarios'][config['current_scenario']]

            matched_scenario = None
            for scenario in scenarios:
                soil_condition = scenario["Humidity of soil (%)"]
                temp_condition = scenario["Air temperature (°C)"]
                air_humidity_condition = scenario["Air humidity (%)"]

                # Vérifier les conditions
                # L'humidité du sol est OBLIGATOIRE (condition critique)
                soil_match = eval_condition(soil_moisture, soil_condition) if soil_moisture is not None else False
                # La température et l'humidité de l'air sont OPTIONNELLES (conditions souhaitables mais non bloquantes)
                temp_match = eval_condition(air_temperature, temp_condition) if air_temperature is not None else True
                humidity_match = eval_condition(air_humidity, air_humidity_condition) if air_humidity is not None else True

                # L'humidité du sol doit correspondre, température et humidité de l'air sont optionnelles
                if soil_match:
                    matched_scenario = scenario
                    break

            # Appliquer l'action du scénario correspondant
            if matched_scenario:
                action = matched_scenario["Action"]
                duration_minutes = matched_scenario["Watering duration (minutes)"]
                
                # Mode vacances : réduire la durée d'arrosage de 50%
                if vacation_mode and duration_minutes > 0:
                    duration_minutes = duration_minutes * 0.5
                    print(f"Mode vacances actif - Durée réduite à {duration_minutes} minutes")
                
                print(f"Scénario correspondant trouvé - Action : {action}, Durée : {duration_minutes} minutes")

                is_pump_on = GPIO.input(18) == 0  # GPIO.LOW = pompe allumée

                if action == "Arroser" or action == "Arroser légèrement":
                    # Vérifier la protection anti-arrosage excessif
                    min_interval = config.get('min_watering_interval', 30)  # minutes
                    can_water = True
                    
                    if last_watering_time:
                        minutes_since_last = (datetime.datetime.now() - last_watering_time).total_seconds() / 60
                        if minutes_since_last < min_interval:
                            can_water = False
                            print(f"Protection anti-arrosage : Dernier arrosage il y a {minutes_since_last:.1f} min (minimum: {min_interval} min)")
                    
                    # Allumer la pompe si elle est éteinte et si la protection le permet
                    if not is_pump_on and can_water:
                        GPIO.output(18, GPIO.LOW)
                        pump_on_time = datetime.datetime.now()
                        watering_duration_minutes = duration_minutes
                        last_watering_time = pump_on_time
                        print(f"Pompe allumée à {pump_on_time} pour {duration_minutes} minutes")
                    # Si la pompe est déjà allumée, NE PAS réinitialiser le timer
                    # Le timer est géré par la vérification en début de boucle (lignes 98-109)
                    # Cela permet à la pompe de s'arrêter après la durée prévue
                
                elif action == "Surveiller, arroser si nécessaire":
                    # Vérifier la protection anti-arrosage excessif
                    min_interval = config.get('min_watering_interval', 30)
                    can_water = True
                    
                    if last_watering_time:
                        minutes_since_last = (datetime.datetime.now() - last_watering_time).total_seconds() / 60
                        if minutes_since_last < min_interval:
                            can_water = False
                    
                    # Arroser légèrement si la pompe est éteinte et si la protection le permet
                    if not is_pump_on and duration_minutes > 0 and can_water:
                        GPIO.output(18, GPIO.LOW)
                        pump_on_time = datetime.datetime.now()
                        watering_duration_minutes = duration_minutes
                        last_watering_time = pump_on_time
                        print(f"Pompe allumée à {pump_on_time} (surveillance) pour {duration_minutes} minutes")
                
                elif action == "Pas d'arrosage":
                    # Éteindre la pompe si elle est allumée
                    if is_pump_on:
                        GPIO.output(18, GPIO.HIGH)
                        if pump_on_time:
                            pump_off_time = datetime.datetime.now()
                            duration_seconds = (pump_off_time - pump_on_time).total_seconds()
                            print(f"Pompe éteinte à {pump_off_time}")
                            print(f"Durée d'arrosage : {duration_seconds} secondes")
                            record_arrosage(pump_on_time, duration_seconds)
                            last_watering_time = pump_off_time
                            pump_on_time = None
                            watering_duration_minutes = None
            else:
                print("Aucun scénario correspondant trouvé")

            record_temp_humidity()
            
        except Exception as e:
            print(f"Erreur dans la boucle de surveillance : {e}")
        
        time.sleep(5)  # Délai entre chaque vérification pour stabiliser les lectures

def eval_condition(value, condition):
    """Évalue si une valeur correspond à une condition donnée"""
    # Gérer les valeurs None
    if value is None:
        return False
    
    if isinstance(condition, str):
        # Nettoyer la condition en enlevant les espaces
        condition = condition.strip()
        
        if '-' in condition:
            # Gérer les plages comme "18-26" ou "30-60"
            parts = condition.split('-')
            if len(parts) == 2:
                try:
                    min_val = float(parts[0].strip())
                    max_val = float(parts[1].strip())
                    return min_val <= value <= max_val
                except ValueError:
                    return False
        elif '>' in condition:
            # Gérer les conditions comme "> 60" ou ">26"
            parts = condition.split('>')
            if len(parts) == 2:
                try:
                    threshold = float(parts[1].strip())
                    return value > threshold
                except ValueError:
                    return False
        elif '<' in condition:
            # Gérer les conditions comme "< 30" ou "<20"
            parts = condition.split('<')
            if len(parts) == 2:
                try:
                    threshold = float(parts[1].strip())
                    return value < threshold
                except ValueError:
                    return False
    return False

def rotate_log_file(filename, max_lines=10000):
    """Rotation des fichiers de logs pour limiter leur taille"""
    try:
        with open(filename, 'r') as file:
            lines = file.readlines()
        
        if len(lines) > max_lines:
            # Garder seulement les dernières lignes
            lines_to_keep = lines[-max_lines:]
            
            # Créer une sauvegarde
            backup_filename = filename.replace('.csv', '_backup.csv')
            with open(backup_filename, 'w') as backup_file:
                backup_file.writelines(lines[:-max_lines])
            
            # Réécrire le fichier avec seulement les dernières lignes
            with open(filename, 'w') as file:
                file.writelines(lines_to_keep)
            
            print(f"Rotation du fichier {filename}: {len(lines)} lignes -> {len(lines_to_keep)} lignes (sauvegarde: {backup_filename})")
    except FileNotFoundError:
        pass  # Fichier n'existe pas encore, c'est normal
    except Exception as e:
        print(f"Erreur lors de la rotation du fichier {filename}: {e}")

def record_arrosage(start_time, duration):
    with open(log_file, "a") as file:
        file.write(f"{start_time}, {duration}\n")
    # Rotation périodique (tous les 1000 enregistrements environ)
    rotate_log_file(log_file, max_lines=10000)

def record_temp_humidity():
    max_retries = 5
    for _ in range(max_retries):
        try:
            temperature = dht_device.temperature
            humidity = dht_device.humidity
            # Ne pas enregistrer si les valeurs sont None
            if temperature is not None and humidity is not None:
                timestamp = datetime.datetime.now().replace(microsecond=0)
                with open(temp_humidity_log_file, "a") as file:
                    file.write(f"{timestamp}, {temperature}, {humidity}\n")
                # Rotation périodique (tous les 5000 enregistrements environ)
                rotate_log_file(temp_humidity_log_file, max_lines=5000)
                break  # Sortir de la boucle si la lecture est réussie
            else:
                print("Valeurs None détectées, nouvelle tentative...")
                time.sleep(2)
        except RuntimeError as e:
            print(f"Erreur lors de l'enregistrement de la température et de l'humidité : {e}")
            time.sleep(2)  # Attendre un peu avant de réessayer
        except Exception as e:
            print(f"Erreur inattendue lors de l'enregistrement : {e}")
            break
    else:
        print("Échec de la lecture du capteur DHT11 après plusieurs tentatives.")

def record_soil_moisture(soil_moisture):
    # Ne pas enregistrer si la valeur est None
    if soil_moisture is None:
        print("Tentative d'enregistrement d'une valeur None pour l'humidité du sol, ignorée")
        return
    
    try:
        timestamp = datetime.datetime.now().replace(microsecond=0)
        with open(soil_moisture_log_file, "a") as file:
            file.write(f"{timestamp}, {soil_moisture}\n")
        # Rotation périodique (tous les 5000 enregistrements environ)
        rotate_log_file(soil_moisture_log_file, max_lines=5000)
        print(f"Enregistrement : {timestamp}, {soil_moisture}%")  # Ajouté pour le débogage
    except Exception as e:
        print(f"Erreur lors de l'enregistrement de l'humidité du sol : {e}")

def format_duration(seconds):
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours}h {minutes}m {seconds}s" if hours > 0 else f"{minutes}m {seconds}s"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data')
def data():
    try:
        temperature = dht_device.temperature
        humidity = dht_device.humidity
        # Vérifier si les valeurs sont None
        if temperature is None:
            temperature = "--"
        if humidity is None:
            humidity = "--"
    except RuntimeError as e:
        print(f"Erreur lors de la lecture du DHT11: {e}")
        temperature = "--"
        humidity = "--"
    except Exception as e:
        print(f"Erreur inattendue lors de la lecture des capteurs: {e}")
        temperature = "--"
        humidity = "--"
    
    soil_moisture = get_soil_moisture()
    if soil_moisture is None:
        soil_moisture = "--"
    
    try:
        pump_status = "Allumée" if GPIO.input(18) == 0 else "Éteinte"
    except Exception as e:
        print(f"Erreur lors de la lecture du statut de la pompe: {e}")
        pump_status = "Inconnu"
    
    return jsonify(
        temperature=temperature,
        air_humidity=humidity,
        pump_status=pump_status,
        soil_humidity=soil_moisture
    )

@app.route('/arrosage_history')
def arrosage_history():
    try:
        with open(log_file, "r") as file:
            lines = file.readlines()
    except FileNotFoundError:
        lines = []  # Si le fichier n'existe pas, utiliser une liste vide.
        try:
            with open(log_file, "w") as file:  # Créer le fichier vide.
                pass
        except Exception:
            pass

    formatted_history = []
    for line in lines:
        line = line.strip()
        if not line:  # Ignorer les lignes vides
            continue
        try:
            parts = line.split(", ")
            if len(parts) >= 2:
                timestamp = parts[0]
                duration_str = parts[1]
                try:
                    duration_seconds = float(duration_str)
                    formatted_history.append([timestamp, format_duration(duration_seconds)])
                except ValueError:
                    print(f"Erreur: durée invalide dans la ligne: {line}")
                    continue
        except Exception as e:
            print(f"Erreur lors du parsing de la ligne d'historique: {line}, erreur: {e}")
            continue
    
    return render_template('history.html', history=formatted_history)

@app.route('/temperature_humidity_history')
def temperature_humidity_history():
    timestamps = []
    temperatures = []
    humidities = []
    soil_timestamps = []
    soil_moistures = []

    try:
        # Lire le fichier de température et humidité
        try:
            with open(temp_humidity_log_file, "r") as file:
                lines = file.readlines()
        except FileNotFoundError:
            lines = []
            # Créer le fichier vide s'il n'existe pas
            try:
                with open(temp_humidity_log_file, "w") as file:
                    pass
            except Exception:
                pass

        # Parser les lignes de température et humidité
        for line in lines:
            line = line.strip()
            if not line:  # Ignorer les lignes vides
                continue
            try:
                parts = line.split(", ")
                if len(parts) >= 3:
                    timestamp = parts[0]
                    temperature_str = parts[1]
                    humidity_str = parts[2]
                    
                    # Vérifier que les valeurs ne sont pas None ou vides
                    if temperature_str and temperature_str.lower() != 'none' and humidity_str and humidity_str.lower() != 'none':
                        temperature = float(temperature_str)
                        humidity = float(humidity_str)
                        timestamps.append(timestamp)
                        temperatures.append(temperature)
                        humidities.append(humidity)
            except (ValueError, IndexError) as e:
                print(f"Erreur lors du parsing de la ligne température/humidité: {line}, erreur: {e}")
                continue

        # Lire le fichier d'humidité du sol
        try:
            with open(soil_moisture_log_file, "r") as soil_file:
                soil_lines = soil_file.readlines()
        except FileNotFoundError:
            soil_lines = []
            # Créer le fichier vide s'il n'existe pas
            try:
                with open(soil_moisture_log_file, "w") as soil_file:
                    pass
            except Exception:
                pass

        # Parser les lignes d'humidité du sol
        for soil_line in soil_lines:
            soil_line = soil_line.strip()
            if not soil_line:  # Ignorer les lignes vides
                continue
            try:
                parts = soil_line.split(", ")
                if len(parts) >= 2:
                    timestamp = parts[0]
                    soil_moisture_str = parts[1]
                    
                    # Vérifier que la valeur n'est pas None ou vide
                    if soil_moisture_str and soil_moisture_str.lower() != 'none':
                        soil_moisture = float(soil_moisture_str)
                        soil_timestamps.append(timestamp)
                        soil_moistures.append(soil_moisture)
            except (ValueError, IndexError) as e:
                print(f"Erreur lors du parsing de la ligne humidité du sol: {soil_line}, erreur: {e}")
                continue

    except Exception as e:
        print(f"Erreur générale dans temperature_humidity_history: {e}")
        import traceback
        traceback.print_exc()
        # Retourner des listes vides en cas d'erreur
        return jsonify(
            timestamps=[],
            temperatures=[],
            humidities=[],
            soil_timestamps=[],
            soil_moistures=[]
        ), 200

    return jsonify(
        timestamps=timestamps,
        temperatures=temperatures,
        humidities=humidities,
        soil_timestamps=soil_timestamps,
        soil_moistures=soil_moistures
    )

@app.route('/configuration')
def configuration():
    return render_template('configuration.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/get_scenarios')
def get_scenarios():
    try:
        with open(data_file, 'r') as file:
            config = json.load(file)
        return jsonify(scenarios=config['scenarios'], current_scenario=config['current_scenario'])
    except Exception as e:
        print(f"Erreur lors de la récupération des scénarios : {e}")
        return str(e), 500

@app.route('/get_scenario_details', methods=['POST'])
def get_scenario_details():
    try:
        plant = request.json['plant']
        with open(data_file, 'r') as file:
            config = json.load(file)
        return jsonify(config['scenarios'][plant])
    except Exception as e:
        print(f"Erreur lors de la récupération des détails du scénario : {e}")
        return str(e), 500

@app.route('/get_settings')
def get_settings():
    """Retourne les paramètres du système"""
    try:
        with open(data_file, 'r') as file:
            config = json.load(file)
        
        settings = {
            'maintenance_mode': config.get('maintenance_mode', False),
            'vacation_mode': config.get('vacation_mode', False),
            'scheduled_waterings': config.get('scheduled_waterings', []),
            'min_watering_interval': config.get('min_watering_interval', 30)  # Minutes minimum entre arrosages
        }
        return jsonify(settings)
    except Exception as e:
        print(f"Erreur lors de la récupération des paramètres: {e}")
        return jsonify({
            'maintenance_mode': False,
            'vacation_mode': False,
            'scheduled_waterings': [],
            'min_watering_interval': 30
        })

@app.route('/update_settings', methods=['POST'])
def update_settings():
    """Met à jour les paramètres du système"""
    try:
        data = request.get_json()
        global _config_cache, _config_cache_time, maintenance_mode, vacation_mode, scheduled_waterings
        
        with open(data_file, 'r') as file:
            config = json.load(file)
        
        # Mettre à jour les paramètres
        if 'maintenance_mode' in data:
            config['maintenance_mode'] = data['maintenance_mode']
            maintenance_mode = data['maintenance_mode']
        
        if 'vacation_mode' in data:
            config['vacation_mode'] = data['vacation_mode']
            vacation_mode = data['vacation_mode']
        
        if 'scheduled_waterings' in data:
            config['scheduled_waterings'] = data['scheduled_waterings']
            scheduled_waterings = data['scheduled_waterings']
        
        if 'min_watering_interval' in data:
            config['min_watering_interval'] = data['min_watering_interval']
        
        with open(data_file, 'w') as file:
            json.dump(config, file, indent=2)
        
        # Invalider le cache pour forcer le rechargement
        _config_cache = config
        _config_cache_time = datetime.datetime.now()
        
        return jsonify({'status': 'success', 'message': 'Paramètres mis à jour avec succès'})
    except Exception as e:
        print(f"Erreur lors de la mise à jour des paramètres: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/alerts')
def alerts():
    """Retourne les alertes actuelles du système"""
    alerts_list = []
    
    try:
        # Vérifier les capteurs
        try:
            temperature = dht_device.temperature
            air_humidity = dht_device.humidity
        except:
            temperature = None
            air_humidity = None
        
        soil_moisture = get_soil_moisture()
        
        # Alerte : Capteurs défaillants
        if temperature is None or air_humidity is None:
            alerts_list.append({
                'level': 'warning',
                'message': 'Capteur DHT11 (température/humidité air) non disponible',
                'icon': 'fa-exclamation-triangle'
            })
        
        if soil_moisture is None:
            alerts_list.append({
                'level': 'warning',
                'message': 'Capteur d\'humidité du sol non disponible',
                'icon': 'fa-exclamation-triangle'
            })
        
        # Alerte : Température critique
        if temperature is not None:
            if temperature < 10:
                alerts_list.append({
                    'level': 'danger',
                    'message': f'Température très basse ({temperature}°C) - Risque pour les plantes',
                    'icon': 'fa-thermometer-empty'
                })
            elif temperature > 35:
                alerts_list.append({
                    'level': 'danger',
                    'message': f'Température très élevée ({temperature}°C) - Risque pour les plantes',
                    'icon': 'fa-thermometer-full'
                })
        
        # Alerte : Humidité du sol critique
        if soil_moisture is not None:
            if soil_moisture < 15:
                alerts_list.append({
                    'level': 'danger',
                    'message': f'Sol très sec ({soil_moisture}%) - Arrosage urgent nécessaire',
                    'icon': 'fa-tint-slash'
                })
            elif soil_moisture > 95:
                alerts_list.append({
                    'level': 'warning',
                    'message': f'Sol très humide ({soil_moisture}%) - Risque de sur-arrosage',
                    'icon': 'fa-tint'
                })
        
        # Alerte : Humidité de l'air
        if air_humidity is not None:
            if air_humidity < 20:
                alerts_list.append({
                    'level': 'warning',
                    'message': f'Air très sec ({air_humidity}%) - Considérer un humidificateur',
                    'icon': 'fa-wind'
                })
        
        # Vérifier la dernière activité
        try:
            with open(log_file, "r") as file:
                lines = file.readlines()
            if lines:
                last_line = lines[-1].strip()
                if last_line:
                    parts = last_line.split(", ")
                    if len(parts) >= 1:
                        last_watering = parse_timestamp(parts[0])
                        if last_watering:
                            hours_since = (datetime.datetime.now() - last_watering).total_seconds() / 3600
                            if hours_since > 48 and soil_moisture is not None and soil_moisture < 30:
                                alerts_list.append({
                                    'level': 'info',
                                    'message': f'Dernier arrosage il y a {int(hours_since)}h - Vérifier si nécessaire',
                                    'icon': 'fa-clock'
                                })
        except:
            pass
            
    except Exception as e:
        print(f"Erreur lors de la vérification des alertes: {e}")
    
    return jsonify({'alerts': alerts_list})

def parse_timestamp(timestamp_str):
    """Parse un timestamp qui peut avoir ou non des microsecondes"""
    try:
        # Essayer d'abord avec microsecondes
        return datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        try:
            # Essayer sans microsecondes
            return datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            # Essayer avec format ISO
            try:
                return datetime.datetime.fromisoformat(timestamp_str.replace(' ', 'T'))
            except:
                return None

@app.route('/trends')
def trends():
    """Retourne les tendances (min, max, moyennes) pour les dernières 24h"""
    trends_data = {
        'temperature': {'min': None, 'max': None, 'avg': None},
        'air_humidity': {'min': None, 'max': None, 'avg': None},
        'soil_moisture': {'min': None, 'max': None, 'avg': None}
    }
    
    try:
        cutoff_time = datetime.datetime.now() - datetime.timedelta(hours=24)
        
        # Tendances température et humidité air
        try:
            with open(temp_humidity_log_file, "r") as file:
                lines = file.readlines()
            
            temps = []
            hums = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    parts = line.split(", ")
                    if len(parts) >= 3:
                        timestamp_str = parts[0]
                        temp_str = parts[1]
                        hum_str = parts[2]
                        
                        if temp_str and temp_str.lower() != 'none' and hum_str and hum_str.lower() != 'none':
                            timestamp = parse_timestamp(timestamp_str)
                            if timestamp and timestamp >= cutoff_time:
                                temps.append(float(temp_str))
                                hums.append(float(hum_str))
                except:
                    continue
            
            if temps:
                trends_data['temperature'] = {
                    'min': round(min(temps), 1),
                    'max': round(max(temps), 1),
                    'avg': round(sum(temps) / len(temps), 1)
                }
            if hums:
                trends_data['air_humidity'] = {
                    'min': round(min(hums), 1),
                    'max': round(max(hums), 1),
                    'avg': round(sum(hums) / len(hums), 1)
                }
        except:
            pass
        
        # Tendances humidité du sol
        try:
            with open(soil_moisture_log_file, "r") as file:
                lines = file.readlines()
            
            moistures = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    parts = line.split(", ")
                    if len(parts) >= 2:
                        timestamp_str = parts[0]
                        moisture_str = parts[1]
                        
                        if moisture_str and moisture_str.lower() != 'none':
                            timestamp = parse_timestamp(timestamp_str)
                            if timestamp and timestamp >= cutoff_time:
                                moistures.append(float(moisture_str))
                except:
                    continue
            
            if moistures:
                trends_data['soil_moisture'] = {
                    'min': round(min(moistures), 1),
                    'max': round(max(moistures), 1),
                    'avg': round(sum(moistures) / len(moistures), 1)
                }
        except:
            pass
            
    except Exception as e:
        print(f"Erreur lors du calcul des tendances: {e}")
    
    return jsonify(trends_data)

@app.route('/statistics')
def statistics():
    """Retourne les statistiques du système"""
    stats = {
        'today_waterings': 0,
        'total_waterings': 0,
        'total_water_volume': 0.0,
        'avg_temperature': None,
        'avg_air_humidity': None,
        'avg_soil_moisture': None,
        'last_watering': None,
        'pump_total_time': 0.0
    }
    
    try:
        # Statistiques d'arrosage
        today = datetime.datetime.now().date()
        with open(log_file, "r") as file:
            lines = file.readlines()
        
        total_duration = 0.0
        last_watering_timestamp = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                parts = line.split(", ")
                if len(parts) >= 2:
                    timestamp_str = parts[0]
                    duration = float(parts[1])
                    total_duration += duration
                    stats['total_waterings'] += 1
                    
                    # Vérifier si c'est aujourd'hui
                    timestamp = parse_timestamp(timestamp_str)
                    if timestamp:
                        if timestamp.date() == today:
                            stats['today_waterings'] += 1
                        
                        # Garder le dernier arrosage
                        if last_watering_timestamp is None or timestamp > last_watering_timestamp:
                            last_watering_timestamp = timestamp
                            stats['last_watering'] = timestamp_str
            except Exception as e:
                print(f"Erreur lors du parsing de la ligne d'arrosage: {line}, erreur: {e}")
                continue
        
        stats['pump_total_time'] = round(total_duration / 60, 2)  # En minutes
        
        # Calculer le volume d'eau (approximatif : 0.3 L/min)
        stats['total_water_volume'] = round(total_duration * 0.3 / 60, 2)
        
        # Statistiques des capteurs (dernières 24h)
        try:
            with open(temp_humidity_log_file, "r") as file:
                lines = file.readlines()
            
            temps = []
            hums = []
            cutoff_time = datetime.datetime.now() - datetime.timedelta(hours=24)
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    parts = line.split(", ")
                    if len(parts) >= 3:
                        timestamp_str = parts[0]
                        temp = float(parts[1])
                        hum = float(parts[2])
                        timestamp = parse_timestamp(timestamp_str)
                        if timestamp and timestamp >= cutoff_time:
                            temps.append(temp)
                            hums.append(hum)
                except:
                    continue
            
            if temps:
                stats['avg_temperature'] = round(sum(temps) / len(temps), 1)
            if hums:
                stats['avg_air_humidity'] = round(sum(hums) / len(hums), 1)
        except:
            pass
        
        # Statistiques humidité du sol (dernières 24h)
        try:
            with open(soil_moisture_log_file, "r") as file:
                lines = file.readlines()
            
            moistures = []
            cutoff_time = datetime.datetime.now() - datetime.timedelta(hours=24)
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    parts = line.split(", ")
                    if len(parts) >= 2:
                        timestamp_str = parts[0]
                        moisture = float(parts[1])
                        timestamp = parse_timestamp(timestamp_str)
                        if timestamp and timestamp >= cutoff_time:
                            moistures.append(moisture)
                except:
                    continue
            
            if moistures:
                stats['avg_soil_moisture'] = round(sum(moistures) / len(moistures), 1)
        except:
            pass
            
    except Exception as e:
        print(f"Erreur lors du calcul des statistiques: {e}")
    
    return jsonify(stats)

@app.route('/manual_pump_control', methods=['POST'])
def manual_pump_control():
    """Contrôle manuel de la pompe"""
    global pump_on_time, watering_duration_minutes
    
    try:
        data = request.get_json()
        action = data.get('action')  # 'start' ou 'stop'
        duration = data.get('duration', 1)  # Durée en minutes (par défaut 1 minute)
        
        if action == 'start':
            # Démarrer la pompe
            if GPIO.input(18) == 1:  # Si la pompe est éteinte
                GPIO.output(18, GPIO.LOW)  # Allumer la pompe
                pump_on_time = datetime.datetime.now()
                watering_duration_minutes = float(duration)
                return jsonify({'status': 'success', 'message': f'Pompe démarrée pour {duration} minute(s)'})
            else:
                return jsonify({'status': 'error', 'message': 'La pompe est déjà allumée'}), 400
        
        elif action == 'stop':
            # Arrêter la pompe
            GPIO.output(18, GPIO.HIGH)  # Éteindre la pompe
            if pump_on_time:
                pump_off_time = datetime.datetime.now()
                duration_seconds = (pump_off_time - pump_on_time).total_seconds()
                record_arrosage(pump_on_time, duration_seconds)
                pump_on_time = None
                watering_duration_minutes = None
            return jsonify({'status': 'success', 'message': 'Pompe arrêtée'})
        
        else:
            return jsonify({'status': 'error', 'message': 'Action invalide'}), 400
            
    except Exception as e:
        print(f"Erreur lors du contrôle manuel de la pompe: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/export_data', methods=['GET'])
def export_data():
    """Exporte les données en CSV"""
    try:
        data_type = request.args.get('type', 'all')  # 'all', 'watering', 'sensors', 'soil'
        format_type = request.args.get('format', 'csv')  # 'csv' ou 'json'
        
        from flask import Response
        
        if data_type == 'watering' or data_type == 'all':
            # Exporter l'historique d'arrosage
            try:
                with open(log_file, "r") as file:
                    watering_data = file.read()
            except:
                watering_data = ""
        
        if data_type == 'sensors' or data_type == 'all':
            # Exporter les données de capteurs
            try:
                with open(temp_humidity_log_file, "r") as file:
                    sensor_data = file.read()
            except:
                sensor_data = ""
        
        if data_type == 'soil' or data_type == 'all':
            # Exporter les données d'humidité du sol
            try:
                with open(soil_moisture_log_file, "r") as file:
                    soil_data = file.read()
            except:
                soil_data = ""
        
        if format_type == 'json':
            result = {
                'watering': watering_data.split('\n') if data_type == 'watering' or data_type == 'all' else [],
                'sensors': sensor_data.split('\n') if data_type == 'sensors' or data_type == 'all' else [],
                'soil': soil_data.split('\n') if data_type == 'soil' or data_type == 'all' else []
            }
            return jsonify(result)
        else:
            # CSV
            csv_content = ""
            if data_type == 'all':
                csv_content = "=== ARROSAGE ===\nTimestamp, Durée (s)\n" + watering_data
                csv_content += "\n\n=== CAPTEURS ===\nTimestamp, Température (°C), Humidité (%)\n" + sensor_data
                csv_content += "\n\n=== HUMIDITÉ SOL ===\nTimestamp, Humidité (%)\n" + soil_data
            elif data_type == 'watering':
                csv_content = "Timestamp, Durée (s)\n" + watering_data
            elif data_type == 'sensors':
                csv_content = "Timestamp, Température (°C), Humidité (%)\n" + sensor_data
            elif data_type == 'soil':
                csv_content = "Timestamp, Humidité (%)\n" + soil_data
            
            return Response(
                csv_content,
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename=homegarden_export_{data_type}_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
            )
            
    except Exception as e:
        print(f"Erreur lors de l'export: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/set_scenario', methods=['POST'])
def set_scenario():
    try:
        data = request.json
        plant = data['plant']
        with open(data_file, 'r') as file:
            config = json.load(file)
        config['current_scenario'] = plant
        with open(data_file, 'w') as file:
            json.dump(config, file)
        print(f"Scénario mis à jour : {plant}")
        return '', 204
    except Exception as e:
        print(f"Erreur lors de la mise à jour du scénario : {e}")
        return str(e), 500

@app.route('/nodes')
def nodes():
    """Page de gestion des nœuds ESP32"""
    return render_template('nodes.html')

# ============================================================================
# API POUR LES NŒUDS ESP32
# ============================================================================

@app.route('/api/nodes/register', methods=['POST'])
def api_register_node():
    """Enregistre ou met à jour un nœud ESP32"""
    try:
        data = request.get_json()
        node_id = data.get('node_id')
        if not node_id:
            return jsonify({'status': 'error', 'message': 'node_id requis'}), 400
        
        # Récupérer l'adresse IP du client
        node_info = {
            'name': data.get('name', f'Node {node_id}'),
            'location': data.get('location', 'Non spécifié'),
            'ip_address': request.remote_addr,
            'battery_level': data.get('battery_level'),
            'solar_charging': data.get('solar_charging', False),
            'firmware_version': data.get('firmware_version', '1.0')
        }
        
        node = register_node(node_id, node_info)
        print(f"Nœud enregistré/mis à jour : {node_id} ({node_info['name']})")
        return jsonify({'status': 'success', 'node': node})
    except Exception as e:
        print(f"Erreur lors de l'enregistrement du nœud : {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/nodes/<node_id>/data', methods=['POST'])
def api_node_data(node_id):
    """Reçoit les données d'un nœud ESP32"""
    try:
        data = request.get_json()
        
        # Enregistrer les données
        sensor_data = {
            'temperature': data.get('temperature'),
            'air_humidity': data.get('air_humidity'),
            'soil_moisture': data.get('soil_moisture'),
            'watering_event': data.get('watering_event', False),
            'watering_duration': data.get('watering_duration', 0),
            'pump_status': data.get('pump_status', 'off')
        }
        
        record_node_data(node_id, sensor_data)
        
        # Mettre à jour le statut du nœud
        node_info = {
            'battery_level': data.get('battery_level'),
            'solar_charging': data.get('solar_charging', False),
            'ip_address': request.remote_addr
        }
        register_node(node_id, node_info)
        
        # Charger la configuration pour déterminer l'action
        try:
            with open(data_file, 'r') as file:
                config = json.load(file)
        except:
            config = {}
        
        # Retourner la commande pour le nœud (si nécessaire)
        response = {
            'status': 'success',
            'action': 'none',  # 'water', 'stop', 'none'
            'duration': 0,
            'maintenance_mode': config.get('maintenance_mode', False),
            'vacation_mode': config.get('vacation_mode', False)
        }
        
        # Logique de décision (simplifiée - peut être étendue)
        if not config.get('maintenance_mode', False):
            scenarios = config.get('scenarios', {}).get(config.get('current_scenario', 'Monstera deliciosa'), [])
            soil_moisture = sensor_data.get('soil_moisture')
            
            if soil_moisture is not None:
                for scenario in scenarios:
                    soil_condition = scenario.get("Humidity of soil (%)", "")
                    if eval_condition(soil_moisture, soil_condition):
                        action = scenario.get("Action", "Pas d'arrosage")
                        if action in ["Arroser", "Arroser légèrement"]:
                            response['action'] = 'water'
                            duration = scenario.get("Watering duration (minutes)", 1)
                            if config.get('vacation_mode', False):
                                duration = duration * 0.5
                            response['duration'] = duration
                        break
        
        print(f"Données reçues du nœud {node_id}: {sensor_data}")
        return jsonify(response)
    except Exception as e:
        print(f"Erreur lors de la réception des données du nœud {node_id}: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/nodes', methods=['GET'])
def api_get_nodes():
    """Récupère la liste de tous les nœuds"""
    try:
        nodes = get_all_nodes()
        return jsonify({'status': 'success', 'nodes': nodes})
    except Exception as e:
        print(f"Erreur lors de la récupération des nœuds : {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/nodes/<node_id>', methods=['GET'])
def api_get_node(node_id):
    """Récupère les informations d'un nœud spécifique"""
    try:
        node = get_node(node_id)
        if node:
            # Ajouter l'historique récent
            history = get_node_history(node_id, hours=24)
            node['history'] = history
            return jsonify({'status': 'success', 'node': node})
        else:
            return jsonify({'status': 'error', 'message': 'Nœud non trouvé'}), 404
    except Exception as e:
        print(f"Erreur lors de la récupération du nœud {node_id}: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/nodes/<node_id>/control', methods=['POST'])
def api_control_node(node_id):
    """Contrôle manuel d'un nœud (démarrer/arrêter la pompe)"""
    try:
        data = request.get_json()
        action = data.get('action')  # 'start', 'stop'
        duration = data.get('duration', 1)  # minutes
        
        # Cette commande sera envoyée au nœud lors de sa prochaine requête
        # Pour l'instant, on retourne la commande
        # Dans une version avancée, on pourrait utiliser WebSocket ou MQTT
        
        return jsonify({
            'status': 'success',
            'command': {
                'action': action,
                'duration': duration
            }
        })
    except Exception as e:
        print(f"Erreur lors du contrôle du nœud {node_id}: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    # Vérifier si le fichier log existe au démarrage, sinon le créer.
    if not os.path.exists(log_file):
        with open(log_file, "w") as file:
            pass  # Créer simplement un fichier vide.

    if not os.path.exists(temp_humidity_log_file):
        with open(temp_humidity_log_file, "w") as file:
            pass  # Créer simplement un fichier vide.

    if not os.path.exists(soil_moisture_log_file):
        with open(soil_moisture_log_file, "w") as file:
            pass  # Créer simplement un fichier vide.

    if not os.path.exists(data_file):
        # Initialiser le fichier data.json avec les scénarios
        initial_config = {
            "scenarios": {
                "Monstera deliciosa": [
                    {
                        "Humidity of soil (%)": "> 55",
                        "Air temperature (°C)": "18-26",
                        "Air humidity (%)": "40-60",
                        "Action": "Pas d'arrosage",
                        "Watering duration (minutes)": 0,
                        "Total water volume (L)": 0
                    },
                    {
                        "Humidity of soil (%)": "< 35",
                        "Air temperature (°C)": "18-26",
                        "Air humidity (%)": "40-60",
                        "Action": "Arroser",
                        "Watering duration (minutes)": 1.5,
                        "Total water volume (L)": 0.45
                    },
                    {
                        "Humidity of soil (%)": "35-55",
                        "Air temperature (°C)": "18-26",
                        "Air humidity (%)": "40-60",
                        "Action": "Arroser légèrement",
                        "Watering duration (minutes)": 0.5,
                        "Total water volume (L)": 0.15
                    }
                ],
                "Ficus benjamina": [
                    {
                        "Humidity of soil (%)": "> 50",
                        "Air temperature (°C)": "16-24",
                        "Air humidity (%)": "40-60",
                        "Action": "Pas d'arrosage",
                        "Watering duration (minutes)": 0,
                        "Total water volume (L)": 0
                    },
                    {
                        "Humidity of soil (%)": "< 30",
                        "Air temperature (°C)": "16-24",
                        "Air humidity (%)": "40-60",
                        "Action": "Arroser",
                        "Watering duration (minutes)": 1,
                        "Total water volume (L)": 0.30
                    },
                    {
                        "Humidity of soil (%)": "30-50",
                        "Air temperature (°C)": "16-24",
                        "Air humidity (%)": "40-60",
                        "Action": "Arroser légèrement",
                        "Watering duration (minutes)": 0.5,
                        "Total water volume (L)": 0.15
                    }
                ],
                "Epipremnum aureum": [
                    {
                        "Humidity of soil (%)": "> 50",
                        "Air temperature (°C)": "15-30",
                        "Air humidity (%)": "40-60",
                        "Action": "Pas d'arrosage",
                        "Watering duration (minutes)": 0,
                        "Total water volume (L)": 0
                    },
                    {
                        "Humidity of soil (%)": "< 25",
                        "Air temperature (°C)": "15-30",
                        "Air humidity (%)": "40-60",
                        "Action": "Arroser",
                        "Watering duration (minutes)": 1,
                        "Total water volume (L)": 0.30
                    },
                    {
                        "Humidity of soil (%)": "25-50",
                        "Air temperature (°C)": "15-30",
                        "Air humidity (%)": "40-60",
                        "Action": "Arroser légèrement",
                        "Watering duration (minutes)": 0.5,
                        "Total water volume (L)": 0.15
                    }
                ],
                "Dracaena marginata": [
                    {
                        "Humidity of soil (%)": "> 55",
                        "Air temperature (°C)": "18-24",
                        "Air humidity (%)": "40-60",
                        "Action": "Pas d'arrosage",
                        "Watering duration (minutes)": 0,
                        "Total water volume (L)": 0
                    },
                    {
                        "Humidity of soil (%)": "< 30",
                        "Air temperature (°C)": "18-24",
                        "Air humidity (%)": "40-60",
                        "Action": "Arroser",
                        "Watering duration (minutes)": 1,
                        "Total water volume (L)": 0.30
                    },
                    {
                        "Humidity of soil (%)": "30-55",
                        "Air temperature (°C)": "18-24",
                        "Air humidity (%)": "40-60",
                        "Action": "Arroser légèrement",
                        "Watering duration (minutes)": 0.5,
                        "Total water volume (L)": 0.15
                    }
                ],
                "Sansevieria trifasciata": [
                    {
                        "Humidity of soil (%)": "> 40",
                        "Air temperature (°C)": "15-24",
                        "Air humidity (%)": "40-60",
                        "Action": "Pas d'arrosage",
                        "Watering duration (minutes)": 0,
                        "Total water volume (L)": 0
                    },
                    {
                        "Humidity of soil (%)": "< 20",
                        "Air temperature (°C)": "15-24",
                        "Air humidity (%)": "40-60",
                        "Action": "Arroser",
                        "Watering duration (minutes)": 0.5,
                        "Total water volume (L)": 0.15
                    },
                    {
                        "Humidity of soil (%)": "20-40",
                        "Air temperature (°C)": "15-24",
                        "Air humidity (%)": "40-60",
                        "Action": "Arroser légèrement",
                        "Watering duration (minutes)": 0.25,
                        "Total water volume (L)": 0.075
                    }
                ],
                "Spathiphyllum spp.": [
                    {
                        "Humidity of soil (%)": "> 60",
                        "Air temperature (°C)": "18-26",
                        "Air humidity (%)": "40-60",
                        "Action": "Pas d'arrosage",
                        "Watering duration (minutes)": 0,
                        "Total water volume (L)": 0
                    },
                    {
                        "Humidity of soil (%)": "< 35",
                        "Air temperature (°C)": "18-26",
                        "Air humidity (%)": "40-60",
                        "Action": "Arroser",
                        "Watering duration (minutes)": 1.5,
                        "Total water volume (L)": 0.45
                    },
                    {
                        "Humidity of soil (%)": "35-60",
                        "Air temperature (°C)": "18-26",
                        "Air humidity (%)": "40-60",
                        "Action": "Arroser légèrement",
                        "Watering duration (minutes)": 0.75,
                        "Total water volume (L)": 0.22
                    }
                ],
                "Chlorophytum comosum": [
                    {
                        "Humidity of soil (%)": "> 55",
                        "Air temperature (°C)": "18-24",
                        "Air humidity (%)": "40-60",
                        "Action": "Pas d'arrosage",
                        "Watering duration (minutes)": 0,
                        "Total water volume (L)": 0
                    },
                    {
                        "Humidity of soil (%)": "< 30",
                        "Air temperature (°C)": "18-24",
                        "Air humidity (%)": "40-60",
                        "Action": "Arroser",
                        "Watering duration (minutes)": 1,
                        "Total water volume (L)": 0.30
                    },
                    {
                        "Humidity of soil (%)": "30-55",
                        "Air temperature (°C)": "18-24",
                        "Air humidity (%)": "40-60",
                        "Action": "Arroser légèrement",
                        "Watering duration (minutes)": 0.5,
                        "Total water volume (L)": 0.15
                    }
                ],
                "Zamioculcas zamiifolia": [
                    {
                        "Humidity of soil (%)": "> 35",
                        "Air temperature (°C)": "15-24",
                        "Air humidity (%)": "40-60",
                        "Action": "Pas d'arrosage",
                        "Watering duration (minutes)": 0,
                        "Total water volume (L)": 0
                    },
                    {
                        "Humidity of soil (%)": "< 15",
                        "Air temperature (°C)": "15-24",
                        "Air humidity (%)": "40-60",
                        "Action": "Arroser",
                        "Watering duration (minutes)": 0.5,
                        "Total water volume (L)": 0.15
                    },
                    {
                        "Humidity of soil (%)": "15-35",
                        "Air temperature (°C)": "15-24",
                        "Air humidity (%)": "40-60",
                        "Action": "Arroser légèrement",
                        "Watering duration (minutes)": 0.25,
                        "Total water volume (L)": 0.075
                    }
                ],
                "Aloe vera": [
                    {
                        "Humidity of soil (%)": "> 40",
                        "Air temperature (°C)": "15-26",
                        "Air humidity (%)": "40-60",
                        "Action": "Pas d'arrosage",
                        "Watering duration (minutes)": 0,
                        "Total water volume (L)": 0
                    },
                    {
                        "Humidity of soil (%)": "< 15",
                        "Air temperature (°C)": "15-26",
                        "Air humidity (%)": "40-60",
                        "Action": "Arroser",
                        "Watering duration (minutes)": 0.5,
                        "Total water volume (L)": 0.15
                    },
                    {
                        "Humidity of soil (%)": "15-40",
                        "Air temperature (°C)": "15-26",
                        "Air humidity (%)": "40-60",
                        "Action": "Arroser légèrement",
                        "Watering duration (minutes)": 0.25,
                        "Total water volume (L)": 0.075
                    }
                ]
            },
            "current_scenario": "Monstera deliciosa"
        }
        with open(data_file, 'w') as file:
            json.dump(initial_config, file)

    # Initialiser les paramètres dans data.json s'ils n'existent pas
    try:
        with open(data_file, 'r') as file:
            config = json.load(file)
        
        if 'maintenance_mode' not in config:
            config['maintenance_mode'] = False
        if 'vacation_mode' not in config:
            config['vacation_mode'] = False
        if 'scheduled_waterings' not in config:
            config['scheduled_waterings'] = []
        if 'min_watering_interval' not in config:
            config['min_watering_interval'] = 30  # minutes
        
        with open(data_file, 'w') as file:
            json.dump(config, file, indent=2)
        
        # Initialiser les variables globales
        maintenance_mode = config.get('maintenance_mode', False)
        vacation_mode = config.get('vacation_mode', False)
        scheduled_waterings = config.get('scheduled_waterings', [])
    except Exception as e:
        print(f"Erreur lors de l'initialisation des paramètres: {e}")

    # Initialiser l'état de la pompe (la pompe doit être éteinte par défaut)
    GPIO.output(18, GPIO.HIGH)

    # Démarrer le thread de surveillance
    thread = threading.Thread(target=monitor_humidity)
    thread.daemon = True
    thread.start()
    
    try:
        app.run(host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        GPIO.cleanup()
