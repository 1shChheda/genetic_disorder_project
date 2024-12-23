import os
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
        try:
            #  Step 1b: Parse VCF file
            parse_result = self.parser.parse(input_vcf, output_dir)
            output_folder = parse_result['output_folder']
            parsed_file = parse_result['parsed_file']
            
            # Step 1a: Setup annotator
            self.annotator.setup()
            
            #  Step 2: Perform annotation
            annotated_file = os.path.join(output_folder, f'{self.annotation_type}_annotated_variants.csv')
            self.annotator.annotate(parsed_file, annotated_file)
            
            return {
                'output_folder': output_folder,
                'parsed_file': parsed_file,
                'annotated_file': annotated_file,
                'timestamp': parse_result['timestamp']
            }
            
        finally:
            self.annotator.cleanup()