from flask import Flask, render_template, request, redirect, url_for, flash
import os
from ..parser.vcf_parser import parse_vcf
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

#PATHS
UPLOAD_FOLDER = './data/raw/'
PROCESSED_FOLDER = './data/processed/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#to ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'vcf_file' not in request.files:
        flash('No file part')
        return redirect(request.url)

    file = request.files['vcf_file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    if file:
        #saving uploaded file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        input_vcf = os.path.join(app.config['UPLOAD_FOLDER'], f"{timestamp}_{file.filename}")
        file.save(input_vcf)

        #processing the VCF file
        parse_vcf(input_vcf, PROCESSED_FOLDER)

        flash(f"File processed successfully. Outputs stored in {PROCESSED_FOLDER}")
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
