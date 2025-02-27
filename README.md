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
│   ├── dbnsfp/                     # Default dbNSFP database directory
│   ├── raw/                        # Raw input VCF files
│   └── processed/                  # Processed output files
│       └── <timestamped-folder>/   # Unique folder for each run
│           ├── parsed_variants.csv
│           ├── annotated_variants.csv
│           └── metadata.txt
├── src/                            # Source code
│   ├── parser/                     # VCF parsing modules
│   │   ├── __init__.py
│   │   ├── base_parser.py          # Abstract base parser
│   │   ├── vep_parser.py           # VEP-specific parser
│   │   └── dbnsfp_parser.py        # dbNSFP-specific parser
│   ├── annotator/                  # Variant annotation modules
│   │   ├── __init__.py
│   │   ├── base_annotator.py       # Abstract base annotator
│   │   ├── vep_annotator.py        # VEP API implementation
│   │   ├── dbnsfp_annotator.py     # dbNSFP implementation
│   │   └── annotation_service.py   # Workflow orchestration
│   ├── process/                    # Process management
│   │   ├── __init__.py
│   │   └── process_manager.py      # Manages annotation processes
│   ├── session/                    # Session management
│   │   ├── __init__.py
│   │   └── session_manager.py      # Handles user sessions
│   └── app/                        # Web application
│       ├── templates/              # HTML templates
│       ├── static/                 # Static assets
│       └── app.py                  # Flask application
├── tests/                          # Unit tests
│   ├── __init__.py
│   └── test_vcf_parser.py          # Parser tests
├── logs/                           # Application logs
├── venv/                           # Virtual environment (Linux)
├── .venv/                          # Virtual environment (Windows)
├── requirements.txt                # Python dependencies
└── README.md                       # Project documentation
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

### 4. Download and Set Up dbNSFP Database
The dbNSFP database is required for annotation. Follow these steps to download and extract it:

1. **Visit the dbNSFP Download Page**:
   - Navigate to [dbNSFP Download Page](https://sites.google.com/site/jpopgen/dbNSFP).

2. **Download the Database**:
   - Locate the latest version of dbNSFP suitable for your needs. 
   - RECOMMENDED VERSION: **dbNSFP v4.7**
   - Download the appropriate compressed file (`.zip` or `.tar.gz`).

3. **Extract the Database**:
   - **For Linux**:
     ```bash
     mkdir -p data/dbnsfp
     tar -xzvf dbNSFP*.tar.gz -C data/dbnsfp
     ```
   - **For Windows**:
     - Use a file extraction tool (e.g., 7-Zip) to extract the contents of the downloaded archive.
     - Extract the files into the `data\dbnsfp` directory within your project.

By default, the application expects the dbNSFP database files to be located in the relative path `/data/dbnsfp`. If you choose a different directory, ensure you provide the correct path during usage.

## Usage

1. **Start the Application**:
    ```bash
    python -m src.app.app
    ```

2. **Access the Web Interface**:
    Open your browser and navigate to `http://127.0.0.1:5000/`

3. **Database Path Configuration**:
    - Specify the dbNSFP database directory path where you have stored/extracted the database. 
    - By default, this is the relative path `/data/dbnsfp`.

4. **Process VCF Files**:
    1. Upload your VCF file through the web interface.
    2. Select annotation type:
        - *VEP*: Uses Ensembl's Variant Effect Predictor.
        - *dbNSFP*: Uses the dbNSFP database.
    3. Submit for processing.
    4. You can cancel the process at any time by clicking the **Cancel Process** button.

5. **View and Download Results**:
    - Once processing is complete, results will be displayed in the web interface.
    - You can download the annotated results directly through the web interface by clicking the **Download Results** button.
    - The downloaded file will be named in the format `<annotation_type>_annotated_variants_<timestamp>.csv`.

## Multi-tab Support
The application now supports working with multiple browser tabs simultaneously:
- Each browser tab gets a unique session
- Process management is isolated between tabs
- Resources are automatically cleaned up
- Session data expires after 24 hours of inactivity

## Project Status
This project is in the initial stages of development. It currently supports:
- VCF file parsing
- Dual annotation pathways (VEP and dbNSFP)
- Configurable dbNSFP database path
- Web interface for file processing
- Process management with cancellation support
- Multi-tab session handling
- Automatic resource cleanup
- Results visualization and download via a dedicated **Download Results** button

Future developments will include:
- Advanced filtering options
- Batch processing
- Additional annotation sources
- Enhanced visualization
- Machine learning integration
