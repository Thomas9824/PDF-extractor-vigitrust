"""
API Serverless pour l'extracteur PCI DSS avec détection automatique de langue
Supports both French and English PCI DSS documents
"""
import json
import os
import tempfile
import re
import io
from typing import List, Dict, Any, Tuple
from http.server import BaseHTTPRequestHandler

# Import PyPDF2
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

# Import our language detector and extractors
from language_detector import PCILanguageDetector
from extractors import PCIRequirementsExtractorFR, PCIRequirementsExtractorEN

class PCIRequirementsExtractor:
    """Classe principale pour extraire les exigences PCI DSS avec détection automatique de langue"""

    def __init__(self, pdf_content: bytes = None, pdf_path: str = None):
        # Support both bytes content and file path for serverless compatibility
        self.pdf_content = pdf_content
        self.pdf_path = pdf_path
        self.requirements = []
        self.language_detector = PCILanguageDetector()
        self.detected_language = None
        self.language_confidence = 0.0
        self.language_info = None
        self.extractor = None

    def detect_language_and_setup_extractor(self):
        """Détecte la langue du document et configure l'extracteur approprié"""
        try:
            # Détecter la langue
            self.detected_language, self.language_confidence = self.language_detector.detect_language_from_pdf(
                pdf_content=self.pdf_content, 
                pdf_path=self.pdf_path
            )
            
            # Obtenir les informations sur la langue
            self.language_info = self.language_detector.get_language_info(
                self.detected_language, 
                self.language_confidence
            )
            
            # Configurer l'extracteur approprié
            if self.detected_language == "french":
                self.extractor = PCIRequirementsExtractorFR(
                    pdf_content=self.pdf_content, 
                    pdf_path=self.pdf_path
                )
            elif self.detected_language == "english":
                self.extractor = PCIRequirementsExtractorEN(
                    pdf_content=self.pdf_content, 
                    pdf_path=self.pdf_path
                )
            else:
                # Fallback vers français si langue inconnue
                print(f"Langue inconnue détectée (confiance: {self.language_confidence:.2f}), utilisation de l'extracteur français par défaut")
                self.extractor = PCIRequirementsExtractorFR(
                    pdf_content=self.pdf_content, 
                    pdf_path=self.pdf_path
                )
                
            print(f"Langue détectée: {self.language_info['name']} (confiance: {self.language_info['confidence_percentage']})")
            print(f"Extracteur utilisé: {self.language_info['extractor']}")
            
        except Exception as e:
            print(f"Erreur lors de la détection de langue: {e}")
            # Fallback vers français
            self.detected_language = "unknown"
            self.language_confidence = 0.0
            self.language_info = self.language_detector.get_language_info("unknown", 0.0)
            self.extractor = PCIRequirementsExtractorFR(
                pdf_content=self.pdf_content, 
                pdf_path=self.pdf_path
            )

    def extract_all_requirements(self) -> List[Dict[str, Any]]:
        """Extrait toutes les exigences du PDF avec détection automatique de langue"""
        if not PyPDF2:
            raise ImportError("PyPDF2 n'est pas disponible")
        
        # Détecter la langue et configurer l'extracteur
        self.detect_language_and_setup_extractor()
        
        if not self.extractor:
            print("Erreur: Aucun extracteur configuré")
            return []
        
        # Utiliser l'extracteur approprié
        self.requirements = self.extractor.extract_all_requirements()
        return self.requirements
    
    def get_language_info(self) -> Dict[str, Any]:
        """Retourne les informations sur la langue détectée"""
        return self.language_info or {}
    
    def get_extraction_summary(self) -> Dict[str, Any]:
        """Retourne un résumé de l'extraction avec informations de langue"""
        summary = {
            'total': len(self.requirements),
            'with_tests': len([req for req in self.requirements if req['tests']]),
            'with_guidance': len([req for req in self.requirements if req['guidance']]),
            'total_tests': sum(len(req['tests']) for req in self.requirements),
            'language_detection': self.get_language_info()
        }
        return summary


# Handler pour Vercel
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Vérifier le chemin
            if self.path != '/api/extract':
                self.send_error(404, "Not Found")
                return

            # Lire le contenu de la requête
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_error(400, "No content provided")
                return

            # Lire les données
            post_data = self.rfile.read(content_length)
            
            # Parser les données multipart/form-data
            boundary = None
            content_type = self.headers.get('Content-Type', '')
            if 'boundary=' in content_type:
                boundary = content_type.split('boundary=')[1].encode()
            
            if not boundary:
                self.send_error(400, "No boundary found in Content-Type")
                return

            # Extraire le fichier PDF des données multipart
            pdf_content = self._extract_pdf_from_multipart(post_data, boundary)
            
            if not pdf_content:
                # Fallback : utiliser le PDF de démo français
                demo_pdf_path = os.path.join(os.path.dirname(__file__), '..', 'PCI-DSS-v4-0-1-SAQ-D-Merchant-FR.pdf')
                if os.path.exists(demo_pdf_path):
                    extractor = PCIRequirementsExtractor(pdf_path=demo_pdf_path)
                else:
                    self.send_error(400, "No PDF file provided and no demo file found")
                    return
            else:
                extractor = PCIRequirementsExtractor(pdf_content=pdf_content)

            # Extraction des exigences avec détection automatique de langue
            requirements = extractor.extract_all_requirements()
            
            if not requirements:
                self.send_error(400, "No PCI requirements found in PDF")
                return

            # Tri des exigences
            def sort_key(req):
                parts = [int(x) for x in req['req_num'].split('.')]
                while len(parts) < 4:
                    parts.append(0)
                return parts
            
            sorted_requirements = sorted(requirements, key=sort_key)
            
            # Préparer la réponse avec informations de langue
            response_data = {
                'success': True,
                'requirements': sorted_requirements,
                'summary': extractor.get_extraction_summary()
            }

            # Envoyer la réponse
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            
            response_json = json.dumps(response_data, ensure_ascii=False, indent=2)
            self.wfile.write(response_json.encode('utf-8'))

        except Exception as e:
            print(f"Error in handler: {str(e)}")
            self.send_error(500, f"Server error: {str(e)}")

    def do_OPTIONS(self):
        """Handle preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def _extract_pdf_from_multipart(self, data: bytes, boundary: bytes) -> bytes:
        """Extrait le contenu PDF des données multipart/form-data"""
        try:
            # Diviser par boundary
            parts = data.split(b'--' + boundary)
            
            for part in parts:
                if b'Content-Disposition: form-data' in part and b'filename=' in part:
                    # Trouver le début du contenu du fichier
                    header_end = part.find(b'\r\n\r\n')
                    if header_end != -1:
                        file_content = part[header_end + 4:]
                        # Supprimer le CRLF final s'il existe
                        if file_content.endswith(b'\r\n'):
                            file_content = file_content[:-2]
                        return file_content
            
            return None
        except Exception as e:
            print(f"Error extracting PDF from multipart data: {e}")
            return None