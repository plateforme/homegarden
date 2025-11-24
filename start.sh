#!/bin/bash
# Script de démarrage pour le système d'arrosage automatique

# Couleurs pour les messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Système d'Arrosage Automatique ===${NC}"
echo ""

# Vérifier si on est dans le bon répertoire
if [ ! -f "app.py" ]; then
    echo -e "${RED}Erreur : app.py non trouvé${NC}"
    echo "Assurez-vous d'être dans le répertoire /home/gregory/homegarden"
    exit 1
fi

# Vérifier si Python 3 est installé
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Erreur : Python 3 n'est pas installé${NC}"
    exit 1
fi

# Vérifier si le processus tourne déjà
if pgrep -f "app.py" > /dev/null; then
    echo -e "${YELLOW}Attention : Le système semble déjà être en cours d'exécution${NC}"
    echo "PID du processus : $(pgrep -f 'app.py')"
    read -p "Voulez-vous l'arrêter et redémarrer ? (o/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Oo]$ ]]; then
        echo "Arrêt du processus existant..."
        pkill -f "app.py"
        sleep 2
    else
        echo "Démarrage annulé"
        exit 0
    fi
fi

# Demander le mode de démarrage
echo ""
echo "Choisissez le mode de démarrage :"
echo "1) Mode normal (session active)"
echo "2) Mode arrière-plan avec nohup"
echo "3) Mode screen (recommandé)"
echo ""
read -p "Votre choix (1-3) : " choice

# Configuration du PYTHONPATH pour utiliser les modules locaux
export PYTHONPATH="$(pwd)/lib/python3.11/site-packages:$PYTHONPATH"

case $choice in
    1)
        echo -e "${GREEN}Démarrage en mode normal...${NC}"
        echo "Appuyez sur Ctrl+C pour arrêter"
        python3 app.py
        ;;
    2)
        echo -e "${GREEN}Démarrage en arrière-plan avec nohup...${NC}"
        nohup python3 app.py > app.log 2>&1 &
        PID=$!
        echo "Processus démarré avec PID : $PID"
        echo "Logs disponibles dans : app.log"
        echo "Pour voir les logs : tail -f app.log"
        echo "Pour arrêter : kill $PID"
        ;;
    3)
        if ! command -v screen &> /dev/null; then
            echo -e "${YELLOW}Screen n'est pas installé. Installation...${NC}"
            sudo apt-get update && sudo apt-get install screen -y
        fi
        echo -e "${GREEN}Démarrage avec screen...${NC}"
        screen -dmS arrosage bash -c "export PYTHONPATH='$(pwd)/lib/python3.11/site-packages:\$PYTHONPATH' && python3 app.py"
        echo "Session screen créée : arrosage"
        echo "Pour voir la session : screen -r arrosage"
        echo "Pour détacher : Ctrl+A puis D"
        ;;
    *)
        echo -e "${RED}Choix invalide${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}✓ Système démarré avec succès !${NC}"
echo ""
echo "Interface web disponible sur : http://$(hostname -I | awk '{print $1}'):5000"
echo "ou http://localhost:5000"


