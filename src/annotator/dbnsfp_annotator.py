# Context: I am trying to use http://database.liulab.science/dbNSFP for annotation via dbNSFP
# It has three main API/Request Calls made
# THIS IS FOR TESTING ON POSTMAN:
# NOTE: I have mimicked the webpage API call as closely as possible, thus IMPORTANTLY make sure to use the given "Headers" for everything to make work!
# First:
    # On homepage, we get options to select "Academic" or "Commercial"
    # URL:
        # POST http://database.liulab.science/dbNSFPconn
    # Body (x-www-form-urlencoded):
        # connDB: academic or commercial
    # Headers:
        # Content-Type: application/x-www-form-urlencoded
        # Origin: http://database.liulab.science
        # Referer: http://database.liulab.science/dbNSFP
        # User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36

# Second:
    # On /dbNSFPconn page, we get to select Select Variant Options
    # URL:
        # POST http://database.liulab.science/aSelect
    # Body (x-www-form-urlencoded):
        # range: hg38
        # selectBasicInfoA: chr, pos, ref, alt, aaref, aaalt, rs_dbSNP, hg19_chr, hg19_pos, hg18_chr, hg18_pos, aapos, genename, Ensembl_geneid, Ensembl_transcriptid, Ensembl_proteinid

        # (DEPENDING ON OPTION YOU CHOOSE)
        # selectA: clinvar_id, clinvar_clnsig, clinvar_trait, clinvar_review, clinvar_hgvs, clinvar_var_source, clinvar_MedGen_id, clinvar_OMIM_id, clinvar_Orphanet_id

    # Headers:
        # Content-Type: application/x-www-form-urlencoded
        # Origin: http://database.liulab.science
        # Referer: http://database.liulab.science/dbNSFPconn
        # User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36

    # NOTE: here you'll get a "204 No Content" response - MEANING: it has worked properly.
        # IF "404 error" or any other error, re-check the settings I have provided above.

# Third (MAIN IMP!):
    # on /dbNSFPconn page, towards the bottom, it also has upload VCF File for Annotation option
    # I tried using similar settings to test on POSTMAN, it failed! (ERROR in Uploading File)

# I've now properly structured each step, 
    # so that the user has choices to select databases (which he wants to be considered to be reffered during annotation)
    # & also web-scraping the response page to extract the results into a csv file

import requests
from bs4 import BeautifulSoup
import csv
import logging
from datetime import datetime
import os
from .base_annotator import BaseAnnotator

class DbNSFPAnnotator(BaseAnnotator):
    def __init__(self, db_type="academic"):
        self.db_type = db_type
        self.base_url = "http://database.liulab.science"
        self.session = requests.Session()
        self.setup_logging()
        
    def setup_logging(self):
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
        #initialize dbNSFP connection and settings
        # Headers (to mimic the browser)
        self.headers = {
            "Origin": self.base_url,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        }
        
        self._select_database_type()
        self._select_variant_options()
        
    # 1. Select the database type
    def _select_database_type(self):
        self.logger.info(f"Selecting {self.db_type} database type...")
        response = self.session.post(
            f"{self.base_url}/dbNSFPconn",
            data={"connDB": self.db_type},
            headers={**self.headers, "Referer": f"{self.base_url}/dbNSFP"}
        )
        response.raise_for_status()
        self.logger.info("Database type selected successfully")

    # 2. Select variant options
    def _select_variant_options(self, range_type="hg38", selected_fields=None):
        if selected_fields is None:
            selected_fields = [
                "DANN_score", "DANN_rankscore",
                "GERP_NR", "GERP_RS", "GERP_RS_rankscore",
                "phastCons100way_vertebrate", "phastCons100way_vertebrate_rankscore",
                "phastCons470way_mammalian", "phastCons470way_mammalian_rankscore",
                "phastCons17way_primate", "phastCons17way_primate_rankscore"
            ]
            
        data = {
            "range": range_type,
            "selectBasicInfoA": "chr, pos, ref, alt, aaref, aaalt, rs_dbSNP, hg19_chr, hg19_pos, hg18_chr, hg18_pos, aapos, genename, Ensembl_geneid, Ensembl_transcriptid, Ensembl_proteinid",
            "selectA": ", ".join(selected_fields)
        }
        
        response = self.session.post(
            f"{self.base_url}/aSelect",
            data=data,
            headers={**self.headers, "Referer": f"{self.base_url}/dbNSFPconn"}
        )
        
        if response.status_code == 204:
            self.logger.info("Variant options selected successfully")
        else:
            self.logger.error(f"Unexpected response: {response.status_code}")
            raise Exception("Failed to select variant options")

    # 3. Upload file and get annotation results
    def annotate(self, input_file, output_file):
        #annotate variants using dbNSFP
        self.logger.info(f"Starting annotation: {input_file} -> {output_file}")
        
        try:
            with open(input_file, "rb") as file:
                response = self.session.post(
                    f"{self.base_url}/MultiQueryFileUpload",
                    files={"queryFile": file},
                    headers={**self.headers, "Referer": f"{self.base_url}/dbNSFPconn"}
                )
                response.raise_for_status()
            
            self._parse_results_to_csv(response.text, output_file)
            self.logger.info("Annotation completed successfully")
            
        except Exception as e:
            self.logger.error(f"Annotation failed: {str(e)}")
            raise

    # 4. [WEB-SCRAPING] [STORING RESPONSE RESULTS INTO CSV FILE]
    def _parse_results_to_csv(self, html_response, output_csv):
        soup = BeautifulSoup(html_response, "html.parser")
        table = soup.find("table")
        
        if not table:
            raise ValueError("No results table found in response")
            
        headers = [th.text.strip() for th in table.find_all("th")]
        rows = []
        for tr in table.find_all("tr")[1:]:
            cells = [td.text.strip() for td in tr.find_all("td")]
            rows.append(cells)
            
        with open(output_csv, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(headers)
            writer.writerows(rows)
            
        self.logger.info(f"Results saved to {output_csv}")

    def cleanup(self):
        """Cleanup session"""
        self.session.close()

# ITS WORKING! (atleast for the sample vcf file from this site itself. Not on our VCF file YET)