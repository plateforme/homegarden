# 🌐 Architecture Multi-Nœuds - Système d'Arrosage Automatique

## Vue d'ensemble

Cette architecture transforme le système d'arrosage automatique en un système distribué avec :
- **1 Hub Central** (Raspberry Pi) : Interface web, logique de décision, agrégation des données
- **Jusqu'à 10 Nœuds ESP32** : Capteurs et contrôle de pompe par zone

## Architecture

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

## Protocole de Communication

### Enregistrement d'un nœud

**Endpoint:** `POST /api/nodes/register`

**Requête:**
```json
{
  "node_id": "ESP32_001",
  "name": "Zone Jardin 1",
  "location": "Jardin avant",
  "battery_level": 85,
  "solar_charging": true,
  "firmware_version": "1.0"
}
```

**Réponse:**
```json
{
  "status": "success",
  "node": {
    "id": "ESP32_001",
    "name": "Zone Jardin 1",
    "status": "online",
    "last_seen": "2024-01-15T10:30:00"
  }
}
```

### Envoi de données

**Endpoint:** `POST /api/nodes/{node_id}/data`

**Requête:**
```json
{
  "temperature": 22.5,
  "air_humidity": 45.0,
  "soil_moisture": 35.2,
  "pump_status": "off",
  "watering_event": false,
  "watering_duration": 0,
  "battery_level": 85,
  "solar_charging": true
}
```

**Réponse:**
```json
{
  "status": "success",
  "action": "water",
  "duration": 1.5,
  "maintenance_mode": false,
  "vacation_mode": false
}
```

### Actions possibles

- `"action": "water"` → Démarrer la pompe pour `duration` minutes
- `"action": "stop"` → Arrêter la pompe immédiatement
- `"action": "none"` → Aucune action requise

## Fréquence d'envoi recommandée

### Envoi périodique normal
- **Intervalle:** 5 minutes (300 secondes)
- **Condition:** État normal, pas d'événement critique

### Envoi immédiat (événements)
- **Seuil d'humidité critique:** < 15% ou > 95%
- **Température critique:** < 5°C ou > 35°C
- **Démarrage/arrêt pompe:** Immédiat
- **Pompe active:** Toutes les minutes

## Gestion de l'alimentation solaire

### Configuration recommandée

1. **Module de charge solaire**
   - Tension: 5V (USB) ou 12V selon votre panneau
   - Courant: Minimum 1A pour ESP32 + pompe
   - Protection: Surcharge, décharge profonde

2. **Batterie LiPo**
   - Capacité: 2000-5000 mAh selon usage
   - Tension: 3.7V nominal (4.2V chargé)
   - Protection: Circuit de protection intégré

3. **Circuit de mesure**
   - Diviseur de tension 1/2 pour lecture batterie
   - Pin GPIO pour détection charge solaire

### Économie d'énergie

Le code ESP32 inclut plusieurs optimisations :

1. **Deep Sleep Mode**
   - Activé si batterie < 20% et pas de charge solaire
   - Réveil toutes les 5 minutes
   - Consommation: ~10 µA en deep sleep

2. **WiFi Low Power**
   - WiFi désactivé entre les envois (optionnel)
   - Réduction de la fréquence d'envoi si batterie faible

3. **Gestion intelligente**
   - Pas d'arrosage si batterie < 30% (sauf si charge solaire active)
   - Réduction de la fréquence d'envoi si batterie < 50%

## Installation

### Sur le Raspberry Pi

1. **Mettre à jour le code**
```bash
cd /home/gregory/homegarden
git pull  # ou copier les nouveaux fichiers
```

2. **Vérifier les dépendances**
```bash
pip3 install flask  # Déjà installé normalement
```

3. **Redémarrer le service**
```bash
./stop.sh
./start.sh
```

### Sur l'ESP32

1. **Installer Arduino IDE**
   - Télécharger depuis https://www.arduino.cc/en/software
   - Installer le support ESP32 via le gestionnaire de cartes

2. **Installer les bibliothèques**
   - WiFi (incluse)
   - HTTPClient (incluse)
   - DHT sensor library (via Library Manager)
   - ArduinoJson (via Library Manager)

3. **Configurer le nœud**
   - Copier `config.h.example` vers `config.h`
   - Modifier les paramètres (WiFi, Hub URL, Node ID)
   - **IMPORTANT:** Chaque nœud doit avoir un `NODE_ID` unique

4. **Compiler et téléverser**
   - Sélectionner la carte: "ESP32 Dev Module"
   - Port: Sélectionner le port USB de l'ESP32
   - Compiler et téléverser

## Câblage ESP32

### Capteur DHT11
```
DHT11 VCC  → ESP32 3.3V
DHT11 GND  → ESP32 GND
DHT11 DATA → ESP32 GPIO4
```

### Capteur d'humidité du sol
```
Capteur VCC → ESP32 3.3V
Capteur GND → ESP32 GND
Capteur SIG → ESP32 GPIO34 (ADC1_CH6)
```

### Relais pompe
```
Relais IN   → ESP32 GPIO2
Relais VCC  → ESP32 5V (ou externe)
Relais GND  → ESP32 GND
Relais COM  → Pompe +
Relais NO   → Pompe -
```

### Module charge solaire (optionnel)
```
Chargeur V+ → Panneau solaire +
Chargeur V- → Panneau solaire -
Chargeur B+ → Batterie +
Chargeur B- → Batterie -
Chargeur OUT+ → ESP32 VIN
Chargeur OUT- → ESP32 GND
Chargeur CHG → ESP32 GPIO32 (détection charge)
```

### Mesure batterie (optionnel)
```
Batterie + → Diviseur (R1: 10kΩ)
Diviseur milieu → ESP32 GPIO35 (ADC1_CH7)
Batterie - → ESP32 GND
```

## Dépannage

### Le nœud ne se connecte pas au WiFi
- Vérifier SSID et mot de passe
- Vérifier la portée WiFi
- Augmenter le timeout de connexion dans le code

### Le nœud ne communique pas avec le hub
- Vérifier l'adresse IP du Raspberry Pi
- Vérifier que le port 5000 est ouvert
- Vérifier les logs du hub: `tail -f app.log`

### La pompe ne démarre pas
- Vérifier le câblage du relais
- Vérifier que le relais est alimenté
- Tester le relais manuellement

### Batterie se décharge trop vite
- Réduire la fréquence d'envoi
- Activer le mode deep sleep
- Vérifier la consommation du panneau solaire

## Sécurité

1. **WiFi**
   - Utiliser WPA2 ou WPA3
   - Changer les mots de passe par défaut

2. **API**
   - Ajouter une authentification (optionnel)
   - Utiliser HTTPS en production (nécessite certificat SSL)

3. **Nœuds**
   - Chaque nœud a un ID unique
   - Validation des données côté hub

## Évolutions futures

- [ ] Support MQTT pour communication asynchrone
- [ ] WebSocket pour contrôle en temps réel
- [ ] Interface web multi-nœuds avec cartes
- [ ] Alertes par email/SMS
- [ ] Intégration Home Assistant
- [ ] Machine learning pour optimisation

