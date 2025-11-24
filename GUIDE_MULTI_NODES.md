# 🚀 Guide de Démarrage - Architecture Multi-Nœuds

## Vue d'ensemble

Ce guide vous explique comment transformer votre système d'arrosage automatique en un système distribué avec plusieurs nœuds ESP32.

## Architecture

- **1 Hub Central (Raspberry Pi)** : Interface web, logique de décision
- **Jusqu'à 10 Nœuds ESP32** : Capteurs et pompes par zone

## Démarrage rapide

### Étape 1 : Préparer le Hub (Raspberry Pi)

Les modifications sont déjà intégrées dans `app.py`. Il suffit de redémarrer :

```bash
cd /home/gregory/homegarden
./stop.sh
./start.sh
```

Le hub expose maintenant les endpoints API :
- `POST /api/nodes/register` - Enregistrement d'un nœud
- `POST /api/nodes/{node_id}/data` - Réception des données
- `GET /api/nodes` - Liste des nœuds
- `GET /api/nodes/{node_id}` - Informations d'un nœud

### Étape 2 : Préparer un nœud ESP32

1. **Installer Arduino IDE et support ESP32**
   - Télécharger Arduino IDE
   - Ajouter l'URL du gestionnaire ESP32
   - Installer "ESP32 Dev Module"

2. **Installer les bibliothèques**
   - DHT sensor library
   - ArduinoJson

3. **Configurer le nœud**
   ```bash
   cd esp32_node
   cp config.h.example config.h
   # Éditer config.h avec vos paramètres
   ```

4. **Compiler et téléverser**
   - Ouvrir `esp32_node.ino`
   - Configurer la carte ESP32
   - Téléverser

### Étape 3 : Câblage

Voir `ARCHITECTURE_MULTI_NODES.md` pour les schémas détaillés.

**Résumé :**
- DHT11 → GPIO4
- Capteur sol → GPIO34
- Relais pompe → GPIO2
- Batterie → GPIO35 (via diviseur)
- Charge solaire → GPIO32

### Étape 4 : Test

1. Alimenter l'ESP32
2. Ouvrir le moniteur série (115200 bauds)
3. Vérifier la connexion WiFi et l'enregistrement
4. Vérifier les données dans l'interface web du hub

## Configuration recommandée

### Fréquence d'envoi

- **Normal :** Toutes les 5 minutes
- **Événements critiques :** Immédiat
- **Pompe active :** Toutes les minutes

### Alimentation solaire

- **Panneau :** 5-10W minimum
- **Batterie :** 2000-5000 mAh LiPo
- **Module de charge :** TP4056 avec protection

## Dépannage

### Le nœud ne se connecte pas

1. Vérifier SSID/mot de passe dans `config.h`
2. Vérifier la portée WiFi
3. Vérifier les logs série de l'ESP32

### Pas de communication avec le hub

1. Vérifier l'adresse IP du Raspberry Pi
2. Vérifier que le port 5000 est ouvert
3. Vérifier les logs du hub : `tail -f app.log`

### Batterie se décharge

1. Vérifier le panneau solaire
2. Réduire la fréquence d'envoi
3. Activer le mode deep sleep (déjà implémenté)

## Prochaines étapes

1. **Interface web multi-nœuds** : Afficher tous les nœuds dans le dashboard
2. **Alertes** : Notifications par email/SMS
3. **MQTT** : Communication asynchrone plus efficace
4. **Machine learning** : Optimisation automatique

## Documentation complète

- `ARCHITECTURE_MULTI_NODES.md` : Architecture détaillée
- `esp32_node/README.md` : Guide ESP32
- `esp32_node/esp32_node.ino` : Code source commenté

## Support

Pour toute question, consulter la documentation ou les logs :
- Hub : `/home/gregory/homegarden/app.log`
- ESP32 : Moniteur série Arduino IDE

