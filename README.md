# 🌱 HomeGarden - Système d'Arrosage Automatique Intelligent

**English version below** 👇

---

## 🇫🇷 Français

### 🎯 Vue d'ensemble

HomeGarden est un système d'arrosage automatique intelligent pour plantes d'intérieur et jardins. Il supporte une architecture **multi-nœuds** avec des ESP32 pour surveiller et contrôler plusieurs zones indépendamment.

### ✨ Fonctionnalités principales

- ✅ **Surveillance automatique** de l'humidité du sol, température et humidité de l'air
- ✅ **Contrôle intelligent** de la pompe d'arrosage avec scénarios personnalisables par type de plante
- ✅ **Architecture multi-nœuds** : 1 hub central (Raspberry Pi) + jusqu'à 10+ nœuds ESP32
- ✅ **Interface web complète** avec graphiques en temps réel et historique
- ✅ **API REST** pour intégration et contrôle à distance
- ✅ **Planification d'arrosages** avec horaires personnalisables
- ✅ **Modes avancés** : Maintenance, Vacances avec réduction automatique
- ✅ **Alimentation solaire** supportée pour les nœuds ESP32
- ✅ **Économie d'énergie** avec mode Deep Sleep sur ESP32

### 🏗️ Architecture Multi-Nœuds

```
┌─────────────────────────────────────────────────────────┐
│              Raspberry Pi (Hub Central)                  │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Flask Web Server (Port 5000)                   │   │
│  │  - Interface Web                                │   │
│  │  - API REST (/api/nodes/*)                     │   │
│  │  - Base de données (JSON + CSV)                │   │
│  │  - Logique de décision centralisée             │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Capteurs locaux (optionnel)                    │   │
│  │  - DHT11, ADS1115, Pompe GPIO18                │   │
│  └──────────────────────────────────────────────────┘   │
└───────────────────────┬─────────────────────────────────┘
                        │
            ┌───────────┴───────────┐
            │     WiFi / HTTP       │
            │                       │
    ┌───────┴────────┐    ┌──────────┴────────┐
    │               │    │                   │
┌───▼──────┐  ┌─────▼─────┐  ┌─────▼──────┐
│ ESP32 #1 │  │ ESP32 #2 │  │ ESP32 #3   │
│          │  │          │  │            │
│ DHT11    │  │ DHT11    │  │ DHT11      │
│ Sol      │  │ Sol      │  │ Sol        │
│ Pompe    │  │ Pompe    │  │ Pompe      │
│ Batterie │  │ Batterie │  │ Batterie   │
│ Solaire  │  │ Solaire  │  │ Solaire    │
└──────────┘  └──────────┘  └────────────┘
```

### 🚀 Démarrage Rapide

#### Installation des dépendances

```bash
cd /home/gregory/homegarden
pip3 install -r requirements.txt
```

#### Lancement du système

```bash
# Méthode recommandée (menu interactif)
./start.sh

# Ou directement
python3 app.py

# Ou en arrière-plan
nohup python3 app.py > app.log 2>&1 &
```

#### Scripts utiles

```bash
./start.sh    # Démarrer le système (menu interactif)
./stop.sh     # Arrêter le système
./status.sh   # Vérifier le statut du système
```

#### Accès à l'interface web

Une fois le système démarré, accédez à :
```
http://votre_adresse_ip:5000
```

### 🔧 Matériel Requis

#### Hub Central (Raspberry Pi)
- Raspberry Pi (modèle 3 ou supérieur)
- Capteur d'humidité du sol (via ADS1115)
- Capteur DHT11 (température/humidité air)
- Pompe d'arrosage avec relais (GPIO 18)
- Connexions I2C pour ADS1115

#### Nœuds ESP32 (optionnel, pour architecture multi-nœuds)
- ESP32 Dev Module
- Capteur DHT11
- Capteur d'humidité du sol (analogique)
- Relais pour pompe
- Module de charge solaire (optionnel)
- Batterie LiPo 2000-5000 mAh (optionnel)

### 📡 API Multi-Nœuds

Le système expose une API REST complète pour la gestion des nœuds ESP32 :

- `POST /api/nodes/register` - Enregistrement d'un nœud
- `POST /api/nodes/{node_id}/data` - Réception des données d'un nœud
- `GET /api/nodes` - Liste de tous les nœuds
- `GET /api/nodes/{node_id}` - Informations d'un nœud spécifique
- `POST /api/nodes/{node_id}/control` - Contrôle manuel (pompe)

