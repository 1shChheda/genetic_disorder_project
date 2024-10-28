# Genetic Disorder Detection Project

## Project Structure (Current Stage Only)

```
genetic_disorder_detection_project/
├── data/                       # Directory to store raw and processed data
│   ├── raw/                    # Raw input VCF files
│   ├── processed/              # Processed output files
├── src/                        # Source code
│   ├── parser/                 # VCF parsing logic
│   │   ├── __init__.py         
│   │   └── vcf_parser.py       # Main VCF parsing module
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

1. **Place the VCF file** you want to parse in the `data/raw` directory.

2. **Run the VCF Parser**:
    In `tests/test_vcf_parser.py`, change the following file location (to your vcf file name):
    ```python
    def test_parse_vcf():
        test_file = os.path.join(os.path.dirname(__file__), '../data/raw/sample.vcf')
    ```

3. **Running Test**:
    To verify that the parsing functionality works as expected, use `pytest` to run the unit test `test_vcf_parser.py`:
    ```bash
    pytest tests/
    ```

This will run all tests in the `tests/` directory. A successful test run confirms that the parser correctly reads the VCF data and stores it in the desired format.

## Project Status
This project is in the initial stages of development. Currently, only VCF parsing and storing functionality is implemented. Future stages will include data filtering, variant annotation, and web interface development.


