# Guide de déploiement sur Vercel

## Étapes rapides

### 1. Préparer le dépôt
```bash
# S'assurer que tous les fichiers sont committés
git add .
git commit -m "Ready for Vercel deployment"
git push origin main
```

### 2. Déployer sur Vercel

#### Option A : Interface web (Recommandé)
1. Aller sur [vercel.com](https://vercel.com)
2. Se connecter avec GitHub
3. Cliquer "New Project"
4. Importer le dépôt `PDF-extractor-vigitrust`
5. Laisser les paramètres par défaut
6. Cliquer "Deploy"

#### Option B : CLI
```bash
# Installer Vercel CLI
npm install -g vercel

# Se connecter
vercel login

# Déployer depuis la racine du projet
vercel --prod
```

### 3. Configuration automatique

Vercel détectera automatiquement :
- ✅ **Frontend Next.js** dans `/pci-extractor-web`
- ✅ **API Python** dans `/api/extract.py`
- ✅ **Dépendances** via `requirements.txt` et `package.json`
- ✅ **Routing** via `vercel.json`

### 4. Test

Une fois déployé :
1. L'URL sera fournie (ex: `https://pdf-extractor-vigitrust.vercel.app`)
2. Tester l'upload de PDF
3. Vérifier l'extraction des exigences PCI DSS

### 5. Mises à jour

Chaque push sur `main` redéploiera automatiquement l'application.

---

## Structure finale du projet

```
├── api/
│   └── extract.py          # API Python serverless
├── pci-extractor-web/      # Frontend Next.js
├── requirements.txt        # Dépendances Python
├── vercel.json            # Configuration Vercel
└── PCI-DSS-v4-0-1-SAQ-D-Merchant-FR.pdf  # PDF de test
```

## Fonctionnalités

- ✅ Upload de PDF PCI DSS
- ✅ Extraction automatique des exigences
- ✅ Téléchargement JSON des résultats
- ✅ Interface responsive moderne
- ✅ API REST serverless