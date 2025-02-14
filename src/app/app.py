import os
from datetime import datetime
from flask import Flask, request, render_template, jsonify, send_file
import pandas as pd
import numpy as np
from src.annotator.annotation_service import AnnotationWorkflow
import logging
from logging.handlers import RotatingFileHandler

class Config:

    # Application configuration!

    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'data/raw')
    PROCESSED_FOLDER = os.path.join(os.getcwd(), 'data/processed')
    CLINVAR_PATH = os.path.join(os.getcwd(), 'data/clinvar/clinvar.vcf')
    LOG_FOLDER = os.path.join(os.getcwd(), 'logs')
    
    # DbNSFP specific configuration
    DBNSFP_DIR = os.path.join(os.getcwd(), 'data/dbnsfp')
    DBNSFP_GENOME_VERSIONS = ['hg18', 'hg19', 'hg38']
    DEFAULT_GENOME_VERSION = 'hg38'
    DEFAULT_JAVA_MEMORY = '5g'
    
    @classmethod
    def validate_paths(cls):

        # Ensure all required directories exist

        for path in [cls.UPLOAD_FOLDER, cls.PROCESSED_FOLDER, 
                    os.path.dirname(cls.CLINVAR_PATH), cls.LOG_FOLDER]:
            os.makedirs(path, exist_ok=True)
    
    @classmethod
    def validate_dbnsfp(cls):

        # Validate DbNSFP setup

        if not os.path.exists(cls.DBNSFP_DIR):
            raise FileNotFoundError(f"DbNSFP directory not found: {cls.DBNSFP_DIR}")
        
        # Check for required Java program
        java_file = os.path.join(cls.DBNSFP_DIR, 'search_dbNSFP47a.class')
        if not os.path.exists(java_file):
            raise FileNotFoundError(f"DbNSFP Java program not found: {java_file}")
        
        # Check for at least one chromosome file
        chr_files = [f for f in os.listdir(cls.DBNSFP_DIR) 
                    if f.startswith('dbNSFP4.7a_variant.chr') and f.endswith('.gz')]
        if not chr_files:
            raise FileNotFoundError("No dbNSFP chromosome files found")

