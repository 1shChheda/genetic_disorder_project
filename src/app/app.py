import os
from flask import Flask, request, render_template, redirect, url_for
from src.parser.vcf_parser import parse_vcf
from src.annotator.vep_annotator import annotate_variants

app = Flask(__name__)

#PATHS
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'data/raw')
PROCESSED_FOLDER = os.path.join(os.getcwd(), 'data/processed')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'vcf_file' not in request.files:
        return 'No file part'
    file = request.files['vcf_file']
    if file.filename == '':
        return 'No selected file'
    if file:
        input_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(input_path)

        # Step 1: Parse VCF
        output_folder = parse_vcf(input_vcf=input_path, output_dir=PROCESSED_FOLDER)

        # Step 2: Annotate variants
        parsed_csv = os.path.join(output_folder, 'parsed_variants.csv')
        annotated_csv = os.path.join(output_folder, 'annotated_variants.csv')
        annotate_variants(parsed_csv, annotated_csv)

        return f'File processed. Outputs saved in {output_folder}'

if __name__ == '__main__':
    app.run(debug=True)
