#!/usr/bin/env python3
"""
Extracteur automatique d'exigences PCI DSS (Version 5 - Améliorée)
Automatic PCI DSS Requirements Extractor (Version 5 - Improved)
Extrait toutes les exigences du document SAQ D v4.0.1 (pages 16-119)
Format de sortie: {'req_num': '...', 'text': '...', 'tests': [...], 'guidance': '...'}
"""
import re
import json
import PyPDF2
from typing import List, Dict, Any, Tuple

class PCIRequirementsExtractor:
    """Classe principale pour extraire les exigences PCI DSS depuis un PDF"""

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.requirements = []
        
        # Marqueurs pour identifier les sections avec plus de précision
        self.test_indicators = ['• Examiner', '• Observer', '• Interroger', '• Vérifier', '• Inspecter']
        self.applicability_marker = "Notes d'Applicabilité"
        self.guidance_marker = "Conseils"

    def read_pdf_content(self) -> str:
        """Lit le contenu du PDF et retourne le texte complet"""
        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                # Lire de la page 16 à 129 (index 15 à 128)
                start_page = 15
                end_page = min(129, len(pdf_reader.pages))
                
                for page_num in range(start_page, end_page):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"Erreur lors de la lecture du PDF: {e}")
            return ""

    def clean_text(self, text: str) -> str:
        """Nettoie le texte extrait du PDF en supprimant les artefacts"""
        text = re.sub(r'SAQ D de PCI DSS v[\d.]+.*?Page \d+.*?(?:En Place|Pas en Place)', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'© 2006-\d+.*?LLC.*?Tous Droits Réservés\.', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Octobre 2024', '', text, flags=re.IGNORECASE)
        text = re.sub(r'♦\s*Se reporter.*?(?=\n)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\(Cocher une réponse.*?\)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Section \d+ :', '', text, flags=re.IGNORECASE)
        
        # Nettoyer les tableaux de réponses 
        text = re.sub(r'En Place\s+En Place avec CCW\s+Non Applicable\s+Non Testé\s+Pas en Place', '', text, flags=re.IGNORECASE)
        text = re.sub(r'avec CCW\s+Non Applicable\s+Non Testé\s+Pas en Place', '', text, flags=re.IGNORECASE)
        text = re.sub(r'avec CCW Non Applicable Non Testé Pas.*', '', text, flags=re.IGNORECASE)
        
        # Remplacer les sauts de ligne multiples par un seul
        text = re.sub(r'\n\s*\n', '\n\n', text)
        # Supprimer les espaces en début/fin de ligne
        lines = [line.strip() for line in text.splitlines()]
        return "\n".join(lines)

    def is_requirement_number(self, line: str) -> str:
        """Vérifie si une ligne commence par un numéro d'exigence valide"""
        # Pattern plus précis pour les numéros d'exigence
        pattern = r'^(\d+\.\d+(?:\.\d+)*(?:\.\d+)*)\s+'
        match = re.match(pattern, line.strip())
        if match:
            req_num = match.group(1)
            # Éviter les numéros de page ou de version et valider la plage
            parts = req_num.split('.')
            if len(parts) >= 2:
                main_num = int(parts[0])
                # Les exigences PCI vont de 1 à 12
                if 1 <= main_num <= 12:
                    return req_num
        return ""

    def is_test_line(self, line: str) -> bool:
        """Vérifie si une ligne est une ligne de test"""
        line_clean = line.strip()
        return any(line_clean.startswith(indicator) for indicator in self.test_indicators)

    def extract_requirement_text(self, line: str, req_num: str) -> str:
        """Extrait le texte de l'exigence en supprimant le numéro"""
        # Trouver la position après le numéro d'exigence
        pattern = rf'^{re.escape(req_num)}\s+'
        cleaned_line = re.sub(pattern, '', line.strip())
        return cleaned_line

    def parse_requirements(self, content: str) -> List[Dict[str, Any]]:
        """Parse les exigences du contenu texte"""
        requirements = []
        lines = content.splitlines()
        i = 0
        current_req = None

        while i < len(lines):
            line = lines[i].strip()
            
            if not line:  # Ignorer les lignes vides
                i += 1
                continue

            # Vérifier si c'est le début d'une nouvelle exigence
            req_num = self.is_requirement_number(line)
            if req_num:
                # Sauvegarder l'exigence précédente si elle existe
                if current_req:
                    self._finalize_requirement(current_req)
                    if not any(req['req_num'] == current_req['req_num'] for req in requirements):
                        requirements.append(current_req)

                # Initialiser une nouvelle exigence
                req_text = self.extract_requirement_text(line, req_num)
                current_req = {
                    'req_num': req_num,
                    'text': req_text,
                    'tests': [],
                    'guidance': ''
                }
                i += 1
                continue

            # Si une exigence est en cours de traitement
            if current_req:
                # Vérifier si c'est une ligne de test 
                if self.is_test_line(line):
                    # Extraire le test complet en préservant le verbe d'action
                    test_text = line
                    # Nettoyer la puce mais garder le verbe
                    test_text = re.sub(r'^•\s*', '', test_text).strip()
                    
                    # Rassembler les lignes de continuation pour ce test
                    j = i + 1
                    while j < len(lines):
                        next_line = lines[j].strip()
                        if not next_line:
                            j += 1
                            continue
                        # Arrêter si on trouve une nouvelle exigence, un nouveau test, ou une section spéciale
                        if (self.is_requirement_number(next_line) or 
                            self.is_test_line(next_line) or
                            next_line.startswith(self.applicability_marker) or
                            next_line.startswith(self.guidance_marker) or
                            self._should_ignore_line(next_line)):
                            break
                        # Ajouter la continuation au test en cours
                        test_text += " " + next_line
                        j += 1
                    
                    # Nettoyer le test des artefacts
                    test_text = self._clean_test_text(test_text)
                    if test_text and len(test_text) > 10:  # Seulement les tests significatifs
                        current_req['tests'].append(test_text)
                    
                    i = j
                    continue

                # Vérifier si c'est la section Notes d'Applicabilité 
                elif line.startswith(self.applicability_marker):
                    # Extraire le contenu des notes d'applicabilité dans le champ guidance
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
                    
                    # Nettoyer et stocker dans guidance
                    current_req['guidance'] = self._clean_guidance_text(guidance_text)
                    i = j
                    continue

                # Vérifier si c'est la section Conseils
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

                # Vérifier si c'est du contenu à ignorer
                elif self._should_ignore_line(line):
                    i += 1
                    continue

                # Sinon, c'est du texte appartenant à l'exigence principale
                else:
                    # Vérifier si le texte contient des tests cachés
                    # ET gérer les tests sur plusieurs lignes
                    cleaned_line, j = self._extract_tests_from_text_line_multiline(line, current_req, lines, i)
                    
                    # Si on a traité des lignes supplémentaires pour des tests multi-lignes
                    if j > i:
                        i = j
                        continue
                    
                    # Ajouter au texte principal seulement si ce n'est pas redondant ou parasite
                    if cleaned_line and self._is_valid_text_line(cleaned_line, current_req['text']):
                        if current_req['text']:
                            current_req['text'] += " " + cleaned_line
                        else:
                            current_req['text'] = cleaned_line

            i += 1

        # Sauvegarder la dernière exigence
        if current_req:
            self._finalize_requirement(current_req)
            if not any(req['req_num'] == current_req['req_num'] for req in requirements):
                requirements.append(current_req)

        return requirements

    def _extract_tests_from_text_line_multiline(self, line: str, current_req: Dict[str, Any], all_lines: List[str], current_index: int) -> Tuple[str, int]:
        """Extrait les tests cachés dans une ligne de texte et gère les tests multi-lignes"""
        remaining_text = line
        processed_lines = current_index
        
        # Trouver tous les tests dans la ligne
        for indicator in self.test_indicators:
            verb = indicator[2:]  # Enlever "• " pour avoir juste "Examiner", "Observer", etc.
            pattern = rf'•\s*{re.escape(verb)}[^•]*'
            matches = list(re.finditer(pattern, remaining_text, re.IGNORECASE))
            
            for match in reversed(matches):  # Traiter de droite à gauche pour préserver les positions
                test_text = match.group(0)
                test_text = re.sub(r'^•\s*', '', test_text).strip()
                
                # Vérifier si le test semble incomplet (très court ou se termine abruptement)
                # et rassembler les lignes suivantes si nécessaire
                if len(test_text) < 30 or not test_text.endswith('.'):
                    # Rassembler les lignes suivantes pour ce test
                    j = current_index + 1
                    while j < len(all_lines):
                        next_line = all_lines[j].strip()
                        if not next_line:
                            j += 1
                            continue
                        
                        # Arrêter si on trouve une nouvelle exigence, un nouveau test, ou une section spéciale
                        if (self.is_requirement_number(next_line) or 
                            self.is_test_line(next_line) or
                            next_line.startswith(self.applicability_marker) or
                            next_line.startswith(self.guidance_marker) or
                            self._should_ignore_line(next_line)):
                            break
                        
                        # Ajouter la continuation au test en cours
                        test_text += " " + next_line
                        processed_lines = j  # Marquer cette ligne comme traitée
                        
                        # Si on a une phrase complète (se termine par . ! ou ?), on peut arrêter
                        if next_line.endswith('.') or next_line.endswith('!') or next_line.endswith('?'):
                            break
                        
                        j += 1
                
                # Nettoyer le test des artefacts
                test_text = self._clean_test_text(test_text)
                
                if test_text and len(test_text) > 10:
                    # Ajouter le test s'il n'existe pas déjà
                    if test_text not in current_req['tests']:
                        current_req['tests'].append(test_text)
                    
                    # Supprimer le test du texte restant
                    remaining_text = remaining_text[:match.start()] + ' ' + remaining_text[match.end():]
        
        # Nettoyer le texte restant
        remaining_text = re.sub(r'\s+', ' ', remaining_text).strip()
        return remaining_text, processed_lines

    def _extract_tests_from_text_line(self, line: str, current_req: Dict[str, Any]) -> str:
        """Extrait les tests cachés dans une ligne de texte et les ajoute à tests[] (version simple)"""
        remaining_text = line
        
        # Trouver tous les tests dans la ligne
        for indicator in self.test_indicators:
            verb = indicator[2:]  # Enlever "• " pour avoir juste "Examiner", "Observer", etc.
            pattern = rf'•\s*{re.escape(verb)}[^•]*'
            matches = list(re.finditer(pattern, remaining_text, re.IGNORECASE))
            
            for match in reversed(matches):  # Traiter de droite à gauche pour préserver les positions
                test_text = match.group(0)
                test_text = re.sub(r'^•\s*', '', test_text).strip()
                test_text = self._clean_test_text(test_text)
                
                if test_text and len(test_text) > 10:
                    # Ajouter le test s'il n'existe pas déjà
                    if test_text not in current_req['tests']:
                        current_req['tests'].append(test_text)
                    
                    # Supprimer le test du texte restant
                    remaining_text = remaining_text[:match.start()] + ' ' + remaining_text[match.end():]
        
        # Nettoyer le texte restant
        remaining_text = re.sub(r'\s+', ' ', remaining_text).strip()
        return remaining_text

    def _clean_test_text(self, text: str) -> str:
        """Nettoie le texte d'un test en supprimant les artefacts"""
        # Supprimer les artefacts de mise en page
        text = re.sub(r'SAQ D de PCI DSS.*?Page \d+.*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'© 2006-.*?LLC.*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'En Place.*?Pas en Place', '', text, flags=re.IGNORECASE)
        text = re.sub(r'♦\s*Se reporter.*', '', text, flags=re.IGNORECASE)
        
        # Supprimer les artefacts de tableau de réponse
        text = re.sub(r'avec CCW Non Applicable Non Testé Pas.*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'En Place\s+En Place avec CCW\s+Non Applicable\s+Non Testé\s+Pas en Place', '', text, flags=re.IGNORECASE)
        text = re.sub(r'(En Place|Pas en Place|Non Applicable|Non Testé|CCW)(\s+(En Place|Pas en Place|Non Applicable|Non Testé|CCW))*', '', text, flags=re.IGNORECASE)
        
        # Normaliser les espaces
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _clean_guidance_text(self, text: str) -> str:
        """Nettoie le texte de guidance en supprimant les artefacts"""
        # Supprimer les artefacts similaires
        text = re.sub(r'SAQ D de PCI DSS.*?Page \d+.*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'© 2006-.*?LLC.*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'En Place.*?Pas en Place', '', text, flags=re.IGNORECASE)
        # Normaliser les espaces
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _is_valid_text_line(self, line: str, current_text: str) -> bool:
        """Vérifie si une ligne est valide pour être ajoutée au texte principal"""
        # Éviter les répétitions
        if line in current_text:
            return False
        
        # Éviter les lignes trop courtes ou qui semblent être des artefacts
        if len(line) < 3:
            return False
            
        # Éviter les lignes qui commencent par des puces non-test
        if line.startswith('•') and not self.is_test_line('• ' + line[1:]):
            return True
            
        return True

    def _should_ignore_line(self, line: str) -> bool:
        """Détermine si une ligne doit être ignorée"""
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
        
        line_lower = line.lower()
        for pattern in ignore_patterns:
            if re.match(pattern, line, re.IGNORECASE):
                return True
                
        # Ignorer les lignes très courtes qui sont probablement du bruit
        if len(line.strip()) <= 2:
            return True
            
        return False

    def _remove_response_artifacts(self, text: str) -> str:
        """Supprime les artefacts de cases de réponse du questionnaire"""
        # Supprimer toutes les variations des cases de réponse
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
        
        # Normaliser les espaces
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _finalize_requirement(self, req: Dict[str, Any]):
        """Nettoie et finalise une exigence avant de la sauvegarder"""
        # Extraire les tests restants du texte principal
        text_remaining = self._extract_tests_from_text_line(req['text'], req)
        req['text'] = text_remaining
        
        # Supprimer les artefacts de cases de réponse du texte principal
        req['text'] = self._remove_response_artifacts(req['text'])
        
        # Nettoyer le texte principal
        req['text'] = req['text'].strip()
        req['text'] = re.sub(r'\s+', ' ', req['text'])  # Normaliser les espaces
        
        # Nettoyer les tests et supprimer les doublons
        cleaned_tests = []
        for test in req['tests']:
            test_clean = self._remove_response_artifacts(test)
            test_clean = test_clean.strip()
            test_clean = re.sub(r'\s+', ' ', test_clean)
            if test_clean and test_clean not in cleaned_tests and len(test_clean) > 10:
                cleaned_tests.append(test_clean)
        req['tests'] = cleaned_tests
        
        # Nettoyer le guidance
        req['guidance'] = self._remove_response_artifacts(req['guidance'])
        req['guidance'] = req['guidance'].strip()
        req['guidance'] = re.sub(r'\s+', ' ', req['guidance'])

    def extract_all_requirements(self) -> List[Dict[str, Any]]:
        """Extrait toutes les exigences du PDF"""
        print("Lecture du PDF...")
        raw_text = self.read_pdf_content()
        if not raw_text:
            print("Échec de la lecture du PDF.")
            return []

        print("Nettoyage du texte...")
        clean_text = self.clean_text(raw_text)

        print("Parsing des exigences...")
        self.requirements = self.parse_requirements(clean_text)
        return self.requirements

    def print_summary(self):
        """Affiche un résumé des exigences extraites"""
        print(f"\nRésumé de l'extraction:")
        print(f"Nombre total d'exigences extraites: {len(self.requirements)}")
        if self.requirements:
            print(f"Première exigence: {self.requirements[0]['req_num']}")
            print(f"Dernière exigence: {self.requirements[-1]['req_num']}")
            
            # Statistiques
            with_tests = sum(1 for req in self.requirements if req['tests'])
            with_guidance = sum(1 for req in self.requirements if req['guidance'])
            total_tests = sum(len(req['tests']) for req in self.requirements)
            
            print(f"Exigences avec tests: {with_tests}")
            print(f"Exigences avec guidance: {with_guidance}")
            print(f"Total des tests extraits: {total_tests}")

    def save_to_json(self, output_file: str = "pci_requirements_v5.json"):
        """Sauvegarde les exigences au format JSON"""
        # Trier par numéro d'exigence
        def sort_key(req):
            parts = [int(x) for x in req['req_num'].split('.')]
            # Pad with zeros to ensure consistent sorting
            while len(parts) < 4:
                parts.append(0)
            return parts
        
        sorted_requirements = sorted(self.requirements, key=sort_key)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(sorted_requirements, f, ensure_ascii=False, indent=2)
        print("=" * 60)
        print(f"Exigences sauvegardées dans {output_file}")

def main():
    pdf_path = "PCI-DSS-v4-0-1-SAQ-D-Merchant-FR.pdf"
    print("EXTRACTEUR PCI DSS FRANÇAIS")
    print("=" * 60)
    
    extractor = PCIRequirementsExtractor(pdf_path)
    requirements = extractor.extract_all_requirements()

    if requirements:
        extractor.print_summary()
        extractor.save_to_json("pci_requirements_v5.json")
    else:
        print("Aucune exigence n'a pu être extraite.")

if __name__ == "__main__":
    main()