# 🛒 Liste d'Achat DigiKey - Composants pour ESP32-C3

## ⚠️ Note Importante

Cette liste est adaptée pour **ESP32-C3**. Les pins GPIO diffèrent de l'ESP32 classique. Vérifiez la compatibilité des pins dans votre code.

---

## 📦 Composants Essentiels

### 1. Capteur DHT11 (Température et Humidité de l'Air)

**Référence DigiKey :**
- **DHT11** : `1528-1034-ND` (DHT11 - Aosong)
- **Alternative** : `1528-1035-ND` (DHT22 - plus précis mais plus cher)

**Caractéristiques :**
- Température : 0-50°C (±2°C)
- Humidité : 20-90% RH (±5%)
- Alimentation : 3.3V-5V
- Interface : 1-wire (DATA)

**Connexion ESP32-C3 :**
- VCC → 3.3V
- GND → GND
- DATA → GPIO4 (ou autre GPIO digital)

**Résistance pull-up requise :**
- **Résistance 4.7kΩ** : `311-4.7KTR-ND` (1/4W, 5%)
- **Alternative 10kΩ** : `311-10KTR-ND` (si 4.7kΩ non disponible)

---

### 2. Capteur d'Humidité du Sol (Analogique)

**Option 1 : Capteur Capacitif (Recommandé)**
- **Référence** : `1528-1898-ND` (Capacitive Soil Moisture Sensor v1.2)
- **Alternative** : Rechercher "soil moisture sensor capacitive" sur DigiKey

**Option 2 : Capteur Résistif (Moins cher mais moins durable)**
- **Référence** : `1528-1897-ND` (Resistive Soil Moisture Sensor)

**Caractéristiques :**
- Sortie analogique : 0-3.3V
- Alimentation : 3.3V-5V
- Interface : Analogique

**Connexion ESP32-C3 :**
- VCC → 3.3V
- GND → GND
- SIG/AOUT → GPIO2 (ADC1_CH2) ou GPIO3 (ADC1_CH3)
- ⚠️ **Note ESP32-C3** : Pins ADC limités, vérifier la disponibilité

---

### 3. Module Relais (Contrôle Pompe)

**Référence DigiKey :**
- **Relais 5V 1 canal** : `1568-1099-ND` (Songle SRD-05VDC-SL-C)
- **Module relais avec optocoupleur** : `1568-1100-ND` (Module 1 canal avec isolation)

**Caractéristiques :**
- Tension bobine : 5V DC
- Courant bobine : ~70mA
- Contact : 10A @ 250VAC / 10A @ 30VDC
- Isolation optique : Oui (recommandé)

**Connexion ESP32-C3 :**
- VCC → 5V (ou 3.3V selon module)
- GND → GND
- IN → GPIO5 (ou autre GPIO digital)
- ⚠️ **Note** : Certains modules nécessitent 5V, vérifier la datasheet

**Alternative (Relais 3.3V) :**
- Rechercher "relay module 3.3V" si vous voulez éviter le 5V

---

### 4. Diviseur de Tension (Mesure Batterie - Optionnel)

**Résistances pour diviseur 1/2 :**
- **R1 = 10kΩ** : `311-10KTR-ND` (2x pour diviseur)
- **R2 = 10kΩ** : `311-10KTR-ND` (même référence)

**Caractéristiques :**
- Tolérance : 1% ou 5% (1% recommandé)
- Puissance : 1/4W minimum
- Type : Résistance standard

**Connexion ESP32-C3 :**
- Batterie + → R1 (10kΩ) → GPIO4 (ADC1_CH2)
- GPIO4 → R2 (10kΩ) → GND
- Batterie - → GND

**Alternative (Diviseur pré-assemblé) :**
- Rechercher "voltage divider module" si vous préférez un module

---

### 5. Détection Charge Solaire (Optionnel)

**Option 1 : Optocoupleur (Isolation)**
- **Référence** : `160-1540-ND` (PC817 - Optocoupleur 4 pins)
- **Alternative** : `160-1541-ND` (PC817X - Variante)

**Option 2 : Transistor NPN (Simple)**
- **Référence** : `2N3904FS-ND` (2N3904 - Transistor NPN général)
- **Résistance base** : `311-10KTR-ND` (10kΩ)

**Connexion ESP32-C3 :**
- Charge solaire détectée → GPIO6 (ou autre GPIO digital)
- Via optocoupleur ou transistor selon circuit

---

## 🔧 Composants de Support

### 6. Résistances Pull-up/Pull-down

**Résistances diverses :**
- **4.7kΩ** (DHT11) : `311-4.7KTR-ND` (x1)
- **10kΩ** (Diviseur, pull-up) : `311-10KTR-ND` (x3)
- **Pack varié** : Rechercher "resistor kit" pour avoir plusieurs valeurs

---

### 7. Condensateurs de Découplage (Recommandé)

**Condensateurs céramique :**
- **100nF (0.1µF)** : `399-4150-ND` (x2-3 pour découplage)
- **10µF** : `399-4151-ND` (x1 pour stabilisation alimentation)

**Usage :**
- 100nF entre VCC et GND près de chaque composant
- 10µF près de l'alimentation ESP32-C3

---

### 8. Connecteurs et Câblage

**Connecteurs Dupont (Jumper Wires) :**
- **Mâle-Mâle** : `1528-1963-ND` (Pack 40 pièces)
- **Mâle-Femelle** : `1528-1964-ND` (Pack 40 pièces)
- **Femelle-Femelle** : `1528-1965-ND` (Pack 40 pièces)

