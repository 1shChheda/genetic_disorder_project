import os
import csv
from datetime import datetime
from .base_parser import BaseParser

class VEPParser(BaseParser):


    # Imp fn.: Parses a VCF file for VEP annotation, extracting essential fields and preserving INFO.
    def parse(self, input_vcf, output_dir):
        
    # args:
        #     input_vcf (str): Path to input VCF file
        #     output_dir (str): Directory to save processed files
            
    # output:
        #     dict: Contains paths to output files and processing info
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_folder = os.path.join(output_dir, timestamp)
        os.makedirs(output_folder, exist_ok=True)
        
        parsed_csv = os.path.join(output_folder, 'vep_parsed_variants.csv')
        metadata_txt = os.path.join(output_folder, 'metadata.txt')
        
        try:
            with open(input_vcf, 'r') as vcf_file:
                reader = vcf_file.readlines()
            
            metadata = [line for line in reader if line.startswith('##')]
            data_lines = [line for line in reader if not line.startswith('#')]
            
            with open(metadata_txt, 'w') as meta_file:
                meta_file.writelines(metadata)
            
            header_line = next(line for line in reader if line.startswith('#CHROM'))
            header = header_line.strip().split('\t')
            info_index = header.index('INFO')
            
            with open(parsed_csv, 'w', newline='') as csv_file:
                writer = csv.writer(csv_file)
                output_header = ['CHROM', 'POS', 'ID', 'REF', 'ALT', 'QUAL', 'FILTER', 'INFO']
                writer.writerow(output_header)
                
                for line in data_lines:
                    fields = line.strip().split('\t')
                    chrom, pos, var_id, ref, alt, qual, filter_status, info = (
                        fields[0], fields[1], fields[2], fields[3], fields[4], 
                        fields[5], fields[6], fields[info_index]
                    )
                    
                    alt_alleles = alt.split(',')
                    for allele in alt_alleles:
                        writer.writerow([chrom, pos, var_id, ref, allele, qual, filter_status, info])
        
        except Exception as e:
            raise RuntimeError(f"Failed to parse VCF file for VEP: {e}")
        
        return {
            'output_folder': output_folder,
            'parsed_file': parsed_csv,
            'metadata_file': metadata_txt,
            'timestamp': timestamp
        }
