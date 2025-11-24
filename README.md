# 🌱 Système d'Arrosage Automatique

Système d'arrosage automatique pour Raspberry Pi avec interface web Flask.

## 🚀 Démarrage Rapide

### Via SSH

```bash
# Se connecter au Raspberry Pi
ssh pi@votre_adresse_ip

# Aller dans le dossier du projet
cd /home/gregory/homegarden

# Lancer le système (choisissez une méthode)
./start.sh                    # Script interactif (recommandé)
python3 app.py                # Mode simple
nohup python3 app.py > app.log 2>&1 &  # Mode arrière-plan
```

### Scripts Utiles

```bash
./start.sh    # Démarrer le système (menu interactif)
./stop.sh     # Arrêter le système
./status.sh   # Vérifier le statut du système
```

## 📖 Documentation Complète

Consultez le **[GUIDE_DEMARRAGE.md](GUIDE_DEMARRAGE.md)** pour :
- Instructions détaillées
- Méthodes de démarrage (simple, arrière-plan, screen)
- Configuration
- Dépannage
- Démarrage automatique au boot

## 🌐 Interface Web

Une fois le système démarré, accédez à l'interface web :

```
http://votre_adresse_ip:5000
```

## 📋 Fonctionnalités

- ✅ Surveillance automatique de l'humidité du sol
- ✅ Contrôle automatique de la pompe d'arrosage
- ✅ Mesure de température et humidité de l'air (DHT11)
- ✅ Interface web en temps réel
- ✅ Historique des arrosages
- ✅ Graphiques de données
- ✅ Configuration du seuil d'humidité

## 🔧 Matériel Requis

- Raspberry Pi
- Capteur d'humidité du sol (via ADS1115)
- Capteur DHT11 (température/humidité air)
- Pompe d'arrosage (relais sur GPIO 18)
- Connexions I2C pour ADS1115

## 📦 Installation des Dépendances

```bash
pip3 install -r requirements.txt
```

## ⚙️ Configuration

Le seuil d'humidité peut être modifié :
- Via l'interface web : `http://IP:5000/configuration`
- Via le fichier `config.json`

## 📝 Logs

Les données sont enregistrées dans :
- `arrosage_log.csv` : Historique des arrosages
- `temp_humidity_log.csv` : Température et humidité de l'air
- `soil_moisture_log.csv` : Humidité du sol
- `app.log` : Logs du système (si lancé avec nohup)

## 🆘 Aide

Pour plus d'informations, consultez le **[GUIDE_DEMARRAGE.md](GUIDE_DEMARRAGE.md)**.


