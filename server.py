#!/usr/bin/env python3
"""
Serveur Flask de développement pour l'API PCI DSS Extractor
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys

# Ajouter le répertoire api au path
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))
from extract import PCIRequirementsExtractor

app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "message": "PCI DSS Extractor API is running"})

@app.route('/api/extract', methods=['POST'])
def extract_pci_requirements():
    try:
        # Vérifier si un fichier a été envoyé
        if 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                return jsonify({"error": "No file selected"}), 400
            
            if file and file.filename.lower().endswith('.pdf'):
                # Lire le contenu du fichier
                pdf_content = file.read()
                extractor = PCIRequirementsExtractor(pdf_content=pdf_content)
            else:
                return jsonify({"error": "Only PDF files are allowed"}), 400
        else:
            # Fallback : utiliser le PDF de démo
            demo_pdf_path = os.path.join(os.path.dirname(__file__), 'PCI-DSS-v4-0-1-SAQ-D-Merchant-FR.pdf')
            if os.path.exists(demo_pdf_path):
                extractor = PCIRequirementsExtractor(pdf_path=demo_pdf_path)
            else:
                return jsonify({"error": "No PDF file provided and no demo file found"}), 400
        
        # Extraction des exigences
        requirements = extractor.extract_all_requirements()
        
        if not requirements:
            return jsonify({"error": "No PCI requirements found in PDF"}), 400
        
        # Tri des exigences
        def sort_key(req):
            parts = [int(x) for x in req['req_num'].split('.')]
            while len(parts) < 4:
                parts.append(0)
            return parts
        
        sorted_requirements = sorted(requirements, key=sort_key)
        
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
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

if __name__ == '__main__':
    print("Starting PCI DSS Extractor API server...")
    print("Server will be available at: http://localhost:8000")
    print("Health check: http://localhost:8000/health")
    print("API endpoint: http://localhost:8000/api/extract")
    app.run(host='0.0.0.0', port=8000, debug=True)