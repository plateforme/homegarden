#!/usr/bin/env python3
"""
Script de test pour déclencher la pompe pendant une durée configurable
Version améliorée avec meilleure gestion des erreurs et validation
"""
import RPi.GPIO as GPIO
import time
import sys
import signal
from typing import Optional

# ============================================
# CONFIGURATION
# ============================================
PUMP_GPIO_PIN = 18  # Pin GPIO pour la pompe (BCM)
TEST_DURATION_SECONDS = 15  # Durée du test en secondes
INITIAL_STABILIZATION_DELAY = 0.5  # Délai de stabilisation initial (secondes)
GPIO_MODE = GPIO.BCM  # Mode de numérotation GPIO

# États de la pompe (logique inverse : HIGH = éteinte, LOW = allumée)
PUMP_OFF = GPIO.HIGH
PUMP_ON = GPIO.LOW

# ============================================
# VARIABLES GLOBALES
# ============================================
pump_initialized = False
interrupted = False

# ============================================
# FONCTIONS UTILITAIRES
# ============================================

# ============================================
# COULEURS ANSI
# ============================================
class Colors:
    GREEN = '\033[0;32m'
    BRIGHT_GREEN = '\033[1;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    BRIGHT_RED = '\033[1;31m'
    BLUE = '\033[0;34m'
    BRIGHT_BLUE = '\033[1;34m'
    CYAN = '\033[0;36m'
    BRIGHT_CYAN = '\033[1;36m'
    MAGENTA = '\033[0;35m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    NC = '\033[0m'  # No Color

def print_header():
    """Affiche un header stylisé"""
    print(f"{Colors.BRIGHT_CYAN}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║                                                            ║")
    print(f"║{Colors.BOLD}{Colors.YELLOW}          💧  TEST DE LA POMPE D'ARROSAGE  💧{Colors.NC}{Colors.BRIGHT_CYAN}          ║")
    print("║                                                            ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"{Colors.NC}")

def print_box(title: str, content: str, color: str = Colors.BRIGHT_BLUE):
    """Affiche une boîte d'information"""
    print(f"{color}")
    print(f"┌─ {title} ────────────────────────────────────────────────┐")
    print(f"│{Colors.NC} {content}{color}")
    print("└───────────────────────────────────────────────────────────┘")
    print(f"{Colors.NC}")

def signal_handler(signum, frame):
    """Gère les signaux d'interruption (Ctrl+C)"""
    global interrupted
    interrupted = True
    print(f"\n\n{Colors.BRIGHT_RED}⚠️  Interruption détectée (Ctrl+C){Colors.NC}")
    emergency_stop()

def emergency_stop():
    """Arrêt d'urgence de la pompe"""
    global pump_initialized
    try:
        if pump_initialized:
            GPIO.output(PUMP_GPIO_PIN, PUMP_OFF)
            print(f"{Colors.BRIGHT_RED}🛑 POMPE ÉTEINTE (arrêt d'urgence){Colors.NC}")
    except Exception as e:
        print(f"{Colors.RED}❌ ERREUR lors de l'arrêt d'urgence : {e}{Colors.NC}")

def validate_gpio_pin(pin: int) -> bool:
    """Valide que le pin GPIO est valide pour le mode BCM"""
    # Pins GPIO valides pour BCM (Raspberry Pi)
    valid_pins = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27]
    return pin in valid_pins

def setup_gpio() -> bool:
    """Configure les GPIO et valide la configuration"""
    global pump_initialized
    
    try:
        print(f"{Colors.CYAN}🔧 Configuration des GPIO...{Colors.NC}")
        
        # Vérifier que le pin est valide
        if not validate_gpio_pin(PUMP_GPIO_PIN):
            print_box("❌ ERREUR", f"Pin GPIO {PUMP_GPIO_PIN} invalide pour le mode BCM", Colors.BRIGHT_RED)
            return False
        
        # Configuration des GPIO
        GPIO.setmode(GPIO_MODE)
        GPIO.setup(PUMP_GPIO_PIN, GPIO.OUT)
        
        # S'assurer que la pompe est éteinte au départ
        GPIO.output(PUMP_GPIO_PIN, PUMP_OFF)
        time.sleep(INITIAL_STABILIZATION_DELAY)
        
        pump_initialized = True
        print(f"{Colors.BRIGHT_GREEN}✓ GPIO configuré avec succès{Colors.NC}")
        return True
        
    except RuntimeError as e:
        print_box("❌ ERREUR", f"Problème d'accès aux GPIO : {e}", Colors.BRIGHT_RED)
        print(f"{Colors.YELLOW}💡 Vérifiez que vous exécutez le script avec les permissions appropriées{Colors.NC}")
        print(f"{Colors.DIM}   (peut nécessiter sudo ou appartenir au groupe gpio){Colors.NC}")
        return False
    except Exception as e:
        print_box("❌ ERREUR", f"Erreur inattendue lors de la configuration GPIO : {e}", Colors.BRIGHT_RED)
        return False

def cleanup_gpio():
    """Nettoie les ressources GPIO"""
    global pump_initialized
    
    try:
        if pump_initialized:
            # S'assurer que la pompe est éteinte avant le nettoyage
            GPIO.output(PUMP_GPIO_PIN, PUMP_OFF)
            time.sleep(0.1)
            GPIO.cleanup()
            pump_initialized = False
    except Exception as e:
        print(f"{Colors.YELLOW}⚠️  AVERTISSEMENT : Erreur lors du nettoyage GPIO : {e}{Colors.NC}")

def run_test(duration: int) -> bool:
    """Exécute le test de la pompe"""
    global interrupted
    
    try:
        print(f"\n{Colors.BRIGHT_CYAN}{'='*60}{Colors.NC}")
        print(f"{Colors.BRIGHT_BLUE}💧 Démarrage de la pompe...{Colors.NC}")
        GPIO.output(PUMP_GPIO_PIN, PUMP_ON)
        print(f"{Colors.BRIGHT_GREEN}✅ POMPE ALLUMÉE{Colors.NC}")
        print(f"{Colors.BRIGHT_CYAN}{'='*60}{Colors.NC}\n")
        
        # Attendre la durée spécifiée avec compte à rebours et barre de progression
        print(f"{Colors.CYAN}⏱️  Test en cours ({duration} secondes)...{Colors.NC}\n")
        
        for i in range(duration, 0, -1):
            if interrupted:
                return False
            
            # Barre de progression
            progress = duration - i + 1
            percentage = int((progress / duration) * 100)
            filled = int((progress / duration) * 50)
            empty = 50 - filled
            
            # Compte à rebours avec barre de progression
            bar = '█' * filled + '░' * empty
            print(f"\r{Colors.CYAN}[{bar}] {percentage:3d}%{Colors.NC} {Colors.YELLOW}⏳ {i:2d}s restantes{Colors.NC}", end='', flush=True)
            time.sleep(1)
        
        print()  # Nouvelle ligne après le compte à rebours
        
        if not interrupted:
            print(f"\n{Colors.BRIGHT_CYAN}{'='*60}{Colors.NC}")
            print(f"{Colors.BRIGHT_BLUE}🛑 Arrêt de la pompe...{Colors.NC}")
            GPIO.output(PUMP_GPIO_PIN, PUMP_OFF)
            print(f"{Colors.BRIGHT_GREEN}✅ POMPE ÉTEINTE{Colors.NC}")
            print(f"{Colors.BRIGHT_CYAN}{'='*60}{Colors.NC}")
            return True
        
        return False
        
    except Exception as e:
        print(f"\n{Colors.BRIGHT_RED}❌ ERREUR pendant le test : {e}{Colors.NC}")
        emergency_stop()
        return False

# ============================================
# SCRIPT PRINCIPAL
# ============================================

def main():
    """Fonction principale"""
    global interrupted
    
    # Enregistrer le gestionnaire de signaux
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Afficher le header
    print_header()
    print()
    
    # Afficher la configuration
    print_box("⚙️  CONFIGURATION", "", Colors.BRIGHT_BLUE)
    config_info = f"""
  📍 Pin GPIO      : {Colors.BRIGHT_CYAN}{PUMP_GPIO_PIN}{Colors.NC} (BCM)
  ⏱️  Durée du test : {Colors.BRIGHT_CYAN}{TEST_DURATION_SECONDS}{Colors.NC} secondes
  🔧 Mode GPIO     : {Colors.BRIGHT_CYAN}BCM{Colors.NC}
  🔌 État initial  : {Colors.BRIGHT_GREEN}POMPE ÉTEINTE{Colors.NC}
"""
    print(config_info)
    
    # Configuration des GPIO
    if not setup_gpio():
        print()
        print_box("❌ ÉCHEC", "La configuration GPIO a échoué", Colors.BRIGHT_RED)
        sys.exit(1)
    
    print()
    
    try:
        # Exécuter le test
        success = run_test(TEST_DURATION_SECONDS)
        
        print()
        if success and not interrupted:
            print_box("✅ SUCCÈS", "Le test s'est terminé avec succès ! 🎉", Colors.BRIGHT_GREEN)
        elif interrupted:
            print_box("⚠️  INTERROMPU", "Le test a été interrompu par l'utilisateur", Colors.YELLOW)
        else:
            print_box("❌ ERREUR", "Le test s'est terminé avec des erreurs", Colors.BRIGHT_RED)
            
    except KeyboardInterrupt:
        # Géré par le signal_handler, mais au cas où
        interrupted = True
        emergency_stop()
        print_box("⚠️  INTERROMPU", "Le test a été interrompu", Colors.YELLOW)
        
    except Exception as e:
        print_box("❌ ERREUR CRITIQUE", f"Une erreur critique s'est produite : {e}", Colors.BRIGHT_RED)
        emergency_stop()
        sys.exit(1)
        
    finally:
        # Nettoyage des GPIO
        print()
        print(f"{Colors.CYAN}🧹 Nettoyage des GPIO...{Colors.NC}")
        cleanup_gpio()
        print(f"{Colors.BRIGHT_GREEN}✓ Nettoyage terminé{Colors.NC}")
        print()

if __name__ == "__main__":
    main()