def setup_logging(app):

    # Configure application logging

    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler(
            'logs/genetic_app.log', 
            maxBytes=10240000, 
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Genetic Analysis App startup')

app = Flask(__name__)

# Initialize configuration and logging
try:
    Config.validate_paths()
    Config.validate_dbnsfp()
    setup_logging(app)
except Exception as e:
    print(f"Initialization error: {e}")
    raise

@app.route('/')
def home():
    # Render home page with configuration options
    return render_template('index.html', 
                         genome_versions=Config.DBNSFP_GENOME_VERSIONS,
                         default_genome=Config.DEFAULT_GENOME_VERSION)

@app.route('/upload', methods=['POST'])
def upload_file():
    # Handle file upload and initiate analysis
    try:

        # Get and validate dbNSFP directory
        dbnsfp_dir = request.form.get('dbnsfp_dir', Config.DBNSFP_DIR).strip()
        
        # Validate the provided directory
        if not os.path.exists(dbnsfp_dir):
            return jsonify({'error': f'dbNSFP directory not found: {dbnsfp_dir}'}), 400

        # Log the dbNSFP directory being used
        app.logger.info(f"Using dbNSFP directory: {dbnsfp_dir}")

        # Validate file existence
        if 'vcf_file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
            
        file = request.files['vcf_file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        if not file.filename.endswith('.vcf'):
            return jsonify({'error': 'Invalid file type. Please upload a VCF file'}), 400
        
        # Get annotation configuration
        annotation_type = request.form.get('annotation_type')
        if not annotation_type or annotation_type not in ['dbnsfp', 'vep']:
            return jsonify({'error': 'Invalid or missing annotation type'}), 400
        
        # Save uploaded file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        input_filename = f"{timestamp}_{file.filename}"
        input_path = os.path.join(Config.UPLOAD_FOLDER, input_filename)
        file.save(input_path)
        
        # Prepare workflow configuration
        workflow_config = {
            'annotation_type': annotation_type
        }
        
        if annotation_type == 'vep':
            workflow_config['clinvar_path'] = Config.CLINVAR_PATH
        elif annotation_type == 'dbnsfp':
            workflow_config.update({
                'dbnsfp_dir': dbnsfp_dir,  #using the user provided dbnsfp directory
                'genome_version': request.form.get('genome_version', Config.DEFAULT_GENOME_VERSION),
                'memory': request.form.get('memory', Config.DEFAULT_JAVA_MEMORY)
            })
        
        # Initialize and run workflow
        workflow = AnnotationWorkflow(**workflow_config)
        result = workflow.process(input_path, Config.PROCESSED_FOLDER)
        
        app.logger.info(f"File processed successfully: {input_filename}")
        
        return jsonify({
            'success': True,
            'message': 'File processed successfully',
            'timestamp': result['timestamp'],
            'annotation_type': annotation_type,
            'output_folder': result['output_folder'],
            'parsed_file': result['parsed_file'],
            'annotated_file': result['annotated_file'],
            'dbnsfp_dir': dbnsfp_dir
        })
        
    except Exception as e:
        app.logger.error(f"Error processing upload: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_results/<timestamp>')
def get_results(timestamp):
    # Retrieve analysis results
    try:
        annotation_type = request.args.get('type', 'dbnsfp')
        
        results_file = os.path.join(
            Config.PROCESSED_FOLDER,
            timestamp,
            f'{annotation_type}_annotated_variants.csv'
        )
        
        if not os.path.exists(results_file):
            return jsonify({'error': 'Results not found'}), 404
        
        # read the tab-separated file correctly
        # df = pd.read_csv(results_file, sep='\t', comment='#', na_values='.')

        df = pd.read_csv(
            results_file,
            sep='\t',              #using tab as delimiter
            comment=None,          #don't treat # as comment!
            quoting=3,            # QUOTE_NONE - Don't use quotes
            dtype=str             #reading all columns as strings initially to preserve values
        )
        
        # Clean up column names by removing '#' if present
        # df.columns = [col.replace('#', '') for col in df.columns]
        
        # Handle data types for JSON serialization
        df = df.replace({np.nan: None})
        
        # Convert boolean values to strings
        for col in df.select_dtypes(include=['bool']).columns:
            df[col] = df[col].map({True: 'Yes', False: 'No'})
        
        # Round floating point numbers
        for col in df.select_dtypes(include=['float64']).columns:
            df[col] = df[col].round(4)
        
        return jsonify({
            'success': True,
            'data': df.to_dict('records'),
            'columns': df.columns.tolist()
        })
        
    except Exception as e:
        app.logger.error(f"Error retrieving results: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/download_results/<timestamp>')
def download_results(timestamp):
    # Download analysis results
    try:
        annotation_type = request.args.get('type', 'dbnsfp')
        results_file = os.path.join(
            Config.PROCESSED_FOLDER,
            timestamp,
            f'{annotation_type}_annotated_variants.csv'
        )
        
        if not os.path.exists(results_file):
            return jsonify({'error': 'Results file not found'}), 404
        
        #read and write the file to ensure consistent formatting
        df = pd.read_csv(
            results_file,
            sep='\t',
            comment=None,
            quoting=3,
            dtype=str
        )
        
        #creating a temporary file with proper formatting
        temp_file = os.path.join(
            Config.PROCESSED_FOLDER,
            timestamp,
            f'temp_{annotation_type}_annotated_variants.csv'
        )
        
        # Save with tab separator and without index
        df.to_csv(temp_file, sep='\t', index=False, quoting=3)
        
        return send_file(
            temp_file,
            as_attachment=True,
            download_name=f'{annotation_type}_annotated_variants_{timestamp}.csv',
            mimetype='text/csv'
        )
        
    except Exception as e:
        app.logger.error(f"Error downloading results: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/status/<timestamp>')
def get_status(timestamp):
    # Check processing status
    try:
        folder_path = os.path.join(Config.PROCESSED_FOLDER, timestamp)
        
        if not os.path.exists(folder_path):
            return jsonify({
                'status': 'not_found',
                'message': 'Process not found'
            }), 404
        
        # Check annotation completion
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
        app.logger.error(f"Error checking status: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    app.logger.error(f"Page not found: {request.url}")
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    app.logger.error(f"Server Error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True)