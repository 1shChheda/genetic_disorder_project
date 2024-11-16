# Genetic Disorder Detection Project

## Project Structure (Current Stage Only)

```
genetic_disorder_detection_project/
├── data/                       # Directory to store raw and processed data
│   ├── raw/                    # Raw input VCF files
│   ├── processed/              # Processed output files
│       ├── <timestamped-folder>/  # Each run generates unique output folder
│           ├── processed_variants_<timestamp>.csv
│           ├── metadata_<timestamp>.txt
├── src/                        # Source code
│   ├── parser/                 # VCF parsing logic
│   │   ├── __init__.py         
│   │   └── vcf_parser.py       # Main VCF parsing module
│   ├── app/                    # Flask app
│   │   ├── templates/          # HTML files for the UI
│   │   ├── static/             # Static assets (CSS, JS, etc.)
│   │   └── app.py              # Main Flask app
├── tests/                      # Unit tests
│   ├── __init__.py
│   └── test_vcf_parser.py      # Tests for the parser module
├── venv/                       # Virtual environment for Linux
├── .venv/                      # Virtual environment for Windows
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation (you are here)
```

## Setup Instructions

### 1. Clone the Repository
Clone the project repository to your local machine:
```bash
git clone https://github.com/1shChheda/genetic_disorder_project.git
cd genetic_disorder_project
```

### 2. Set Up Virtual Environments
The project supports both Linux (`venv`) and Windows (`.venv`) environments. Follow the steps below to activate the correct environment for your operating system.

#### For Linux
```bash
source venv/bin/activate
```

#### For Windows
```bash
.\.venv\Scripts\activate
```

### 3. Install Dependencies
With the virtual environment activated, install the required packages listed in `requirements.txt`:
```bash
pip install -r requirements.txt
```

## Usage

The `vcf_parser.py` script parses VCF files, extracts metadata, and saves the variant information to a CSV file.

1. **Start the Flask server**:
    ```bash
    python -m src.app.app
    ```

2. Open your browser and navigate to **http://127.0.0.1:5000/** to access the web interface.

3. Upload a VCF file, and the parser will process it. The output CSV and metadata file will be saved in the `data/processed/<timestamped-folder>/` directory.

4. **(Optional) Running Test**:
    To verify that the parsing functionality works as expected, use `pytest` to run the unit test `test_vcf_parser.py`:
    ```bash
    pytest tests/
    ```
    This will run all tests in the `tests/` directory. A successful test run confirms that the parser correctly reads the VCF data and stores it in the desired format.

## Project Status
This project is in the initial stages of development. Currently, only VCF parsing and storing functionality is implemented. Future stages will include data filtering, variant annotation, and web interface development.


