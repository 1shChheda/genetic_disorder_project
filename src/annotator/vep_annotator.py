import csv
import requests
import time
import json
import os
import logging
from datetime import datetime
from tqdm import tqdm

class VEPAnnotator:
    def __init__(self, clinvar_path=None):

        self.clinvar_path = clinvar_path
        
        self.setup_logging()
        
        #loading clinvar data
        self.logger.info("Initializing VEP Annotator")
        self.clinvar_data = self._load_clinvar_data() if clinvar_path else {}
        
        # Ensembl VEP API base URL
        self.vep_base_url = "https://rest.ensembl.org/vep/human/region/"
        
        self.api_call_count = 0
        self.error_count = 0
    
    def setup_logging(self):

        log_dir = 'logs'
        os.makedirs(log_dir, exist_ok=True)
        

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        log_file = os.path.join(log_dir, f'annotation_{timestamp}.log')
        

        self.logger = logging.getLogger('VEPAnnotator')
        self.logger.setLevel(logging.INFO)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    #loading clinvar data from clinvar.vcf file, along with progress tracking
    def _load_clinvar_data(self):

        self.logger.info(f"Loading ClinVar data from: {self.clinvar_path}")
        clinvar_variants = {}
        
        try:
            #counting total lines first for progress bar
            total_lines = sum(1 for _ in open(self.clinvar_path, 'r'))
            loaded_variants = 0
            
            with open(self.clinvar_path, 'r') as f:
                for line in tqdm(f, total=total_lines, desc="Loading ClinVar data"):
                    if line.startswith('#'):
                        continue
                    fields = line.strip().split('\t')
                    if len(fields) > 7:
                        chrom, pos, var_id, ref, alt = fields[0], fields[1], fields[2], fields[3], fields[4]
                        info = fields[7]
                        clinvar_key = f"{chrom}:{pos}:{ref}>{alt}"
                        clinvar_variants[clinvar_key] = {
                            'id': var_id,
                            'info': info
                        }
                        loaded_variants += 1
            
            self.logger.info(f"Successfully loaded {loaded_variants} ClinVar variants")
            return clinvar_variants
            
        except Exception as e:
            self.logger.error(f"Error loading ClinVar data: {str(e)}")
            return {}
        
    #extracting the "END" position from "INFO" field
    def _extract_end_position(self, info_field):

        for entry in info_field.split(";"):
            if entry.startswith("END="):
                return entry.split("=")[1]
        return None
    
    #extracting clinical significance from ClinVar INFO field
    def _extract_clinvar_significance(self, info_field):

        if 'CLNSIG=' in info_field:
            sig_start = info_field.index('CLNSIG=') + 7
            sig_end = info_field.index(';', sig_start) if ';' in info_field[sig_start:] else len(info_field)
            return info_field[sig_start:sig_end]
        return ''
    
    # IMP fn no.1: 
    def _query_ensembl_vep(self, chrom, start, end, ref, alt):
    # args:
        # chrom: Chromosome
        # pos: Position
        # ref: Reference allele
        # alt: Alternate allele

        #NOTE: skipping API call if there's no alternate allele
        if alt == '.' or not alt:
            self.logger.debug(f"Skipping VEP query for {chrom}:{start} - reference call or missing ALT")
            return None
        
        self.api_call_count += 1
        variant_id = f"{chrom}:{start}:{ref}>{alt}"
        
        try:
            #removing 'chr' prefix (ensembl api call mein better padta hai)
            region = f"{chrom.replace('chr', '')}:{start}-{end}"
            url = f"{self.vep_base_url}{region}/{alt}"
            
            self.logger.debug(f"Querying VEP API for variant {variant_id}")
            
            headers = {"Content-Type": "application/json"}
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                self.logger.debug(f"Successfully retrieved VEP data for {variant_id}")
                return response.json()
            else:
                self.error_count += 1
                self.logger.warning(f"VEP API error for {variant_id}: Status {response.status_code}")
                return {}
                
        except requests.exceptions.RequestException as e:
            self.error_count += 1
            self.logger.error(f"Failed to query VEP API for {variant_id}: {str(e)}")
            return {}
    
    # IMP fn no.2:
    def annotate_variants(self, input_csv, output_csv):
        # args:
        #     input_csv: path to input parsed variants CSV
        #     output_csv: path to output annotated variants CSV
        self.logger.info(f"Starting variant annotation: {input_csv} → {output_csv}")
        
        try:
            #counting total variants first for progress tracking
            total_variants = sum(1 for _ in open(input_csv)) - 1  #subtracting header
            self.logger.info(f"Total variants to process: {total_variants}")
            
            processed = 0
            start_time = time.time()
            
            with open(input_csv, 'r') as infile, \
                 open(output_csv, 'w', newline='') as outfile:
                
                reader = csv.DictReader(infile)
                fieldnames = reader.fieldnames + [
                    'VEP_Consequence', 'VEP_Impact', 'VEP_Gene', 
                    'ClinVar_Significance', 'ClinVar_ID',
                    'Variant_End_Position', 'Is_Reference'
                ]
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for row in tqdm(reader, total=total_variants, desc="Annotating variants"):
                    #if there's no "end" position, we will use "start" position itself
                    end_pos = self._extract_end_position(row.get('INFO', '')) or row['POS']
                    
                    #initializing annotation fields (to later update in the output file)
                    row.update({
                        'VEP_Consequence': '',
                        'VEP_Impact': '',
                        'VEP_Gene': '',
                        'ClinVar_Significance': '',
                        'ClinVar_ID': '',
                        'Variant_End_Position': end_pos,
                        'Is_Reference': 'Yes' if row['ALT'] == '.' else 'No'
                    })
                    
                    # Only query VEP for actual variants
                    if row['ALT'] != '.':
                        variant_id = f"{row['CHROM']}:{row['POS']}:{row['REF']}>{row['ALT']}"
                        self.logger.info(f"Processing variant: {variant_id}")
                        
                        #getting vep annotations
                        vep_result = self._query_ensembl_vep(
                            row['CHROM'], row['POS'], end_pos, row['REF'], row['ALT']
                        )
                        
                        #getting clinvar information
                        clinvar_key = variant_id
                        clinvar_info = self.clinvar_data.get(clinvar_key, {})
                        
                        if vep_result and len(vep_result) > 0:
                            first_result = vep_result[0]
                            row['VEP_Consequence'] = first_result.get('most_severe_consequence', '')
                            if 'transcript_consequences' in first_result:
                                transcript = first_result['transcript_consequences'][0]
                                row['VEP_Impact'] = transcript.get('impact', '')
                                row['VEP_Gene'] = transcript.get('gene_symbol', '')
                                
                            self.logger.debug(f"VEP annotations for {variant_id}: "
                                            f"consequence={row['VEP_Consequence']}, "
                                            f"impact={row['VEP_Impact']}, "
                                            f"gene={row['VEP_Gene']}")
                        

                        row['ClinVar_Significance'] = self._extract_clinvar_significance(
                            clinvar_info.get('info', '')
                        )
                        row['ClinVar_ID'] = clinvar_info.get('id', '')
                    
                    writer.writerow(row)
                    processed += 1
                    
                    #logging progress every 100 variants
                    if processed % 100 == 0:
                        elapsed_time = time.time() - start_time
                        rate = processed / elapsed_time
                        self.logger.info(f"Processed {processed}/{total_variants} variants "
                                       f"({rate:.2f} variants/second)")
                    
                    #delay added to not violate api rate limits
                    time.sleep(0.5)
            
            # final statistics
            elapsed_time = time.time() - start_time
            self.logger.info(f"\nAnnotation completed:")
            self.logger.info(f"Total variants processed: {processed}")
            self.logger.info(f"API calls made: {self.api_call_count}")
            self.logger.info(f"Errors encountered: {self.error_count}")
            self.logger.info(f"Total time: {elapsed_time:.2f} seconds")
            self.logger.info(f"Average rate: {processed/elapsed_time:.2f} variants/second")
            
        except Exception as e:
            self.logger.error(f"Error during annotation process: {str(e)}")
            raise

def annotate_variants(input_csv, output_csv, clinvar_path='data/clinvar/clinvar.vcf'):

    annotator = VEPAnnotator(clinvar_path)
    annotator.annotate_variants(input_csv, output_csv)