Voir [ARCHITECTURE_MULTI_NODES.md](ARCHITECTURE_MULTI_NODES.md) pour plus de détails.

### ⚙️ Configuration

#### Configuration via interface web
- Accédez à `http://IP:5000/configuration`
- Modifiez les scénarios, seuils, modes et planifications

#### Configuration via fichiers
- `config.json` : Configuration générale
- `data.json` : Scénarios, modes, planification
- `nodes.json` : Registre des nœuds ESP32

### 📝 Logs et Données

Les données sont enregistrées dans :
- `arrosage_log.csv` : Historique des arrosages
- `temp_humidity_log.csv` : Température et humidité de l'air
- `soil_moisture_log.csv` : Humidité du sol
- `nodes_data/{node_id}_*.csv` : Données par nœud ESP32
- `app.log` : Logs du système

### 📖 Documentation Complète

- **[GUIDE_DEMARRAGE.md](GUIDE_DEMARRAGE.md)** - Guide complet de démarrage et configuration
- **[ARCHITECTURE_MULTI_NODES.md](ARCHITECTURE_MULTI_NODES.md)** - Architecture détaillée multi-nœuds
- **[GUIDE_MULTI_NODES.md](GUIDE_MULTI_NODES.md)** - Guide de démarrage multi-nœuds
- **[FONCTIONNALITES.md](FONCTIONNALITES.md)** - Liste complète des fonctionnalités
- **[esp32_node/README.md](esp32_node/README.md)** - Documentation ESP32

### 🆘 Dépannage

Consultez le **[GUIDE_DEMARRAGE.md](GUIDE_DEMARRAGE.md)** pour :
- Instructions détaillées
- Méthodes de démarrage
- Configuration
- Dépannage
- Démarrage automatique au boot

---

## 🇬🇧 English

### 🎯 Overview

HomeGarden is an intelligent automatic watering system for indoor plants and gardens. It supports a **multi-node architecture** with ESP32 devices to monitor and control multiple zones independently.

### ✨ Key Features

- ✅ **Automatic monitoring** of soil moisture, temperature, and air humidity
- ✅ **Intelligent control** of watering pump with customizable scenarios per plant type
- ✅ **Multi-node architecture**: 1 central hub (Raspberry Pi) + up to 10+ ESP32 nodes
- ✅ **Complete web interface** with real-time graphs and history
- ✅ **REST API** for integration and remote control
- ✅ **Scheduled watering** with customizable times
- ✅ **Advanced modes**: Maintenance, Vacation with automatic reduction
- ✅ **Solar power** support for ESP32 nodes
- ✅ **Energy saving** with Deep Sleep mode on ESP32

