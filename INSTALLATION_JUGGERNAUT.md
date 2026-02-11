# Installation de Juggernaut XL pour ComfyUI

## Méthode 1 : Téléchargement direct avec wget/curl

```bash
# Naviguez vers le dossier des checkpoints ComfyUI
cd /path/to/ComfyUI/models/checkpoints/

# Téléchargez avec wget
wget --content-disposition "https://civitai.com/api/download/models/456194" -O juggernautXL_v9Rdphoto2Lightning.safetensors

# OU avec curl
curl -L "https://civitai.com/api/download/models/456194" -o juggernautXL_v9Rdphoto2Lightning.safetensors
```

## Méthode 2 : Via le navigateur

1. Allez sur https://civitai.com/models/133005/juggernaut-xl
2. Connectez-vous (compte Civitai requis - gratuit)
3. Cliquez sur le bouton "Download" pour la version **v9 Rdphoto2 Lightning**
4. Déplacez le fichier `.safetensors` téléchargé vers :
   ```
   ComfyUI/models/checkpoints/juggernautXL_v9Rdphoto2Lightning.safetensors
   ```

## Méthode 3 : ComfyUI Manager (si installé)

1. Dans ComfyUI, cliquez sur "Manager"
2. Allez dans "Install Models"
3. Recherchez "Juggernaut XL"
4. Cliquez sur "Install"

## Vérification

Une fois téléchargé, le modèle devrait apparaître dans :
- ComfyUI → Node "CheckpointLoaderSimple" → Liste déroulante "ckpt_name"

## Emplacement du dossier ComfyUI

Emplacements courants :
- Linux : `/opt/ComfyUI/` ou `~/ComfyUI/`
- Docker : `/config/ComfyUI/` ou volume monté
- Windows : `C:\ComfyUI\`

Pour trouver votre installation ComfyUI, vous pouvez exécuter :
```bash
# Linux/Mac
find ~ -name "ComfyUI" -type d 2>/dev/null
# ou
ps aux | grep comfy
```

## Taille et spécifications

- **Nom du fichier :** `juggernautXL_v9Rdphoto2Lightning.safetensors`
- **Taille :** ~6.46 GB
- **Type :** SDXL Checkpoint
- **Format :** SafeTensors

## Après installation

Une fois le modèle installé, je créerai un nouveau workflow optimisé pour Juggernaut XL qui :
- Générera des headers sans texte
- Utilisera des prompts optimisés pour illustrations de BD
- Produira des images en format banner (1536x1024)

## Alternative : Autres modèles recommandés

Si Juggernaut XL ne fonctionne pas, voici des alternatives :

### SDXL Base (officiel Stability AI)
```
https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors
```

### DreamShaper XL Turbo
```
https://civitai.com/api/download/models/351306
```

---

**Question :** Pouvez-vous me dire où se trouve votre installation ComfyUI ?
Cela m'aidera à vous donner les commandes exactes à exécuter.
