"""
Détecteur de langue pour les documents PCI DSS
Language detector for PCI DSS documents
"""
import re
import PyPDF2
import io
from typing import Tuple

class PCILanguageDetector:
    """Détecte automatiquement la langue d'un document PCI DSS"""
    
    def __init__(self):
        # Mots-clés français spécifiques aux documents PCI DSS
        self.french_keywords = [
            "exigences", "conseils", "examiner", "observer", "interroger", 
            "vérifier", "inspecter", "applicabilité", "en place", "pas en place",
            "non applicable", "non testé", "cocher une réponse", "tous droits réservés",
            "octobre", "saq d de pci dss", "notes d'applicabilité"
        ]
        
        # Mots-clés anglais spécifiques aux documents PCI DSS
        self.english_keywords = [
            "requirements", "guidance", "examine", "observe", "interview",
            "verify", "inspect", "applicability", "in place", "not in place", 
            "not applicable", "not tested", "check one response", "all rights reserved",
            "october", "pci dss saq d", "applicability notes"
        ]
    
    def detect_language_from_content(self, text: str) -> Tuple[str, float]:
        """
        Détecte la langue à partir du contenu textuel
        Returns: (language, confidence_score)
        """
        text_lower = text.lower()
        
        # Compter les occurrences des mots-clés
        french_score = sum(1 for keyword in self.french_keywords if keyword in text_lower)
        english_score = sum(1 for keyword in self.english_keywords if keyword in text_lower)
        
        total_keywords = len(self.french_keywords) + len(self.english_keywords)
        total_found = french_score + english_score
        
        if total_found == 0:
            return "unknown", 0.0
        
        if french_score > english_score:
            confidence = french_score / len(self.french_keywords)
            return "french", min(confidence, 1.0)
        elif english_score > french_score:
            confidence = english_score / len(self.english_keywords)
            return "english", min(confidence, 1.0)
        else:
            return "unknown", 0.5
    
    def detect_language_from_pdf(self, pdf_content: bytes = None, pdf_path: str = None) -> Tuple[str, float]:
        """
        Détecte la langue à partir d'un fichier PDF
        Returns: (language, confidence_score)
        """
        try:
            if pdf_content:
                pdf_file = io.BytesIO(pdf_content)
            elif pdf_path:
                pdf_file = open(pdf_path, 'rb')
            else:
                return "unknown", 0.0
            
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            # Lire les premières pages pour la détection (pages 1-5 et 15-20)
            sample_text = ""
            
            # Pages de titre et introduction
            for page_num in range(min(5, len(pdf_reader.pages))):
                page = pdf_reader.pages[page_num]
                sample_text += page.extract_text() + "\n"
            
            # Pages de contenu principal
            start_page = 15
            end_page = min(20, len(pdf_reader.pages))
            for page_num in range(start_page, end_page):
                if page_num < len(pdf_reader.pages):
                    page = pdf_reader.pages[page_num]
                    sample_text += page.extract_text() + "\n"
            
            if pdf_content:
                pdf_file.close()
            elif pdf_path:
                pdf_file.close()
            
            return self.detect_language_from_content(sample_text)
            
        except Exception as e:
            print(f"Erreur lors de la détection de langue: {e}")
            return "unknown", 0.0
    
    def get_language_info(self, language: str, confidence: float) -> dict:
        """Retourne des informations détaillées sur la langue détectée"""
        language_info = {
            "french": {
                "code": "fr",
                "name": "Français",
                "name_en": "French",
                "extractor": "testv5.py (French)",
                "markers": {
                    "test_indicators": ['• Examiner', '• Observer', '• Interroger', '• Vérifier', '• Inspecter'],
                    "applicability_marker": "Notes d'Applicabilité",
                    "guidance_marker": "Conseils"
                }
            },
            "english": {
                "code": "en", 
                "name": "English",
                "name_en": "English",
                "extractor": "testv5_EN.py (English)",
                "markers": {
                    "test_indicators": ['• Examine', '• Observe', '• Interview', '• Verify', '• Inspect'],
                    "applicability_marker": "Applicability Notes",
                    "guidance_marker": "Guidance"
                }
            },
            "unknown": {
                "code": "unknown",
                "name": "Langue inconnue",
                "name_en": "Unknown language", 
                "extractor": "Default (French)",
                "markers": {
                    "test_indicators": ['• Examiner', '• Observer', '• Interroger', '• Vérifier', '• Inspecter'],
                    "applicability_marker": "Notes d'Applicabilité",
                    "guidance_marker": "Conseils"
                }
            }
        }
        
        info = language_info.get(language, language_info["unknown"])
        info["confidence"] = confidence
        info["confidence_percentage"] = f"{confidence * 100:.1f}%"
        
        return info