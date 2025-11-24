# 🚀 Guide de Démarrage Rapide - ESP32 WiFi

Guide rapide pour installer et connecter votre ESP32 au WiFi.

## ⚡ Installation Express (5 minutes)

### Étape 1 : Installer Arduino IDE

1. **Télécharger Arduino IDE** : https://www.arduino.cc/en/software
   - Version 1.8.x ou 2.x (recommandé)
   - Installer sur votre ordinateur

### Étape 2 : Ajouter le support ESP32

1. Ouvrir **Arduino IDE**
2. Aller dans **Fichier → Préférences**
3. Dans **"URL de gestionnaire de cartes supplémentaires"**, ajouter :
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
4. Cliquer sur **OK**
5. Aller dans **Outils → Type de carte → Gestionnaire de cartes**
6. Rechercher **"ESP32"** et installer **"esp32 by Espressif Systems"**
   - ⏱️ Installation : ~2-3 minutes

### Étape 3 : Installer les bibliothèques

Via **Croquis → Inclure une bibliothèque → Gérer les bibliothèques**, installer :

- **DHT sensor library** (par Adafruit)
- **ArduinoJson** (par Benoit Blanchon) - Version 6.x

## 📡 Configuration WiFi

### Option A : Configuration directe dans le code (Rapide)

1. Ouvrir `esp32_node.ino` dans Arduino IDE
2. Modifier les lignes **30-32** :

```cpp
// WiFi
const char* ssid = "VOTRE_SSID_WIFI";        // ← Votre nom de réseau WiFi
const char* password = "VOTRE_MOT_DE_PASSE"; // ← Votre mot de passe WiFi
```

3. Modifier l'adresse du hub (ligne **35**) :

```cpp
const char* hub_url = "http://192.168.1.100:5000";  // ← IP de votre Raspberry Pi
```

4. Modifier l'ID du nœud (ligne **36**) :

```cpp
const char* node_id = "ESP32_001";  // ← UNIQUE pour chaque ESP32 !
```

### Option B : Utiliser config.h (Recommandé pour plusieurs nœuds)

1. Copier `config.h.example` vers `config.h` :
   ```bash
   cp config.h.example config.h
   ```

2. Modifier `config.h` :

```cpp
// Configuration WiFi
#define WIFI_SSID "VOTRE_SSID_WIFI"
#define WIFI_PASSWORD "VOTRE_MOT_DE_PASSE"

// Adresse du hub Raspberry Pi
#define HUB_URL "http://192.168.1.100:5000"

// Identification du nœud (UNIQUE pour chaque nœud)
#define NODE_ID "ESP32_001"
```

3. Si vous utilisez `config.h`, modifier `esp32_node.ino` pour inclure :
   ```cpp
   #include "config.h"
   ```
   Et remplacer les constantes par les définitions de `config.h`.

## 🔌 Téléversement sur l'ESP32

### Préparation

1. **Connecter l'ESP32** à votre ordinateur via USB
2. **Installer les drivers USB** si nécessaire (CP2102 ou CH340)

### Configuration Arduino IDE

1. **Sélectionner la carte** :
   - **Outils → Type de carte → ESP32 Dev Module**

2. **Sélectionner le port** :
   - **Outils → Port → COMx** (Windows) ou **/dev/ttyUSB0** (Linux) ou **/dev/cu.usbserial-xxx** (Mac)

3. **Paramètres recommandés** :
   - **Vitesse de téléversement** : 115200
   - **Fréquence CPU** : 240MHz
   - **Flash Frequency** : 80MHz
   - **Partition Scheme** : Default 4MB with spiffs

### Téléverser le code

1. Cliquer sur **✓ (Vérifier)** pour compiler
2. Si compilation OK, cliquer sur **→ (Téléverser)**
3. ⏱️ Attendre la fin du téléversement (~30 secondes)

## ✅ Vérifier la connexion WiFi

### Ouvrir le Moniteur Série

1. **Outils → Moniteur série** (ou `Ctrl+Shift+M`)
2. **Vitesse** : 115200 bauds
3. **Appuyer sur le bouton RESET** de l'ESP32

### Résultat attendu

Vous devriez voir dans le moniteur série :

```
=== Système d'Arrosage ESP32 ===
Nœud ID: ESP32_001
Connexion WiFi...
WiFi connecté : 192.168.1.50
Enregistrement nœud : 200
Système prêt
```

✅ **Si vous voyez "WiFi connecté"** → Tout fonctionne !

## 🔧 Dépannage WiFi

### ❌ "Échec connexion WiFi"

**Solutions :**

1. **Vérifier le SSID et mot de passe**
   - Attention aux majuscules/minuscules
   - Vérifier qu'il n'y a pas d'espaces en trop

2. **Vérifier la bande WiFi**
   - ESP32 ne supporte **QUE le 2.4 GHz**
   - Si votre routeur émet en 5 GHz, désactiver ou créer un réseau 2.4 GHz

