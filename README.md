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
│           ├── dbnsfp_input.vcf    
│           ├── <annotation_type>_annotated_variants_<timestamp>.csv
│           ├── <annotation_type>_annotated_variants_<timestamp>.csv.err
│           └── status.json         # Process status tracking file
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

## Process Status Tracking System
The application implements a robust process status tracking system to handle multiprocessing challenges:

### Status.json File Format
Each process creates a `status.json` file in its output directory to track processing status:

```json
{
  "status": "running",
  "steps": [
    {"name": "annotation", "status": "completed", "timestamp": "2025-03-01T12:34:56"},
    {"name": "feature_selection", "status": "running", "timestamp": "2025-03-01T12:35:01"},
    {"name": "model_training", "status": "pending"}
  ],
  "current_step": "feature_selection",
  "progress": 45
}
```

### Key Components
- `status`: Overall process status (running, completed, error, cancelled)
- `steps`: Array of workflow steps with individual status tracking
- `current_step`: The active processing step
- `progress`: Optional percentage completion value

### Implementation Details
- Status file is created by the worker process and read by the main Flask application
- Ensures reliable status communication between separate processes
- Provides granular tracking of each workflow step

## For Developers (Adding New Workflow Steps)

When extending the application with new analysis steps (feature selection, ML models, etc.), follow these guidelines to maintain compatibility with the status tracking system:

### 1. Update the Workflow Class
When adding a new step to the `AnnotationWorkflow` class:

```python
def process(self, input_vcf, output_dir):
    """Process the complete annotation workflow with multiple steps"""
    
    # Initialize the status structure
    status = {
        "status": "running",
        "steps": [
            {"name": "annotation", "status": "pending", "timestamp": None},
            {"name": "feature_selection", "status": "pending", "timestamp": None},
            {"name": "model_training", "status": "pending", "timestamp": None}
        ],
        "current_step": "annotation",
        "progress": 0
    }
    
    # Write initial status
    self._update_status_file(output_dir, status)
    
    try:
        # Step 1: Annotation
        status["steps"][0]["status"] = "running"
        status["steps"][0]["timestamp"] = datetime.now().isoformat()
        self._update_status_file(output_dir, status)
        
        # Run annotation...
        
        # Update status after annotation completes
        status["steps"][0]["status"] = "completed"
        status["current_step"] = "feature_selection"
        status["progress"] = 33
        self._update_status_file(output_dir, status)
        
        # Step 2: Feature Selection
        status["steps"][1]["status"] = "running"
        status["steps"][1]["timestamp"] = datetime.now().isoformat()
        self._update_status_file(output_dir, status)
        
        # Run feature selection...
        
        # Continue with remaining steps...
        
        # Mark process as completed when all steps finish
        status["status"] = "completed"
        status["progress"] = 100
        self._update_status_file(output_dir, status)
        
        return status
        
    except Exception as e:
        status["status"] = "error"
        status["error_message"] = str(e)
        self._update_status_file(output_dir, status)
        raise
    
def _update_status_file(self, output_dir, status):
    """Helper method to update the status.json file"""
    status_file = os.path.join(output_dir, "status.json")
    with open(status_file, 'w') as f:
        json.dump(status, f, indent=2)
```

### 2. Update Process Manager
Ensure the `get_process_info` method is implemented in the `ProcessManager` class:

```python
def get_process_info(self, process_key: str) -> Optional[ProcessInfo]:
    """Get complete process info"""
    with self._lock:
        if process_key in self._processes:
            return self._processes[process_key]
        return None
```

### 3. Status Checking in Flask Routes
When adding new routes for additional processing steps, implement status checking:

```python
@app.route('/check_process/<process_key>')
def check_process(process_key):
    """Check process status and all workflow steps"""
    try:
        process_info = process_manager.get_process_info(process_key)
        if not process_info:
            return jsonify({'error': 'Process not found'}), 404
            
        status_file = os.path.join(process_info.output_folder, "status.json")
        
        if os.path.exists(status_file):
            with open(status_file, 'r') as f:
                status = json.load(f)
                
            # Update the process manager status
            process_manager.update_process_status(process_key, status.get('status', 'running'))
            
            return jsonify(status)
        
        # Fallback if no status file exists
        return jsonify({'status': process_manager.get_process_status(process_key)})
        
    except Exception as e:
        app.logger.error(f"Error checking process: {str(e)}")
        return jsonify({'error': str(e)}), 500
```

### 4. Frontend Status Updates
Make sure frontend is working properly based on the detailed status information:

```javascript
//poll for processing status
async function pollStatus(processKey, timestamp, annotationType) {
    try {
        const response = await fetch(`/process_status/${processKey}`);
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'Failed to check status');
        }
        
        console.log(`Process status: ${result.status}`); //added browsor console logging for debugging
        
        switch (result.status) {
            case 'running':
                showStatus('Processing in progress...', 'info');
                break;
            case 'completed':
                clearStatusPolling();
                showStatus('Processing completed!', 'success');
                await fetchResults(timestamp, annotationType);
                loadingSpinner.style.display = 'none';
                break;
            case 'cancelled':
                clearStatusPolling();
                loadingSpinner.style.display = 'none';
                showStatus('Process was cancelled', 'warning', 3000);
                showMessage('Process was cancelled');
                break;
            case 'error':
                clearStatusPolling();
                loadingSpinner.style.display = 'none';
                showStatus('Processing failed', 'error', 3000);
                throw new Error('Processing failed');
            default:
                showStatus(`Unknown status: ${result.status}`, 'warning');
        }
        
    } catch (error) {
        console.error('Status polling error:', error);
        clearStatusPolling();
        showError(`Status check failed: ${error.message}`);
        showStatus('Error occurred', 'error', 3000);
        loadingSpinner.style.display = 'none';
    }
}
```

### 5. Testing Multi-Step Workflows
When implementing new steps, test thoroughly with both successful and error scenarios to ensure proper status updates.

## Project Status
This project is in active development. It currently supports:
- VCF file parsing
- Dual annotation pathways (VEP and dbNSFP)
- Configurable dbNSFP database path
- Web interface for file processing
- Robust process management with cancellation support
- Reliable status tracking for multiprocessing workflows
- Multi-tab session handling
- Automatic resource cleanup
- Results visualization and download via a dedicated **Download Results** button

## Future Development Roadmap
The project will be extended with:
- Feature engineering and selection:
  - Random Forest, XGBoost, Catboost, Hybrid ( RF + Catboost )
  - BorutaPY + Best Model (XGBoost)
- Pathogenicity prediction:
  - Deep Learning Model (Neural Network)
  - Variant classification (Benign/Pathogenic)
- Advanced filtering options
- Batch processing
- Enhanced visualization dashboards
