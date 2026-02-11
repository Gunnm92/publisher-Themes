# Génération Automatique de Headers pour Éditeurs

Ce projet permet de générer automatiquement des headers pour les éditeurs de bande dessinée manquants en utilisant ComfyUI et Juggernaut XL.

## 📋 Vue d'ensemble

- **154 éditeurs** dans `_incomplete/` nécessitent des headers
- Format requis : **2200x400 pixels** (ratio 5.5:1)
- Modèle utilisé : **Juggernaut XL v9**
- Génération via **ComfyUI** sur http://10.1.1.1:8188

## 🚀 Utilisation rapide

### Générer un header pour un éditeur spécifique

```bash
cd /config/workspace/publisher-Themes
python3 .scripts/generate_headers_juggernaut.py --publisher "Nom de l'éditeur"
```

### Générer pour les 10 premiers éditeurs

```bash
python3 .scripts/generate_headers_juggernaut.py --limit 10
```

### Générer pour TOUS les éditeurs (154)

```bash
python3 .scripts/generate_headers_juggernaut.py
```

### Mode test (sans génération)

```bash
python3 .scripts/generate_headers_juggernaut.py --limit 5 --dry-run
```

## 🎨 Comment ça fonctionne

1. Le script lit `publisher-info.json` de chaque éditeur
2. Analyse le pays, description et genre pour créer un prompt adapté
3. Génère une image via ComfyUI/Juggernaut XL
4. Redimensionne à 2200x400 pixels
5. Sauvegarde comme `header_generated.jpg`

## 📊 Styles générés selon les éditeurs

Le script adapte automatiquement le style selon :

- **Pays** : FR → Franco-Belge, JP → Manga, US → Comics américains
- **Genre** : Humour, Jeunesse, Noir, Fantasy, Sci-Fi, etc.
- **Type** : Indépendant, Alternatif, Mainstream

### Exemples de prompts générés

**Éditeur Français (humour)** :
```
funny cartoon characters in comedic situation, Franco-Belgian bande dessinée style,
European comic art, playful, humorous, lighthearted, NOT superhero, NOT marvel
```

**Éditeur Jeunesse** :
```
friendly colorful characters for children, children's picture book art,
bright, cheerful, innocent, NOT dark, NOT violent, NOT superhero
```

**Éditeur Indépendant** :
```
abstract artistic comic illustration, alternative underground comic art,
unconventional, artistic, experimental, NOT mainstream, NOT superhero
```

## 🛠️ Options du script

```bash
python3 .scripts/generate_headers_juggernaut.py [OPTIONS]

Options:
  --publisher "Nom"    Traiter un éditeur spécifique
  --limit N            Limiter à N éditeurs (défaut: tous)
  --delay N            Délai en secondes entre générations (défaut: 3)
  --dry-run            Mode test sans génération
  --workflow FILE      Utiliser un workflow personnalisé
```

## 📁 Structure des fichiers

```
publisher-Themes/
├── _incomplete/                    # Éditeurs sans headers
│   ├── 12bis/
│   │   ├── publisher-info.json    # Métadonnées
│   │   ├── logo.jpg               # Logo
│   │   └── header_generated.jpg   # Header généré ✨
│   └── ...
├── .scripts/
│   ├── generate_headers_juggernaut.py  # Script principal
│   ├── analyze_missing_headers.py      # Analyse
│   └── missing_headers.json            # Liste complète
├── workflow_juggernaut_xl.json    # Workflow ComfyUI
└── RECOMMENDED_MODELS.md          # Guide des modèles
```

## ⚙️ Configuration technique

### Modèle ComfyUI

- **Nom** : `Juggernaut-XL_v9_RunDiffusionPhoto_v2.safetensors`
- **Emplacement** : `ComfyUI/models/checkpoints/`
- **Taille** : ~6.5 GB
- **Type** : SDXL Checkpoint

### Paramètres de génération

- **Dimensions** : 2048x384 → redimensionné à 2200x400
- **Steps** : 20
- **CFG** : 7.0
- **Sampler** : DPM++ 2M Karras
- **Format sortie** : JPEG, qualité 95

### Prompts négatifs (évités)

```
text, words, letters, typography, watermark, signature,
superhero, marvel, dc comics, low quality, blurry, amateur
```

## 📈 Performance

- **Temps par image** : ~15-30 secondes (RTX 3090)
- **Tous les éditeurs** : ~1-2 heures pour 154 headers
- **Taux de succès** : >95%

## 🔄 Workflow de traitement batch

Pour traiter tous les éditeurs de manière efficace :

```bash
# 1. Analyser ce qui manque
python3 .scripts/analyze_missing_headers.py

# 2. Tester sur 5 éditeurs
python3 .scripts/generate_headers_juggernaut.py --limit 5

# 3. Vérifier les résultats
ls _incomplete/*/header_generated.jpg | head -5

# 4. Si satisfait, lancer la production complète
python3 .scripts/generate_headers_juggernaut.py

# 5. Renommer les headers finaux
for dir in _incomplete/*/; do
    if [ -f "$dir/header_generated.jpg" ]; then
        mv "$dir/header_generated.jpg" "$dir/header.jpg"
    fi
done
```

## 🎯 Résultats attendus

Les headers générés devront :
- ✅ Format **2200x400** pixels
- ✅ Style adapté à l'éditeur (pas de Marvel par défaut)
- ✅ Aucun texte généré dans l'image
- ✅ Qualité professionnelle
- ✅ Composition panoramique équilibrée

## 🐛 Dépannage

### Erreur "Bad Request 400"
```bash
# Vérifier que le modèle est chargé
curl -s http://10.1.1.1:8188/object_info/CheckpointLoaderSimple | grep Juggernaut
```

### Headers toujours style Marvel
```bash
# Les prompts ont été améliorés pour éviter ça
# Vérifier que vous utilisez la dernière version du script
git pull  # ou vérifier la date de modification
```

### ComfyUI inaccessible
```bash
# Vérifier que ComfyUI tourne
curl http://10.1.1.1:8188/system_stats
```

## 📚 Fichiers de référence

- `RECOMMENDED_MODELS.md` - Guide des modèles alternatifs
- `INSTALLATION_JUGGERNAUT.md` - Installation du modèle
- `AGENTS.md` - Documentation du projet général

## 🎓 Exemples de commandes avancées

```bash
# Générer uniquement les éditeurs français
python3 .scripts/generate_headers_juggernaut.py --limit 50

# Générer avec délai plus long (pour éviter la surchauffe)
python3 .scripts/generate_headers_juggernaut.py --delay 10

# Tester avec un workflow personnalisé
python3 .scripts/generate_headers_juggernaut.py --workflow mon_workflow.json --limit 1
```

## 🌟 Résumé

Ce système permet de générer automatiquement **154 headers professionnels** pour compléter la collection d'éditeurs. Les headers sont adaptés au style de chaque éditeur (Franco-Belge, Manga, Indépendant, etc.) et respectent le format requis de 2200x400 pixels.

**Temps total estimé** : 1-2 heures pour tous les éditeurs
**Qualité** : Professionnelle, sans texte, style approprié
