#!/bin/bash
# Script pour vérifier le statut du système

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Statut du Système d'Arrosage ===${NC}"
echo ""

# Vérifier le processus app.py
PID=$(pgrep -f "app.py")

if [ -z "$PID" ]; then
    echo -e "${RED}✗ Le système n'est PAS en cours d'exécution${NC}"
else
    echo -e "${GREEN}✓ Le système est en cours d'exécution${NC}"
    echo "   PID : $PID"
    echo "   Uptime : $(ps -p $PID -o etime= | tr -d ' ')"
    echo "   Mémoire : $(ps -p $PID -o rss= | awk '{printf "%.1f MB", $1/1024}')"
fi

echo ""

# Vérifier les sessions screen
if screen -list | grep -q "arrosage"; then
    echo -e "${GREEN}✓ Session screen 'arrosage' active${NC}"
    screen -list | grep arrosage
else
    echo -e "${YELLOW}○ Aucune session screen trouvée${NC}"
fi

echo ""

# Vérifier les fichiers de log
echo "Fichiers de log :"
if [ -f "app.log" ]; then
    echo -e "  ${GREEN}✓ app.log existe${NC} ($(wc -l < app.log) lignes)"
    echo "    Dernière ligne : $(tail -1 app.log | cut -c1-80)..."
else
    echo -e "  ${YELLOW}○ app.log n'existe pas${NC}"
fi

if [ -f "arrosage_log.csv" ]; then
    echo -e "  ${GREEN}✓ arrosage_log.csv existe${NC} ($(wc -l < arrosage_log.csv) entrées)"
else
    echo -e "  ${YELLOW}○ arrosage_log.csv n'existe pas${NC}"
fi

echo ""

# Vérifier le port 5000
if netstat -tuln 2>/dev/null | grep -q ":5000" || ss -tuln 2>/dev/null | grep -q ":5000"; then
    echo -e "${GREEN}✓ Le serveur web écoute sur le port 5000${NC}"
    IP=$(hostname -I | awk '{print $1}')
    echo "   URL : http://$IP:5000"
else
    echo -e "${RED}✗ Le serveur web n'écoute PAS sur le port 5000${NC}"
fi

echo ""

# Vérifier la configuration
if [ -f "config.json" ]; then
    echo -e "${GREEN}✓ Configuration trouvée${NC}"
    echo "   Seuil d'humidité : $(grep -o '"humidity_threshold": [0-9]*' config.json | grep -o '[0-9]*')%"
else
    echo -e "${YELLOW}○ Fichier de configuration non trouvé${NC}"
fi

echo ""


