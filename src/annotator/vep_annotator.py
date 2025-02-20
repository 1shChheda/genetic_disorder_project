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
        self.clinvar_data = self._load_clinvar_data() if clinvar_path else {}
        self.vep_base_url = "https://rest.ensembl.org/vep/human/region/"
        self.api_call_count = 0
        self.error_count = 0
        
    def setup(self):
        # Required by BaseAnnotator interface
        self.logger.info("VEP Annotator setup complete")
        
    def cleanup(self):
        # Required by BaseAnnotator interface
        self.logger.info("VEP Annotator cleanup complete")

    def setup_logging(self):
        log_dir = 'logs'
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f'vep_annotation_{timestamp}.log')
        
        self.logger = logging.getLogger('VEPAnnotator')
        self.logger.setLevel(logging.INFO)
        
        handlers = [
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
        
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        for handler in handlers:
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    #loading clinvar data from clinvar.vcf file, along with progress tracking
    def _load_clinvar_data(self):
        if not self.clinvar_path:
            self.logger.warning("No ClinVar path provided, skipping ClinVar data loading")
            return {}
            
        self.logger.info(f"Loading ClinVar data from: {self.clinvar_path}")
        clinvar_variants = {}
        
        try:
            if not os.path.exists(self.clinvar_path):
                self.logger.warning(f"ClinVar file not found at {self.clinvar_path}")
                return {}
                
            total_lines = sum(1 for _ in open(self.clinvar_path, 'r'))
            
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
                        
            self.logger.info(f"Successfully loaded {len(clinvar_variants)} ClinVar variants")
            return clinvar_variants
            
        except Exception as e:
            self.logger.error(f"Error loading ClinVar data: {str(e)}")
            return {}

    #extracting the "END" position from "INFO" field
    def _extract_end_position(self, info_field):
        if not info_field:
            return None
        for entry in info_field.split(";"):
            if entry.startswith("END="):
                return entry.split("=")[1]
        return None

    #extracting clinical significance from ClinVar INFO field
    def _extract_clinvar_significance(self, info_field):
        if not info_field or 'CLNSIG=' not in info_field:
            return ''
        sig_start = info_field.index('CLNSIG=') + 7
        sig_end = info_field.index(';', sig_start) if ';' in info_field[sig_start:] else len(info_field)
        return info_field[sig_start:sig_end]

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
            
        variant_id = f"{chrom}:{start}:{ref}>{alt}"
        self.api_call_count += 1
        
        try:
            #removing 'chr' prefix (ensembl api call mein better padta hai)
            region = f"{chrom.replace('chr', '')}:{start}-{end}"
            url = f"{self.vep_base_url}{region}/{alt}"
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:  # Rate limit exceeded
                self.logger.warning("Rate limit exceeded, waiting before retry...")
                time.sleep(60)  #wait for 60 seconds before retry
                return self._query_ensembl_vep(chrom, start, end, ref, alt)
            else:
                self.error_count += 1
                self.logger.warning(f"VEP API error for {variant_id}: Status {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            self.error_count += 1
            self.logger.error(f"Failed to query VEP API for {variant_id}: {str(e)}")
            return None

    # IMP fn no.2:
    def annotate(self, input_file, output_file):
        # Main annotation method required by BaseAnnotator interface
        self.logger.info(f"Starting VEP annotation: {input_file} -> {output_file}")
        
        try:
            total_variants = sum(1 for line in open(input_file)) - 1  #subtracting header
            processed = 0
            start_time = time.time()
            
            with open(input_file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
                reader = csv.DictReader(infile)
                fieldnames = reader.fieldnames + [
                    'VEP_Consequence', 'VEP_Impact', 'VEP_Gene',
                    'VEP_Protein_Position', 'VEP_Amino_Acids',
                    'ClinVar_Significance', 'ClinVar_ID',
                    'Variant_End_Position', 'Is_Reference'
                ]
                
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for row in tqdm(reader, total=total_variants, desc="Processing variants"):
                    end_pos = self._extract_end_position(row.get('INFO', '')) or row['POS']
                    
                    #initializing annotation fields (to later update in the output file)
                    annotation_fields = {
                        'VEP_Consequence': '',
                        'VEP_Impact': '',
                        'VEP_Gene': '',
                        'VEP_Protein_Position': '',
                        'VEP_Amino_Acids': '',
                        'ClinVar_Significance': '',
                        'ClinVar_ID': '',
                        'Variant_End_Position': end_pos,
                        'Is_Reference': 'Yes' if row['ALT'] == '.' else 'No'
                    }
                    
                    # Only query VEP for actual variants
                    if row['ALT'] != '.':
                        variant_id = f"{row['CHROM']}:{row['POS']}:{row['REF']}>{row['ALT']}"
                        
                        #getting VEP annotations
                        vep_result = self._query_ensembl_vep(
                            row['CHROM'], row['POS'], end_pos, row['REF'], row['ALT']
                        )
                        
                        if vep_result and len(vep_result) > 0:
                            first_result = vep_result[0]
                            annotation_fields['VEP_Consequence'] = first_result.get('most_severe_consequence', '')
                            
                            if 'transcript_consequences' in first_result:
                                transcript = first_result['transcript_consequences'][0]
                                annotation_fields.update({
                                    'VEP_Impact': transcript.get('impact', ''),
                                    'VEP_Gene': transcript.get('gene_symbol', ''),
                                    'VEP_Protein_Position': transcript.get('protein_start', ''),
                                    'VEP_Amino_Acids': f"{transcript.get('amino_acids', '')}"
                                })
                        
                        # Get ClinVar annotations
                        clinvar_info = self.clinvar_data.get(variant_id, {})
                        annotation_fields.update({
                            'ClinVar_Significance': self._extract_clinvar_significance(clinvar_info.get('info', '')),
                            'ClinVar_ID': clinvar_info.get('id', '')
                        })
                    
                    # Update row with annotations and write
                    row.update(annotation_fields)
                    writer.writerow(row)
                    processed += 1
                    
                    # Add delay to respect API rate limits
                    time.sleep(0.1)
                    
            # final statistics
            elapsed_time = time.time() - start_time
            self.logger.info(f"\nAnnotation completed:")
            self.logger.info(f"Total variants processed: {processed}")
            self.logger.info(f"API calls made: {self.api_call_count}")
            self.logger.info(f"Errors encountered: {self.error_count}")
            self.logger.info(f"Total time: {elapsed_time:.2f} seconds")
            
        except Exception as e:
            self.logger.error(f"Error during annotation process: {str(e)}")
            raise