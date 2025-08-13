"""
API Serverless pour l'extracteur PCI DSS avec détection automatique de langue
Supports both French and English PCI DSS documents - All modules consolidated
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

# ============================================================================
# LANGUAGE DETECTOR - Consolidated from language_detector.py
# ============================================================================

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
        """Détecte la langue à partir du contenu textuel"""
        text_lower = text.lower()
        
        # Compter les occurrences des mots-clés
        french_score = sum(1 for keyword in self.french_keywords if keyword in text_lower)
        english_score = sum(1 for keyword in self.english_keywords if keyword in text_lower)
        
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
        """Détecte la langue à partir d'un fichier PDF"""
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
                "extractor": "French Extractor",
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
                "extractor": "English Extractor",
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


# ============================================================================
# EXTRACTORS - Consolidated from extractors.py
# ============================================================================

class PCIRequirementsExtractorBase:
    """Classe de base pour les extracteurs PCI DSS"""
    
    def __init__(self, pdf_content: bytes = None, pdf_path: str = None):
        self.pdf_content = pdf_content
        self.pdf_path = pdf_path
        self.requirements = []
        
        # À définir dans les classes filles
        self.test_indicators = []
        self.applicability_marker = ""
        self.guidance_marker = ""
        self.language = "unknown"

    def read_pdf_content(self) -> str:
        """Lit le contenu du PDF et retourne le texte complet"""
        if not PyPDF2:
            raise ImportError("PyPDF2 n'est pas disponible")
            
        try:
            if self.pdf_content:
                pdf_file = io.BytesIO(self.pdf_content)
            elif self.pdf_path and os.path.exists(self.pdf_path):
                pdf_file = open(self.pdf_path, 'rb')
            else:
                return ""
            
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            # Lire de la page 16 à 129 (index 15 à 128)
            start_page = 15
            end_page = min(129, len(pdf_reader.pages))
            
            for page_num in range(start_page, end_page):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"
            
            if self.pdf_content:
                pdf_file.close()
            elif self.pdf_path:
                pdf_file.close()
            
            return text
        except Exception as e:
            print(f"Erreur lors de la lecture du PDF: {e}")
            return ""

    def is_requirement_number(self, line: str) -> str:
        """Vérifie si une ligne commence par un numéro d'exigence valide"""
        pattern = r'^(\d+\.\d+(?:\.\d+)*(?:\.\d+)*)\s+'
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
        """Vérifie si une ligne est une ligne de test"""
        line_clean = line.strip()
        return any(line_clean.startswith(indicator) for indicator in self.test_indicators)

    def extract_requirement_text(self, line: str, req_num: str) -> str:
        """Extrait le texte de l'exigence en supprimant le numéro"""
        pattern = rf'^{re.escape(req_num)}\s+'
        cleaned_line = re.sub(pattern, '', line.strip())
        return cleaned_line

    # Méthodes communes à implémenter dans les classes filles
    def clean_text(self, text: str) -> str:
        raise NotImplementedError
    
    def _clean_test_text(self, text: str) -> str:
        raise NotImplementedError
    
    def _clean_guidance_text(self, text: str) -> str:
        raise NotImplementedError
    
    def _should_ignore_line(self, line: str) -> bool:
        raise NotImplementedError
    
    def _remove_response_artifacts(self, text: str) -> str:
        raise NotImplementedError

    # Méthodes communes implémentées
    def _extract_tests_from_text_line_multiline(self, line: str, current_req: Dict[str, Any], all_lines: List[str], current_index: int) -> Tuple[str, int]:
        """Extrait les tests cachés dans une ligne de texte et gère les tests multi-lignes"""
        remaining_text = line
        processed_lines = current_index
        
        for indicator in self.test_indicators:
            verb = indicator[2:]  # Enlever "• "
            pattern = rf'•\s*{re.escape(verb)}[^•]*'
            matches = list(re.finditer(pattern, remaining_text, re.IGNORECASE))
            
            for match in reversed(matches):
                test_text = match.group(0)
                test_text = re.sub(r'^•\s*', '', test_text).strip()
                
                if len(test_text) < 30 or not test_text.endswith('.'):
                    j = current_index + 1
                    while j < len(all_lines):
                        next_line = all_lines[j].strip()
                        if not next_line:
                            j += 1
                            continue
                        
                        if (self.is_requirement_number(next_line) or 
                            self.is_test_line(next_line) or
                            next_line.startswith(self.applicability_marker) or
                            next_line.startswith(self.guidance_marker) or
                            self._should_ignore_line(next_line)):
                            break
                        
                        test_text += " " + next_line
                        processed_lines = j
                        
                        if next_line.endswith('.') or next_line.endswith('!') or next_line.endswith('?'):
                            break
                        
                        j += 1
                
                test_text = self._clean_test_text(test_text)
                
                if test_text and len(test_text) > 10:
                    if test_text not in current_req['tests']:
                        current_req['tests'].append(test_text)
                    
                    remaining_text = remaining_text[:match.start()] + ' ' + remaining_text[match.end():]
        
        remaining_text = re.sub(r'\s+', ' ', remaining_text).strip()
        return remaining_text, processed_lines

    def _extract_tests_from_text_line(self, line: str, current_req: Dict[str, Any]) -> str:
        """Extrait les tests cachés dans une ligne de texte"""
        remaining_text = line
        
        for indicator in self.test_indicators:
            verb = indicator[2:]
            pattern = rf'•\s*{re.escape(verb)}[^•]*'
            matches = list(re.finditer(pattern, remaining_text, re.IGNORECASE))
            
            for match in reversed(matches):
                test_text = match.group(0)
                test_text = re.sub(r'^•\s*', '', test_text).strip()
                test_text = self._clean_test_text(test_text)
                
                if test_text and len(test_text) > 10:
                    if test_text not in current_req['tests']:
                        current_req['tests'].append(test_text)
                    
                    remaining_text = remaining_text[:match.start()] + ' ' + remaining_text[match.end():]
        
        remaining_text = re.sub(r'\s+', ' ', remaining_text).strip()
        return remaining_text

    def _is_valid_text_line(self, line: str, current_text: str) -> bool:
        """Vérifie si une ligne est valide pour être ajoutée au texte principal"""
        if line in current_text:
            return False
        if len(line) < 3:
            return False
        if line.startswith('•') and not self.is_test_line('• ' + line[1:]):
            return True
        return True

    def _finalize_requirement(self, req: Dict[str, Any]):
        """Nettoie et finalise une exigence avant de la sauvegarder"""
        text_remaining = self._extract_tests_from_text_line(req['text'], req)
        req['text'] = text_remaining
        
        req['text'] = self._remove_response_artifacts(req['text'])
        req['text'] = req['text'].strip()
        req['text'] = re.sub(r'\s+', ' ', req['text'])
        
        cleaned_tests = []
        for test in req['tests']:
            test_clean = self._remove_response_artifacts(test)
            test_clean = test_clean.strip()
            test_clean = re.sub(r'\s+', ' ', test_clean)
            if test_clean and test_clean not in cleaned_tests and len(test_clean) > 10:
                cleaned_tests.append(test_clean)
        req['tests'] = cleaned_tests
        
        req['guidance'] = self._remove_response_artifacts(req['guidance'])
        req['guidance'] = req['guidance'].strip()
        req['guidance'] = re.sub(r'\s+', ' ', req['guidance'])

    def parse_requirements(self, content: str) -> List[Dict[str, Any]]:
        """Parse les exigences du contenu texte"""
        requirements = []
        lines = content.splitlines()
        i = 0
        current_req = None

        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                i += 1
                continue

            req_num = self.is_requirement_number(line)
            if req_num:
                if current_req:
                    self._finalize_requirement(current_req)
                    if not any(req['req_num'] == current_req['req_num'] for req in requirements):
                        requirements.append(current_req)

                req_text = self.extract_requirement_text(line, req_num)
                current_req = {
                    'req_num': req_num,
                    'text': req_text,
                    'tests': [],
                    'guidance': ''
                }
                i += 1
                continue

            if current_req:
                if self.is_test_line(line):
                    test_text = line
                    test_text = re.sub(r'^•\s*', '', test_text).strip()
                    
                    j = i + 1
                    while j < len(lines):
                        next_line = lines[j].strip()
                        if not next_line:
                            j += 1
                            continue
                        if (self.is_requirement_number(next_line) or 
                            self.is_test_line(next_line) or
                            next_line.startswith(self.applicability_marker) or
                            next_line.startswith(self.guidance_marker) or
                            self._should_ignore_line(next_line)):
                            break
                        test_text += " " + next_line
                        j += 1
                    
                    test_text = self._clean_test_text(test_text)
                    if test_text and len(test_text) > 10:
                        current_req['tests'].append(test_text)
                    
                    i = j
                    continue

                elif line.startswith(self.applicability_marker):
                    guidance_text = line[len(self.applicability_marker):].strip(': ')
                    j = i + 1
                    while j < len(lines):
                        next_line = lines[j].strip()
                        if not next_line:
                            j += 1
                            continue
                        if (self.is_requirement_number(next_line) or 
                            self.is_test_line(next_line) or
                            next_line.startswith(self.guidance_marker) or
                            self._should_ignore_line(next_line)):
                            break
                        guidance_text += " " + next_line
                        j += 1
                    
                    current_req['guidance'] = self._clean_guidance_text(guidance_text)
                    i = j
                    continue

                elif line.startswith(self.guidance_marker):
                    guidance_text = line[len(self.guidance_marker):].strip(': ')
                    j = i + 1
                    while j < len(lines):
                        next_line = lines[j].strip()
                        if not next_line:
                            j += 1
                            continue
                        if (self.is_requirement_number(next_line) or 
                            self.is_test_line(next_line) or
                            next_line.startswith(self.applicability_marker) or
                            self._should_ignore_line(next_line)):
                            break
                        guidance_text += " " + next_line
                        j += 1
                    
                    current_req['guidance'] = self._clean_guidance_text(guidance_text)
                    i = j
                    continue

                elif self._should_ignore_line(line):
                    i += 1
                    continue

                else:
                    cleaned_line, j = self._extract_tests_from_text_line_multiline(line, current_req, lines, i)
                    
                    if j > i:
                        i = j
                        continue
                    
                    if cleaned_line and self._is_valid_text_line(cleaned_line, current_req['text']):
                        if current_req['text']:
                            current_req['text'] += " " + cleaned_line
                        else:
                            current_req['text'] = cleaned_line

            i += 1

        if current_req:
            self._finalize_requirement(current_req)
            if not any(req['req_num'] == current_req['req_num'] for req in requirements):
                requirements.append(current_req)

        return requirements

    def extract_all_requirements(self) -> List[Dict[str, Any]]:
        """Extrait toutes les exigences du PDF"""
        raw_text = self.read_pdf_content()
        if not raw_text:
            return []

        clean_text = self.clean_text(raw_text)
        self.requirements = self.parse_requirements(clean_text)
        return self.requirements


