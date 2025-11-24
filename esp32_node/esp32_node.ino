/*
 * Système d'Arrosage Automatique - Nœud ESP32
 * 
 * Ce code gère un nœud ESP32 avec :
 * - Capteurs DHT11 (température/humidité air)
 * - Capteur d'humidité du sol (analogique)
 * - Contrôle de pompe via relais
 * - Communication WiFi avec le hub Raspberry Pi
 * - Gestion de l'alimentation solaire et économie d'énergie
 * 
 * Matériel requis :
 * - ESP32 (ESP32-WROOM-32 ou équivalent)
 * - DHT11 (température/humidité)
 * - Capteur d'humidité du sol (analogique)
 * - Relais pour la pompe
 * - Module de charge solaire (optionnel)
 * - Batterie LiPo (optionnel)
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>
#include <ArduinoJson.h>
#include <esp_sleep.h>

// ============================================================================
// CONFIGURATION
// ============================================================================

// WiFi
const char* ssid = "VOTRE_SSID_WIFI";
const char* password = "VOTRE_MOT_DE_PASSE";

// Hub Raspberry Pi
const char* hub_url = "http://192.168.1.100:5000";  // Adresse IP du Raspberry Pi
const char* node_id = "ESP32_001";  // ID unique du nœud (à changer pour chaque nœud)
const char* node_name = "Zone Jardin 1";
const char* node_location = "Jardin avant";

// Pins
#define DHTPIN 4           // GPIO4 pour DHT11
#define DHTTYPE DHT11
#define SOIL_MOISTURE_PIN 34  // GPIO34 (ADC1_CH6) pour capteur humidité sol
#define PUMP_RELAY_PIN 2      // GPIO2 pour relais pompe
#define BATTERY_PIN 35        // GPIO35 (ADC1_CH7) pour lecture batterie (via diviseur)
#define SOLAR_CHARGE_PIN 32   // GPIO32 pour détection charge solaire

// Paramètres
const int SEND_INTERVAL = 300000;  // Envoi toutes les 5 minutes (300000 ms)
const int SEND_INTERVAL_FAST = 60000;  // Envoi rapide toutes les minutes si événement
const int SENSOR_READ_INTERVAL = 10000;  // Lecture capteurs toutes les 10 secondes
const int PUMP_MAX_DURATION = 30;  // Durée max pompe en minutes (sécurité)

// Seuils pour envoi immédiat
const float SOIL_MOISTURE_CRITICAL_LOW = 15.0;  // Envoi immédiat si < 15%
const float SOIL_MOISTURE_CRITICAL_HIGH = 95.0;  // Envoi immédiat si > 95%
const float TEMP_CRITICAL_LOW = 5.0;   // Envoi immédiat si < 5°C
const float TEMP_CRITICAL_HIGH = 35.0; // Envoi immédiat si > 35°C

// ============================================================================
// VARIABLES GLOBALES
// ============================================================================

DHT dht(DHTPIN, DHTTYPE);

// État du système
struct NodeState {
  float temperature = 0;
  float air_humidity = 0;
  float soil_moisture = 0;
  bool pump_running = false;
  unsigned long pump_start_time = 0;
  float pump_duration_minutes = 0;
  int battery_level = 0;
  bool solar_charging = false;
  bool maintenance_mode = false;
  bool vacation_mode = false;
  unsigned long last_send = 0;
  unsigned long last_sensor_read = 0;
  bool needs_immediate_send = false;
  String last_command = "";
};

NodeState state;

// ============================================================================
// FONCTIONS UTILITAIRES
// ============================================================================

float readSoilMoisture() {
  // Lecture analogique (0-4095 sur ESP32, 0-3.3V)
  int analogValue = analogRead(SOIL_MOISTURE_PIN);
  float voltage = (analogValue / 4095.0) * 3.3;
  
  // Conversion en pourcentage
  // Tension basse = sol humide, tension haute = sol sec
  float moisture = (1 - (voltage / 3.3)) * 100;
  moisture = constrain(moisture, 0, 100);
  
  return moisture;
}

int readBatteryLevel() {
  // Lecture de la batterie via diviseur de tension
  // Si pas de batterie, retourner 100 (alimentation secteur)
  int analogValue = analogRead(BATTERY_PIN);
  if (analogValue == 0) return 100;  // Probablement alimentation secteur
  
  // Conversion (ajuster selon votre circuit)
  // Exemple : 3.0V = 0%, 4.2V = 100%
  float voltage = (analogValue / 4095.0) * 3.3 * 2;  // *2 si diviseur 1/2
  int level = map(voltage * 100, 300, 420, 0, 100);
  return constrain(level, 0, 100);
}

bool isSolarCharging() {
  // Détection de la charge solaire (logique à adapter selon votre circuit)
  return digitalRead(SOLAR_CHARGE_PIN) == HIGH;
}

void controlPump(bool on, float duration_minutes = 0) {
  if (on && !state.pump_running) {
    digitalWrite(PUMP_RELAY_PIN, HIGH);  // Activer le relais
    state.pump_running = true;
    state.pump_start_time = millis();
    state.pump_duration_minutes = duration_minutes;
    Serial.println("Pompe démarrée");
  } else if (!on && state.pump_running) {
    digitalWrite(PUMP_RELAY_PIN, LOW);  // Désactiver le relais
    state.pump_running = false;
    unsigned long duration_ms = millis() - state.pump_start_time;
    state.pump_duration_minutes = duration_ms / 60000.0;
    Serial.println("Pompe arrêtée");
  }
}

void checkPumpTimeout() {
  // Vérifier si la pompe doit être arrêtée
  if (state.pump_running) {
    unsigned long elapsed_minutes = (millis() - state.pump_start_time) / 60000;
    
    // Arrêt automatique après la durée prévue ou max
    if (elapsed_minutes >= state.pump_duration_minutes || 
        elapsed_minutes >= PUMP_MAX_DURATION) {
      controlPump(false);
      state.needs_immediate_send = true;  // Envoyer immédiatement l'événement
    }
  }
}

bool shouldSendImmediately() {
  // Déterminer si on doit envoyer immédiatement
  if (state.needs_immediate_send) return true;
  if (state.soil_moisture < SOIL_MOISTURE_CRITICAL_LOW) return true;
  if (state.soil_moisture > SOIL_MOISTURE_CRITICAL_HIGH) return true;
  if (state.temperature < TEMP_CRITICAL_LOW) return true;
  if (state.temperature > TEMP_CRITICAL_HIGH) return true;
  if (state.pump_running && (millis() - state.last_send) > 60000) return true;  // Si pompe active, envoyer toutes les minutes
  return false;
}

// ============================================================================
// COMMUNICATION AVEC LE HUB
// ============================================================================

void registerNode() {
  if (WiFi.status() != WL_CONNECTED) return;
  
  HTTPClient http;
  String url = String(hub_url) + "/api/nodes/register";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  
  StaticJsonDocument<200> doc;  // Optimisé : 200 au lieu de 256
  doc["node_id"] = node_id;
  doc["name"] = node_name;
  doc["location"] = node_location;
  doc["battery_level"] = state.battery_level;
  doc["solar_charging"] = state.solar_charging;
  doc["firmware_version"] = "1.0";
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  int httpResponseCode = http.POST(jsonString);
  
  if (httpResponseCode > 0) {
    Serial.print("Enregistrement nœud : ");
    Serial.println(httpResponseCode);
  } else {
    Serial.print("Erreur enregistrement : ");
    Serial.println(httpResponseCode);
  }
  
  http.end();
}

void sendDataToHub() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi non connecté");
    return;
  }
  
  HTTPClient http;
  String url = String(hub_url) + "/api/nodes/" + String(node_id) + "/data";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  
  StaticJsonDocument<400> doc;  // Optimisé : 400 au lieu de 512
  doc["temperature"] = state.temperature;
  doc["air_humidity"] = state.air_humidity;
  doc["soil_moisture"] = state.soil_moisture;
  doc["pump_status"] = state.pump_running ? "on" : "off";
  doc["watering_event"] = state.needs_immediate_send;
  doc["watering_duration"] = state.pump_duration_minutes;
  doc["battery_level"] = state.battery_level;
  doc["solar_charging"] = state.solar_charging;
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  Serial.print("Envoi données : ");
  Serial.println(jsonString);
  
  int httpResponseCode = http.POST(jsonString);
  
  if (httpResponseCode == 200) {
    String response = http.getString();
    Serial.print("Réponse hub : ");
    Serial.println(response);
    
    // Parser la réponse pour les commandes
    StaticJsonDocument<200> responseDoc;  // Optimisé : 200 au lieu de 256
    deserializeJson(responseDoc, response);
    
    if (responseDoc["action"] == "water") {
      float duration = responseDoc["duration"];
      controlPump(true, duration);
    } else if (responseDoc["action"] == "stop") {
      controlPump(false);
    }
    
    state.maintenance_mode = responseDoc["maintenance_mode"] | false;
    state.vacation_mode = responseDoc["vacation_mode"] | false;
    
  } else {
    Serial.print("Erreur envoi : ");
    Serial.println(httpResponseCode);
  }
  
  http.end();
  state.last_send = millis();
  state.needs_immediate_send = false;
}

// ============================================================================
// SETUP
// ============================================================================

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("=== Système d'Arrosage ESP32 ===");
  Serial.print("Nœud ID: ");
  Serial.println(node_id);
  
  // Configuration des pins
  pinMode(PUMP_RELAY_PIN, OUTPUT);
  digitalWrite(PUMP_RELAY_PIN, LOW);  // Pompe éteinte par défaut
  pinMode(SOIL_MOISTURE_PIN, INPUT);
  pinMode(BATTERY_PIN, INPUT);
  pinMode(SOLAR_CHARGE_PIN, INPUT);
  
  // Initialisation DHT11
  dht.begin();
  
  // Connexion WiFi
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  
  Serial.print("Connexion WiFi");
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.print("WiFi connecté : ");
    Serial.println(WiFi.localIP());
    
    // Enregistrer le nœud
    delay(1000);
    registerNode();
  } else {
    Serial.println();
    Serial.println("Échec connexion WiFi");
  }
  
  // Lecture initiale des capteurs
  readSensors();
  
  Serial.println("Système prêt");
}

// ============================================================================
// LECTURE DES CAPTEURS
// ============================================================================

void readSensors() {
  // Lecture DHT11
  float temp = dht.readTemperature();
  float hum = dht.readHumidity();
  
  if (!isnan(temp)) {
    state.temperature = temp;
  }
  if (!isnan(hum)) {
    state.air_humidity = hum;
  }
  
  // Lecture humidité du sol
  state.soil_moisture = readSoilMoisture();
  
  // Lecture batterie et charge solaire
  state.battery_level = readBatteryLevel();
  state.solar_charging = isSolarCharging();
  
  // Vérifier si envoi immédiat nécessaire
  if (shouldSendImmediately()) {
    state.needs_immediate_send = true;
  }
  
  Serial.print("Temp: ");
  Serial.print(state.temperature);
  Serial.print("°C, Hum: ");
  Serial.print(state.air_humidity);
  Serial.print("%, Sol: ");
  Serial.print(state.soil_moisture);
  Serial.print("%, Bat: ");
  Serial.print(state.battery_level);
  Serial.print("%, Solaire: ");
  Serial.println(state.solar_charging ? "Oui" : "Non");
  
  state.last_sensor_read = millis();
}

// ============================================================================
// LOOP PRINCIPAL
// ============================================================================

void loop() {
  unsigned long now = millis();
  
  // Lecture périodique des capteurs
  if (now - state.last_sensor_read >= SENSOR_READ_INTERVAL) {
    readSensors();
  }
  
  // Vérifier la pompe
  checkPumpTimeout();
  
  // Envoi périodique ou immédiat
  bool should_send = false;
  if (shouldSendImmediately()) {
    should_send = true;
  } else if (now - state.last_send >= SEND_INTERVAL) {
    should_send = true;
  }
  
  if (should_send && WiFi.status() == WL_CONNECTED) {
    sendDataToHub();
  }
  
  // Gestion de l'économie d'énergie (mode deep sleep si batterie faible)
  if (state.battery_level < 20 && !state.solar_charging && !state.pump_running) {
    // Mode économie d'énergie : deep sleep pendant 5 minutes
    Serial.println("Mode économie d'énergie activé");
    esp_sleep_enable_timer_wakeup(300000000);  // 5 minutes en microsecondes
    esp_deep_sleep_start();
  }
  
  delay(1000);  // Délai de base
}

