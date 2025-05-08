document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('input_file');
    const fileName = document.getElementById('file-name');
    const loadingSpinner = document.getElementById('loading');
    const errorMessage = document.getElementById('error-message');
    const resultsContainer = document.getElementById('results-container');
    const resultsTable = document.getElementById('results-table');
    const closeResults = document.getElementById('close-results');
    const searchInput = document.getElementById('table-search');
    const dbnsfpPathInput = document.getElementById('dbnsfp_path');
    const resetPathBtn = document.getElementById('reset-path');
    const downloadBtn = document.getElementById('download-results');

    // Create a status indicator element
    const statusIndicator = document.createElement('div');
    statusIndicator.id = 'status-indicator';
    statusIndicator.className = 'status-indicator';
    statusIndicator.style.display = 'none';
    document.querySelector('.container').appendChild(statusIndicator);

    let statusPollingInterval = null;

    //to keep track of current result timestamp
    let currentResultTimestamp = null;
    const DEFAULT_DBNSFP_PATH = '/data/dbnsfp';
    dbnsfpPathInput.value = DEFAULT_DBNSFP_PATH;
    
    //handle path reset
    resetPathBtn.addEventListener('click', function() {
        dbnsfpPathInput.value = DEFAULT_DBNSFP_PATH;
    });

    //file input change handler
    fileInput.addEventListener('change', function(e) {
        const fileName = this.files[0] ? this.files[0].name : 'No file chosen';
        document.getElementById('file-name').textContent = fileName;
        
        // Check if the file extension is supported
        if (fileName !== 'No file chosen') {
            const fileExtension = fileName.split('.').pop().toLowerCase();
            if (fileExtension !== 'vcf' && fileExtension !== 'csv') {
                showError('Invalid file type. Please upload a VCF or CSV file.');
                this.value = '';
                document.getElementById('file-name').textContent = 'No file chosen';
            }
        }
    });

