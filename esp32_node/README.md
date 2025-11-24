# 🌱 Nœud ESP32 - Système d'Arrosage Automatique

Code pour nœud ESP32 du système d'arrosage automatique distribué.

## Matériel requis

- **ESP32** (ESP32-WROOM-32 ou équivalent)
- **Capteur DHT11** (température et humidité de l'air)
- **Capteur d'humidité du sol** (analogique)
- **Relais 5V** pour contrôler la pompe
- **Module de charge solaire** (optionnel, recommandé)
- **Batterie LiPo 3.7V** (optionnel, 2000-5000 mAh)
- **Panneau solaire** (optionnel, 5W minimum)

## Installation

### 1. Préparer l'environnement Arduino

1. Installer **Arduino IDE** (version 1.8.x ou 2.x)
2. Ajouter le support ESP32 :
   - Fichier → Préférences
   - Dans "URL de gestionnaire de cartes supplémentaires", ajouter :
     ```
     https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
     ```
   - Outils → Type de carte → Gestionnaire de cartes
   - Rechercher "ESP32" et installer

### 2. Installer les bibliothèques

Via le Gestionnaire de bibliothèques (Croquis → Inclure une bibliothèque → Gérer les bibliothèques) :

- **DHT sensor library** (par Adafruit)
- **ArduinoJson** (par Benoit Blanchon) - Version 6.x

### 3. Configuration

1. Copier `config.h.example` vers `config.h`
2. Modifier `config.h` avec vos paramètres :
   ```cpp
   #define WIFI_SSID "VotreSSID"
   #define WIFI_PASSWORD "VotreMotDePasse"
   #define HUB_URL "http://192.168.1.100:5000"
   #define NODE_ID "ESP32_001"  // UNIQUE pour chaque nœud !
   ```

3. **IMPORTANT:** Chaque nœud doit avoir un `NODE_ID` différent :
   - ESP32_001, ESP32_002, ESP32_003, etc.

### 4. Câblage

Voir le fichier `ARCHITECTURE_MULTI_NODES.md` pour le schéma de câblage détaillé.

**Résumé rapide:**
- DHT11 DATA → GPIO4
- Capteur sol SIG → GPIO34
- Relais IN → GPIO2
- Batterie (via diviseur) → GPIO35
- Charge solaire → GPIO32

### 5. Compilation et téléversement

1. Ouvrir `esp32_node.ino` dans Arduino IDE
2. Sélectionner la carte : **Outils → Type de carte → ESP32 Dev Module**
3. Sélectionner le port USB
4. Compiler (✓) puis Téléverser (→)

## Utilisation

### Premier démarrage

1. Après le téléversement, ouvrir le **Moniteur série** (115200 bauds)
2. Le nœud va :
   - Se connecter au WiFi
   - S'enregistrer auprès du hub
   - Commencer à envoyer des données

### Vérification

Dans le moniteur série, vous devriez voir :
```
=== Système d'Arrosage ESP32 ===
Nœud ID: ESP32_001
Connexion WiFi...
WiFi connecté : 192.168.1.50
Enregistrement nœud : 200
Système prêt
Temp: 22.5°C, Hum: 45.0%, Sol: 35.2%, Bat: 85%, Solaire: Oui
```

### Interface web

Accéder à l'interface du hub : `http://IP_RASPBERRY_PI:5000`

Les nœuds apparaîtront automatiquement dans l'interface (à implémenter).

## Paramètres configurables

Dans le code `esp32_node.ino`, vous pouvez modifier :

- `SEND_INTERVAL` : Intervalle d'envoi normal (défaut: 5 minutes)
- `SENSOR_READ_INTERVAL` : Fréquence de lecture capteurs (défaut: 10 secondes)
- `PUMP_MAX_DURATION` : Durée max pompe en minutes (sécurité)
- Seuils critiques pour envoi immédiat

## Dépannage

### Erreur de compilation

- Vérifier que toutes les bibliothèques sont installées
- Vérifier la version d'Arduino IDE (1.8.x minimum)

### WiFi ne se connecte pas

- Vérifier SSID et mot de passe dans `config.h`
- Vérifier que le WiFi est en 2.4 GHz (ESP32 ne supporte pas le 5 GHz)
- Augmenter le timeout dans le code si nécessaire

### Pas de communication avec le hub

- Vérifier l'adresse IP du Raspberry Pi dans `config.h`
- Vérifier que le port 5000 est ouvert
- Vérifier les logs du hub : `tail -f /home/gregory/homegarden/app.log`

### Batterie se décharge

- Vérifier le panneau solaire (orientation, ombre)
- Réduire la fréquence d'envoi
- Activer le mode deep sleep (déjà implémenté)

## Optimisation pour l'alimentation solaire

### Configuration recommandée

- **Panneau solaire:** 5-10W, 5V ou 12V
- **Batterie:** 2000-5000 mAh LiPo
- **Module de charge:** TP4056 ou équivalent avec protection

### Mode économie d'énergie

Le code active automatiquement le mode deep sleep si :
- Batterie < 20%
- Pas de charge solaire active
- Pompe non active

En deep sleep, la consommation est d'environ **10 µA**.

## Support

Pour plus d'informations, consulter :
- `ARCHITECTURE_MULTI_NODES.md` : Architecture complète
- Documentation principale du projet

## Licence

Même licence que le projet principal.

