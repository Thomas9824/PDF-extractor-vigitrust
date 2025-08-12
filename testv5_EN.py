#!/usr/bin/env python3
"""
Automatic PCI DSS Requirements Extractor 
Extracts all requirements from SAQ D v4.0.1 document (pages 16-129)
Output format: {'req_num': '...', 'text': '...', 'tests': [...], 'guidance': '...'}
"""
import re
import json
import PyPDF2
from typing import List, Dict, Any, Tuple

class PCIRequirementsExtractor:
    """Main class to extract PCI DSS requirements from a PDF"""

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.requirements = []
        
        # Markers to identify sections with more precision
        self.test_indicators = ['• Examiner', '• Observer', '• Interroger', '• Vérifier', '• Inspecter']
        self.applicability_marker = "Notes d'Applicabilité"
        self.guidance_marker = "Conseils"

    def read_pdf_content(self) -> str:
        """Reads the PDF content and returns the complete text"""
        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                # Read from page 16 to 129 (index 15 to 128)
                start_page = 15
                end_page = min(129, len(pdf_reader.pages))
                
                for page_num in range(start_page, end_page):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return ""

    def clean_text(self, text: str) -> str:
        """Cleans the extracted PDF text by removing artifacts"""
        text = re.sub(r'SAQ D de PCI DSS v[\d.]+.*?Page \d+.*?(?:En Place|Pas en Place)', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'© 2006-\d+.*?LLC.*?Tous Droits Réservés\.', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Octobre 2024', '', text, flags=re.IGNORECASE)
        text = re.sub(r'♦\s*Se reporter.*?(?=\n)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\(Cocher une réponse.*?\)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Section \d+ :', '', text, flags=re.IGNORECASE)
        
        # Clean response tables
        text = re.sub(r'En Place\s+En Place avec CCW\s+Non Applicable\s+Non Testé\s+Pas en Place', '', text, flags=re.IGNORECASE)
        text = re.sub(r'avec CCW\s+Non Applicable\s+Non Testé\s+Pas en Place', '', text, flags=re.IGNORECASE)
        text = re.sub(r'avec CCW Non Applicable Non Testé Pas.*', '', text, flags=re.IGNORECASE)
        
        # Replace multiple line breaks with a single one
        text = re.sub(r'\n\s*\n', '\n\n', text)
        # Remove spaces at beginning/end of lines
        lines = [line.strip() for line in text.splitlines()]
        return "\n".join(lines)

    def is_requirement_number(self, line: str) -> str:
        """Checks if a line starts with a valid requirement number"""
        # More precise pattern for requirement numbers
        pattern = r'^(\d+\.\d+(?:\.\d+)*(?:\.\d+)*)\s+'
        match = re.match(pattern, line.strip())
        if match:
            req_num = match.group(1)
            # Avoid page numbers or version numbers and validate range
            parts = req_num.split('.')
            if len(parts) >= 2:
                main_num = int(parts[0])
                # PCI requirements range from 1 to 12
                if 1 <= main_num <= 12:
                    return req_num
        return ""

    def is_test_line(self, line: str) -> bool:
        """Checks if a line is a test line"""
        line_clean = line.strip()
        return any(line_clean.startswith(indicator) for indicator in self.test_indicators)

    def extract_requirement_text(self, line: str, req_num: str) -> str:
        """Extracts the requirement text by removing the number"""
        # Find the position after the requirement number
        pattern = rf'^{re.escape(req_num)}\s+'
        cleaned_line = re.sub(pattern, '', line.strip())
        return cleaned_line

    def parse_requirements(self, content: str) -> List[Dict[str, Any]]:
        """Parse requirements from text content"""
        requirements = []
        lines = content.splitlines()
        i = 0
        current_req = None

        while i < len(lines):
            line = lines[i].strip()
            
            if not line:  # Ignore empty lines
                i += 1
                continue

            # Check if it's the start of a new requirement
            req_num = self.is_requirement_number(line)
            if req_num:
                # Save the previous requirement if it exists
                if current_req:
                    self._finalize_requirement(current_req)
                    if not any(req['req_num'] == current_req['req_num'] for req in requirements):
                        requirements.append(current_req)

                # Initialize a new requirement
                req_text = self.extract_requirement_text(line, req_num)
                current_req = {
                    'req_num': req_num,
                    'text': req_text,
                    'tests': [],
                    'guidance': ''
                }
                i += 1
                continue

            # If a requirement is being processed
            if current_req:
                # Check if it's a test line
                if self.is_test_line(line):
                    # Extract the complete test while preserving the action verb
                    test_text = line
                    # Clean the bullet but keep the verb
                    test_text = re.sub(r'^•\s*', '', test_text).strip()
                    
                    # Gather continuation lines for this test
                    j = i + 1
                    while j < len(lines):
                        next_line = lines[j].strip()
                        if not next_line:
                            j += 1
                            continue
                        # Stop if we find a new requirement, a new test, or a special section
                        if (self.is_requirement_number(next_line) or 
                            self.is_test_line(next_line) or
                            next_line.startswith(self.applicability_marker) or
                            next_line.startswith(self.guidance_marker) or
                            self._should_ignore_line(next_line)):
                            break
                        # Add continuation to the current test
                        test_text += " " + next_line
                        j += 1
                    
                    # Clean the test from artifacts
                    test_text = self._clean_test_text(test_text)
                    if test_text and len(test_text) > 10:  # Only significant tests
                        current_req['tests'].append(test_text)
                    
                    i = j
                    continue

                # Check if it's the Applicability Notes section
                elif line.startswith(self.applicability_marker):
                    # Extract applicability notes content into the guidance field
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
                    
                    # Clean and store in guidance
                    current_req['guidance'] = self._clean_guidance_text(guidance_text)
                    i = j
                    continue

                # Check if it's the Guidance section
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

                # Check if it's content to ignore
                elif self._should_ignore_line(line):
                    i += 1
                    continue

                # Otherwise, it's text belonging to the main requirement
                else:
                    # Check if the text contains hidden tests
                    # AND handle multi-line tests
                    cleaned_line, j = self._extract_tests_from_text_line_multiline(line, current_req, lines, i)
                    
                    # If we processed additional lines for multi-line tests
                    if j > i:
                        i = j
                        continue
                    
                    # Add to main text only if it's not redundant or parasitic
                    if cleaned_line and self._is_valid_text_line(cleaned_line, current_req['text']):
                        if current_req['text']:
                            current_req['text'] += " " + cleaned_line
                        else:
                            current_req['text'] = cleaned_line

            i += 1

        # Save the last requirement
        if current_req:
            self._finalize_requirement(current_req)
            if not any(req['req_num'] == current_req['req_num'] for req in requirements):
                requirements.append(current_req)

        return requirements

    def _extract_tests_from_text_line_multiline(self, line: str, current_req: Dict[str, Any], all_lines: List[str], current_index: int) -> Tuple[str, int]:
        """Extracts hidden tests from a text line and handles multi-line tests"""
        remaining_text = line
        processed_lines = current_index
        
        # Find all tests in the line
        for indicator in self.test_indicators:
            verb = indicator[2:]  # Remove "• " to get just "Examiner", "Observer", etc.
            pattern = rf'•\s*{re.escape(verb)}[^•]*'
            matches = list(re.finditer(pattern, remaining_text, re.IGNORECASE))
            
            for match in reversed(matches):  # Process from right to left to preserve positions
                test_text = match.group(0)
                test_text = re.sub(r'^•\s*', '', test_text).strip()
                
                # Check if the test seems incomplete (very short or ends abruptly)
                # and gather following lines if necessary
                if len(test_text) < 30 or not test_text.endswith('.'):
                    # Gather following lines for this test
                    j = current_index + 1
                    while j < len(all_lines):
                        next_line = all_lines[j].strip()
                        if not next_line:
                            j += 1
                            continue
                        
                        # Stop if we find a new requirement, a new test, or a special section
                        if (self.is_requirement_number(next_line) or 
                            self.is_test_line(next_line) or
                            next_line.startswith(self.applicability_marker) or
                            next_line.startswith(self.guidance_marker) or
                            self._should_ignore_line(next_line)):
                            break
                        
                        # Add continuation to the current test
                        test_text += " " + next_line
                        processed_lines = j  # Mark this line as processed
                        
                        # If we have a complete sentence (ends with . ! or ?), we can stop
                        if next_line.endswith('.') or next_line.endswith('!') or next_line.endswith('?'):
                            break
                        
                        j += 1
                
                # Clean the test from artifacts
                test_text = self._clean_test_text(test_text)
                
                if test_text and len(test_text) > 10:
                    # Add the test if it doesn't already exist
                    if test_text not in current_req['tests']:
                        current_req['tests'].append(test_text)
                    
                    # Remove the test from the remaining text
                    remaining_text = remaining_text[:match.start()] + ' ' + remaining_text[match.end():]
        
        # Clean the remaining text
        remaining_text = re.sub(r'\s+', ' ', remaining_text).strip()
        return remaining_text, processed_lines

    def _extract_tests_from_text_line(self, line: str, current_req: Dict[str, Any]) -> str:
        """Extracts hidden tests from a text line and adds them to tests[] (simple version)"""
        remaining_text = line
        
        # Find all tests in the line
        for indicator in self.test_indicators:
            verb = indicator[2:]  # Remove "• " to get just "Examiner", "Observer", etc.
            pattern = rf'•\s*{re.escape(verb)}[^•]*'
            matches = list(re.finditer(pattern, remaining_text, re.IGNORECASE))
            
            for match in reversed(matches):  # Process from right to left to preserve positions
                test_text = match.group(0)
                test_text = re.sub(r'^•\s*', '', test_text).strip()
                test_text = self._clean_test_text(test_text)
                
                if test_text and len(test_text) > 10:
                    # Add the test if it doesn't already exist
                    if test_text not in current_req['tests']:
                        current_req['tests'].append(test_text)
                    
                    # Remove the test from the remaining text
                    remaining_text = remaining_text[:match.start()] + ' ' + remaining_text[match.end():]
        
        # Clean the remaining text
        remaining_text = re.sub(r'\s+', ' ', remaining_text).strip()
        return remaining_text

    def _clean_test_text(self, text: str) -> str:
        """Cleans test text by removing artifacts"""
        # Remove layout artifacts
        text = re.sub(r'SAQ D de PCI DSS.*?Page \d+.*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'© 2006-.*?LLC.*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'En Place.*?Pas en Place', '', text, flags=re.IGNORECASE)
        text = re.sub(r'♦\s*Se reporter.*', '', text, flags=re.IGNORECASE)
        
        # Remove response table artifacts
        text = re.sub(r'avec CCW Non Applicable Non Testé Pas.*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'En Place\s+En Place avec CCW\s+Non Applicable\s+Non Testé\s+Pas en Place', '', text, flags=re.IGNORECASE)
        text = re.sub(r'(En Place|Pas en Place|Non Applicable|Non Testé|CCW)(\s+(En Place|Pas en Place|Non Applicable|Non Testé|CCW))*', '', text, flags=re.IGNORECASE)
        
        # Normalize spaces
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _clean_guidance_text(self, text: str) -> str:
        """Cleans guidance text by removing artifacts"""
        # Remove similar artifacts
        text = re.sub(r'SAQ D de PCI DSS.*?Page \d+.*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'© 2006-.*?LLC.*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'En Place.*?Pas en Place', '', text, flags=re.IGNORECASE)
        # Normalize spaces
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _is_valid_text_line(self, line: str, current_text: str) -> bool:
        """Checks if a line is valid to be added to the main text"""
        # Avoid repetitions
        if line in current_text:
            return False
        
        # Avoid lines that are too short or seem to be artifacts
        if len(line) < 3:
            return False
            
        # Avoid lines that start with non-test bullets
        if line.startswith('•') and not self.is_test_line('• ' + line[1:]):
            return True
            
        return True

    def _should_ignore_line(self, line: str) -> bool:
        """Determines if a line should be ignored"""
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
                
        # Ignore very short lines that are probably noise
        if len(line.strip()) <= 2:
            return True
            
        return False

    def _remove_response_artifacts(self, text: str) -> str:
        """Removes response checkbox artifacts from the questionnaire"""
        # Remove all variations of response checkboxes
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
        
        # Normalize spaces
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _finalize_requirement(self, req: Dict[str, Any]):
        """Cleans and finalizes a requirement before saving it"""
        # Extract remaining tests from the main text
        text_remaining = self._extract_tests_from_text_line(req['text'], req)
        req['text'] = text_remaining
        
        # Remove response checkbox artifacts from the main text
        req['text'] = self._remove_response_artifacts(req['text'])
        
        # Clean the main text
        req['text'] = req['text'].strip()
        req['text'] = re.sub(r'\s+', ' ', req['text'])  # Normalize spaces
        
        # Clean tests and remove duplicates
        cleaned_tests = []
        for test in req['tests']:
            test_clean = self._remove_response_artifacts(test)
            test_clean = test_clean.strip()
            test_clean = re.sub(r'\s+', ' ', test_clean)
            if test_clean and test_clean not in cleaned_tests and len(test_clean) > 10:
                cleaned_tests.append(test_clean)
        req['tests'] = cleaned_tests
        
        # Clean the guidance
        req['guidance'] = self._remove_response_artifacts(req['guidance'])
        req['guidance'] = req['guidance'].strip()
        req['guidance'] = re.sub(r'\s+', ' ', req['guidance'])

    def extract_all_requirements(self) -> List[Dict[str, Any]]:
        """Extracts all requirements from the PDF"""
        print("Reading PDF...")
        raw_text = self.read_pdf_content()
        if not raw_text:
            print("Failed to read PDF.")
            return []

        print("Cleaning text...")
        clean_text = self.clean_text(raw_text)

        print("Parsing requirements...")
        self.requirements = self.parse_requirements(clean_text)
        return self.requirements

    def print_summary(self):
        """Displays a summary of extracted requirements"""
        print(f"\nExtraction Summary:")
        print(f"Total number of extracted requirements: {len(self.requirements)}")
        if self.requirements:
            print(f"First requirement: {self.requirements[0]['req_num']}")
            print(f"Last requirement: {self.requirements[-1]['req_num']}")
            
            # Statistics
            with_tests = sum(1 for req in self.requirements if req['tests'])
            with_guidance = sum(1 for req in self.requirements if req['guidance'])
            total_tests = sum(len(req['tests']) for req in self.requirements)
            
            print(f"Requirements with tests: {with_tests}")
            print(f"Requirements with guidance: {with_guidance}")
            print(f"Total tests extracted: {total_tests}")

    def save_to_json(self, output_file: str = "pci_requirements_v5.json"):
        """Saves requirements in JSON format"""
        # Sort by requirement number
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
        print(f"Requirements saved in {output_file}")

def main():
    pdf_path = "PCI-DSS-v4-0-1-SAQ-D-Merchant-FR.pdf"
    print("FRENCH PCI DSS EXTRACTOR")
    print("=" * 60)
    
    extractor = PCIRequirementsExtractor(pdf_path)
    requirements = extractor.extract_all_requirements()

    if requirements:
        extractor.print_summary()
        extractor.save_to_json("pci_requirements_v5.json")
    else:
        print("No requirements could be extracted.")

if __name__ == "__main__":
    main()