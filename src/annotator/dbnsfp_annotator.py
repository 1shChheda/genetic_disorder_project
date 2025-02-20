import os
import subprocess
import logging
from datetime import datetime
from .base_annotator import BaseAnnotator

class DbNSFPAnnotator(BaseAnnotator):
    def __init__(self, dbnsfp_dir=None, genome_version="hg38", memory="5g"):

        # args:
        #     dbnsfp_dir (str): Path to dbNSFP database directory
        #     genome_version (str): Genome version (hg18/hg19/hg38)
        #     memory (str): Memory allocation for Java

        self.dbnsfp_dir = dbnsfp_dir or os.path.join(os.getcwd(), 'data', 'dbnsfp')
        self.genome_version = genome_version
        self.memory = memory
        self.setup_logging()
        
    def setup_logging(self):
        # Set up logging configuration
        log_dir = 'logs'
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f'dbnsfp_annotation_{timestamp}.log')
        
        self.logger = logging.getLogger('DbNSFPAnnotator')
        self.logger.setLevel(logging.INFO)
        
        handlers = [
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
        
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        for handler in handlers:
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            
    def setup(self):
        # CHECK 1: Verify dbNSFP files and Java environment
        self.logger.info("Setting up DbNSFP annotator...")
        
        # CHECK 2: Check Java installation
        try:
            result = subprocess.run(['java', '-version'], 
                                 capture_output=True, 
                                 text=True, 
                                 check=True)
            self.logger.info("Java installation verified")
        except subprocess.CalledProcessError as e:
            raise RuntimeError("Java not found. Please install Java 1.8 or later")
            
        # CHECK 3: Verify dbNSFP files
        required_files = ['search_dbNSFP47a.class']
        for file in required_files:
            file_path = os.path.join(self.dbnsfp_dir, file)
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Required file not found: {file_path}")
                
        self.logger.info("DbNSFP setup completed successfully")
        
    def annotate(self, input_file, output_file):

        # Annotate variants using dbNSFP
        
        # args:
        #     input_file (str): Path to input VCF file
        #     output_file (str): Path to output file

        self.logger.info(f"Starting annotation: {input_file} -> {output_file}")
        
        try:
            # Change to dbNSFP directory to ensure proper file access
            original_dir = os.getcwd()
            os.chdir(self.dbnsfp_dir)
            
            # Build command
            cmd = [
                'java',
                f'-Xmx{self.memory}',
                'search_dbNSFP47a',
                '-i', input_file,
                '-o', output_file,
                '-v', self.genome_version,
                '-p'  # Preserve VCF columns
            ]
            
            # Execute command
            self.logger.info(f"Executing command: {' '.join(cmd)}")
            result = subprocess.run(cmd, 
                                 capture_output=True, 
                                 text=True, 
                                 check=True)
            
            self.logger.info("Annotation completed successfully")
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Annotation failed: {e.stderr}")
            raise RuntimeError(f"DbNSFP annotation failed: {e.stderr}")
            
        finally:
            os.chdir(original_dir)
            
    def cleanup(self):
        """Clean up resources"""
        # Close log handlers
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)

# configuration for app.py
class DbNSFPConfig:
    """Configuration settings for DbNSFP integration"""
    
    DBNSFP_DIR = os.path.join(os.getcwd(), 'data', 'dbnsfp')
    GENOME_VERSION = "hg38"  # Default genome version
    JAVA_MEMORY = "5g"      # Default Java memory allocation
    
    @classmethod
    def validate_config(cls):

        # to validate DbNSFP configuration

        if not os.path.exists(cls.DBNSFP_DIR):
            raise FileNotFoundError(f"DbNSFP directory not found: {cls.DBNSFP_DIR}")
            
        java_file = os.path.join(cls.DBNSFP_DIR, 'search_dbNSFP47a.class')
        if not os.path.exists(java_file):
            raise FileNotFoundError(f"DbNSFP Java program not found: {java_file}")