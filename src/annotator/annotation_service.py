import os
from datetime import datetime
import logging
import pandas as pd
from typing import Dict, Any, Optional
from .vep_annotator import VEPAnnotator
from .dbnsfp_annotator import DbNSFPAnnotator
from ..parser.vep_parser import VEPParser
from ..parser.dbnsfp_parser import DbNSFPParser

class AnnotationWorkflow:
    """TO Manage the complete annotation workflow for different annotators"""
    
    def __init__(self, annotation_type="dbnsfp", **kwargs):
        self.annotation_type = annotation_type
        self.parser = self._get_parser()
        self.annotator = self._get_annotator(**kwargs)
        self.logger = logging.getLogger(__name__)
        
    def _get_parser(self):
        """Get appropriate parser based on annotation type"""
        if self.annotation_type == "vep":
            return VEPParser()
        elif self.annotation_type == "dbnsfp":
            return DbNSFPParser()
        else:
            raise ValueError(f"Unknown annotation type: {self.annotation_type}")
            
    def _get_annotator(self, **kwargs):
        """Get appropriate annotator based on annotation type"""
        if self.annotation_type == "vep":
            return VEPAnnotator(**kwargs)
        elif self.annotation_type == "dbnsfp":
            return DbNSFPAnnotator(**kwargs)
        else:
            raise ValueError(f"Unknown annotation type: {self.annotation_type}")
            
    def process(self, input_vcf, output_dir):
        """Process the complete annotation workflow"""

        self.logger.info(f"Starting {self.annotation_type} annotation for {input_vcf}")
        output_folder = None
        parse_result = None

        try:
            # Step 1: Parse VCF file
            self.logger.info(f"Parsing VCF file: {input_vcf}")
            parse_result = self.parser.parse(input_vcf, output_dir)
            output_folder = parse_result['output_folder']
            parsed_file = parse_result['parsed_file']
            
            # Create a cancellation marker file path (will check if this exists)
            cancel_file = os.path.join(output_folder, "cancel.txt")
            
            # Check if process is already cancelled
            if os.path.exists(cancel_file):
                raise InterruptedError("Process cancelled by user")
            
            # Step 2: Setup annotator
            self.annotator.setup()
            
            # Check for cancellation again
            if os.path.exists(cancel_file):
                raise InterruptedError("Process cancelled by user")
            
            # Step 3: Perform annotation
            self.logger.info(f"Annotating variants using {self.annotation_type}")
            annotated_file = os.path.join(output_folder, f'{self.annotation_type}_annotated_variants.csv')
            
            # Get the result of annotation
            annotation_result = self.annotator.annotate(parsed_file, annotated_file)

            # Check for cancellation again
            if os.path.exists(cancel_file):
                raise InterruptedError("Process cancelled by user")

            # Ensure it properly logs completion before returning
            self.logger.info(f"Annotation workflow completed successfully for {self.annotation_type}")

            return {
                'output_folder': output_folder,
                'parsed_file': parsed_file,
                'annotated_file': annotated_file,
                'timestamp': parse_result['timestamp'],
                'status': 'completed'
            }

        except InterruptedError as e:
            self.logger.warning(f"Process cancelled: {str(e)}")
            return {
                'timestamp': parse_result['timestamp'] if parse_result else None,
                'output_folder': output_folder if output_folder else None,
                'status': 'cancelled',
                'error': str(e)
            }

        except Exception as e:
            self.logger.error(f"Error in annotation workflow: {str(e)}")
            return {
                'timestamp': parse_result['timestamp'] if parse_result else None,
                'output_folder': output_folder if output_folder else None,
                'status': 'error',
                'error': str(e)
            }

        finally:
            try:
                self.annotator.cleanup()
            except Exception as cleanup_error:
                self.logger.warning(f"Error during cleanup: {str(cleanup_error)}")