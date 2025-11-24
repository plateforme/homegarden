# 📤 Guide pour envoyer le code sur GitHub

## Étape 1 : Créer un dépôt sur GitHub

1. Allez sur [GitHub.com](https://github.com) et connectez-vous
2. Cliquez sur le bouton **"+"** en haut à droite, puis **"New repository"**
3. Donnez un nom à votre dépôt (ex: `homegarden`)
4. Choisissez **Public** ou **Private**
5. **NE COCHEZ PAS** "Initialize this repository with a README" (vous avez déjà un README)
6. Cliquez sur **"Create repository"**

## Étape 2 : Initialiser Git et envoyer le code

### Option A : Utiliser le script automatique

Exécutez simplement :
```bash
./push_to_github.sh
```

Le script vous demandera l'URL de votre dépôt GitHub.

### Option B : Commandes manuelles

Exécutez ces commandes une par une :

```bash
# 1. Initialiser Git
git init

# 2. Ajouter tous les fichiers (sauf ceux dans .gitignore)
git add .

# 3. Faire le premier commit
git commit -m "Initial commit: Système d'arrosage automatique"

# 4. Renommer la branche principale en 'main' (si nécessaire)
git branch -M main

# 5. Ajouter le dépôt GitHub comme remote
# REMPLACEZ par votre URL GitHub (ex: https://github.com/votre-username/homegarden.git)
git remote add origin https://github.com/VOTRE-USERNAME/VOTRE-REPO.git

# 6. Envoyer le code sur GitHub
git push -u origin main
```

## Étape 3 : Vérification

Allez sur votre dépôt GitHub et vérifiez que tous vos fichiers sont bien présents.

## 🔄 Mises à jour futures

Pour envoyer des modifications futures :

```bash
git add .
git commit -m "Description de vos modifications"
git push
```

## ⚠️ Notes importantes

- Le fichier `.gitignore` exclut automatiquement les fichiers sensibles (logs, données, etc.)
- Si `config.json` contient des mots de passe, vous devriez le renommer en `config.json.example` et créer un template
- Les fichiers de logs (`.log`, `.csv`) ne seront pas envoyés sur GitHub

