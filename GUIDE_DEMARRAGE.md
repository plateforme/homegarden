# 🌱 Guide de Démarrage - Système d'Arrosage Automatique

Ce guide vous explique comment lancer votre système d'arrosage automatique une fois connecté en SSH à votre Raspberry Pi.

## 📋 Prérequis

Avant de commencer, assurez-vous que :
- ✅ Votre Raspberry Pi est allumé et connecté au réseau
- ✅ Vous avez accès SSH à votre Raspberry Pi
- ✅ Les capteurs sont correctement branchés (ADS1115, DHT11, pompe)
- ✅ Python 3 est installé sur votre Raspberry Pi

## 🔌 Connexion SSH

### Étape 1 : Se connecter au Raspberry Pi

```bash
ssh pi@votre_adresse_ip
# ou
ssh utilisateur@votre_adresse_ip
```

Remplacez `votre_adresse_ip` par l'adresse IP de votre Raspberry Pi (ex: `192.168.1.100`).

### Étape 2 : Naviguer vers le dossier du projet

```bash
cd /home/gregory/homegarden
```

## 🚀 Démarrage du Système

### Option 1 : Démarrage Simple (Session Active)

Pour tester rapidement le système :

```bash
python3 app.py
```

Le système va démarrer et afficher des messages de statut. Vous verrez :
- L'initialisation des capteurs
- Les lectures d'humidité toutes les 5 secondes
- Les actions de la pompe

**Note** : Cette méthode arrête le système si vous fermez la session SSH.

### Option 2 : Démarrage en Arrière-plan (Recommandé)

Pour que le système continue de fonctionner même après avoir fermé SSH :

```bash
# Démarrer en arrière-plan
nohup python3 app.py > app.log 2>&1 &

# Voir le numéro du processus (PID)
echo $!
```

**Explication** :
- `nohup` : Permet au processus de continuer après la déconnexion SSH
- `> app.log` : Redirige la sortie vers un fichier de log
- `2>&1` : Redirige aussi les erreurs vers le même fichier
- `&` : Lance le processus en arrière-plan

### Option 3 : Utiliser screen (Alternative Recommandée)

`screen` est très pratique pour gérer des sessions longues :

```bash
# Installer screen si nécessaire
sudo apt-get update
sudo apt-get install screen -y

# Créer une nouvelle session screen
screen -S arrosage

# Lancer le programme
python3 app.py

# Détacher la session : Appuyez sur Ctrl+A puis D
# Pour revenir à la session : screen -r arrosage
```

**Commandes screen utiles** :
- `screen -S nom_session` : Créer une nouvelle session nommée
- `screen -r nom_session` : Reconnecter à une session
- `screen -ls` : Lister toutes les sessions
- `Ctrl+A puis D` : Détacher la session (le programme continue)
- `Ctrl+A puis K puis Y` : Tuer la session actuelle

## 📊 Vérifier que le Système Fonctionne

### Vérifier les logs en temps réel

```bash
# Si vous avez utilisé nohup
tail -f app.log

# Si vous avez utilisé screen
screen -r arrosage
```

### Vérifier que le processus tourne

```bash
ps aux | grep app.py
```

Vous devriez voir une ligne avec `python3 app.py`.

### Accéder à l'interface web

Ouvrez un navigateur sur votre ordinateur et allez à :

```
http://votre_adresse_ip:5000
```

Exemple : `http://192.168.1.100:5000`

Vous devriez voir l'interface web avec :
- Les données des capteurs en temps réel
- L'historique des arrosages
- Les graphiques de température et d'humidité
- La page de configuration

## 🛑 Arrêter le Système

### Si lancé en arrière-plan (nohup)

```bash
# Trouver le processus
ps aux | grep app.py

# Arrêter le processus (remplacez PID par le numéro trouvé)
kill PID

# Ou forcer l'arrêt si nécessaire
kill -9 PID
```

### Si lancé avec screen

```bash
# Se reconnecter à la session
screen -r arrosage

# Arrêter avec Ctrl+C dans la session
# Puis quitter screen avec : exit
```

### Arrêt propre

Pour un arrêt propre qui éteint aussi la pompe :

```bash
# Trouver le PID
ps aux | grep app.py | grep -v grep | awk '{print $2}'

# Arrêter proprement
kill -SIGINT $(ps aux | grep app.py | grep -v grep | awk '{print $2}')
```

## 🔄 Redémarrer le Système

```bash
# Arrêter d'abord (voir section précédente)
# Puis relancer avec votre méthode préférée
python3 app.py
# ou
nohup python3 app.py > app.log 2>&1 &
# ou
screen -S arrosage
python3 app.py
```

## 📝 Vérifier les Fichiers de Log

Les données sont enregistrées dans plusieurs fichiers CSV :

```bash
# Voir l'historique des arrosages
cat arrosage_log.csv

# Voir l'historique de température/humidité
tail -20 temp_humidity_log.csv

# Voir l'historique d'humidité du sol
tail -20 soil_moisture_log.csv

# Voir la configuration
cat config.json
```

