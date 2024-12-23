import os
from datetime import datetime
from .base_parser import BaseParser

class DbNSFPParser(BaseParser):


    # Imp fn: Prepares VCF file for dbNSFP annotation by filtering headers and data.
    def parse(self, input_vcf, output_dir):
        
    # args:
        #     input_vcf (str): Path to input VCF file
        #     output_dir (str): Directory to save processed files
            
    # output:
        #     dict: Contains paths to output files and processing info
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_folder = os.path.join(output_dir, timestamp)
        os.makedirs(output_folder, exist_ok=True)
        
        processed_vcf = os.path.join(output_folder, 'dbnsfp_input.vcf')
        
        try:
            with open(input_vcf, 'r') as infile:
                lines = infile.readlines()
                
            #keeping only the header line and variant data (exclude metadata)
            header = next(line for line in lines if line.startswith('#CHROM'))
            variant_lines = [line for line in lines if not line.startswith('#')]
            
            with open(processed_vcf, 'w') as outfile:
                outfile.write(header)
                outfile.writelines(variant_lines)
                
        except Exception as e:
            raise RuntimeError(f"Failed to parse VCF file for dbNSFP: {e}")
            
        return {
            'output_folder': output_folder,
            'parsed_file': processed_vcf,
            'timestamp': timestamp
        }