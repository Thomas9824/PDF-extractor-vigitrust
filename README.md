# PCI DSS Requirements Extractor

Un extracteur automatique d'exigences PCI DSS qui utilise Python pour le parsing et Next.js pour l'interface utilisateur.

## Architecture

- **Backend**: API Flask en Python utilisant le script `testv5.py` pour l'extraction
- **Frontend**: Application Next.js avec interface de téléchargement
- **Déploiement**: Configuré pour Vercel avec support Python

## Installation et utilisation en local

### Prérequis
- Python 3.9+
- Node.js 18+
- npm ou pnpm

### Backend Python

```bash
# Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'API Flask
python api/extract.py
```

L'API sera disponible sur `http://localhost:8000`

### Frontend Next.js

```bash
cd pci-extractor-web

# Installer les dépendances
npm install

# Lancer le serveur de développement
npm run dev
```

L'interface sera disponible sur `http://localhost:3001`

## Tests en local

1. Lancer d'abord l'API Python : `python api/extract.py`
2. Lancer le frontend Next.js : `cd pci-extractor-web && npm run dev`
3. Ouvrir `http://localhost:3001` dans votre navigateur
4. Télécharger un PDF PCI DSS et tester l'extraction

## Déploiement sur Vercel

### Préparation
1. Créer un compte sur [Vercel](https://vercel.com)
2. Connecter votre dépôt GitHub à Vercel
3. S'assurer que le projet contient tous les fichiers nécessaires

### Configuration automatique
Le projet est configuré avec `vercel.json` pour un déploiement automatique :

- **Frontend** : Application Next.js dans `/pci-extractor-web`  
- **Backend** : API Python serverless dans `/api/index.py`
- **Routing** : `/api/extract` → fonction Python

### Déploiement manuel
```bash
# Installer Vercel CLI
npm install -g vercel

# Se connecter à Vercel
vercel login

# Déployer depuis la racine du projet
vercel --prod
```

### Variables d'environnement
Aucune variable d'environnement n'est requise pour ce projet.

### Structure de déploiement
```
├── api/
│   └── index.py          # Fonction serverless Python
├── pci-extractor-web/    # Application Next.js
├── requirements.txt      # Dépendances Python
└── vercel.json          # Configuration Vercel
```

## Structure du projet

```
├── api/
│   └── extract.py          # API Flask pour l'extraction
├── pci-extractor-web/      # Frontend Next.js
│   └── src/app/page.tsx    # Interface utilisateur
├── testv5.py               # Script Python d'extraction
├── requirements.txt        # Dépendances Python
├── Dockerfile             # Configuration Docker
└── vercel.json            # Configuration Vercel
```

## Fonctionnalités

- Upload de fichiers PDF PCI DSS
- Extraction automatique des exigences, tests et conseils
- Téléchargement automatique du JSON des résultats
- Interface utilisateur moderne et responsive
- API REST pour l'intégration

## Script Python original

Le script `testv5.py` peut aussi être utilisé en standalone :

```bash
python testv5.py
```

Il lit directement le fichier `PCI-DSS-v4-0-1-SAQ-D-Merchant-FR.pdf` et génère `pci_requirements_v5.json`.
