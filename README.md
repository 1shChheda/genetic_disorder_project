# Genetic Disorder Detection Project

## Project Overview (Current Stage Only)
This project processes VCF (Variant Call Format) files to detect genetic disorders through variant annotation. 
Currently, it supports two annotation methods:
- Ensembl VEP (Variant Effect Predictor) REST API
- dbNSFP (database of human non-synonymous SNVs and their functional predictions)

## Project Structure (Current Stage Only)
```
genetic_disorder_detection_project/
├── data/                           # Data storage directory
│   ├── raw/                        # Raw input VCF files
│   └── processed/                  # Processed output files
│       └── <timestamped-folder>/   # Unique folder for each run
│           ├── parsed_variants.csv
│           ├── annotated_variants.csv
│           └── metadata.txt
├── src/                           # Source code
│   ├── parser/                    # VCF parsing modules
│   │   ├── __init__.py
│   │   ├── base_parser.py        # Abstract base parser
│   │   ├── vep_parser.py         # VEP-specific parser
│   │   └── dbnsfp_parser.py      # dbNSFP-specific parser
│   ├── annotator/                 # Variant annotation modules
│   │   ├── __init__.py
│   │   ├── base_annotator.py     # Abstract base annotator
│   │   ├── vep_annotator.py      # VEP API implementation
│   │   ├── dbnsfp_annotator.py   # dbNSFP API implementation
│   │   └── annotation_service.py  # Workflow orchestration
│   └── app/                       # Web application
│       ├── templates/             # HTML templates
│       ├── static/               # Static assets
│       └── app.py                # Flask application
├── tests/                        # Unit tests
│   ├── __init__.py
│   └── test_vcf_parser.py       # Parser tests
├── logs/                        # Application logs
├── venv/                       # Virtual environment (Linux)
├── .venv/                      # Virtual environment (Windows)
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation
```

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/1shChheda/genetic_disorder_project.git
cd genetic_disorder_project
```

### 2. Set Up Virtual Environment
Choose the appropriate command based on your operating system:

#### For Linux
```bash
python -m venv venv
source venv/bin/activate
```

#### For Windows
```bash
python -m venv .venv
.\.venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

## Usage

1. **Start the Application**:
    ```bash
    python -m src.app.app
    ```

2. **Access the Web Interface**:
    Open your browser and navigate to `http://127.0.0.1:5000/`

3. **Process VCF Files**:
    i. Upload your VCF file through the web interface
    ii. Select annotation type:
        - *VEP*: Uses Ensembl's Variant Effect Predictor
        - *dbNSFP*: Uses the dbNSFP database (academic or commercial)
    iii. Submit for processing

4. **View Results**:
    - Results are stored in `data/processed/<timestamp>/`
    - Download options available through the web interface
    - Results include:
      - Parsed variant data
      - Annotation results
      - Processing metadata

5. **(Optional) Run Tests**
    To verify that the parsing functionality works as expected, use `pytest` to run the unit test `test_vcf_parser.py`:
    ```bash
    pytest tests/
    ```
    This will run all tests in the `tests/` directory. A successful test run confirms that the parser correctly reads the VCF data and stores it in the desired format.

## Project Status
This project is in the initial stages of development. The project currently supports:
- VCF file parsing
- Dual annotation pathways (VEP and dbNSFP)
- Web interface for file processing
- Results visualization and download

Future developments will include:
- Advanced filtering options
- Batch processing
- Additional annotation sources
- Enhanced visualization
- Machine learning integration