// CANCEL PROCESS stuff 
    let currentProcessKey = null;

    // adding cancel button to loading spinner
    const cancelButton = document.createElement('button');
    cancelButton.id = 'cancel-process';
    cancelButton.className = 'cancel-btn';
    cancelButton.innerHTML = '<i class="fas fa-times"></i> Cancel Process';
    loadingSpinner.appendChild(cancelButton);

    //handle process cancellation
    cancelButton.addEventListener('click', async function() {
        if (!currentProcessKey) {
            showMessage('No active process to cancel');
            showStatus('No active process to cancel', 'error', 3000);
            return;
        }

        try {

            // Display cancellation request status
            showStatus('Cancelling process...', 'warning');

            const response = await fetch(`/cancel_process/${currentProcessKey}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.error || 'Failed to cancel process');
            }
            
            // Reset UI
            clearStatusPolling();
            loadingSpinner.style.display = 'none';
            errorMessage.style.display = 'none';
            showMessage('Process cancelled successfully');
            showStatus('Process cancelled', 'success', 3000);

            // Reset current process tracking
            currentProcessKey = null;
            
        } catch (error) {
            showError(`Cancellation error: ${error.message}`);
            showStatus('Cancellation failed', 'error', 3000);
        }
    });

    //form submission handler
    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        if (!fileInput.files[0]) {
            showError('Please select a file first');
            return;
        }

        //FIX: to GET selected annotation type
        const selectedAnnotationType = document.querySelector('input[name="annotation_type"]:checked');
        if (!selectedAnnotationType) {
            showError('Please select an annotation type');
            return;
        }

        //to display loading spinner and hide other elements
        loadingSpinner.style.display = 'block';
        errorMessage.style.display = 'none';
        resultsContainer.style.display = 'none';

        showStatus('Starting process...', 'info');

        const formData = new FormData(uploadForm);
        formData.append('input_file', fileInput.files[0]);
        formData.append('annotation_type', selectedAnnotationType.value);

        //adding the dbNSFP path to form data
        const dbnsfpPath = dbnsfpPathInput.value.trim() || DEFAULT_DBNSFP_PATH;
        const normalizedPath = dbnsfpPath.replace(/\\/g, '/'); //normalizing path separators for consistency
        formData.append('dbnsfp_dir', normalizedPath);

        try {
            //upload and process file
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'Failed to process file');
            }

            //store the timestamp for download
            currentResultTimestamp = result.timestamp;

            currentProcessKey = result.process_key;

            // Display process information for debugging (can be removed in production)
            showStatus(`Process started: ${currentProcessKey} (PID: ${result.pid})`, 'info');
            console.log('Process details:', result);

            // Start polling for status
            startStatusPolling(currentProcessKey, result.timestamp, result.annotation_type);
            
        } catch (error) {
            showError(error.message);
            showStatus('Process failed to start', 'error', 3000);        
        } finally {
            loadingSpinner.style.display = 'none';
        }
    });

    // Start polling for process status
    function startStatusPolling(processKey, timestamp, annotationType) {
        // Clear any existing polling
        clearStatusPolling();
        
        // Start new polling
        statusPollingInterval = setInterval(async () => {
            try {
                await pollStatus(processKey, timestamp, annotationType);
            } catch (error) {
                console.error('Error polling status:', error);
                showStatus('Error checking status', 'error');
            }
        }, 2000);
    }

    // Clear status polling
    function clearStatusPolling() {
        if (statusPollingInterval) {
            clearInterval(statusPollingInterval);
            statusPollingInterval = null;
        }
    }

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
                    loadingSpinner.style.display = 'block';
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

    //fetch and display results
    async function fetchResults(timestamp, annotationType) {
        try {

            showStatus('Fetching results...', 'info');

            const response = await fetch(`/get_results/${timestamp}?type=${annotationType}`);
            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'Failed to fetch results');
            }

            displayResults(result.data, result.columns);
            showStatus('Results loaded successfully', 'success', 3000);

        } catch (error) {
            showError(error.message);
            showStatus('Failed to fetch results', 'error', 3000);        
        }
    }

    //display results in table
    function displayResults(data, columns) {
        //clearing previous results (if any)
        resultsTable.querySelector('thead').innerHTML = '';
        resultsTable.querySelector('tbody').innerHTML = '';

        const headerRow = document.createElement('tr');
        columns.forEach(column => {
            const th = document.createElement('th');
            th.textContent = column;
            th.title = column; //adding tooltip for long column names
            headerRow.appendChild(th);
        });
        resultsTable.querySelector('thead').appendChild(headerRow);

        data.forEach(row => {
            const tr = document.createElement('tr');
            columns.forEach(column => {
                const td = document.createElement('td');
                const cellContent = row[column] || '';
                td.textContent = cellContent;
                td.title = cellContent; //adding tooltip for full content
                
                //adding expandable class for long content
                //so you can click on the cell, and it will expand
                //try it on INFO field cell of any row
                if (cellContent.length > 50) {
                    td.className = 'expandable';
                    td.addEventListener('click', function() {
                        this.classList.toggle('expanded');
                    });
                }
                
                tr.appendChild(td);
            });
            resultsTable.querySelector('tbody').appendChild(tr);
        });

        resultsContainer.style.display = 'block';
        
        //scroll to results
        resultsContainer.scrollIntoView({ behavior: 'smooth' });
    }

    //handle results download
    downloadBtn.addEventListener('click', async function() {
        if (!currentResultTimestamp) {
            alert('No results available for download');
            return;
        }
        
        try {

            showStatus('Preparing download...', 'info');

            const annotationType = document.querySelector('input[name="annotation_type"]:checked').value;
            const response = await fetch(`/download_results/${currentResultTimestamp}?type=${annotationType}`);
            
            if (!response.ok) {
                throw new Error('Download failed');
            }
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${annotationType}_annotated_variants_${currentResultTimestamp}.csv`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            showStatus('Download complete', 'success', 3000);
            
        } catch (error) {
            showStatus('Download failed', 'error', 3000);
            alert('Error downloading results: ' + error.message);        
        }
    });

    //adding a beforeunload handler for tab close
    window.addEventListener('beforeunload', function(e) {
        if (currentProcessKey) {
            //creating a synchronous request for tab close
            navigator.sendBeacon(`/cancel_process/${currentProcessKey}`);
            console.log('Sent cancellation request via beacon');
        }
    });

    //show status indicator
    function showStatus(message, type = 'info', duration = 0) {
        statusIndicator.textContent = message;
        statusIndicator.className = `status-indicator ${type}`;
        statusIndicator.style.display = 'block';
        
        if (duration > 0) {
            setTimeout(() => {
                statusIndicator.style.display = 'none';
            }, duration);
        }
    }

    //message display function
    function showMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message';
        messageDiv.textContent = message;
        document.querySelector('.container').appendChild(messageDiv);
        setTimeout(() => messageDiv.remove(), 5000);
    }

    //show error message
    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
        // setTimeout(() => {
        //     errorMessage.style.display = 'none';
        // }, 5000); // Hide error after 5 seconds
    }

    //close results handler
    closeResults.addEventListener('click', function() {
        resultsContainer.style.display = 'none';
        // Clear file input and file name
        fileInput.value = '';
        fileName.textContent = 'No file chosen';
    });

    //adding keyboard support for closing results (not necessary, just seemed convenient for the UserExperience)
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && resultsContainer.style.display === 'block') {
            closeResults.click();
        }
    });

    //added column sorting functionality
    function sortTable(columnIndex) {
        const tbody = resultsTable.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const isNumeric = rows.every(row => 
            !isNaN(row.cells[columnIndex].textContent.trim()) || 
            row.cells[columnIndex].textContent.trim() === ''
        );

        rows.sort((a, b) => {
            let aValue = a.cells[columnIndex].textContent.trim();
            let bValue = b.cells[columnIndex].textContent.trim();

            if (isNumeric) {
                aValue = aValue === '' ? -Infinity : parseFloat(aValue);
                bValue = bValue === '' ? -Infinity : parseFloat(bValue);
            }

            if (aValue < bValue) return -1;
            if (aValue > bValue) return 1;
            return 0;
        });

        //clear and re-append sorted rows
        tbody.innerHTML = '';
        rows.forEach(row => tbody.appendChild(row));
    }

    //added click handlers for column sorting
    resultsTable.querySelector('thead').addEventListener('click', function(e) {
        const th = e.target.closest('th');
        if (th) {
            const columnIndex = Array.from(th.parentNode.children).indexOf(th);
            sortTable(columnIndex);
        }
    });

    //added search functionality
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            const rows = resultsTable.querySelectorAll('tbody tr');

            rows.forEach(row => {
                const text = Array.from(row.cells)
                    .map(cell => cell.textContent.toLowerCase())
                    .join(' ');
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        });
    }
});