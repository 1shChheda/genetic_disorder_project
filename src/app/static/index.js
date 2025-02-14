document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('vcf_file');
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


    //to keep track of current result timestamp
    let currentResultTimestamp = null;
    const DEFAULT_DBNSFP_PATH = '/data/dbnsfp';
    
    //handle path reset
    resetPathBtn.addEventListener('click', function() {
        dbnsfpPathInput.value = DEFAULT_DBNSFP_PATH;
    });

    //file input change handler
    fileInput.addEventListener('change', function(e) {
        fileName.textContent = e.target.files[0] ? e.target.files[0].name : 'No file chosen';
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

        const formData = new FormData(uploadForm);
        formData.append('vcf_file', fileInput.files[0]);
        formData.append('annotation_type', selectedAnnotationType.value);

        //adding the dbNSFP path to form data
        const dbnsfpPath = dbnsfpPathInput.value.trim() || DEFAULT_DBNSFP_PATH;
        formData.append('dbnsfp_dir', dbnsfpPath);

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

            //start polling for status
            await pollStatus(result.timestamp, result.annotation_type);

        } catch (error) {
            showError(error.message);
        } finally {
            loadingSpinner.style.display = 'none';
        }
    });

    //poll for processing status
    async function pollStatus(timestamp, annotationType) {
        try {
            const response = await fetch(`/status/${timestamp}`);
            const result = await response.json();

            if (result.status === 'completed') {
                //to fetch results when processing is complete
                await fetchResults(timestamp, annotationType);
            } else if (result.status === 'processing') {
                // NOTE: polling every 2 seconds
                setTimeout(() => pollStatus(timestamp, annotationType), 2000);
            } else if (result.status === 'error') {
                throw new Error(result.message || 'Processing failed');
            }
        } catch (error) {
            showError(error.message);
        }
    }

    //fetch and display results
    async function fetchResults(timestamp, annotationType) {
        try {
            const response = await fetch(`/get_results/${timestamp}?type=${annotationType}`);
            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'Failed to fetch results');
            }

            displayResults(result.data, result.columns);
        } catch (error) {
            showError(error.message);
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
            
        } catch (error) {
            alert('Error downloading results: ' + error.message);
        }
    });

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