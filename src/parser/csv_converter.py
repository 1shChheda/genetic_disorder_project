import os
import csv
import pandas as pd
import logging
from datetime import datetime

class CSVConverter:
    """
    Converts CSV files to VCF format compatible with dbNSFP annotation.
    
    This class handles the transformation of CSV files containing variant data
    into a VCF format that can be processed by the dbNSFP annotation tool.
    """
    
    def __init__(self):
        """Initialize the CSV converter with logging"""
        self.logger = logging.getLogger(__name__)
        
    def setup_logging(self):
        """Set up logging configuration"""
        log_dir = 'logs'
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f'csv_converter_{timestamp}.log')
        
        self.logger = logging.getLogger('CSVConverter')
        self.logger.setLevel(logging.INFO)
        
        handlers = [
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
        
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        for handler in handlers:
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def convert_to_vcf(self, csv_file, output_dir):
        """
        Convert a CSV file to VCF format for dbNSFP annotation
        
        Args:
            csv_file (str): Path to input CSV file
            output_dir (str): Directory to save the converted VCF file
            
        Returns:
            dict: Contains paths to output files and processing info
        """
        self.logger.info(f"Converting CSV file to VCF: {csv_file}")
        
        # Extract timestamp from the output_dir
        timestamp = os.path.basename(output_dir)
        os.makedirs(output_dir, exist_ok=True)
        
        # Define output VCF file path
        output_vcf = os.path.join(output_dir, 'dbnsfp_input.vcf')
        
        try:
            # Read the CSV file using pandas
            df = pd.read_csv(csv_file)
            
            # Check required columns - at minimum we need chromosome, position, reference, and alternate alleles
            required_cols = self._identify_required_columns(df)
            if not required_cols:
                raise ValueError("CSV file is missing required columns for VCF conversion")
            
            # Create VCF file
            with open(output_vcf, 'w') as vcf_file:
                # Write VCF header (minimal required for dbNSFP)
                # vcf_file.write("##fileformat=VCFv4.2\n")
                vcf_file.write('#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n')
                
                # Write data rows
                for _, row in df.iterrows():
                    chrom = str(row[required_cols['chrom']])
                    pos = str(row[required_cols['pos']])
                    ref = str(row[required_cols['ref']])
                    alt = str(row[required_cols['alt']])
                    
                    # Format with required VCF fields
                    vcf_line = f"{chrom}\t{pos}\t.\t{ref}\t{alt}\t.\t.\t.\n"
                    vcf_file.write(vcf_line)
            
            self.logger.info(f"CSV successfully converted to VCF: {output_vcf}")
            
            return {
                'output_folder': output_dir,
                'parsed_file': output_vcf,
                'timestamp': timestamp
            }
            
        except Exception as e:
            self.logger.error(f"Error converting CSV to VCF: {str(e)}")
            raise RuntimeError(f"Failed to convert CSV to VCF: {e}")
    
    def _identify_required_columns(self, df):
        """
        Identify required columns in the CSV file
        
        This method tries to find the columns containing chromosome, position, 
        reference, and alternate allele information using common naming patterns.
        
        Args:
            df (DataFrame): Pandas DataFrame containing the CSV data
            
        Returns:
            dict: Mapping of required fields to column names
        """
        columns = df.columns
        result = {}
        
        # Try to identify chromosome column
        chrom_candidates = [col for col in columns if col.lower() in 
                           ['chrom', 'chromosome', 'chr', '#chrom', '#chromosome']]
        if chrom_candidates:
            result['chrom'] = chrom_candidates[0]
        
        # Try to identify position column
        pos_candidates = [col for col in columns if col.lower() in 
                         ['pos', 'position', 'start', 'pos_hg38', 'pos_hg19']]
        if pos_candidates:
            result['pos'] = pos_candidates[0]
        
        # Try to identify reference allele column
        ref_candidates = [col for col in columns if col.lower() in 
                         ['ref', 'reference', 'ref_allele']]
        if ref_candidates:
            result['ref'] = ref_candidates[0]
        
        # Try to identify alternate allele column
        alt_candidates = [col for col in columns if col.lower() in 
                         ['alt', 'alternate', 'alt_allele']]
        if alt_candidates:
            result['alt'] = alt_candidates[0]
        
        # Return result only if all required columns were found
        if len(result) == 4:
            return result
        
        self.logger.warning("Could not identify all required columns in CSV file")
        self.logger.warning(f"Found columns: {', '.join(columns)}")
        self.logger.warning(f"Required: chromosome, position, reference allele, alternate allele")
        
        return None