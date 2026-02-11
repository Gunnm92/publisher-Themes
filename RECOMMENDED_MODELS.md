# Modèles Recommandés pour Génération de Headers

## Pour headers de bande dessinée sans texte

### Option 1: SDXL (Stable Diffusion XL) - RECOMMANDÉ
**Modèle:** `sd_xl_base_1.0.safetensors`
- **Taille:** ~6.9 GB
- **URL:** https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/blob/main/sd_xl_base_1.0.safetensors
- **Avantages:**
  - Excellent pour illustrations professionnelles
  - Très peu de texte généré involontairement
  - Comprend bien les prompts artistiques
  - Résolution native 1024x1024 (excellent pour banners)
- **Installation:** Télécharger dans `ComfyUI/models/checkpoints/`

### Option 2: Flux.1 Dev/Schnell - TRÈS RECOMMANDÉ
**Modèle:** `flux1-dev.safetensors` ou `flux1-schnell.safetensors`
- **Taille:** ~23 GB (dev) ou ~23 GB (schnell)
- **URL:** https://huggingface.co/black-forest-labs/FLUX.1-dev
- **Avantages:**
  - Modèle le plus récent et performant
  - Qualité exceptionnelle pour art conceptuel
  - Pas de texte généré
  - Excellent pour scènes artistiques complexes
- **Note:** Schnell = plus rapide, Dev = meilleure qualité

### Option 3: Juggernaut XL - RECOMMANDÉ POUR BD
**Modèle:** `juggernautXL_v9Rdphoto2Lightning.safetensors`
- **Taille:** ~6.5 GB
- **URL:** https://civitai.com/models/133005/juggernaut-xl
- **Avantages:**
  - Spécialement bon pour illustrations artistiques
  - Style semi-réaliste parfait pour BD
  - Pas de texte
  - Compatible SDXL

### Option 4: DreamShaper XL - BON COMPROMIS
**Modèle:** `dreamshaperXL_v21TurboDPMSDE.safetensors`
- **Taille:** ~6.5 GB
- **URL:** https://civitai.com/models/112902/dreamshaper-xl
- **Avantages:**
  - Rapide (turbo version)
  - Style artistique polyvalent
  - Excellent pour headers

## Modèles spécialisés BD/Comics

### Comic Diffusion XL
**Modèle:** `comicDiffusion_v2.safetensors`
- **URL:** https://civitai.com/models/44960/comic-diffusion
- **Style:** Comic book américain classique

### Mistoon Anime XL
**Modèle:** `mistoonAnime_v30.safetensors`
- **URL:** https://civitai.com/models/24149/mistoonanime
- **Style:** BD/Manga fusion, excellent pour éditeurs franco-belges

## Installation

```bash
# Aller dans le dossier des modèles ComfyUI
cd /path/to/ComfyUI/models/checkpoints/

# Télécharger avec wget (exemple SDXL)
wget https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors

# Ou avec curl
curl -L -o sd_xl_base_1.0.safetensors "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors"
```

## Mon Choix #1: Flux.1 Schnell
Pour ce projet, je recommande **Flux.1 Schnell** car:
- Qualité exceptionnelle pour art conceptuel
- Rapide malgré la taille
- Zéro texte généré
- Parfait pour scènes artistiques de BD

## Mon Choix #2 (si GPU limité): Juggernaut XL
Alternative plus légère avec excellents résultats pour BD.
