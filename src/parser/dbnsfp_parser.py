import os
import subprocess
from datetime import datetime
from .base_parser import BaseParser

class DbNSFPParser(BaseParser):
    def __init__(self, dbnsfp_dir=None):
        """
        Initialize DbNSFP parser with database directory
        
        Args:
            dbnsfp_dir (str): Path to dbNSFP database directory
        """
        self.dbnsfp_dir = dbnsfp_dir or os.path.join(os.getcwd(), 'data', 'dbnsfp')
        
    # Imp fn: Prepares VCF file for dbNSFP annotation by filtering headers and data.
    def parse(self, input_vcf, output_dir):

        # args:
            #     input_vcf (str): Path to input VCF file
            #     output_dir (str): Directory to save processed files
                
        # output:
            #     dict: Contains paths to output files and processing info
        
        # Extract timestamp from the output_dir instead of creating a new one
        timestamp = os.path.basename(output_dir)
        output_folder = output_dir  # Use the directory passed in, don't create a new one
        os.makedirs(output_folder, exist_ok=True)
        
        # Copy input VCF to output folder
        processed_vcf = os.path.join(output_folder, 'dbnsfp_input.vcf')
        
        try:
            # Filter and keep only necessary VCF content
            with open(input_vcf, 'r') as infile, open(processed_vcf, 'w') as outfile:
                for line in infile:
                    if line.startswith('#CHROM') or not line.startswith('#'):
                        outfile.write(line)
                        
        except Exception as e:
            raise RuntimeError(f"Failed to parse VCF file for dbNSFP: {e}")
            
        return {
            'output_folder': output_folder,
            'parsed_file': processed_vcf,
            'timestamp': timestamp
        }