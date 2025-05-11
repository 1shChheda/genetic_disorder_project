import os
from datetime import datetime, timedelta
import time
import threading
import multiprocessing
from functools import partial
from flask import Flask, request, render_template, jsonify, send_file, session
import pandas as pd
import numpy as np
from src.annotator.annotation_service import AnnotationWorkflow
from src.process.process_manager import process_manager
from src.session.session_manager import session_manager
import logging
from logging.handlers import RotatingFileHandler

class Config:

    # Application configuration!

    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'data/raw')
    PROCESSED_FOLDER = os.path.join(os.getcwd(), 'data/processed')
    CLINVAR_PATH = os.path.join(os.getcwd(), 'data/clinvar/clinvar.vcf')
    LOG_FOLDER = os.path.join(os.getcwd(), 'logs')
    
    # DbNSFP specific configuration
    DBNSFP_DIR = os.path.join(os.getcwd(), 'data', 'dbnsfp')
    DEFAULT_DBNSFP_PATH = '/data/dbnsfp'  #default path shown in UI
    DBNSFP_GENOME_VERSIONS = ['hg18', 'hg19', 'hg38']
    DEFAULT_GENOME_VERSION = 'hg38'
    DEFAULT_JAVA_MEMORY = '5g'
    
    @staticmethod
    def resolve_dbnsfp_path(path):
        # TO Resolve the dbNSFP directory path
        # handle both relative and absolute paths

        if path == Config.DEFAULT_DBNSFP_PATH:
            # If using default path, resolve it relative to current working directory
            return Config.DBNSFP_DIR
        elif os.path.isabs(path):
            # If absolute path provided, use it as is
            return path
        else:
            # If relative path provided, resolve it relative to current working directory
            return os.path.join(os.getcwd(), path)

    @classmethod
    def validate_paths(cls):

        # Ensure all required directories exist

        for path in [cls.UPLOAD_FOLDER, cls.PROCESSED_FOLDER, 
                    os.path.dirname(cls.CLINVAR_PATH), cls.LOG_FOLDER]:
            os.makedirs(path, exist_ok=True)
    
    @classmethod
    def validate_dbnsfp(cls, custom_path=None):
        # Validate DbNSFP setup
        dbnsfp_dir = custom_path if custom_path else cls.DBNSFP_DIR
        
        if not os.path.exists(dbnsfp_dir):
            raise FileNotFoundError(f"DbNSFP directory not found: {dbnsfp_dir}")
        
        # Check for required Java program
        java_file = os.path.join(dbnsfp_dir, 'search_dbNSFP47a.class')
        if not os.path.exists(java_file):
            raise FileNotFoundError(f"DbNSFP Java program not found: {java_file}")
        
        # Check for at least one chromosome file
        chr_files = [f for f in os.listdir(dbnsfp_dir) 
                    if f.startswith('dbNSFP4.7a_variant.chr') and f.endswith('.gz')]
        if not chr_files:
            raise FileNotFoundError(f"No dbNSFP chromosome files found: {dbnsfp_dir}")

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

#adding a secret key for session management
# In a production env, this should be a secure random key stored in environment variables
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev_key_h7j3k2h5j2k5h7j2k5h72jk5')

# security settings (optional, but i recommend)
app.config.update(
    SESSION_COOKIE_SECURE=True,      # only send cookies over HTTPS
    SESSION_COOKIE_HTTPONLY=True,    # prevent javaScript access to session cookie
    SESSION_COOKIE_SAMESITE='Lax',   # Protect against CSRF (imp)
    PERMANENT_SESSION_LIFETIME=timedelta(hours=24)  # session expiry time
)

# Initialize configuration and logging
try:
    Config.validate_paths()
    # Config.validate_dbnsfp()
    setup_logging(app)
except Exception as e:
    print(f"Initialization error: {e}")
    raise

@app.before_request
def before_request():
    # THis will ensure session exists and is valid
    if 'session_id' not in session:
        session['session_id'] = session_manager.create_session()
    session_manager.update_session_activity(session['session_id'])