class PCIRequirementsExtractorFR(PCIRequirementsExtractorBase):
    """Extracteur PCI DSS pour documents français"""
    
    def __init__(self, pdf_content: bytes = None, pdf_path: str = None):
        super().__init__(pdf_content, pdf_path)
        self.test_indicators = ['• Examiner', '• Observer', '• Interroger', '• Vérifier', '• Inspecter']
        self.applicability_marker = "Notes d'Applicabilité"
        self.guidance_marker = "Conseils"
        self.language = "french"

    def clean_text(self, text: str) -> str:
        """Nettoie le texte extrait du PDF en supprimant les artefacts français"""
        text = re.sub(r'SAQ D de PCI DSS v[\d.]+.*?Page \d+.*?(?:En Place|Pas en Place)', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'© 2006-\d+.*?LLC.*?Tous Droits Réservés\.', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Octobre 2024', '', text, flags=re.IGNORECASE)
        text = re.sub(r'♦\s*Se reporter.*?(?=\n)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\(Cocher une réponse.*?\)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Section \d+ :', '', text, flags=re.IGNORECASE)
        
        text = re.sub(r'En Place\s+En Place avec CCW\s+Non Applicable\s+Non Testé\s+Pas en Place', '', text, flags=re.IGNORECASE)
        text = re.sub(r'avec CCW\s+Non Applicable\s+Non Testé\s+Pas en Place', '', text, flags=re.IGNORECASE)
        text = re.sub(r'avec CCW Non Applicable Non Testé Pas.*', '', text, flags=re.IGNORECASE)
        
        text = re.sub(r'\n\s*\n', '\n\n', text)
        lines = [line.strip() for line in text.splitlines()]
        return "\n".join(lines)

    def _clean_test_text(self, text: str) -> str:
        """Nettoie le texte d'un test en supprimant les artefacts français"""
        text = re.sub(r'SAQ D de PCI DSS.*?Page \d+.*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'© 2006-.*?LLC.*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'En Place.*?Pas en Place', '', text, flags=re.IGNORECASE)
        text = re.sub(r'♦\s*Se reporter.*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'avec CCW Non Applicable Non Testé Pas.*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'En Place\s+En Place avec CCW\s+Non Applicable\s+Non Testé\s+Pas en Place', '', text, flags=re.IGNORECASE)
        text = re.sub(r'(En Place|Pas en Place|Non Applicable|Non Testé|CCW)(\s+(En Place|Pas en Place|Non Applicable|Non Testé|CCW))*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _clean_guidance_text(self, text: str) -> str:
        """Nettoie le texte de guidance en supprimant les artefacts français"""
        text = re.sub(r'SAQ D de PCI DSS.*?Page \d+.*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'© 2006-.*?LLC.*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'En Place.*?Pas en Place', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _should_ignore_line(self, line: str) -> bool:
        """Détermine si une ligne doit être ignorée (français)"""
        ignore_patterns = [
            r'^SAQ D de PCI DSS',
            r'^© 2006-\d+',
            r'^Page \d+',
            r'^Octobre 2024',
            r'^Exigence de PCI DSS',
            r'^Tests Prévus',
            r'^Réponse',
            r'^En Place',
            r'^Pas en Place',
            r'^Non Applicable',
            r'^Non Testé',
            r'^♦ Se reporter',
            r'^\(Cocher une réponse',
            r'^Section \d+',
            r'^Tous Droits Réservés',
            r'^LLC\.',
            r'^PCI Security Standards Council',
        ]
        
        for pattern in ignore_patterns:
            if re.match(pattern, line, re.IGNORECASE):
                return True
                
        if len(line.strip()) <= 2:
            return True
            
        return False

    def _remove_response_artifacts(self, text: str) -> str:
        """Supprime les artefacts de cases de réponse du questionnaire français"""
        patterns_to_remove = [
            r'avec CCW Non Applicable Non Testé Pas.*?(?=\n|$)',
            r'En Place\s+En Place avec CCW\s+Non Applicable\s+Non Testé\s+Pas en Place',
            r'avec CCW\s+Non Applicable\s+Non Testé\s+Pas en Place',
            r'En Place.*?Pas en Place.*?(?=\n|$)',
            r'(En Place|Pas en Place|Non Applicable|Non Testé|CCW)(\s+(En Place|Pas en Place|Non Applicable|Non Testé|CCW))+',
            r'♦\s*Se reporter.*?(?=\n|$)',
            r'\(Cocher une réponse.*?\)',
        ]
        
        for pattern in patterns_to_remove:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        text = re.sub(r'\s+', ' ', text)
        return text.strip()


class PCIRequirementsExtractorEN(PCIRequirementsExtractorBase):
    """Extracteur PCI DSS pour documents anglais"""
    
    def __init__(self, pdf_content: bytes = None, pdf_path: str = None):
        super().__init__(pdf_content, pdf_path)
        self.test_indicators = ['• Examine', '• Observe', '• Interview', '• Verify', '• Inspect']
        self.applicability_marker = "Applicability Notes"
        self.guidance_marker = "Guidance"
        self.language = "english"

    def clean_text(self, text: str) -> str:
        """Nettoie le texte extrait du PDF en supprimant les artefacts anglais"""
        # Patterns spécifiques au format anglais
        text = re.sub(r'PCI DSS v[\d.]+\s+SAQ D for Merchants.*?Page \d+', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'PCI DSS SAQ D v[\d.]+.*?Page \d+.*?(?:In Place|Not in Place)', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'© 2006[−-]\d+.*?PCI Security Standards Council.*?LLC.*?All Rights Reserved\.', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Section \d+:\s*Self[−-]Assessment Questionnaire', '', text, flags=re.IGNORECASE)
        text = re.sub(r'October 2024', '', text, flags=re.IGNORECASE)
        text = re.sub(r'♦\s*Refer to.*?(?=\n)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\(Check one response.*?\)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Section \d+\s*:', '', text, flags=re.IGNORECASE)
        
        text = re.sub(r'In Place\s+In Place with CCW\s+Not Applicable\s+Not Tested\s+Not in Place', '', text, flags=re.IGNORECASE)
        text = re.sub(r'with CCW\s+Not Applicable\s+Not Tested\s+Not in Place', '', text, flags=re.IGNORECASE)
        text = re.sub(r'with CCW Not Applicable Not Tested Not.*', '', text, flags=re.IGNORECASE)
        
        text = re.sub(r'\n\s*\n', '\n\n', text)
        lines = [line.strip() for line in text.splitlines()]
        return "\n".join(lines)

    def _clean_test_text(self, text: str) -> str:
        """Nettoie le texte d'un test en supprimant les artefacts anglais"""
        # Patterns spécifiques aux artefacts anglais
        text = re.sub(r'PCI DSS v[\d.]+\s+SAQ D for Merchants.*?Page \d+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'PCI DSS SAQ D.*?Page \d+.*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'© 2006[−-]\d+.*?PCI Security Standards Council.*?LLC.*?All Rights Reserved\.', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Section \d+:\s*Self[−-]Assessment Questionnaire', '', text, flags=re.IGNORECASE)
        text = re.sub(r'October 2024', '', text, flags=re.IGNORECASE)
        text = re.sub(r'In Place.*?Not in Place', '', text, flags=re.IGNORECASE)
        text = re.sub(r'♦\s*Refer to.*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'with CCW Not Applicable Not Tested Not.*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'In Place\s+In Place with CCW\s+Not Applicable\s+Not Tested\s+Not in Place', '', text, flags=re.IGNORECASE)
        text = re.sub(r'(In Place|Not in Place|Not Applicable|Not Tested|CCW)(\s+(In Place|Not in Place|Not Applicable|Not Tested|CCW))*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _clean_guidance_text(self, text: str) -> str:
        """Nettoie le texte de guidance en supprimant les artefacts anglais"""
        text = re.sub(r'PCI DSS v[\d.]+\s+SAQ D for Merchants.*?Page \d+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'PCI DSS SAQ D.*?Page \d+.*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'© 2006[−-]\d+.*?PCI Security Standards Council.*?LLC.*?All Rights Reserved\.', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Section \d+:\s*Self[−-]Assessment Questionnaire', '', text, flags=re.IGNORECASE)
        text = re.sub(r'October 2024', '', text, flags=re.IGNORECASE)
        text = re.sub(r'In Place.*?Not in Place', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _should_ignore_line(self, line: str) -> bool:
        """Détermine si une ligne doit être ignorée (anglais)"""
        ignore_patterns = [
            r'^PCI DSS v[\d.]+\s+SAQ D for Merchants',
            r'^PCI DSS SAQ D',
            r'^© 2006[−-]\d+',
            r'^Page \d+',
            r'^October 2024',
            r'^Section \d+:\s*Self[−-]Assessment Questionnaire',
            r'^PCI Security Standards Council',
            r'^PCI DSS Requirement',
            r'^Testing Procedures',
            r'^Response',
            r'^In Place',
            r'^Not in Place',
            r'^Not Applicable',
            r'^Not Tested',
            r'^♦ Refer to',
            r'^\(Check one response',
            r'^Section \d+',
            r'^All Rights Reserved',
            r'^LLC\.',
        ]
        
        for pattern in ignore_patterns:
            if re.match(pattern, line, re.IGNORECASE):
                return True
                
        if len(line.strip()) <= 2:
            return True
            
        return False

    def _remove_response_artifacts(self, text: str) -> str:
        """Supprime les artefacts de cases de réponse du questionnaire anglais"""
        patterns_to_remove = [
            r'PCI DSS v[\d.]+\s+SAQ D for Merchants.*?(?=\n|$)',
            r'© 2006[−-]\d+.*?PCI Security Standards Council.*?LLC.*?All Rights Reserved\..*?(?=\n|$)',
            r'Section \d+:\s*Self[−-]Assessment Questionnaire.*?(?=\n|$)',
            r'October 2024.*?(?=\n|$)',
            r'with CCW Not Applicable Not Tested Not.*?(?=\n|$)',
            r'In Place\s+In Place with CCW\s+Not Applicable\s+Not Tested\s+Not in Place',
            r'with CCW\s+Not Applicable\s+Not Tested\s+Not in Place',
            r'In Place.*?Not in Place.*?(?=\n|$)',
            r'(In Place|Not in Place|Not Applicable|Not Tested|CCW)(\s+(In Place|Not in Place|Not Applicable|Not Tested|CCW))+',
            r'♦\s*Refer to.*?(?=\n|$)',
            r'\(Check one response.*?\)',
        ]
        
        for pattern in patterns_to_remove:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        text = re.sub(r'\s+', ' ', text)
        return text.strip()


# ============================================================================
# MAIN EXTRACTOR CLASS - Consolidated from original extract.py
# ============================================================================

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


# ============================================================================
# MULTIPART PARSING HELPER
# ============================================================================

def parse_multipart_data(body: bytes, content_type: str):
    """Parse multipart form data"""
    if b'file' not in body:
        return None
    
    # Simple parsing pour récupérer le contenu PDF
    try:
        boundary = content_type.split('boundary=')[1].encode()
        parts = body.split(b'--' + boundary)
        
        for part in parts:
            if b'filename=' in part and b'Content-Type: application/pdf' in part:
                # Trouver le début des données PDF
                header_end = part.find(b'\r\n\r\n')
                if header_end != -1:
                    pdf_data = part[header_end + 4:]
                    # Supprimer les données de fin
                    if pdf_data.endswith(b'\r\n'):
                        pdf_data = pdf_data[:-2]
                    return pdf_data
    except:
        pass
    return None


# ============================================================================
# VERCEL HANDLER
# ============================================================================

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
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else b''
            
            content_type = self.headers.get('Content-Type', '')
            pdf_content = None
            
            # Parser multipart si présent
            if 'multipart/form-data' in content_type and body:
                pdf_content = parse_multipart_data(body, content_type)
            
            # Fallback : PDF de démo
            if not pdf_content:
                demo_pdf_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'PCI-DSS-v4-0-1-SAQ-D-Merchant-FR.pdf')
                if os.path.exists(demo_pdf_path):
                    extractor = PCIRequirementsExtractor(pdf_path=demo_pdf_path)
                else:
                    self.send_error(400, "No PDF file provided and no demo file found")
                    return
            else:
                extractor = PCIRequirementsExtractor(pdf_content=pdf_content)
            
            # Extraction avec détection automatique de langue
            requirements = extractor.extract_all_requirements()
            
            if not requirements:
                self.send_error(400, "No PCI requirements found in PDF")
                return
            
            # Tri - utilise la même logique
            def sort_key(req):
                parts = [int(x) for x in req['req_num'].split('.')]
                # Pad with zeros to ensure consistent sorting
                while len(parts) < 4:
                    parts.append(0)
                return parts
            
            sorted_requirements = sorted(requirements, key=sort_key)
            
            response_data = {
                'success': True,
                'requirements': sorted_requirements,
                'summary': extractor.get_extraction_summary()
            }
            
            # Réponse JSON
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self._set_cors_headers()
            self.end_headers()
            
            json_response = json.dumps(response_data, ensure_ascii=False, indent=None)
            self.wfile.write(json_response.encode('utf-8'))
            
        except Exception as e:
            print(f"Error in handler: {str(e)}")
            import traceback
            traceback.print_exc()
            self.send_error(500, f"Server error: {str(e)}")