### 🏗️ Multi-Node Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Raspberry Pi (Central Hub)                 │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Flask Web Server (Port 5000)                   │   │
│  │  - Web Interface                                │   │
│  │  - REST API (/api/nodes/*)                     │   │
│  │  - Database (JSON + CSV)                       │   │
│  │  - Centralized decision logic                   │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Local sensors (optional)                       │   │
│  │  - DHT11, ADS1115, Pump GPIO18                 │   │
│  └──────────────────────────────────────────────────┘   │
└───────────────────────┬─────────────────────────────────┘
                        │
            ┌───────────┴───────────┐
            │     WiFi / HTTP       │
            │                       │
    ┌───────┴────────┐    ┌──────────┴────────┐
    │               │    │                   │
┌───▼──────┐  ┌─────▼─────┐  ┌─────▼──────┐
│ ESP32 #1 │  │ ESP32 #2 │  │ ESP32 #3   │
│          │  │          │  │            │
│ DHT11    │  │ DHT11    │  │ DHT11      │
│ Soil     │  │ Soil     │  │ Soil       │
│ Pump     │  │ Pump     │  │ Pump       │
│ Battery  │  │ Battery  │  │ Battery    │
│ Solar    │  │ Solar    │  │ Solar      │
└──────────┘  └──────────┘  └────────────┘
```

### 🚀 Quick Start

#### Install dependencies

```bash
cd /home/gregory/homegarden
pip3 install -r requirements.txt
```

#### Launch the system

```bash
# Recommended method (interactive menu)
./start.sh

# Or directly
python3 app.py

# Or in background
nohup python3 app.py > app.log 2>&1 &
```

#### Useful scripts

```bash
./start.sh    # Start the system (interactive menu)
./stop.sh     # Stop the system
./status.sh   # Check system status
```

#### Access web interface

Once the system is started, access:
```
http://your_ip_address:5000
```

### 🔧 Required Hardware

#### Central Hub (Raspberry Pi)
- Raspberry Pi (model 3 or higher)
- Soil moisture sensor (via ADS1115)
- DHT11 sensor (air temperature/humidity)
- Watering pump with relay (GPIO 18)
- I2C connections for ADS1115

#### ESP32 Nodes (optional, for multi-node architecture)
- ESP32 Dev Module
- DHT11 sensor
- Soil moisture sensor (analog)
- Relay for pump
- Solar charging module (optional)
- LiPo battery 2000-5000 mAh (optional)

### 📡 Multi-Node API

The system exposes a complete REST API for managing ESP32 nodes:

- `POST /api/nodes/register` - Register a node
- `POST /api/nodes/{node_id}/data` - Receive data from a node
- `GET /api/nodes` - List all nodes
- `GET /api/nodes/{node_id}` - Information about a specific node
- `POST /api/nodes/{node_id}/control` - Manual control (pump)

See [ARCHITECTURE_MULTI_NODES.md](ARCHITECTURE_MULTI_NODES.md) for more details.

### ⚙️ Configuration

#### Configuration via web interface
- Access `http://IP:5000/configuration`
- Modify scenarios, thresholds, modes, and schedules

#### Configuration via files
- `config.json`: General configuration
- `data.json`: Scenarios, modes, scheduling
- `nodes.json`: ESP32 nodes registry

### 📝 Logs and Data

Data is recorded in:
- `arrosage_log.csv`: Watering history
- `temp_humidity_log.csv`: Air temperature and humidity
- `soil_moisture_log.csv`: Soil moisture
- `nodes_data/{node_id}_*.csv`: Data per ESP32 node
- `app.log`: System logs

### 📖 Complete Documentation

- **[GUIDE_DEMARRAGE.md](GUIDE_DEMARRAGE.md)** - Complete startup and configuration guide
- **[ARCHITECTURE_MULTI_NODES.md](ARCHITECTURE_MULTI_NODES.md)** - Detailed multi-node architecture
- **[GUIDE_MULTI_NODES.md](GUIDE_MULTI_NODES.md)** - Multi-node startup guide
- **[FONCTIONNALITES.md](FONCTIONNALITES.md)** - Complete feature list
- **[esp32_node/README.md](esp32_node/README.md)** - ESP32 documentation

### 🆘 Troubleshooting

See **[GUIDE_DEMARRAGE.md](GUIDE_DEMARRAGE.md)** for:
- Detailed instructions
- Startup methods
- Configuration
- Troubleshooting
- Automatic boot startup

---

## 📊 System Capabilities

### Hub Raspberry Pi
- ✅ 1 central hub
- ✅ Complete web interface
- ✅ Complete REST API
- ✅ Multi-node support (up to 10+ nodes)

### ESP32 Nodes
- ✅ Up to 10+ simultaneous nodes
- ✅ WiFi communication
- ✅ Solar power possible
- ✅ Independent zone control

### Sensors
- ✅ Soil moisture (per node)
- ✅ Air temperature (per node)
- ✅ Air humidity (per node)
- ✅ Battery (per ESP32 node)
- ✅ Solar charging (per ESP32 node)

### Control
- ✅ 1 pump per node (hub + ESP32)
- ✅ Intelligent automatic control
- ✅ Manual control via web interface
- ✅ Watering scheduling

---

## 🔒 Security & Reliability

- ✅ Protection against excessive watering
- ✅ Leak detection with automatic shutdown
- ✅ Error handling with automatic retry
- ✅ Data persistence with automatic backup
- ✅ Automatic reconnection for WiFi

---

## 📈 Statistics & Analysis

- ✅ Daily statistics (watering count, water volume, runtime)
- ✅ 24h trends (Min/Max/Average for all sensors)
- ✅ Complete history with temporal graphs
- ✅ Intelligent alerts (info, warning, danger levels)

---

## 🛠️ Technologies Used

- **Backend**: Python 3, Flask
- **Hardware**: Raspberry Pi, ESP32
- **Sensors**: DHT11, ADS1115, Analog soil sensors
- **Communication**: WiFi, HTTP/REST API
- **Storage**: JSON, CSV files
- **Frontend**: HTML, CSS, JavaScript (Chart.js)

---

## 📄 License

This project is open source. See repository for details.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

**Made with ❤️ for plant lovers**
