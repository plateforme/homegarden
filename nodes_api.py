"""
API pour la gestion des nœuds ESP32
Ce module gère la communication avec les nœuds ESP32 distants
"""
import json
import os
import datetime
from threading import Lock

# Fichier de stockage des nœuds
NODES_FILE = "nodes.json"
NODES_LOCK = Lock()

def load_nodes():
    """Charge la configuration des nœuds depuis le fichier"""
    if os.path.exists(NODES_FILE):
        try:
            with open(NODES_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_nodes(nodes_data):
    """Sauvegarde la configuration des nœuds"""
    with NODES_LOCK:
        with open(NODES_FILE, 'w') as f:
            json.dump(nodes_data, f, indent=2)

def register_node(node_id, node_info):
    """Enregistre ou met à jour un nœud"""
    nodes = load_nodes()
    if node_id not in nodes:
        nodes[node_id] = {
            'id': node_id,
            'name': node_info.get('name', f'Node {node_id}'),
            'location': node_info.get('location', 'Non spécifié'),
            'registered_at': datetime.datetime.now().isoformat(),
            'last_seen': None,
            'status': 'offline',
            'battery_level': None,
            'solar_charging': False
        }
    
    # Mise à jour des informations
    nodes[node_id].update({
        'last_seen': datetime.datetime.now().isoformat(),
        'status': 'online',
        'battery_level': node_info.get('battery_level'),
        'solar_charging': node_info.get('solar_charging', False),
        'ip_address': node_info.get('ip_address'),
        'firmware_version': node_info.get('firmware_version', '1.0')
    })
    
    save_nodes(nodes)
    return nodes[node_id]

def get_node(node_id):
    """Récupère les informations d'un nœud"""
    nodes = load_nodes()
    return nodes.get(node_id)

def get_all_nodes():
    """Récupère tous les nœuds"""
    nodes = load_nodes()
    # Marquer les nœuds offline s'ils n'ont pas été vus depuis plus de 5 minutes
    now = datetime.datetime.now()
    for node_id, node in nodes.items():
        if node.get('last_seen'):
            last_seen = datetime.datetime.fromisoformat(node['last_seen'])
            if (now - last_seen).total_seconds() > 300:  # 5 minutes
                node['status'] = 'offline'
    return nodes

def record_node_data(node_id, sensor_data):
    """Enregistre les données d'un nœud dans les fichiers de log"""
    timestamp = datetime.datetime.now().replace(microsecond=0)
    
    # Fichiers de log par nœud
    node_log_dir = "nodes_data"
    if not os.path.exists(node_log_dir):
        os.makedirs(node_log_dir)
    
    # Log température/humidité
    if sensor_data.get('temperature') is not None or sensor_data.get('air_humidity') is not None:
        temp_hum_file = os.path.join(node_log_dir, f"{node_id}_temp_humidity.csv")
        with open(temp_hum_file, "a") as f:
            f.write(f"{timestamp}, {sensor_data.get('temperature', '--')}, {sensor_data.get('air_humidity', '--')}\n")
    
    # Log humidité du sol
    if sensor_data.get('soil_moisture') is not None:
        soil_file = os.path.join(node_log_dir, f"{node_id}_soil_moisture.csv")
        with open(soil_file, "a") as f:
            f.write(f"{timestamp}, {sensor_data.get('soil_moisture', '--')}\n")
    
    # Log arrosage
    if sensor_data.get('watering_event'):
        watering_file = os.path.join(node_log_dir, f"{node_id}_watering.csv")
        with open(watering_file, "a") as f:
            f.write(f"{timestamp}, {sensor_data.get('watering_duration', 0)}\n")

def get_node_history(node_id, hours=24):
    """Récupère l'historique d'un nœud"""
    node_log_dir = "nodes_data"
    cutoff_time = datetime.datetime.now() - datetime.timedelta(hours=hours)
    
    history = {
        'timestamps': [],
        'temperatures': [],
        'humidities': [],
        'soil_moistures': [],
        'waterings': []
    }
    
    # Lire température/humidité
    temp_hum_file = os.path.join(node_log_dir, f"{node_id}_temp_humidity.csv")
    if os.path.exists(temp_hum_file):
        with open(temp_hum_file, "r") as f:
            for line in f:
                parts = line.strip().split(", ")
                if len(parts) >= 3:
                    try:
                        ts = datetime.datetime.strptime(parts[0], "%Y-%m-%d %H:%M:%S")
                        if ts >= cutoff_time:
                            history['timestamps'].append(parts[0])
                            temp_val = parts[1] if parts[1] != '--' else None
                            hum_val = parts[2] if parts[2] != '--' else None
                            history['temperatures'].append(float(temp_val) if temp_val else None)
                            history['humidities'].append(float(hum_val) if hum_val else None)
                    except:
                        continue
    
    # Lire humidité du sol
    soil_file = os.path.join(node_log_dir, f"{node_id}_soil_moisture.csv")
    if os.path.exists(soil_file):
        with open(soil_file, "r") as f:
            for line in f:
                parts = line.strip().split(", ")
                if len(parts) >= 2:
                    try:
                        ts = datetime.datetime.strptime(parts[0], "%Y-%m-%d %H:%M:%S")
                        if ts >= cutoff_time:
                            moisture_val = parts[1] if parts[1] != '--' else None
                            history['soil_moistures'].append({
                                'timestamp': parts[0],
                                'moisture': float(moisture_val) if moisture_val else None
                            })
                    except:
                        continue
    
    return history

