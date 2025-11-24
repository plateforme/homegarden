#!/bin/bash
# Script d'arrêt pour le système d'arrosage automatique
# Version améliorée avec meilleure gestion des erreurs et configuration

set -euo pipefail  # Arrêt en cas d'erreur, variables non définies, erreurs dans les pipes

# ============================================
# CONFIGURATION
# ============================================
APP_NAME="app.py"
SCREEN_SESSION="arrosage"
SERVICE_NAME="homegarden.service"
GRACEFUL_TIMEOUT=3      # Secondes d'attente avant arrêt forcé
FORCE_TIMEOUT=1         # Secondes d'attente après arrêt forcé
SERVICE_TIMEOUT=2       # Secondes d'attente après arrêt du service

# ============================================
# COULEURS ET FORMATAGE
# ============================================
GREEN='\033[0;32m'
BRIGHT_GREEN='\033[1;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BRIGHT_RED='\033[1;31m'
BLUE='\033[0;34m'
BRIGHT_BLUE='\033[1;34m'
CYAN='\033[0;36m'
BRIGHT_CYAN='\033[1;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'  # No Color

# ============================================
# FONCTIONS UTILITAIRES
# ============================================

# Fonction pour afficher un header stylisé
print_header() {
    echo -e "${BRIGHT_CYAN}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                                                            ║"
    echo -e "║${BOLD}${YELLOW}        🌱  ARRÊT DU SYSTÈME D'ARROSAGE  🌱${NC}${BRIGHT_CYAN}           ║"
    echo "║                                                            ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Fonction pour afficher une boîte d'information
print_box() {
    local title="$1"
    local content="$2"
    local color="${3:-$BRIGHT_BLUE}"
    echo -e "${color}"
    echo "┌─ ${title} ────────────────────────────────────────────────┐"
    echo -e "│${NC} ${content}${color}"
    echo "└───────────────────────────────────────────────────────────┘"
    echo -e "${NC}"
}

# Fonction pour afficher un message d'information
info() {
    echo -e "${BRIGHT_BLUE}ℹ${NC} ${BLUE}$1${NC}"
}

# Fonction pour afficher un message de succès
success() {
    echo -e "${BRIGHT_GREEN}✓${NC} ${GREEN}$1${NC}"
}

# Fonction pour afficher un message d'avertissement
warning() {
    echo -e "${YELLOW}⚠${NC} ${YELLOW}$1${NC}"
}

# Fonction pour afficher un message d'erreur
error() {
    echo -e "${BRIGHT_RED}✗${NC} ${RED}$1${NC}" >&2
}

# Fonction pour afficher une animation de chargement
show_spinner() {
    local pid=$1
    local message="$2"
    local spinstr='|/-\'
    local delay=0.1
    
    echo -ne "${CYAN}${message}${NC} "
    while [ "$(ps a | awk '{print $1}' | grep $pid)" ]; do
        local temp=${spinstr#?}
        printf "${CYAN}[%c]${NC}" "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b"
    done
    printf "   \b\b\b"
}

# Fonction pour afficher une barre de progression
progress_bar() {
    local current=$1
    local total=$2
    local width=50
    local percentage=$((current * 100 / total))
    local filled=$((current * width / total))
    local empty=$((width - filled))
    
    printf "\r${CYAN}["
    printf "%${filled}s" | tr ' ' '█'
    printf "%${empty}s" | tr ' ' '░'
    printf "] ${percentage}%%${NC}"
}

# Fonction pour vérifier si une commande existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Fonction pour arrêter un processus proprement
stop_process() {
    local pid=$1
    local signal=${2:-SIGINT}
    
    if ! kill -0 "$pid" 2>/dev/null; then
        return 0  # Le processus n'existe plus
    fi
    
    if kill -"$signal" "$pid" 2>/dev/null; then
        return 0
    else
        error "Impossible d'envoyer $signal au processus $pid"
        return 1
    fi
}

# Fonction pour vérifier si un processus existe
process_exists() {
    local pid=$1
    kill -0 "$pid" 2>/dev/null
}

# ============================================
# SCRIPT PRINCIPAL
# ============================================

clear
print_header
echo ""

# Vérifier les dépendances
if ! command_exists pgrep; then
    print_box "❌ ERREUR" "La commande 'pgrep' n'est pas disponible" "$BRIGHT_RED"
    exit 1
fi

# Chercher TOUS les processus app.py
echo -e "${CYAN}🔍 Recherche des processus en cours...${NC}"
PIDS=$(pgrep -f "$APP_NAME" 2>/dev/null || true)

if [ -z "$PIDS" ]; then
    print_box "ℹ️  INFORMATION" "Aucun processus $APP_NAME trouvé" "$BRIGHT_BLUE"
    
    # Vérifier si une session screen existe
    if command_exists screen && screen -list 2>/dev/null | grep -q "$SCREEN_SESSION"; then
        echo ""
        echo -e "${YELLOW}📺 Session screen '$SCREEN_SESSION' détectée${NC}"
        echo -ne "${CYAN}❓ Voulez-vous arrêter la session screen ? (o/n) ${NC}"
        read -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[OoYy]$ ]]; then
            if screen -S "$SCREEN_SESSION" -X quit 2>/dev/null; then
                success "Session screen arrêtée avec succès 🎉"
            else
                error "Impossible d'arrêter la session screen"
            fi
        else
            info "Session screen conservée"
        fi
    else
        echo ""
        success "Le système ne semble pas être en cours d'exécution ✅"
    fi
    echo ""
    exit 0
fi

# Afficher tous les processus trouvés
echo ""
print_box "📋 PROCESSUS DÉTECTÉS" "Les processus suivants vont être arrêtés :" "$YELLOW"
for PID in $PIDS; do
    if process_exists "$PID"; then
        # Afficher des informations sur le processus
        if command_exists ps; then
            PROCESS_INFO=$(ps -p "$PID" -o pid,cmd --no-headers 2>/dev/null || echo "PID $PID")
            echo -e "  ${CYAN}🔸${NC} ${DIM}$PROCESS_INFO${NC}"
        else
            echo -e "  ${CYAN}🔸${NC} PID $PID"
        fi
    fi
done
echo ""
echo -e "${BRIGHT_CYAN}⏳ Arrêt en cours...${NC}"
echo ""

# Arrêter tous les processus proprement avec SIGINT
SIGNAL_SENT=0
echo -e "${BRIGHT_BLUE}📤 Envoi du signal d'arrêt gracieux (SIGINT)...${NC}"
for PID in $PIDS; do
    if process_exists "$PID"; then
        if stop_process "$PID" "SIGINT"; then
            SIGNAL_SENT=1
            echo -e "  ${GREEN}✓${NC} Signal envoyé au processus ${CYAN}$PID${NC}"
        fi
    fi
done

if [ $SIGNAL_SENT -eq 1 ]; then
    echo ""
    echo -e "${CYAN}⏱️  Attente de ${GRACEFUL_TIMEOUT}s pour arrêt gracieux...${NC}"
    for i in $(seq $GRACEFUL_TIMEOUT -1 1); do
        printf "\r${CYAN}   ${i}s...${NC}"
        sleep 1
    done
    printf "\r${CYAN}   ✓${NC}\n"
    echo ""
fi

# Vérifier et forcer l'arrêt si nécessaire
FORCE_STOPPED=0
for PID in $PIDS; do
    if process_exists "$PID"; then
        warning "Le processus $PID n'a pas répondu, arrêt forcé... 💥"
        if stop_process "$PID" "9"; then
            FORCE_STOPPED=1
            echo -e "  ${RED}✗${NC} Processus ${CYAN}$PID${NC} arrêté de force"
        fi
    fi
done

if [ $FORCE_STOPPED -eq 1 ]; then
    sleep "$FORCE_TIMEOUT"
fi

# Vérifier et arrêter les sessions screen
if command_exists screen; then
    if screen -list 2>/dev/null | grep -q "$SCREEN_SESSION"; then
        echo -e "${BRIGHT_BLUE}📺 Arrêt de la session screen...${NC}"
        if screen -S "$SCREEN_SESSION" -X quit 2>/dev/null; then
            success "Session screen arrêtée ✅"
        else
            warning "Impossible d'arrêter la session screen (peut-être déjà arrêtée)"
        fi
        echo ""
    fi
fi

# Vérifier et arrêter le service systemd si présent
if command_exists systemctl; then
    if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
        echo -e "${BRIGHT_BLUE}⚙️  Service systemd '$SERVICE_NAME' détecté${NC}"
        echo -e "${CYAN}   Arrêt en cours...${NC}"
        if sudo systemctl stop "$SERVICE_NAME" 2>/dev/null; then
            sleep "$SERVICE_TIMEOUT"
            if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
                error "Le service n'a pas pu être arrêté ❌"
            else
                success "Service systemd arrêté avec succès ✅"
            fi
        else
            warning "Impossible d'arrêter le service (permissions insuffisantes ?) ⚠️"
        fi
        echo ""
    fi
fi

# Vérification finale
echo -e "${BRIGHT_CYAN}🔍 Vérification finale...${NC}"
REMAINING_PIDS=$(pgrep -f "$APP_NAME" 2>/dev/null || true)

if [ -z "$REMAINING_PIDS" ]; then
    echo ""
    print_box "✅ SUCCÈS" "Le système a été arrêté avec succès ! 🎉" "$BRIGHT_GREEN"
    echo ""
    exit 0
else
    echo ""
    print_box "⚠️  ATTENTION" "Des processus sont encore actifs, tentative d'arrêt forcé..." "$YELLOW"
    echo ""
    
    # Arrêt forcé de tous les processus restants
    echo -e "${BRIGHT_RED}💥 Arrêt forcé en cours...${NC}"
    if command_exists pkill; then
        if pkill -9 -f "$APP_NAME" 2>/dev/null; then
            sleep "$FORCE_TIMEOUT"
        fi
    else
        # Fallback si pkill n'est pas disponible
        for PID in $REMAINING_PIDS; do
            stop_process "$PID" "9"
        done
        sleep "$FORCE_TIMEOUT"
    fi
    
    # Vérification finale
    FINAL_CHECK=$(pgrep -f "$APP_NAME" 2>/dev/null || true)
    if [ -z "$FINAL_CHECK" ]; then
        echo ""
        print_box "✅ SUCCÈS" "Tous les processus ont été arrêtés ! 🎉" "$BRIGHT_GREEN"
        echo ""
        exit 0
    else
        echo ""
        print_box "❌ ERREUR" "Certains processus sont toujours actifs" "$BRIGHT_RED"
        echo -e "${RED}Processus restants :${NC}"
        for PID in $FINAL_CHECK; do
            if command_exists ps; then
                PROCESS_INFO=$(ps -p "$PID" -o pid,user,cmd --no-headers 2>/dev/null || echo "PID $PID")
                echo -e "  ${RED}🔴${NC} ${DIM}$PROCESS_INFO${NC}"
            else
                echo -e "  ${RED}🔴${NC} PID $PID"
            fi
        done
        echo ""
        exit 1
    fi
fi


