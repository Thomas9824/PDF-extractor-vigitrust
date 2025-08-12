#!/usr/bin/env python3
"""
API Flask pour l'extracteur PCI DSS
Flask API for PCI DSS extractor
"""
import json
import sys
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import base64
import tempfile

# Ajouter le répertoire parent au path pour importer testv5
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from testv5 import PCIRequirementsExtractor

app = Flask(__name__)
CORS(app)

@app.route('/api/extract', methods=['POST'])
def extract_pdf():
    try:
        # Récupérer le fichier PDF depuis la requête
        if 'file' not in request.files:
            return jsonify({'error': 'Aucun fichier fourni'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Aucun fichier sélectionné'}), 400
        
        # Vérifier que c'est un PDF
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'Le fichier doit être un PDF'}), 400
        
        # Créer un fichier temporaire pour sauvegarder le PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            file.save(temp_file.name)
            temp_file_path = temp_file.name
        
        try:
            print(f"Traitement du fichier: {temp_file_path}")
            
            # Utiliser l'extracteur Python exactement comme dans testv5.py
            extractor = PCIRequirementsExtractor(temp_file_path)
            requirements = extractor.extract_all_requirements()
            
            print(f"Extraction terminée. {len(requirements)} exigences trouvées.")
            
            # Afficher le résumé comme dans le script original
            extractor.print_summary()
            
            # Supprimer le fichier temporaire
            os.unlink(temp_file_path)
            
            # Trier les exigences par numéro
            def sort_key(req):
                parts = [int(x) for x in req['req_num'].split('.')]
                while len(parts) < 4:
                    parts.append(0)
                return parts
            
            sorted_requirements = sorted(requirements, key=sort_key)
            
            # Retourner les résultats
            return jsonify({
                'success': True,
                'requirements': sorted_requirements,
                'summary': {
                    'total': len(sorted_requirements),
                    'with_tests': len([req for req in sorted_requirements if req['tests']]),
                    'with_guidance': len([req for req in sorted_requirements if req['guidance']]),
                    'total_tests': sum(len(req['tests']) for req in sorted_requirements)
                }
            })
        
        except Exception as e:
            # Supprimer le fichier temporaire en cas d'erreur
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            raise e
            
    except Exception as e:
        print(f"Erreur lors de l'extraction: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'OK', 'message': 'API PCI Extractor fonctionne'})

if __name__ == '__main__':
    app.run(debug=True, port=8000)