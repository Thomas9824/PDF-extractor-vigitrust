# PCI DSS Extractor - Détection Automatique de Langue

## 🌍 Nouvelle Fonctionnalité : Détection Automatique de Langue

Le projet PCI DSS Extractor supporte maintenant la **détection automatique de langue** pour les documents PCI DSS en français et en anglais.

### ✨ Fonctionnalités

- **Détection automatique** : Le système détecte automatiquement si votre PDF est en français ou en anglais
- **Extracteurs spécialisés** : Utilise l'extracteur approprié selon la langue détectée
- **Interface améliorée** : Affiche les informations de langue dans l'interface web
- **Noms de fichiers intelligents** : Les fichiers téléchargés incluent le code de langue

### 🔧 Architecture

#### Nouveaux Fichiers

1. **`api/language_detector.py`** - Détecteur de langue PCI DSS
2. **`api/extractors.py`** - Extracteurs spécialisés français et anglais
3. **`testv5_EN.py`** - Version anglaise de l'extracteur standalone

#### Classes Principales

- `PCILanguageDetector` : Détecte la langue du document
- `PCIRequirementsExtractorFR` : Extracteur pour documents français
- `PCIRequirementsExtractorEN` : Extracteur pour documents anglais

### 🎯 Comment ça fonctionne

1. **Upload du PDF** : L'utilisateur upload un PDF PCI DSS
2. **Détection de langue** : Le système analyse le contenu pour détecter la langue
3. **Sélection de l'extracteur** : Choix automatique de l'extracteur approprié
4. **Extraction** : Traitement avec les règles spécifiques à la langue
5. **Résultats** : Affichage avec informations de langue et confiance

### 📊 Informations de Langue Affichées

```json
{
  "language_detection": {
    "code": "fr",
    "name": "Français", 
    "name_en": "French",
    "extractor": "testv5.py (French)",
    "confidence": 0.765,
    "confidence_percentage": "76.5%"
  }
}
```

### 🔍 Mots-clés de Détection

#### Français
- "exigences", "conseils", "examiner", "observer", "interroger"
- "vérifier", "inspecter", "applicabilité", "en place", "pas en place"
- "non applicable", "non testé", "notes d'applicabilité"

#### Anglais  
- "requirements", "guidance", "examine", "observe", "interview"
- "verify", "inspect", "applicability", "in place", "not in place"
- "not applicable", "not tested", "applicability notes"

### 📁 Noms de Fichiers

Les fichiers téléchargés incluent maintenant le code de langue :

- `pci_requirements_fr_2024-01-15T10-30-45.json` (français)
- `pci_requirements_en_2024-01-15T10-30-45.json` (anglais)
- `pci_requirements_2024-01-15T10-30-45.json` (langue inconnue)

### 🚀 Utilisation

#### Interface Web
1. Uploadez votre PDF PCI DSS (français ou anglais)
2. Cliquez sur "Extract Requirements"
3. Visualisez les informations de langue détectée
4. Téléchargez les résultats avec le nom de fichier approprié

#### API
```bash
curl -X POST http://localhost:8000/api/extract \
  -F "file=@your-pci-document.pdf"
```

#### Script Python
```python
from api.extract import PCIRequirementsExtractor

extractor = PCIRequirementsExtractor(pdf_path="document.pdf")
requirements = extractor.extract_all_requirements()
language_info = extractor.get_language_info()
summary = extractor.get_extraction_summary()
```

### 🔄 Fallback

Si la langue ne peut pas être déterminée avec certitude :
- **Fallback automatique** vers l'extracteur français
- **Confiance affichée** pour transparence
- **Fonctionnement garanti** même avec documents non standard

### 🧪 Tests

Exécutez le script de test :
```bash
python tmp_rovodev_test_language_detection.py
```

### 📈 Améliorations Futures

- Support d'autres langues (espagnol, allemand, etc.)
- Amélioration de la précision de détection
- Détection basée sur les métadonnées PDF
- Interface multilingue

---

**Note** : Cette fonctionnalité est rétrocompatible. Les anciens PDFs français continueront de fonctionner normalement.