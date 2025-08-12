"""
API Serverless pour l'extracteur PCI DSS - Vercel Compatible
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import tempfile
import re
from typing import List, Dict, Any

# Import PyPDF2
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

class PCIRequirementsExtractor:
    """Version simplifiée pour Vercel"""

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.requirements = []
        self.test_indicators = ['• Examiner', '• Observer', '• Interroger', '• Vérifier', '• Inspecter']

    def read_pdf_content(self) -> str:
        """Lit le contenu du PDF"""
        if not PyPDF2:
            raise ImportError("PyPDF2 n'est pas disponible")
            
        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                start_page = 15
                end_page = min(129, len(pdf_reader.pages))
                
                for page_num in range(start_page, end_page):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"Erreur: {e}")
            return ""

    def clean_text(self, text: str) -> str:
        """Nettoie le texte et échappe les caractères problématiques pour JSON"""
        text = re.sub(r'SAQ D de PCI DSS v[\d.]+.*?Page \d+.*?(?:En Place|Pas en Place)', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'© 2006-\d+.*?LLC.*?Tous Droits Réservés\.', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Octobre 2024', '', text, flags=re.IGNORECASE)
        text = re.sub(r'♦\s*Se reporter.*?(?=\n)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\(Cocher une réponse.*?\)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'En Place\s+En Place avec CCW\s+Non Applicable\s+Non Testé\s+Pas en Place', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        lines = [line.strip() for line in text.splitlines()]
        return "\n".join(lines)

    def is_requirement_number(self, line: str) -> str:
        """Vérifie si c'est un numéro d'exigence"""
        pattern = r'^(\d+\.\d+(?:\.\d+)*)\s+'
        match = re.match(pattern, line.strip())
        if match:
            req_num = match.group(1)
            parts = req_num.split('.')
            if len(parts) >= 2:
                main_num = int(parts[0])
                if 1 <= main_num <= 12:
                    return req_num
        return ""

    def is_test_line(self, line: str) -> bool:
        """Vérifie si c'est une ligne de test"""
        return any(line.strip().startswith(indicator) for indicator in self.test_indicators)

    def extract_requirement_text(self, line: str, req_num: str) -> str:
        """Extrait le texte de l'exigence"""
        pattern = rf'^{re.escape(req_num)}\s+'
        return re.sub(pattern, '', line.strip())

    def parse_requirements(self, content: str) -> List[Dict[str, Any]]:
        """Parse les exigences"""
        requirements = []
        lines = content.splitlines()
        current_req = None

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            req_num = self.is_requirement_number(line)
            if req_num:
                if current_req:
                    requirements.append(current_req)
                
                current_req = {
                    'req_num': req_num,
                    'text': self.extract_requirement_text(line, req_num),
                    'tests': [],
                    'guidance': ''
                }
            elif current_req:
                if self.is_test_line(line):
                    test_text = re.sub(r'^•\s*', '', line).strip()
                    if test_text and len(test_text) > 10:
                        current_req['tests'].append(test_text)
                elif len(line) > 3:
                    if current_req['text']:
                        current_req['text'] += " " + line
                    else:
                        current_req['text'] = line

        if current_req:
            requirements.append(current_req)
        return requirements

    def _clean_for_json(self, text: str) -> str:
        """Nettoie agressivement le texte pour éviter les erreurs JSON"""
        if not text:
            return ""
        
        # Convertir en string au cas où
        text = str(text)
        
        # Supprimer tous les caractères problématiques
        # Garder seulement les caractères alphanumériques, espaces et ponctuation de base
        text = re.sub(r'[^\w\s\.\,\;\:\!\?\(\)\[\]\-\+\=\@\#\$\%\&\*\/\\\|\<\>]', ' ', text, flags=re.UNICODE)
        
        # Remplacer les retours à la ligne et tabulations
        text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        
        # Supprimer les caractères de contrôle et non-ASCII problématiques
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        # Supprimer les guillemets doubles et simples pour éviter les conflits
        text = text.replace('"', '').replace("'", "")
        
        # Normaliser les espaces multiples
        text = re.sub(r'\s+', ' ', text)
        
        # Limiter la longueur pour éviter les très longues chaînes
        if len(text) > 1000:
            text = text[:1000] + "..."
            
        return text.strip()

    def extract_all_requirements(self) -> List[Dict[str, Any]]:
        """Extrait toutes les exigences"""
        raw_text = self.read_pdf_content()
        if not raw_text:
            return []
        clean_text = self.clean_text(raw_text)
        self.requirements = self.parse_requirements(clean_text)
        
        # Nettoyer tous les textes pour JSON
        for req in self.requirements:
            req['text'] = self._clean_for_json(req['text'])
            req['guidance'] = self._clean_for_json(req['guidance'])
            req['tests'] = [self._clean_for_json(test) for test in req['tests']]
        
        return self.requirements


class handler(BaseHTTPRequestHandler):
    def _set_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_POST(self):
        try:
            # Simple handling for demo - in production, proper multipart parsing needed
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_error(400, "No content")
                return

            # Pour la démo, on utilise le PDF existant
            pdf_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'PCI-DSS-v4-0-1-SAQ-D-Merchant-FR.pdf')
            
            if not os.path.exists(pdf_path):
                self.send_error(404, "PDF de test non trouvé")
                return

            # Extraction
            extractor = PCIRequirementsExtractor(pdf_path)
            requirements = extractor.extract_all_requirements()
            
            # Tri
            def sort_key(req):
                parts = [int(x) for x in req['req_num'].split('.')]
                while len(parts) < 4:
                    parts.append(0)
                return parts
            
            sorted_requirements = sorted(requirements, key=sort_key)
            
            # Réponse
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self._set_cors_headers()
            self.end_headers()
            
            response_data = {
                'success': True,
                'requirements': sorted_requirements,
                'summary': {
                    'total': len(sorted_requirements),
                    'with_tests': len([req for req in sorted_requirements if req['tests']]),
                    'with_guidance': len([req for req in sorted_requirements if req['guidance']]),
                    'total_tests': sum(len(req['tests']) for req in sorted_requirements)
                }
            }
            
            try:
                # Utiliser json.dumps avec des paramètres très sûrs
                json_response = json.dumps(response_data, ensure_ascii=True, separators=(',', ':'), indent=None)
                self.wfile.write(json_response.encode('utf-8'))
            except Exception as json_error:
                # Si la sérialisation JSON échoue, retourner une erreur simple
                error_response = {
                    'success': False,
                    'error': f'JSON serialization failed: {str(json_error)}',
                    'requirements_count': len(sorted_requirements)
                }
                safe_json = json.dumps(error_response, ensure_ascii=True)
                self.wfile.write(safe_json.encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, str(e))