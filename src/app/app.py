import os
from datetime import datetime
from flask import Flask, request, render_template, jsonify, send_file
import pandas as pd
import numpy as np
from src.annotator.annotation_service import AnnotationWorkflow

app = Flask(__name__)

#PATHS
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'data/raw')
PROCESSED_FOLDER = os.path.join(os.getcwd(), 'data/processed')
CLINVAR_PATH = os.path.join(os.getcwd(), 'data/clinvar/clinvar.vcf')

#to ensure directories exist
for folder in [UPLOAD_FOLDER, PROCESSED_FOLDER, os.path.dirname(CLINVAR_PATH)]:
    os.makedirs(folder, exist_ok=True)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'vcf_file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
        
    file = request.files['vcf_file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
        
    if not file.filename.endswith('.vcf'):
        return jsonify({'error': 'Invalid file type. Please upload a VCF file'}), 400
    
    #IMP: get annotation configuration from form data
    form_data = request.form
    annotation_type = form_data.get('annotation_type')
    print(f"Annotation Type Selected: {annotation_type}")
    
    # Validate annotation type
    if not annotation_type or annotation_type not in ['dbnsfp', 'vep']:
        return jsonify({'error': 'Invalid or missing annotation type'}), 400
        
    try:
        #saving uploaded input file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        input_filename = f"{timestamp}_{file.filename}"
        input_path = os.path.join(UPLOAD_FOLDER, input_filename)
        file.save(input_path)
        
        # for "annotation_service.py":
            # 1) initialize workflow with appropriate configuration
        workflow_config = {
            'annotation_type': annotation_type
        }
        
            #2) add type-specific configuration
        if annotation_type == 'vep':
            workflow_config['clinvar_path'] = CLINVAR_PATH
        elif annotation_type == 'dbnsfp':
            workflow_config['db_type'] = form_data.get('db_type', 'academic')
            
        workflow = AnnotationWorkflow(**workflow_config)
        
            # 3) process the file
        result = workflow.process(input_path, PROCESSED_FOLDER)
        
        return jsonify({
            'success': True,
            'message': 'File processed successfully',
            'timestamp': result['timestamp'],
            'annotation_type': annotation_type,
            'output_folder': result['output_folder'],
            'parsed_file': result['parsed_file'],
            'annotated_file': result['annotated_file']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_results/<timestamp>')
def get_results(timestamp):
    try:
        #IMP: get annotation type from query parameter (default to dbNSFP)
        annotation_type = request.args.get('type', 'dbnsfp')
        
        results_file = os.path.join(
            PROCESSED_FOLDER,
            timestamp,
            f'{annotation_type}_annotated_variants.csv'
        )
        
        if not os.path.exists(results_file):
            return jsonify({'error': 'Results not found'}), 404
            
        df = pd.read_csv(results_file)
        
        #error handling: to handle NaN values before JSON serialization
        df = df.replace({np.nan: None}) #replacing NaN with None (will become null in JSON)
        
        #converting boolean values to strings if present
        for col in df.select_dtypes(include=['bool']).columns:
            df[col] = df[col].map({True: 'Yes', False: 'No'})
            
        #format numeric columns
        for col in df.select_dtypes(include=['float64']).columns:
            df[col] = df[col].round(4)
            
        return jsonify({
            'success': True,
            'data': df.to_dict('records'),
            'columns': df.columns.tolist()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download_results/<timestamp>')
def download_results(timestamp):
    try:
        annotation_type = request.args.get('type', 'dbnsfp')
        results_file = os.path.join(
            PROCESSED_FOLDER,
            timestamp,
            f'{annotation_type}_annotated_variants.csv'
        )
        
        if not os.path.exists(results_file):
            return jsonify({'error': 'Results file not found'}), 404
            
        return send_file(
            results_file,
            as_attachment=True,
            download_name=f'{annotation_type}_annotated_variants_{timestamp}.csv',
            mimetype='text/csv'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/status/<timestamp>')
def get_status(timestamp):
    ## check the status of annotation process - POLL STATUS
    try:
        folder_path = os.path.join(PROCESSED_FOLDER, timestamp)
        
        if not os.path.exists(folder_path):
            return jsonify({
                'status': 'not_found',
                'message': 'Process not found'
            }), 404
            
        #check for annotation completion
        annotation_types = ['dbnsfp', 'vep']
        completed_files = []
        
        for ann_type in annotation_types:
            result_file = os.path.join(folder_path, f'{ann_type}_annotated_variants.csv')
            if os.path.exists(result_file):
                completed_files.append(ann_type)
        
        if not completed_files:
            return jsonify({
                'status': 'processing',
                'message': 'Annotation in progress'
            })
            
        return jsonify({
            'status': 'completed',
            'completed_annotations': completed_files,
            'message': 'Annotation completed'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True)