## ⚙️ Configuration

### Modifier le seuil d'humidité

**Méthode 1 : Via l'interface web**
1. Allez sur `http://votre_adresse_ip:5000/configuration`
2. Modifiez le seuil d'humidité
3. Cliquez sur "Enregistrer"

**Méthode 2 : Via le fichier de configuration**

```bash
nano config.json
```

Modifiez la valeur `humidity_threshold` (entre 0 et 100), puis sauvegardez avec `Ctrl+X`, puis `Y`, puis `Entrée`.

Le système rechargera automatiquement la configuration au prochain cycle de vérification.

## 🔧 Dépannage

### Le système ne démarre pas

```bash
# Vérifier les erreurs Python
python3 app.py

# Vérifier que les bibliothèques sont installées
pip3 list | grep -E "flask|adafruit|RPi"
```

### Les capteurs ne fonctionnent pas

```bash
# Vérifier que I2C est activé
sudo raspi-config
# Allez dans "Interface Options" > "I2C" > "Enable"

# Vérifier la connexion I2C
i2cdetect -y 1
```

### Le port 5000 est déjà utilisé

```bash
# Vérifier quel processus utilise le port 5000
sudo lsof -i :5000

# Arrêter le processus ou modifier le port dans app.py
```

### La pompe ne s'allume pas

1. Vérifiez les connexions GPIO
2. Vérifiez que le GPIO 18 est bien configuré
3. Testez manuellement :
```python
python3
>>> import RPi.GPIO as GPIO
>>> GPIO.setmode(GPIO.BCM)
>>> GPIO.setup(18, GPIO.OUT)
>>> GPIO.output(18, GPIO.LOW)  # Allumer
>>> GPIO.output(18, GPIO.HIGH)  # Éteindre
```

## 📦 Installation des Dépendances (si nécessaire)

Si vous avez des erreurs d'import, installez les dépendances :

```bash
# Installer pip si nécessaire
sudo apt-get install python3-pip -y

# Installer les bibliothèques nécessaires
pip3 install flask
pip3 install adafruit-circuitpython-dht
pip3 install adafruit-circuitpython-ads1x15
pip3 install RPi.GPIO

# Ou créer un fichier requirements.txt et installer tout d'un coup
pip3 install -r requirements.txt
```

## 🎯 Démarrage Automatique au Boot (Optionnel)

Pour que le système démarre automatiquement au démarrage du Raspberry Pi :

### Méthode 1 : systemd (Recommandé)

Créez un fichier de service :

```bash
sudo nano /etc/systemd/system/arrosage.service
```

Ajoutez ce contenu :

```ini
[Unit]
Description=Système d'arrosage automatique
After=network.target

[Service]
Type=simple
User=gregory
WorkingDirectory=/home/gregory/homegarden
ExecStart=/usr/bin/python3 /home/gregory/homegarden/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Activez et démarrez le service :

```bash
# Recharger systemd
sudo systemctl daemon-reload

# Activer le service (démarrage automatique)
sudo systemctl enable arrosage.service

# Démarrer le service
sudo systemctl start arrosage.service

# Vérifier le statut
sudo systemctl status arrosage.service

# Voir les logs
sudo journalctl -u arrosage.service -f
```

**Commandes utiles** :
- `sudo systemctl stop arrosage.service` : Arrêter
- `sudo systemctl restart arrosage.service` : Redémarrer
- `sudo systemctl disable arrosage.service` : Désactiver le démarrage automatique

### Méthode 2 : rc.local (Alternative)

```bash
sudo nano /etc/rc.local
```

Ajoutez avant `exit 0` :

```bash
cd /home/gregory/homegarden
nohup python3 app.py > /home/gregory/homegarden/app.log 2>&1 &
```

## 📞 Commandes Rapides de Référence

```bash
# Démarrer
python3 app.py

# Démarrer en arrière-plan
nohup python3 app.py > app.log 2>&1 &

# Voir les logs
tail -f app.log

# Vérifier si ça tourne
ps aux | grep app.py

# Arrêter
kill $(ps aux | grep app.py | grep -v grep | awk '{print $2}')

# Accéder à l'interface web
# http://votre_ip:5000
```

## ✅ Checklist de Démarrage

- [ ] Connecté en SSH au Raspberry Pi
- [ ] Navigué vers `/home/gregory/homegarden`
- [ ] Vérifié que les capteurs sont branchés
- [ ] Lancé le programme (`python3 app.py`)
- [ ] Vérifié les messages de démarrage
- [ ] Accédé à l'interface web (`http://IP:5000`)
- [ ] Vérifié que les données s'affichent correctement
- [ ] Configuré le seuil d'humidité si nécessaire

---

**Besoin d'aide ?** Vérifiez les logs avec `tail -f app.log` ou consultez la section Dépannage ci-dessus.