# Start processing in a separate process
def run_workflow(workflow_config, input_path, output_folder, process_key):
    try:
        # Register this process with the process manager
        child_pid = os.getpid()
        app.logger.info(f"Starting annotation process with PID {child_pid} for key {process_key}")
        
        # Update the process manager with child PID
        from flask import current_app
        with app.app_context():
            process_manager.register_child_process(process_key, child_pid)
        
        # Initialize workflow
        workflow = AnnotationWorkflow(**workflow_config)
        
        # Run the workflow
        result = workflow.process(input_path, output_folder)
        
        # Create a status file to signal completion to the main process
        status_file = os.path.join(output_folder, "status.json")
        import json
        with open(status_file, 'w') as f:
            json.dump(result, f)
        
        app.logger.info(f"Process {process_key} completed successfully with status: {result.get('status', 'unknown')}")
        return result
        
    except Exception as e:
        app.logger.error(f"Error in workflow process: {str(e)}")
        # Write error status to a file that parent process can check
        try:
            status_file = os.path.join(output_folder, "status.json")
            import json
            with open(status_file, 'w') as f:
                json.dump({"status": "error", "error": str(e)}, f)
        except Exception as write_err:
            app.logger.error(f"Failed to write status file: {str(write_err)}")
        return None

@app.route('/')
def home():
    # Render home page with configuration options
    return render_template('index.html', 
                         genome_versions=Config.DBNSFP_GENOME_VERSIONS,
                         default_genome=Config.DEFAULT_GENOME_VERSION)

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        # Get and validate dbNSFP directory
        dbnsfp_dir = request.form.get('dbnsfp_dir', Config.DEFAULT_DBNSFP_PATH).strip()
        
        # Resolve the path (convert relative to absolute if needed)
        resolved_dbnsfp_dir = Config.resolve_dbnsfp_path(dbnsfp_dir)
        
        # Validate the provided directory
        Config.validate_dbnsfp(resolved_dbnsfp_dir)
        
        # Log the dbNSFP directory being used
        app.logger.info(f"Using dbNSFP directory: {resolved_dbnsfp_dir}")

        # Validate file existence
        if 'input_file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
            
        file = request.files['input_file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        # Check file extension - allow both VCF and CSV
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in ['.vcf', '.csv']:
            return jsonify({'error': 'Invalid file type. Please upload a VCF or CSV file'}), 400
        
        # Get annotation configuration
        annotation_type = request.form.get('annotation_type')
        if not annotation_type or annotation_type not in ['dbnsfp', 'vep']:
            return jsonify({'error': 'Invalid or missing annotation type'}), 400
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save uploaded file
        input_filename = f"{timestamp}_{file.filename}"
        input_path = os.path.join(Config.UPLOAD_FOLDER, input_filename)
        file.save(input_path)
        
        # Create output directory
        output_folder = os.path.join(Config.PROCESSED_FOLDER, timestamp)
        os.makedirs(output_folder, exist_ok=True)

        # Create unique process identifier
        process_key = process_manager.start_process(
            session['session_id'],
            timestamp,
            annotation_type,
            input_path,
            output_folder
        )

        # Associate process with session
        session_manager.add_process_to_session(session['session_id'], process_key)
        
        # Prepare workflow configuration
        workflow_config = {
            'annotation_type': annotation_type
        }
        
        if annotation_type == 'vep':
            workflow_config['clinvar_path'] = Config.CLINVAR_PATH
        elif annotation_type == 'dbnsfp':
            workflow_config.update({
                'dbnsfp_dir': resolved_dbnsfp_dir,  #using the user provided dbnsfp directory
                'genome_version': request.form.get('genome_version', Config.DEFAULT_GENOME_VERSION),
                'memory': request.form.get('memory', Config.DEFAULT_JAVA_MEMORY)
            })
        
        # Start the process
        process = multiprocessing.Process(
            target=run_workflow,
            args=(workflow_config, input_path, output_folder, process_key)
        )
        process.daemon = True  # Ensure process terminates when parent does
        process.start()
        
        # Log the process ID
        app.logger.info(f"Started annotation process with PID {process.pid} for key {process_key}")
        
        # Register the child process with our process manager
        process_manager.register_child_process(process_key, process.pid)
        
        return jsonify({
            'success': True,
            'process_key': process_key,
            'message': 'File processing started',
            'timestamp': timestamp,
            'annotation_type': annotation_type,
            'output_folder': output_folder,
            'pid': process.pid,
            'dbnsfp_dir': dbnsfp_dir,
            'file_type': file_extension[1:]  # 'vcf' or 'csv' without the dot
        })
        
    except Exception as e:
        if 'process_key' in locals():
            process_manager.update_process_status(process_key, 'error')
        app.logger.error(f"Error processing upload: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/check_process/<process_key>')
def check_process(process_key):

    # to check if a process has completed by checking for a status file

    try:
        # Get process info
        status = process_manager.get_process_status(process_key)
        
        if status != 'running':
            # Already marked as completed or error
            return jsonify({'status': status})
        
        # If it's marked as running, check if a status file exists
        process_info = process_manager.get_process_info(process_key)
        if not process_info:
            return jsonify({'error': 'Process not found'}), 404
            
        status_file = os.path.join(process_info.output_folder, "status.json")
        
        if os.path.exists(status_file):
            # Read status from file
            import json
            with open(status_file, 'r') as f:
                result = json.load(f)
                
            # Update the process status
            process_manager.update_process_status(process_key, result.get('status', 'completed'))
            
            return jsonify({
                'status': result.get('status', 'completed'),
                'details': result
            })
        
        # Process is still running
        return jsonify({'status': 'running'})
        
    except Exception as e:
        app.logger.error(f"Error checking process: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/cancel_process/<process_key>', methods=['POST'])
def cancel_process(process_key):

    # Cancel a running process

    # process_key = request.view_args['process_key']
    
    if process_manager.cancel_process(process_key):
        session_manager.remove_process_from_session(session['session_id'], process_key)
        return jsonify({'success': True, 'message': 'Process cancelled successfully'})
    else:
        return jsonify({'error': 'Failed to cancel process'}), 400

@app.route('/process_status/<process_key>')
def get_process_status(process_key):
    # Get current status of a process
    status = process_manager.get_process_status(process_key)
    
    if status == 'running':
        # Check if a status file exists
        process_info = process_manager.get_process_info(process_key)
        if process_info:
            status_file = os.path.join(process_info.output_folder, "status.json")
            
            if os.path.exists(status_file):
                # Read status from file
                import json
                with open(status_file, 'r') as f:
                    result = json.load(f)
                    
                # Update the process status
                new_status = result.get('status', 'completed')
                process_manager.update_process_status(process_key, new_status)
                status = new_status
    
    if status:
        return jsonify({'status': status})
    else:
        return jsonify({'error': 'Process not found'}), 404

# adding cleanup task
def cleanup_task():
    # Periodic cleanup of old processes and sessions (NICEEEE idea)
    while True:
        process_manager.cleanup_old_processes()
        session_manager.cleanup_inactive_sessions()
        time.sleep(3600)  # this will run every hour

# start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
cleanup_thread.start()

@app.route('/get_results/<timestamp>')
def get_results(timestamp):
    # Retrieve analysis results
    try:
        annotation_type = request.args.get('type', 'dbnsfp')
        
        results_file = os.path.join(
            Config.PROCESSED_FOLDER,
            timestamp,
            f'{annotation_type}_annotated_variants.tsv'
        )
        
        if not os.path.exists(results_file):
            return jsonify({'error': 'Results not found'}), 404

        df = pd.read_table(results_file)
        
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

#  THIS IS WRONG - GIVES WRONGLY FORMATTED CSV FILE
# TO RE-FORMAT OG ANNOTATED FILE (to properly separate fields in different columns IN THE OG FILE ITSELF)
        #read original messed-up annotated_variants file
        # with open(results_file, 'r', encoding='utf-8') as infile:
        #     lines = infile.readlines()
        
        # #replace "tabs" with "commas" ---
        # converted_lines = [line.replace('\t', ',') for line in lines]

        # #saving the csv file
        # with open(results_file, 'w', encoding='utf-8') as outfile:
        #     outfile.writelines(converted_lines)
        
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
    try:
        annotation_type = request.args.get('type', 'dbnsfp')
        results_file = os.path.join(
            Config.PROCESSED_FOLDER,
            timestamp,
            f'{annotation_type}_annotated_variants.tsv'
        )
        
        if not os.path.exists(results_file):
            return jsonify({'error': 'Results file not found'}), 404
        
        return send_file(
            results_file,
            as_attachment=True,
            download_name=f'{annotation_type}_annotated_variants_{timestamp}.tsv',
            mimetype='text/tab-separated-values'
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
            result_file = os.path.join(folder_path, f'{ann_type}_annotated_variants.tsv')
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