import os
from datetime import datetime
from flask import Flask, request, render_template, jsonify, send_file
import pandas as pd
import numpy as np
from src.parser.vcf_parser import parse_vcf
from src.annotator.vep_annotator import annotate_variants

app = Flask(__name__)

#PATHS
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'data/raw')
PROCESSED_FOLDER = os.path.join(os.getcwd(), 'data/processed')

#to ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

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

    try:
        #saving uploaded input file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        input_filename = f"{timestamp}_{file.filename}"
        input_path = os.path.join(UPLOAD_FOLDER, input_filename)
        
        file.save(input_path)

        # Step 1: Parse VCF
        output_folder = parse_vcf(input_vcf=input_path, output_dir=PROCESSED_FOLDER)
        
        # Step 2: Annotate variants
        parsed_csv = os.path.join(output_folder, 'parsed_variants.csv')
        annotated_csv = os.path.join(output_folder, 'annotated_variants.csv')
        annotate_variants(parsed_csv, annotated_csv)

        return jsonify({
            'success': True,
            'message': 'File processed successfully',
            'timestamp': timestamp
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

#for getting & displaying the results
@app.route('/get_results/<timestamp>')
def get_results(timestamp):
    try:
        annotated_file = os.path.join(PROCESSED_FOLDER, timestamp, 'annotated_variants.csv')
        if not os.path.exists(annotated_file):
            return jsonify({'error': 'Results not found'}), 404

        df = pd.read_csv(annotated_file)
        
        #error handling: to handle NaN values before JSON serialization
        df = df.replace({np.nan: None})  #replacing NaN with None (will become null in JSON)
        
        #converting boolean values to strings if present
        for col in df.select_dtypes(include=['bool']).columns:
            df[col] = df[col].map({True: 'Yes', False: 'No'})
        
        return jsonify({
            'success': True,
            'data': df.to_dict('records'),
            'columns': df.columns.tolist()
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)