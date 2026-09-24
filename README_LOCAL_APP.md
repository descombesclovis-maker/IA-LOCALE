# LocalVisionAI — interface locale

Cette interface est la surcouche façon ChatGPT de ComfyUI.

## Ce qui est en place

- interface sombre, épurée, conversationnelle ;
- sélection des workflows dans la barre latérale ;
- champ de prompt unique ;
- ajout d'une image d'entrée ;
- génération via ComfyUI local ;
- galerie des résultats ;
- import d'un nouveau workflow JSON directement depuis l'interface ;
- les workflows importés sont conservés dans `workflows/imported/` ;
- détection automatique des workflows du dépôt ;
- conversion des workflows ComfyUI UI vers le format API en utilisant `/object_info`.

## Workflows actuellement présents dans IA-LOCALE

1. Text to image flux.json — Image
2. text to image sdxl.json — Image
3. Image to video wan.json — Vidéo
4. Text to Video LTX (très lourd).json — Vidéo lourd

Je ne vois actuellement aucun workflow explicitement identifié comme Retouche / Img2Img / Inpaint dans le dépôt. L'interface est toutefois prête à l'accueillir : importe simplement son JSON depuis **＋ Importer un workflow**.

## Démarrage

1. ComfyUI doit être lancé sur `127.0.0.1:8188`.
2. Double-clique sur **START_LOCAL_AI.bat**.
3. L'interface est disponible sur `http://127.0.0.1:3000`.

Le serveur LocalVisionAI n'utilise aucune API cloud pour les générations.

## Ajouter un modèle

Dans ComfyUI : crée ou ouvre un workflow, sauvegarde/exporte son JSON, puis dans LocalVisionAI :

**＋ Importer un workflow → sélectionner le JSON**

Le nouveau workflow apparaît dans la barre latérale sans modification du code.

### Point technique important

Un workflow ComfyUI enregistré dans l'interface n'est pas directement le même objet que le prompt API attendu par `POST /prompt`. Le convertisseur de LocalVisionAI récupère les définitions des nœuds avec `GET /object_info`, reconstruit les liens et mappe les widgets avant l'envoi.

Les workflows utilisant des custom nodes ou des subgraphs très spécifiques peuvent néanmoins demander une adaptation si ComfyUI retourne une validation d'erreur. L'application ne masque pas cette erreur.
