# execute this file using the command: python -m src.app.dbNSFP

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

# Base URLs
BASE_URL = "http://database.liulab.science"
DB_CONN_URL = f"{BASE_URL}/dbNSFPconn"
ASELECT_URL = f"{BASE_URL}/aSelect"
MULTIQUERY_UPLOAD_URL = f"{BASE_URL}/MultiQueryFileUpload"

# Headers (to mimic the browser)
HEADERS = {
    "Origin": "http://database.liulab.science",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}

# 1. Select the database type
def select_database_type(session, db_type="academic"):
    print("Selecting database type...")
    data = {"connDB": db_type}
    response = session.post(DB_CONN_URL, data=data, headers={**HEADERS, "Referer": f"{BASE_URL}/dbNSFP"})
    response.raise_for_status()
    print("Database type selected successfully.")

# 2. Select variant options
def select_variant_options(session, range_type="hg38", selected_fields=None):
    print("Selecting variant options...")
    if selected_fields is None:
        selected_fields = [
            "REVEL_score",
            "REVEL_rankscore",
            "genename",
            "Ensembl_geneid",
        ]  # default fields

    # combining all selected fields into a single comma-separated string
    selected_fields_string = ", ".join(selected_fields)

    data = {
        "range": range_type,
        "selectBasicInfoA": "chr, pos, ref, alt, aaref, aaalt, rs_dbSNP, hg19_chr, hg19_pos, hg18_chr, hg18_pos, aapos, genename, Ensembl_geneid, Ensembl_transcriptid, Ensembl_proteinid",
        "selectA": selected_fields_string,
    }

    response = session.post(ASELECT_URL, data=data, headers={**HEADERS, "Referer": DB_CONN_URL})
    if response.status_code == 204:
        print("Variant options selected successfully.")
    else:
        print("Unexpected response during variant selection:", response.text)

# 3. Upload file and get annotation results
def upload_file_for_annotation(session, file_path):
    print("Uploading file for annotation...")
    with open(file_path, "rb") as file:
        files = {"queryFile": file}
        response = session.post(MULTIQUERY_UPLOAD_URL, files=files, headers={**HEADERS, "Referer": DB_CONN_URL})
        response.raise_for_status()
    print("File uploaded successfully.")
    return response.text

# 4. [WEB-SCRAPING] [STORING RESPONSE RESULTS INTO CSV FILE]
def parse_results_to_csv(html_response, output_csv_path):
    print("Parsing HTML response and saving results to CSV...")
    soup = BeautifulSoup(html_response, "html.parser")
    table = soup.find("table")

    # extract headers
    headers = [th.text.strip() for th in table.find_all("th")]

    # extract rows
    rows = []
    for tr in table.find_all("tr")[1:]:
        cells = [td.text.strip() for td in tr.find_all("td")]
        rows.append(cells)

    # write to CSV
    with open(output_csv_path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(headers)
        writer.writerows(rows)

    print(f"Results saved to {output_csv_path}.")

# Main function to orchestrate the process
def main():
    vcf_file_path = "src/app/tryhg38.vcf"
    output_csv_path = "src/app/annotated_results.csv"

    with requests.Session() as session:
        # Step 1: Select database type
        select_database_type(session, db_type="academic")

        # Step 2: Select variant options
        selected_fields = ["DANN_score", "DANN_rankscore", "GERP_NR", "GERP_RS", "GERP_RS_rankscore", "phastCons100way_vertebrate", "phastCons100way_vertebrate_rankscore", "phastCons470way_mammalian", "phastCons470way_mammalian_rankscore", "phastCons17way_primate", "phastCons17way_primate_rankscore"]
        select_variant_options(session, range_type="hg38", selected_fields=selected_fields)

        # Step 3: Upload file and get results
        html_response = upload_file_for_annotation(session, file_path=vcf_file_path)

        # Step 4: Parse results and save to CSV
        parse_results_to_csv(html_response, output_csv_path)

if __name__ == "__main__":
    main()

# ITS WORKING! (atleast for the sample vcf file from this site itself. Not on our VCF file YET)