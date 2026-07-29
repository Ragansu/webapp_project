const PAGE_SIZE = 15;
let currentPage = 0;
let fileIndex = [];
let dataCache = new Map(); // filename -> JSON


document.addEventListener('DOMContentLoaded', function () {
    const table = document.getElementById('data-table');
    const tableBody = document.getElementById('table-body');
    const loading = document.getElementById('loading');
    const errorDiv = document.getElementById('error');
    const reloadButton = document.getElementById('reload-button');
    const notification = document.getElementById('notification');

    // Show notification
    function showNotification(message, isSuccess) {
        notification.textContent = message;
        notification.className = 'notification ' + (isSuccess ? 'success' : 'error');
        notification.classList.add('show');

        setTimeout(() => {
            notification.classList.remove('show');
        }, 3000);
    }
    let is24Hour = true;
    const clockElement = document.getElementById('digital-clock');
    const toggleBtn = document.getElementById('toggle-format');

    function updateClock() {
        const now = new Date();
        let hours = now.getHours();
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');
        let ampm = '';

        if (!is24Hour) {
            // Convert 24h to 12h logic
            ampm = hours >= 12 ? ' PM' : ' AM';
            hours = hours % 12;
            hours = hours ? hours : 12; // The hour '0' should be '12'
        }

        const displayHours = String(hours).padStart(2, '0');
        clockElement.textContent = `${displayHours}:${minutes}:${seconds}${ampm}`;
    }

    // Event listener for the toggle button
    toggleBtn.addEventListener('click', () => {
        is24Hour = !is24Hour;
        toggleBtn.textContent = is24Hour ? 'Switch to 12h' : 'Switch to 24h';
        updateClock(); // Update immediately on click
    });

    setInterval(updateClock, 1000);
    updateClock();

    // Function to execute shell script with option selection
    function executeScript(rowData) {
        // Extract the model type from the row data
        const modelType = rowData.type;

        // If model type is "comparison", directly send comparison_job request
        if (modelType === "comparison") {
            sendComparisonJobRequest(rowData);
            return; // Exit the function early
        }

        // Create custom modal/dialog for option selection
        const modal = document.createElement('div');
        modal.className = 'action-modal-overlay';

        modal.innerHTML = `
            <div class="action-modal-content">
                <h3>Select Action for ${modelType}</h3>
                <p>Choose what you want to do with this model:</p>
                
                    <div class="checkbox-container" style="margin-bottom: 20px;">
                        <div style="display: flex; align-items: center; justify-content: center; gap: 20px;">
                            
                            <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                                <input type="checkbox" id="syst-checkbox">
                                Run with systematics
                            </label>

                            <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                                <input type="checkbox" id="float-checkbox">
                                Run with Bkg Floating
                            </label>

                        </div>
                    </div>

                <div class="action-button-container">
                    <button class="action-btn action-btn-rerun" data-action="re-run">Re-run</button>
                    <button class="action-btn action-btn-retrain" data-action="re-train">Re-train</button>
                    <button class="action-btn action-btn-retest" data-action="re-test">Re-test</button>
                </div>
                <button class="action-btn action-btn-cancel">Cancel</button>
            </div>
        `;

        // Add event listeners to buttons
        const buttons = modal.querySelectorAll('.action-btn');
        buttons.forEach(button => {
            if (button.classList.contains('action-btn-cancel')) {
                button.addEventListener('click', closeModal);
            } else {
                const action = button.getAttribute('data-action');
                button.addEventListener('click', () => {
                    const isSystChecked = modal.querySelector('#syst-checkbox').checked;
                    const isFloatChecked = modal.querySelector('#float-checkbox').checked;
                    handleOption(action, modelType, isSystChecked, isFloatChecked);
                });
            }
        });

        document.body.appendChild(modal);

        // Store the modal reference for cleanup
        window.currentModal = modal;
    }

    // Handle the selected option
    function handleOption(action, modelType, isSystChecked, isFloatChecked) {
        closeModal();

        let notificationMessage = '';

        switch (action) {
            case 're-run':
                notificationMessage = `Re-running model: ${modelType}`;
                break;
            case 're-train':
                notificationMessage = `Re-training model: ${modelType}`;
                break;
            case 're-test':
                notificationMessage = `Re-validating model: ${modelType}`;
                break;
            default:
                notificationMessage = `Executing ${action} for model: ${modelType}`;
        }

        // Show notification
        if (typeof showNotification === 'function') {
            showNotification(notificationMessage, true);
        }



        // Send the request with both modelType and action
        fetch("/send_sbatch_job", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                modelType: modelType,
                action: action,
                syst: isSystChecked,
                floating: isFloatChecked
            })
        })
            .then(response => response.json())
            .then(data => {
                alert(`${action} ${data.status}:\n${data.output}`);
            })
            .catch(error => {
                console.error("Error:", error);
                alert(`Error during ${action}: ${error.message}`);
            });
    }

    // Close the modal
    function closeModal() {
        if (window.currentModal) {
            document.body.removeChild(window.currentModal);
            window.currentModal = null;
        }
    }

    // Close modal when clicking outside
    document.addEventListener('click', function (event) {
        if (window.currentModal && event.target === window.currentModal) {
            closeModal();
        }
    });

    // Function to send comparison_job request
    function sendComparisonJobRequest(rowData) {
        const date = rowData.date;
        const job_id = rowData.job_id;

        fetch('/send_comparison_job', {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                jobId: job_id,
                date: date
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data.status === "success") {
                    showNotification("Comparison Job sent successfully", true);
                } else {
                    alert("Failed to send job: " + data.output);
                }
            })
            .catch(error => {
                console.error("Error sendding job:", error);
            });
    }


    function cancelJob(rowData) {
        const modelType = rowData.type;
        const date = rowData.date;
        const job_id = rowData.job_id;

        fetch("/cancel_sbatch_job", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                jobId: job_id,
                modelType: modelType,
                date: date
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data.status === "success") {
                    showNotification("Job cancelled successfully", true);
                } else {
                    alert("Failed to cancel job: " + data.output);
                }
            })
            .catch(error => {
                console.error("Error cancelling job:", error);
            });
    }

    function loadDataFromJSON() {
        loading.style.display = 'block';
        errorDiv.style.display = 'none';
        table.style.display = 'none';

        fetch('/static/index.json?' + Date.now())
            .then(res => {
                if (!res.ok) {
                    throw new Error('Failed to load index.json');
                }
                return res.json();
            })
            .then(files => {
                if (!files.length) {
                    showError('No JSON entries found');
                    return;
                }

                fileIndex = files;
                currentPage = 0;

                loadPage(currentPage);

                table.style.display = 'table';
            })
            .catch(err => {
                showError('Error loading JSON data: ' + err.message);
            });
    }

    function loadPage(page) {
        loading.style.display = 'block';

        const start = page * PAGE_SIZE;
        const end = Math.min(start + PAGE_SIZE, fileIndex.length);
        const filesToLoad = fileIndex.slice(start, end);

        const fetches = filesToLoad.map(file => {
            if (dataCache.has(file)) {
                return Promise.resolve(dataCache.get(file));
            }

            return fetch(`/json_file/${file}`)
                .then(r => {
                    if (!r.ok) {
                        throw new Error(`Failed to load ${file}`);
                    }
                    return r.json();
                })
                .then(json => {
                    dataCache.set(file, json);
                    return json;
                });
        });

        Promise.all(fetches)
            .then(pageData => {
                renderTable(pageData);
                prefetchNextPage(page);

                pageInfo.textContent = `Showing ${start + 1}–${end} of ${fileIndex.length}`;

                prevBtn.disabled = page === 0;
                nextBtn.disabled = end >= fileIndex.length;

                loading.style.display = 'none';
            })
            .catch(err => {
                showError('Error loading JSON data: ' + err.message);
            });
    }


    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const pageInfo = document.getElementById('pageInfo');

    prevBtn.onclick = () => {
        if (currentPage > 0) {
            currentPage--;
            loadPage(currentPage);
        }
    };

    nextBtn.onclick = () => {
        if ((currentPage + 1) * PAGE_SIZE < fileIndex.length) {
            currentPage++;
            loadPage(currentPage);
        }
    };

    function renderCurrentPage() {
        const start = currentPage * PAGE_SIZE;
        const end = Math.min(start + PAGE_SIZE, allData.length);

        const pageData = allData.slice(start, end);
        renderTable(pageData);
        prefetchNextPage(currentPage);

        pageInfo.textContent = `Showing ${start + 1}–${end} of ${allData.length}`;

        updatePaginationButtons();
    }

    function updatePaginationButtons() {
        prevBtn.disabled = currentPage === 0;
        // Use filteredIndex.length here so pagination works with the filters
        nextBtn.disabled = (currentPage + 1) * PAGE_SIZE >= filteredIndex.length;
    }

    prevBtn.addEventListener('click', () => {
        if (currentPage > 0) {
            currentPage--;
            renderCurrentPage();
        }
    });

    nextBtn.addEventListener('click', () => {
        if ((currentPage + 1) * PAGE_SIZE < allData.length) {
            currentPage++;
            renderCurrentPage();
        }
    });


    function updatePaginationButtons() {
        prevBtn.disabled = currentPage === 0;
        nextBtn.disabled = (currentPage + 1) * PAGE_SIZE >= allData.length;
    }

    function prefetchNextPage(page) {
        const start = (page + 1) * PAGE_SIZE;
        const end = Math.min(start + PAGE_SIZE, fileIndex.length);

        fileIndex.slice(start, end).forEach(file => {
            if (!dataCache.has(file)) {
                fetch(`/json_file/${file}`)
                    .then(r => r.json())
                    .then(json => dataCache.set(file, json))
                    .catch(() => { });
            }
        });
    }

    let filteredIndex = []; // This will hold the filenames that pass the test

    function applyFilters() {
        const statusValue = document.getElementById('statusFilter').value;
        const modelValue = document.getElementById('modelFilter').value;

        // Filter the fileIndex (the list of filenames)
        filteredIndex = fileIndex.filter(fileName => {
            const cachedData = dataCache.get(fileName);

            // If "All" is selected, we let it through
            // If a specific filter is set, we check the cache
            if (statusValue === 'all' && modelValue === 'all') return true;

            // CRITICAL: If the file isn't in cache yet, we can't "see" its status
            // So we exclude it from the filtered view to prevent errors
            if (!cachedData) return false;

            const matchesStatus = statusValue === 'all' || cachedData.status === statusValue;
            const matchesModel = modelValue === 'all' || cachedData.model_type === modelValue;

            return matchesStatus && matchesModel;
        });

        currentPage = 0;
        renderFilteredPage();
    }

    function renderFilteredPage() {
        const start = currentPage * PAGE_SIZE;
        const end = Math.min(start + PAGE_SIZE, filteredIndex.length);
        const filesToRender = filteredIndex.slice(start, end);

        // Map filenames to their cached JSON objects
        const pageData = filesToRender.map(file => dataCache.get(file));

        // Send to your existing table renderer
        renderTable(pageData);

        // Update the UI text
        const totalCount = filteredIndex.length;
        pageInfo.textContent = `Showing ${totalCount > 0 ? start + 1 : 0}–${end} of ${totalCount} filtered results`;

        updatePaginationButtons();
    }
    // Link the HTML to the logic
    document.getElementById('statusFilter').addEventListener('change', applyFilters);
    document.getElementById('modelFilter').addEventListener('change', applyFilters);

    document.getElementById('resetFilters').onclick = () => {
        document.getElementById('statusFilter').value = 'all';
        document.getElementById('modelFilter').value = 'all';
        applyFilters();
    };

    // Show error message
    function showError(message) {
        loading.style.display = 'none';
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        reloadButton.style.display = 'block';
    }

    // Render table with data
    function renderTable(data) {
        tableBody.innerHTML = '';

        data.forEach(row => {
            const tr = document.createElement('tr');

            // Store the link as a data attribute
            if (row.link) {
                tr.setAttribute('data-link', row.link);
            }

            // Date column
            const dateTd = document.createElement('td');
            dateTd.textContent = row.date;
            tr.appendChild(dateTd);

            // Type column
            const typeTd = document.createElement('td');
            typeTd.textContent = row.type;
            tr.appendChild(typeTd);

            // Type column
            const jobIdTd = document.createElement('td');
            jobIdTd.textContent = row.job_id;
            tr.appendChild(jobIdTd);

            // Run Time column
            const runTimeTd = document.createElement('td');
            runTimeTd.textContent = row.run_time;
            tr.appendChild(runTimeTd);

            // Status column
            const statusTd = document.createElement('td');
            statusTd.textContent = row.Status;
            tr.appendChild(statusTd);

            // Score columns
            const noBkgTd = document.createElement('td');
            noBkgTd.textContent = row.No_bkg;
            tr.appendChild(noBkgTd);

            const allBkgTd = document.createElement('td');
            allBkgTd.textContent = row.All_bkg;
            tr.appendChild(allBkgTd);

            const singleHTd = document.createElement('td');
            singleHTd.textContent = row.singleH;
            tr.appendChild(singleHTd);

            const runSettingTd = document.createElement('td');
            runSettingTd.textContent = row.run_setting;
            tr.appendChild(runSettingTd);

            // Action button column
            const actionTd = document.createElement('td');
            const actionButton = document.createElement('button');

            const status = (row.Status || '').toString().trim();

            if (status && !['Completed', 'Cancelled'].includes(status) && !status.startsWith('Failed')) {
                // Job is running/pending - Show Cancel button
                actionButton.textContent = 'Cancel\nJob';
                actionButton.classList.add('action-button-red');

                actionButton.onclick = (e) => {
                    e.stopPropagation();
                    cancelJob(row, actionButton);
                };
            } else {
                // Job is completed/failed/no status - Show Run/Rerun button
                actionButton.textContent = 'Run\nScript';
                actionButton.classList.add('action-button-green');
                actionButton.onclick = (e) => {
                    e.stopPropagation();
                    executeScript(row, actionButton);
                };
            }

            // Clear any existing status classes
            statusTd.classList.remove('status-completed', 'status-failed', 'status-cancelled', 'status-success', 'status-launched', 'status-skipped');

            // Apply color based on status
            if (status === 'Completed') {
                statusTd.classList.add('status-completed'); // BLUE
            } else if (status === 'Launched') {
                statusTd.classList.add('status-launched'); // ORANGE
            } else if (status === 'Cancelled') {
                statusTd.classList.add('status-skipped'); // GRAY
            } else if (status.startsWith('Failed')) {
                statusTd.classList.add('status-failed'); // RED
            } else if (status.startsWith('Success')) {
                statusTd.classList.add('status-success'); // GREEN
            } else if (status.startsWith('Skipped')) {
                statusTd.classList.add('status-skipped'); // GRAY
            }
            // Note: Running/Pending statuses won't get colored

            actionTd.appendChild(actionButton);
            tr.appendChild(actionTd);


            // Make row clickable if link is provided
            if (row.link) {
                tr.style.cursor = 'pointer';
                tr.addEventListener('click', () => {
                    // Navigate to page.
                    window.location.href = row.link;
                });

                // Add hover effect
                tr.addEventListener('mouseenter', () => {
                    tr.style.backgroundColor = '#e3f2fd';
                });

                tr.addEventListener('mouseleave', () => {
                    // Reset to original background color
                    if (Array.from(tableBody.children).indexOf(tr) % 2 === 0) {
                        tr.style.backgroundColor = '';
                    } else {
                        tr.style.backgroundColor = '#f8f9fa';
                    }
                });
            }

            tableBody.appendChild(tr);
        });
    }

    // Sort table data
    function sortTable(column, direction) {
        // Get current data from table
        const data = [];
        const rows = tableBody.querySelectorAll('tr');

        rows.forEach(row => {
            const cells = row.querySelectorAll('td');
            data.push({
                date: cells[0].textContent,
                type: cells[1].textContent,
                job_id: cells[2].textContent,
                run_time: cells[3].textContent,
                Status: cells[4].textContent,
                No_bkg: cells[5].textContent,
                All_bkg: cells[6].textContent,
                singleH: cells[7].textContent,
                run_setting: cells[8].textContent,
                link: row.getAttribute('data-link') || ''
            });
        });

        data.sort((a, b) => {
            let valueA = a[column];
            let valueB = b[column];

            if (['No_bkg', 'All_bkg', 'singleH'].includes(column)) {
                valueA = Number(valueA);
                valueB = Number(valueB);
            }

            // Handle date sorting
            if (column === 'date') {
                valueA = new Date(valueA);
                valueB = new Date(valueB);
            }

            if (valueA < valueB) {
                return direction === 'asc' ? -1 : 1;
            }
            if (valueA > valueB) {
                return direction === 'asc' ? 1 : -1;
            }
            return 0;
        });

        renderTable(data);

        // Update sort indicators
        document.querySelectorAll('th').forEach(header => {
            const icon = header.querySelector('.sort-icon');
            if (header.dataset.sort === column) {
                icon.textContent = direction === 'asc' ? '↑' : '↓';
            } else {
                icon.textContent = '↕';
            }
        });
    }

    // Set up sorting
    document.querySelectorAll('th').forEach(header => {
        let sortDirection = 'asc';

        header.addEventListener('click', () => {
            const column = header.dataset.sort;

            // Toggle direction
            sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';

            sortTable(column, sortDirection);
        });
    });

    // Set up reload button
    reloadButton.addEventListener('click', loadDataFromJSON);

    // Initial load
    loadDataFromJSON();
});
