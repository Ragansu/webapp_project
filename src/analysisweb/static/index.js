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
    async function executeScript(rowData) {
        // Find the action configuration
        const actionConfig = DASHBOARD_CONFIG.action?.find(
            action => action.key === "run_script"
        );

        if (!actionConfig) {
            console.error("run_script action not found in config");
            return;
        }

        // Create modal container
        const modal = document.createElement("div");
        modal.className = "action-modal-overlay";

        try {
            const response = await fetch("/action-modal");

            if (!response.ok) {
                throw new Error("Failed to load action modal template");
            }

            modal.innerHTML = await response.text();
        } catch (error) {
            console.error(error);
            return;
        }

        // Function to close and cleanup modal
        const closeModal = () => {
            if (modal.parentNode) {
                modal.parentNode.removeChild(modal);
            }
            if (window.currentModal === modal) {
                window.currentModal = null;
            }
        };

        // 1. Populate Flags (Checkboxes)
        const flagsContainer = modal.querySelector("#job-flags-container");
        if (flagsContainer) {
            flagsContainer.innerHTML = "";

            (actionConfig.job_flags || []).forEach((flag, index) => {
                const label = document.createElement("label");
                label.style.display = "flex";
                label.style.alignItems = "center";
                label.style.gap = "8px";
                label.style.cursor = "pointer";

                const checkbox = document.createElement("input");
                checkbox.type = "checkbox";
                checkbox.id = `job-flag-${index}`;
                checkbox.dataset.flag = flag.key;
                checkbox.dataset.value = flag.value ?? "";

                label.appendChild(checkbox);
                label.appendChild(document.createTextNode(flag.label || flag.key));

                flagsContainer.appendChild(label);
            });
        }

        // 2. Populate Arguments (Text Inputs / Options)
        const argsContainer = modal.querySelector("#job-arguments-container");
        if (argsContainer) {
            argsContainer.innerHTML = "";

            (actionConfig.job_arguments || []).forEach((arg, index) => {
                const wrapper = document.createElement("div");
                wrapper.style.display = "flex";
                wrapper.style.flexDirection = "column";
                wrapper.style.gap = "4px";

                const label = document.createElement("label");
                label.htmlFor = `job-arg-${index}`;
                label.textContent = arg.label || arg.key;

                const input = document.createElement("input");
                input.type = "text";
                input.id = `job-arg-${index}`;
                input.className = "job-argument-input";
                input.dataset.argKey = arg.key;
                input.value = arg.default_value || "";
                if (arg.placeholder) input.placeholder = arg.placeholder;

                wrapper.appendChild(label);
                wrapper.appendChild(input);
                argsContainer.appendChild(wrapper);
            });
        }

        // 3. Configure Run Button (Targeting matching HTML class .action-btn-retrain)
        const runButton = modal.querySelector(".action-btn-retrain");
        if (runButton) {
            if (actionConfig.title) {
                runButton.textContent = actionConfig.title;
            }
            runButton.dataset.actionKey = actionConfig.key;
            runButton.dataset.actionType = actionConfig.action_type || "";
            runButton.dataset.jobPlugin = actionConfig.job_plugin || "";
        }

        // 4. Attach Event Listeners to Buttons
        const cancelButton = modal.querySelector(".action-btn-cancel");
        if (cancelButton) {
            cancelButton.addEventListener("click", closeModal);
        }

        if (runButton) {
            runButton.addEventListener("click", () => {
                // Collect Selected Flags
                const selectedFlags = [];
                modal.querySelectorAll("#job-flags-container input[type='checkbox']:checked")
                    .forEach(checkbox => {
                        selectedFlags.push({
                            key: checkbox.dataset.flag,
                            value: checkbox.dataset.value
                        });
                    });

                // Collect Populated Arguments
                const selectedArguments = [];
                modal.querySelectorAll("#job-arguments-container .job-argument-input")
                    .forEach(input => {
                        const val = input.value.trim();
                        if (val !== "") {
                            selectedArguments.push({
                                key: input.dataset.argKey,
                                value: val
                            });
                        }
                    });

                // Execute handler with modal data
                handleOption(
                    runButton.dataset.actionKey || "run_script",
                    rowData,
                    selectedFlags,
                    selectedArguments
                );

                closeModal();
            });
        }

        // Add modal to page
        document.body.appendChild(modal);
        window.currentModal = modal;
    }
    function handleOption(action, rowData, selectedFlags,selectedArguments) {
        closeModal();

        const notificationMessage =
            `Executing ${action}`;

        // Show notification
        if (typeof showNotification === 'function') {
            showNotification(notificationMessage, true);
        }

        // Send the request
        fetch("/send_sbatch_job", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                ...rowData,
                action: action,
                job_flags: selectedFlags,
                job_arguments : selectedArguments
            })
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                return response.json();
            })
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

    function cancelJob(rowData) {

        fetch("/cancel_sbatch_job", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(rowData)
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

        const jsonFile = DASHBOARD_CONFIG.data.index_file;

        fetch(`/json/${jsonFile}?${Date.now()}`)
            .then(res => {

                if (!res.ok) {
                    throw new Error(`Failed to load ${jsonFile}`);
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

            return fetch(`/json/${file}`)
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
                return fetch(`/json/${file}`)
                    .then(r => r.json())
                    .then(json => dataCache.set(file, json))
                    .catch(() => { });
            }
        });
    }



    // Show error message
    function showError(message) {
        loading.style.display = 'none';
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        reloadButton.style.display = 'block';
    }

    // Render table with data
    function renderTable(data) {
        tableBody.innerHTML = "";

        const columns = DASHBOARD_CONFIG.columns;

        data.forEach(row => {
            const tr = document.createElement("tr");

            // Store the link as a data attribute
            if (row.link) {
                tr.setAttribute("data-link", row.link);
            }

            // Render configured columns
            columns.forEach(column => {

                const td = document.createElement("td");

                switch (column.type) {

                    case "status": {

                        const status = (row[column.key] || "").toString().trim();
                        td.textContent = status;

                        if (status === "Completed") {
                            td.classList.add("status-completed");
                        } else if (status === "Launched") {
                            td.classList.add("status-launched");
                        } else if (status === "Cancelled") {
                            td.classList.add("status-skipped");
                        } else if (status.startsWith("Failed")) {
                            td.classList.add("status-failed");
                        } else if (status.startsWith("Success")) {
                            td.classList.add("status-success");
                        } else if (status.startsWith("Skipped")) {
                            td.classList.add("status-skipped");
                        }

                        break;
                    }

                    case "action": {

                        const button = document.createElement("button");
                        const status = (row.Status || "").toString().trim();

                        if (
                            status &&
                            !["Completed", "Cancelled"].includes(status) &&
                            !status.startsWith("Failed")
                        ) {
                            button.textContent = "Cancel\nJob";
                            button.classList.add("action-button-red");

                            button.onclick = (e) => {
                                e.stopPropagation();
                                cancelJob(row, button);
                            };

                        } else {

                            button.textContent = "Run\nScript";
                            button.classList.add("action-button-green");

                            button.onclick = (e) => {
                                e.stopPropagation();
                                executeScript(row, button);
                            };
                        }

                        td.appendChild(button);
                        break;
                    }

                    case "normal":
                    default:

                        td.textContent = row[column.key] ?? "";
                        break;
                }

                tr.appendChild(td);
            });

            // Make row clickable if link is provided
            if (row.link) {

                tr.style.cursor = "pointer";

                tr.addEventListener("click", () => {
                    window.location.href = row.link;
                });

                tr.addEventListener("mouseenter", () => {
                    tr.style.backgroundColor = "#e3f2fd";
                });

                tr.addEventListener("mouseleave", () => {

                    if (Array.from(tableBody.children).indexOf(tr) % 2 === 0) {
                        tr.style.backgroundColor = "";
                    } else {
                        tr.style.backgroundColor = "#f8f9fa";
                    }
                });
            }

            tableBody.appendChild(tr);
        });
    }

    // Sort table data
    function sortTable(column, direction) {

        const data = [];
        const rows = tableBody.querySelectorAll("tr");
        const columns = DASHBOARD_CONFIG.columns;

        rows.forEach(row => {

            const cells = row.querySelectorAll("td");
            const rowData = {};

            columns.forEach((col, index) => {

                // Skip action columns since they don't contain data
                if (col.type === "action") {
                    return;
                }

                rowData[col.key] = cells[index].textContent;
            });

            rowData.link = row.getAttribute("data-link") || "";

            data.push(rowData);
        });

        data.sort((a, b) => {

            let valueA = a[column];
            let valueB = b[column];

            const columnConfig = columns.find(c => c.key === column);

            // Numeric columns
            if (columnConfig?.dataType === "number") {
                valueA = Number(valueA);
                valueB = Number(valueB);
            }

            // Date columns
            if (columnConfig?.dataType === "date") {
                valueA = new Date(valueA);
                valueB = new Date(valueB);
            }

            if (valueA < valueB) {
                return direction === "asc" ? -1 : 1;
            }

            if (valueA > valueB) {
                return direction === "asc" ? 1 : -1;
            }

            return 0;
        });

        renderTable(data);

        // Update sort indicators
        document.querySelectorAll("th").forEach(header => {

            const icon = header.querySelector(".sort-icon");
            if (!icon) return;

            if (header.dataset.sort === column) {
                icon.textContent = direction === "asc" ? "↑" : "↓";
            } else {
                icon.textContent = "↕";
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

    console.log("Reached end of script!"); // If this doesn't log, code crashed above it
    // Set up reload button
    reloadButton.addEventListener('click', loadDataFromJSON);

    // Initial load
    loadDataFromJSON();
});
