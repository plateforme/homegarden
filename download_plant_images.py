#!/usr/bin/env python3
"""
Script pour télécharger les images des plantes depuis Wikipedia/Wikimedia Commons
"""
import requests
import os
import json
from urllib.parse import quote

# Mapping des noms de plantes vers leurs noms Wikipedia (avec alternatives)
PLANT_MAPPING = {
    "Monstera deliciosa": ["Monstera_deliciosa", "Faux_philodendron"],
    "Ficus benjamina": ["Ficus_benjamina"],
    "Epipremnum aureum": ["Epipremnum_aureum"],
    "Dracaena marginata": ["Dracaena_marginata", "Dracaena", "Dracena_marginata"],
    "Sansevieria trifasciata": ["Sansevieria_trifasciata"],
    "Spathiphyllum spp.": ["Spathiphyllum"],
    "Chlorophytum comosum": ["Chlorophytum_comosum"],
    "Zamioculcas zamiifolia": ["Zamioculcas_zamiifolia"],
    "Aloe vera": ["Aloe_vera"]
}

def get_wikipedia_image_url(plant_name_wiki):
    """Récupère l'URL de l'image principale depuis Wikipedia"""
    try:
        # API Wikipedia pour obtenir les images
        api_url = "https://fr.wikipedia.org/w/api.php"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        params = {
            "action": "query",
            "format": "json",
            "titles": plant_name_wiki,
            "prop": "pageimages",
            "pithumbsize": "500",
            "piprop": "thumbnail"
        }
        
        response = requests.get(api_url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        
        if not response.text:
            print(f"  Réponse vide pour {plant_name_wiki}")
            return None
            
        data = response.json()
        
        pages = data.get("query", {}).get("pages", {})
        for page_id, page_data in pages.items():
            if "thumbnail" in page_data:
                return page_data["thumbnail"]["source"]
        
        # Si pas d'image principale, chercher dans les images de la page
        params = {
            "action": "query",
            "format": "json",
            "titles": plant_name_wiki,
            "prop": "images",
            "imlimit": "10"
        }
        
        response = requests.get(api_url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        pages = data.get("query", {}).get("pages", {})
        for page_id, page_data in pages.items():
            images = page_data.get("images", [])
            for img in images[:5]:  # Limiter à 5 images
                img_title = img.get("title", "")
                if not img_title.startswith("File:"):
                    continue
                    
                # Obtenir l'URL de l'image
                img_params = {
                    "action": "query",
                    "format": "json",
                    "titles": img_title,
                    "prop": "imageinfo",
                    "iiprop": "url"
                }
                try:
                    img_response = requests.get(api_url, params=img_params, headers=headers, timeout=15)
                    img_response.raise_for_status()
                    img_data = img_response.json()
                    img_pages = img_data.get("query", {}).get("pages", {})
                    for img_page_id, img_page_data in img_pages.items():
                        if "imageinfo" in img_page_data and img_page_data["imageinfo"]:
                            # Obtenir l'URL originale (url) plutôt que thumburl
                            img_info = img_page_data["imageinfo"][0]
                            url = img_info.get("url", "")
                            if url:
                                return url
                except:
                    continue
        
        return None
    except requests.exceptions.RequestException as e:
        print(f"  Erreur réseau pour {plant_name_wiki}: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"  Erreur JSON pour {plant_name_wiki}: {e}")
        print(f"  Réponse: {response.text[:200] if 'response' in locals() else 'N/A'}")
        return None
    except Exception as e:
        print(f"  Erreur lors de la recherche d'image pour {plant_name_wiki}: {e}")
        return None

def download_image(url, filepath):
    """Télécharge une image depuis une URL"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # Si c'est une URL thumbnail, convertir en URL originale
        if "/thumb/" in url:
            # Format: https://upload.wikimedia.org/wikipedia/commons/thumb/5/53/Ficus_benjamina_San_Jos%C3%A9.jpg/500px-Ficus_benjamina_San_Jos%C3%A9.jpg
            # URL originale: https://upload.wikimedia.org/wikipedia/commons/5/53/Ficus_benjamina_San_Jos%C3%A9.jpg
            url = url.replace("/thumb/", "/").rsplit("/", 1)[0]  # Enlever le dernier segment avec "px-"
        
        response = requests.get(url, headers=headers, timeout=30, stream=True, allow_redirects=True)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return True
    except Exception as e:
        print(f"  Erreur lors du téléchargement: {e}")
        return False

def get_plant_filename(plant_name):
    """Convertit le nom de la plante en nom de fichier"""
    return plant_name.replace(" ", "_").replace(".", "").replace("/", "_")

def main():
    # Créer le dossier images s'il n'existe pas
    images_dir = "/home/gregory/homegarden/static/images"
    os.makedirs(images_dir, exist_ok=True)
    
    # Charger les plantes depuis data.json
    with open("/home/gregory/homegarden/data.json", "r") as f:
        data = json.load(f)
    
    plants = list(data["scenarios"].keys())
    
    print(f"Recherche d'images pour {len(plants)} plantes...")
    
    for plant_name in plants:
        print(f"\nTraitement de: {plant_name}")
        
        # Obtenir le(s) nom(s) Wikipedia (peut être une liste)
        wiki_names = PLANT_MAPPING.get(plant_name, [plant_name.replace(" ", "_")])
        if not isinstance(wiki_names, list):
            wiki_names = [wiki_names]
        
        # Chercher l'image en essayant chaque nom alternatif
        image_url = None
        for wiki_name in wiki_names:
            image_url = get_wikipedia_image_url(wiki_name)
            if image_url:
                break
        
        if image_url:
            # Déterminer l'extension
            ext = "jpg"
            if ".png" in image_url.lower():
                ext = "png"
            elif ".webp" in image_url.lower():
                ext = "webp"
            
            filename = get_plant_filename(plant_name)
            filepath = os.path.join(images_dir, f"{filename}.{ext}")
            
            print(f"  Image trouvée: {image_url}")
            print(f"  Téléchargement vers: {filepath}")
            
            if download_image(image_url, filepath):
                print(f"  ✓ Téléchargé avec succès")
            else:
                print(f"  ✗ Échec du téléchargement")
        else:
            print(f"  ✗ Aucune image trouvée sur Wikipedia")
    
    print("\nTerminé!")

if __name__ == "__main__":
    main()