**Alternative :**
- Rechercher "jumper wires" ou "dupont wires" sur DigiKey

---

### 9. Breadboard (Prototypage)

**Breadboard standard :**
- **Référence** : `1568-1514-ND` (Breadboard 830 points)
- **Alternative** : `1568-1515-ND` (Breadboard 400 points - plus petit)

**Usage :**
- Prototypage et tests avant soudure définitive

---

### 10. Alimentation (Si nécessaire)

**Régulateur de tension 3.3V (Si alimentation externe) :**
- **Référence** : `296-1581-ND` (AMS1117-3.3 - Régulateur 3.3V)
- **Condensateurs** : 10µF (entrée) + 10µF (sortie)

**Module USB-C (Pour ESP32-C3) :**
- L'ESP32-C3 a généralement un port USB-C intégré
- Câble USB-C : `WM13999-ND` (Câble USB-C vers USB-A)

---

## 📋 Liste Récapitulative

### Composants Principaux

| Composant | Quantité | Référence DigiKey | Prix Approx. |
|-----------|----------|-------------------|--------------|
| DHT11 | 1 | `1528-1034-ND` | ~$5 |
| Capteur humidité sol | 1 | `1528-1898-ND` | ~$8 |
| Module relais 5V | 1 | `1568-1100-ND` | ~$3 |
| Résistance 4.7kΩ | 1 | `311-4.7KTR-ND` | ~$0.10 |
| Résistance 10kΩ | 3 | `311-10KTR-ND` | ~$0.30 |
| Condensateur 100nF | 3 | `399-4150-ND` | ~$0.30 |
| Condensateur 10µF | 2 | `399-4151-ND` | ~$0.20 |
| Jumper wires | 1 pack | `1528-1964-ND` | ~$5 |
| Breadboard | 1 | `1568-1514-ND` | ~$8 |

**Total approximatif : ~$30-35 CAD**

### Composants Optionnels (Batterie/Solaire)

| Composant | Quantité | Référence DigiKey | Prix Approx. |
|-----------|----------|-------------------|--------------|
| Optocoupleur PC817 | 1 | `160-1540-ND` | ~$0.50 |
| Transistor 2N3904 | 1 | `2N3904FS-ND` | ~$0.20 |

---

## ⚠️ Notes Importantes pour ESP32-C3

### Différences avec ESP32 Classique

1. **Pins ADC limités** :
   - ESP32-C3 a seulement 2 canaux ADC (ADC1_CH2, ADC1_CH3)
   - GPIO2 et GPIO3 sont les pins ADC disponibles
   - Vérifier la disponibilité selon votre configuration

2. **Pins GPIO** :
   - ESP32-C3 a moins de pins GPIO que l'ESP32 classique
   - Adapter les pins dans le code si nécessaire

3. **Alimentation** :
   - ESP32-C3 fonctionne en 3.3V
   - Certains modules relais nécessitent 5V (vérifier)

### Adaptation du Code

Vous devrez modifier les pins dans `esp32_node.ino` :

```cpp
// Pour ESP32-C3 (exemple)
#define DHTPIN 4           // GPIO4 (digital)
#define SOIL_MOISTURE_PIN 2  // GPIO2 (ADC1_CH2) - Vérifier disponibilité
#define PUMP_RELAY_PIN 5     // GPIO5 (digital)
#define BATTERY_PIN 3        // GPIO3 (ADC1_CH3) - si disponible
#define SOLAR_CHARGE_PIN 6   // GPIO6 (digital)
```

---

## 🔍 Recherche sur DigiKey

### Comment trouver les composants

1. **Aller sur https://www.digikey.ca/**
2. **Rechercher par numéro de référence** (ex: `1528-1034-ND`)
3. **Ou rechercher par nom** :
   - "DHT11 temperature humidity sensor"
   - "soil moisture sensor capacitive"
   - "relay module 5V"
   - "resistor 10k ohm"

### Filtres utiles

- **Stock** : En stock uniquement
- **Prix** : Trier par prix croissant
- **Quantité minimum** : Ajuster selon vos besoins
- **Fabricant** : Vérifier la qualité

---

## 📦 Alternative : Kits Complets

Si vous préférez, recherchez sur DigiKey :
- "ESP32 development kit"
- "sensor kit arduino"
- "relay module kit"

Ces kits peuvent contenir plusieurs composants à meilleur prix.

---

## ✅ Checklist de Commande

- [ ] DHT11 capteur température/humidité
- [ ] Capteur humidité sol (analogique)
- [ ] Module relais 5V (avec optocoupleur)
- [ ] Résistances (4.7kΩ, 10kΩ)
- [ ] Condensateurs (100nF, 10µF)
- [ ] Jumper wires (mâle-femelle)
- [ ] Breadboard (pour prototypage)
- [ ] Composants optionnels (batterie/solaire)

---

## 🔗 Liens Utiles

- **DigiKey Canada** : https://www.digikey.ca/
- **Documentation ESP32-C3** : https://docs.espressif.com/projects/esp-idf/en/latest/esp32c3/
- **Pinout ESP32-C3** : Rechercher "ESP32-C3 pinout" pour le schéma exact

---

**Note** : Les références DigiKey peuvent changer. Vérifiez la disponibilité et les prix avant de commander. Les prix sont approximatifs en CAD.

