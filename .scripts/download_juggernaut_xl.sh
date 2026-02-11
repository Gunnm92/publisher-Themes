#!/bin/bash
# Script pour télécharger Juggernaut XL pour ComfyUI

# Couleurs pour output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Téléchargement de Juggernaut XL${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Trouver le dossier ComfyUI
COMFYUI_DIR=""

# Chercher dans les emplacements communs
if [ -d "$HOME/ComfyUI" ]; then
    COMFYUI_DIR="$HOME/ComfyUI"
elif [ -d "/opt/ComfyUI" ]; then
    COMFYUI_DIR="/opt/ComfyUI"
elif [ -d "/config/ComfyUI" ]; then
    COMFYUI_DIR="/config/ComfyUI"
else
    echo -e "${RED}Erreur: Dossier ComfyUI non trouvé${NC}"
    echo "Veuillez spécifier le chemin manuellement:"
    read -p "Chemin vers ComfyUI: " COMFYUI_DIR
fi

CHECKPOINT_DIR="$COMFYUI_DIR/models/checkpoints"

echo -e "${GREEN}✓ Dossier ComfyUI trouvé: $COMFYUI_DIR${NC}"
echo -e "${GREEN}✓ Dossier checkpoints: $CHECKPOINT_DIR${NC}\n"

# Créer le dossier s'il n'existe pas
mkdir -p "$CHECKPOINT_DIR"

# URL du modèle Juggernaut XL (version 9)
MODEL_URL="https://civitai.com/api/download/models/456194"
MODEL_NAME="juggernautXL_v9Rdphoto2Lightning.safetensors"
MODEL_PATH="$CHECKPOINT_DIR/$MODEL_NAME"

# Vérifier si le modèle existe déjà
if [ -f "$MODEL_PATH" ]; then
    echo -e "${BLUE}Le modèle existe déjà: $MODEL_PATH${NC}"
    read -p "Voulez-vous le retélécharger? (y/N): " response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}✓ Utilisation du modèle existant${NC}"
        exit 0
    fi
    rm "$MODEL_PATH"
fi

echo -e "${BLUE}Téléchargement de Juggernaut XL v9...${NC}"
echo -e "${BLUE}Taille: ~6.5 GB - Cela peut prendre du temps${NC}\n"

# Télécharger avec wget (avec barre de progression)
if command -v wget &> /dev/null; then
    wget --continue --progress=bar:force:noscroll \
         --content-disposition \
         -O "$MODEL_PATH" \
         "$MODEL_URL"
# Alternative avec curl
elif command -v curl &> /dev/null; then
    curl -L --progress-bar \
         -o "$MODEL_PATH" \
         "$MODEL_URL"
else
    echo -e "${RED}Erreur: wget ou curl requis pour télécharger${NC}"
    exit 1
fi

# Vérifier si le téléchargement a réussi
if [ -f "$MODEL_PATH" ]; then
    FILE_SIZE=$(du -h "$MODEL_PATH" | cut -f1)
    echo -e "\n${GREEN}✓ Téléchargement réussi!${NC}"
    echo -e "${GREEN}✓ Modèle sauvegardé: $MODEL_PATH${NC}"
    echo -e "${GREEN}✓ Taille: $FILE_SIZE${NC}\n"

    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Installation terminée avec succès!${NC}"
    echo -e "${BLUE}========================================${NC}\n"

    echo "Le modèle Juggernaut XL est maintenant disponible dans ComfyUI."
    echo "Vous pouvez le sélectionner dans le node 'CheckpointLoaderSimple'."
else
    echo -e "\n${RED}✗ Erreur lors du téléchargement${NC}"
    exit 1
fi
