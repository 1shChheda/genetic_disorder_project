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

# This is for simulating 3rd MAIN API call (MultiQueryFileUpload), since it wont work on Postman
import requests

#setting the URL for MultiQueryFileUpload
url = "http://database.liulab.science/MultiQueryFileUpload"

#open the VCF file
files = {'queryFile': open('src/app/tryhg38.vcf', 'rb')}

#adding headers (mimicking browser behavior)
headers = {
    "Origin": "http://database.liulab.science",
    "Referer": "http://database.liulab.science/dbNSFPconn",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}

#send the POST request
response = requests.post(url, files=files, headers=headers)

#print the response
print(response.status_code)
print(response.text)

# ITS WORKING! (atleast for the sample vcf file from this site itself. Not on our VCF file YET)
# Now, I'll refine it ahead