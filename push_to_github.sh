#!/bin/bash

# Script pour envoyer le code sur GitHub
# Usage: ./push_to_github.sh

set -e

echo "🚀 Script d'envoi sur GitHub"
echo "=============================="
echo ""

# Vérifier si Git est installé
if ! command -v git &> /dev/null; then
    echo "❌ Git n'est pas installé. Installez-le avec: sudo apt install git"
    exit 1
fi

# Vérifier si Git est déjà initialisé
if [ -d .git ]; then
    echo "ℹ️  Git est déjà initialisé"
    read -p "Voulez-vous continuer ? (o/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[OoYy]$ ]]; then
        exit 1
    fi
else
    echo "📦 Initialisation de Git..."
    git init
fi

# Demander l'URL du dépôt GitHub
echo ""
echo "📝 Entrez l'URL de votre dépôt GitHub"
echo "   Exemple: https://github.com/votre-username/homegarden.git"
read -p "URL: " GITHUB_URL

if [ -z "$GITHUB_URL" ]; then
    echo "❌ URL vide. Abandon."
    exit 1
fi

# Ajouter tous les fichiers
echo ""
echo "📁 Ajout des fichiers..."
git add .

# Vérifier s'il y a des changements à commiter
if git diff --staged --quiet; then
    echo "⚠️  Aucun changement à commiter."
else
    # Faire le commit
    echo ""
    echo "💾 Création du commit..."
    git commit -m "Initial commit: Système d'arrosage automatique"
fi

# Renommer la branche en main
echo ""
echo "🌿 Configuration de la branche principale..."
git branch -M main 2>/dev/null || true

# Ajouter le remote (supprimer l'ancien s'il existe)
echo ""
echo "🔗 Configuration du dépôt distant..."
git remote remove origin 2>/dev/null || true
git remote add origin "$GITHUB_URL"

# Envoyer sur GitHub
echo ""
echo "📤 Envoi du code sur GitHub..."
echo "   Vous devrez peut-être entrer vos identifiants GitHub"
git push -u origin main

echo ""
echo "✅ Terminé ! Votre code est maintenant sur GitHub :"
echo "   $GITHUB_URL"
echo ""