3. **Vérifier la distance**
   - L'ESP32 doit être à portée du routeur
   - Tester près du routeur d'abord

4. **Vérifier le type de sécurité**
   - WPA2 fonctionne bien
   - WPA3 peut poser problème (utiliser WPA2/WPA3 mixte)

5. **Augmenter le timeout** (dans le code) :
   ```cpp
   while (WiFi.status() != WL_CONNECTED && attempts < 30) {  // Augmenter de 20 à 30
   ```

### ❌ "Pas de communication avec le hub"

**Solutions :**

1. **Vérifier l'adresse IP du Raspberry Pi**
   ```bash
   # Sur le Raspberry Pi
   hostname -I
   ```

2. **Vérifier que le hub est démarré**
   ```bash
   # Sur le Raspberry Pi
   ps aux | grep app.py
   ```

3. **Tester la connexion depuis l'ESP32**
   - Vérifier les logs dans le moniteur série
   - Chercher les messages d'erreur HTTP

### ❌ Port USB non détecté

**Solutions :**

1. **Linux** : Ajouter l'utilisateur au groupe dialout
   ```bash
   sudo usermod -a -G dialout $USER
   # Puis se déconnecter/reconnecter
   ```

2. **Windows** : Installer les drivers CP2102 ou CH340

3. **Vérifier le câble USB** : Utiliser un câble de données (pas seulement charge)

## 📋 Checklist Rapide

- [ ] Arduino IDE installé
- [ ] Support ESP32 ajouté
- [ ] Bibliothèques installées (DHT, ArduinoJson)
- [ ] SSID et mot de passe WiFi configurés
- [ ] Adresse IP du Raspberry Pi configurée
- [ ] ID du nœud unique configuré
- [ ] ESP32 connecté en USB
- [ ] Carte et port sélectionnés dans Arduino IDE
- [ ] Code téléversé avec succès
- [ ] Moniteur série ouvert (115200 bauds)
- [ ] WiFi connecté visible dans les logs

## 🎯 Commandes Rapides

### Trouver l'IP du Raspberry Pi
```bash
hostname -I
```

### Vérifier que le hub tourne
```bash
ps aux | grep app.py
```

### Voir les logs du hub
```bash
tail -f /home/gregory/homegarden/app.log
```

### Tester la connexion depuis l'ESP32
Dans le moniteur série, chercher :
- `WiFi connecté : [IP]` ✅
- `Enregistrement nœud : 200` ✅

## 💾 Optimisation de la Mémoire Flash

### Message de compilation

Si vous voyez ce message lors de la compilation :
```
Le croquis utilise 1097998 octets (83%) de l'espace de stockage de programmes.
Les variables globales utilisent 36072 octets (11%) de mémoire dynamique.
```

**✅ C'est normal !** Le code compile et fonctionne correctement. Vous avez encore **17% d'espace libre** pour ajouter des fonctionnalités.

### Quand s'inquiéter ?

- ⚠️ **Si > 90%** : Commencer à optimiser
- ❌ **Si > 95%** : Optimisation nécessaire
- ❌ **Si erreur "pas assez d'espace"** : Optimisation obligatoire

### Optimisations possibles

#### 1. Changer la partition (Recommandé)

Dans Arduino IDE :
- **Outils → Partition Scheme → Huge APP (3MB No OTA/1MB SPIFFS)**
- Cela donne plus d'espace pour le code (3MB au lieu de 1.3MB)

#### 2. Réduire les messages Serial

Dans le code, commenter les messages Serial non essentiels :
```cpp
// Serial.println("Message de debug");  // Désactivé pour économiser l'espace
```

#### 3. Optimiser les buffers JSON

Réduire la taille des `StaticJsonDocument` si possible :
```cpp
StaticJsonDocument<256> doc;  // Au lieu de 512 si suffisant
```

#### 4. Compiler avec optimisations

Dans Arduino IDE :
- **Outils → Optimisation du compilateur → Optimiser pour la taille (-Os)**

#### 5. Désactiver les fonctionnalités non utilisées

Si vous n'utilisez pas certaines fonctionnalités, les commenter :
- Mode deep sleep
- Gestion batterie
- Détection solaire

### Vérifier l'espace après optimisation

Après chaque optimisation, recompiler et vérifier :
```
Le croquis utilise X octets (Y%) de l'espace de stockage de programmes.
```

### Espace mémoire dynamique (RAM)

**11% utilisé = Excellent !** Vous avez encore **89% de RAM disponible**.

- ✅ **< 50%** : Parfait
- ⚠️ **50-70%** : Acceptable
- ❌ **> 70%** : Risque de crash, optimiser

## 📚 Documentation Complète

Pour plus de détails, consultez :
- `README.md` : Documentation complète du nœud ESP32
- `ARCHITECTURE_MULTI_NODES.md` : Architecture système
- `GUIDE_MULTI_NODES.md` : Guide multi-nœuds

---

**Besoin d'aide ?** Vérifiez les logs du moniteur série et du hub Raspberry Pi.

