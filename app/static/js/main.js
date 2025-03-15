document.addEventListener('DOMContentLoaded', function() {
    loadVolcanoPlot();

    function loadVolcanoPlot() {
        const loadingElement = document.getElementById('volcano-loading');
        const plotElement = document.getElementById('volcano-plot');
        const errorElement = document.getElementById('volcano-error') || document.createElement('div');

        if (!document.getElementById('volcano-error')) {
            errorElement.id = 'volcano-error';
            errorElement.className = 'error-message hidden';
            plotElement.parentNode.insertBefore(errorElement, plotElement);
        }

        loadingElement.classList.remove('hidden');
        plotElement.classList.add('hidden');
        errorElement.classList.add('hidden');

        fetch('/api/volcano-data')
            .then(response => response.ok ? response.json() : Promise.reject(`HTTP error! status: ${response.status}`))
            .then(data => {
                if (data.error) throw new Error(data.error);

                const plotData = JSON.parse(data.plot);
                Plotly.newPlot('volcano-plot', plotData.data, {
                    ...plotData.layout,
                    autosize: true,
                    margin: { l: 70, r: 70, b: 70, t: 70, pad: 10 },
                    hovermode: 'closest'
                }, { responsive: true });

                document.getElementById('volcano-plot').on('plotly_click', function(data) {
                    const geneName = data.points[0].customdata[0];
                    loadGeneData(geneName);
                });

                loadingElement.classList.add('hidden');
                plotElement.classList.remove('hidden');
            })
            .catch(error => {
                console.error('Error loading volcano plot:', error);
                errorElement.textContent = `Error loading volcano plot: ${error.message}`;
                errorElement.classList.remove('hidden');
                loadingElement.classList.add('hidden');
            });
    }

    function loadGeneData(geneName) {
        const boxplotContainer = document.getElementById('boxplot-container');
        const boxplotLoading = document.getElementById('boxplot-loading');
        const boxplotElement = document.getElementById('boxplot');
        const geneInfoElement = document.getElementById('gene-info');
        const geneTitleElement = document.getElementById('gene-title');
        const boxplotErrorElement = document.getElementById('boxplot-error') || document.createElement('div');

        if (!document.getElementById('boxplot-error')) {
            boxplotErrorElement.id = 'boxplot-error';
            boxplotErrorElement.className = 'error-message hidden';
            boxplotElement.parentNode.insertBefore(boxplotErrorElement, boxplotElement);
        }

        // Remove existing papers
        const existingPapersContainer = boxplotContainer.querySelector('.papers-container');
        if (existingPapersContainer) existingPapersContainer.remove();

        const existingNoPapers = boxplotContainer.querySelector('.no-papers');
        if (existingNoPapers) existingNoPapers.remove();

        // Show loading, hide results
        boxplotContainer.classList.remove('hidden');
        boxplotLoading.classList.remove('hidden');
        boxplotElement.classList.add('hidden');
        boxplotErrorElement.classList.add('hidden');
        geneInfoElement.innerHTML = '';
        geneTitleElement.textContent = `Loading data for ${geneName}...`;
        boxplotContainer.scrollIntoView({ behavior: 'smooth' });

        fetch(`/api/gene/${geneName}`)
            .then(response => response.ok ? response.json() :
                  Promise.reject(response.status === 404 ?
                  `Gene "${geneName}" not found or has no data` :
                  `HTTP error! status: ${response.status}`))
            .then(data => {
                if (data.error) throw new Error(data.error);

                // Update gene info
                geneTitleElement.textContent = `${geneName} Information`;
                displayGeneInfo(geneInfoElement, data.gene_info);

                // Plot boxplot
                const boxplotData = JSON.parse(data.boxplot);
                Plotly.newPlot('boxplot', boxplotData.data, {
                    ...boxplotData.layout,
                    autosize: true,
                    margin: { l: 70, r: 70, b: 70, t: 70, pad: 10 },
                    hovermode: 'closest'
                }, { responsive: true });

                boxplotLoading.classList.add('hidden');
                boxplotElement.classList.remove('hidden');

                // Create papers section
                createPapersSection(geneName, boxplotContainer, data.papers || [], {
                    currentPage: 1,
                    hasMore: data.has_more_papers,
                    totalPapers: data.total_papers || data.papers.length
                });
            })
            .catch(error => {
                console.error('Error loading gene data:', error);
                geneTitleElement.textContent = 'Error';
                boxplotErrorElement.textContent = `Error: ${error.message}`;
                boxplotErrorElement.classList.remove('hidden');
                boxplotLoading.classList.add('hidden');
            });
    }

    function displayGeneInfo(container, geneInfo) {
        container.innerHTML = `
            <table>
                <tr><td>Gene Symbol:</td><td>${geneInfo.EntrezGeneSymbol}</td></tr>
                <tr><td>Log2 Fold Change:</td><td>${typeof geneInfo.logFC === 'number' ? geneInfo.logFC.toFixed(4) : geneInfo.logFC}</td></tr>
                <tr><td>Adjusted P-value:</td><td>${typeof geneInfo['adj.P.Val'] === 'number' ? geneInfo['adj.P.Val'].toExponential(4) : geneInfo['adj.P.Val']}</td></tr>
                <tr><td>Regulation:</td><td>${geneInfo.regulation}</td></tr>
            </table>`;
    }

    function createPapersSection(geneName, container, initialPapers, paginationInfo) {
        // Create papers container
        const papersContainer = document.createElement('div');
        papersContainer.className = 'papers-container';

        // Store gene name and pagination info
        papersContainer.dataset.geneName = geneName;
        papersContainer.dataset.currentPage = paginationInfo.currentPage;
        papersContainer.dataset.totalPapers = paginationInfo.totalPapers;

        // Header with title and loading indicator
        papersContainer.innerHTML = `
            <div class="papers-header">
                <h3>Related Scientific Papers</h3>
                <span class="papers-loading">${initialPapers.length > 0 ? '' : 'Loading papers...'}</span>
            </div>
            <ul class="papers-list"></ul>
            <div class="pagination-controls"></div>`;

        const papersList = papersContainer.querySelector('.papers-list');
        const paginationControls = papersContainer.querySelector('.pagination-controls');

        // Add initial papers or loading placeholder
        if (initialPapers.length > 0) {
            initialPapers.forEach(paper => papersList.appendChild(createPaperItem(paper)));
            addSortControls(papersContainer, initialPapers);

            // Only add pagination if there are more papers to show
            if (paginationInfo.hasMore || paginationInfo.currentPage > 1) {
                updatePaginationControls(papersContainer, paginationControls, paginationInfo);
            }
        } else {
            papersList.innerHTML = '<li class="paper-loading">Searching for publications...</li>';
            fetchAdditionalPapers(geneName, papersContainer, 1);
        }

        container.appendChild(papersContainer);
    }

    function updatePaginationControls(papersContainer, controlsContainer, paginationInfo) {
        const currentPage = parseInt(papersContainer.dataset.currentPage) || 1;
        const totalPapers = parseInt(papersContainer.dataset.totalPapers) || 0;
        const pageSize = 5; // Default page size
        const totalPages = Math.ceil(totalPapers / pageSize);

        let controlsHTML = '';

        // Only show pagination if we have more than one page
        if (totalPages > 1 || paginationInfo.hasMore) {
            controlsHTML += '<div class="pagination">';

            // Previous button
            if (currentPage > 1) {
                controlsHTML += `<button class="pagination-prev">Previous</button>`;
            }

            // Page indicator
            controlsHTML += `<span class="pagination-info">Page ${currentPage}${totalPages ? ' of ' + totalPages : ''}</span>`;

            // Next button - show if hasMore is true or we're not on the last page
            if (paginationInfo.hasMore || (totalPages && currentPage < totalPages)) {
                controlsHTML += `<button class="pagination-next">Next</button>`;
            }

            controlsHTML += '</div>';
        }

        controlsContainer.innerHTML = controlsHTML;

        // Add event listeners to pagination buttons
        const prevButton = controlsContainer.querySelector('.pagination-prev');
        const nextButton = controlsContainer.querySelector('.pagination-next');

        if (prevButton) {
            prevButton.addEventListener('click', function() {
                const newPage = currentPage - 1;
                if (newPage >= 1) {
                    fetchAdditionalPapers(papersContainer.dataset.geneName, papersContainer, newPage);
                }
            });
        }

        if (nextButton) {
            nextButton.addEventListener('click', function() {
                const newPage = currentPage + 1;
                fetchAdditionalPapers(papersContainer.dataset.geneName, papersContainer, newPage);
            });
        }
    }

    function fetchAdditionalPapers(geneName, papersContainer, page) {
        const loadingSpan = papersContainer.querySelector('.papers-loading');
        const papersList = papersContainer.querySelector('.papers-list');
        const pageSize = 5; // Default page size, should match server

        // Show loading indicator
        loadingSpan.textContent = 'Loading papers...';

        // Set loading timeout for 30 seconds
        const loadingTimeout = setTimeout(() => {
            if (loadingSpan.textContent.includes('Loading')) {
                loadingSpan.textContent = '';
                papersList.innerHTML = '<li class="papers-error">Timeout loading papers. Please try again later.</li>';
            }
        }, 30000);

        fetch(`/api/papers/${geneName}?page=${page}&page_size=${pageSize}`)
            .then(response => {
                clearTimeout(loadingTimeout);
                return response.ok ? response.json() : Promise.reject(`HTTP error! status: ${response.status}`);
            })
            .then(data => {
                const papers = data.papers || [];
                loadingSpan.textContent = '';
                papersList.innerHTML = '';

                if (papers.length > 0) {
                    // Update container with new page info
                    papersContainer.dataset.currentPage = data.page;
                    papersContainer.dataset.totalPapers = data.total_papers;

                    // Add papers to list
                    papers.forEach(paper => papersList.appendChild(createPaperItem(paper)));

                    // Add sort controls
                    addSortControls(papersContainer, papers);

                    // Update pagination controls
                    updatePaginationControls(
                        papersContainer,
                        papersContainer.querySelector('.pagination-controls'),
                        {
                            currentPage: data.page,
                            hasMore: data.has_more,
                            totalPapers: data.total_papers
                        }
                    );
                } else {
                    // No papers found
                    papersList.innerHTML = '<li class="no-papers">No scientific papers found for this gene.</li>';
                }
            })
            .catch(error => {
                clearTimeout(loadingTimeout);
                console.error('Error loading papers:', error);
                loadingSpan.textContent = '';
                papersList.innerHTML = `<li class="papers-error">Error loading papers: ${error.message}</li>`;
            });
    }

    function createPaperItem(paper) {
        const paperItem = document.createElement('li');
        paperItem.innerHTML = `
            <a href="${paper.url}" target="_blank" rel="noopener noreferrer">
                ${paper.title || `PubMed ID: ${paper.pmid}`}
            </a>
            <div class="paper-meta">
                ${paper.date && paper.date !== "Unknown" ? 
                  `<span class="paper-date">Published: ${paper.date}</span>` : ''}
                <span class="paper-citations">Citations: ${paper.citations}</span>
            </div>`;
        return paperItem;
    }

    function addSortControls(papersContainer, papers) {
        // Remove existing sort controls
        const existingSortControls = papersContainer.querySelector('.sort-controls');
        if (existingSortControls) existingSortControls.remove();

        // Create sort controls
        const sortDiv = document.createElement('div');
        sortDiv.className = 'sort-controls';
        sortDiv.innerHTML = `
            <span>Sort by: </span>
            <select id="paper-sort">
                <option value="default">Default</option>
                <option value="date-desc">Date (newest first)</option>
                <option value="date-asc">Date (oldest first)</option>
                <option value="citations-desc">Citations (high to low)</option>
                <option value="citations-asc">Citations (low to high)</option>
            </select>`;

        papersContainer.querySelector('.papers-header').appendChild(sortDiv);

        // Store papers data for current page only
        papersContainer.dataset.currentPagePapers = JSON.stringify(papers);

        // Add event listener
        papersContainer.querySelector('#paper-sort').addEventListener('change', function() {
            renderSortedPapers(papersContainer);
        });
    }

    function renderSortedPapers(container) {
        const papersList = container.querySelector('.papers-list');
        const sortSelect = container.querySelector('#paper-sort');
        const currentPagePapers = JSON.parse(container.dataset.currentPagePapers || '[]');

        if (currentPagePapers.length === 0) return;

        // Sort papers (only the ones visible on the current page)
        const sortedPapers = [...currentPagePapers];

        switch (sortSelect.value) {
            case 'date-desc':
                sortedPapers.sort((a, b) => {
                    if (a.date === "Unknown") return 1;
                    if (b.date === "Unknown") return -1;
                    return new Date(b.date) - new Date(a.date);
                });
                break;
            case 'date-asc':
                sortedPapers.sort((a, b) => {
                    if (a.date === "Unknown") return 1;
                    if (b.date === "Unknown") return -1;
                    return new Date(a.date) - new Date(b.date);
                });
                break;
            case 'citations-desc':
                sortedPapers.sort((a, b) => b.citations - a.citations);
                break;
            case 'citations-asc':
                sortedPapers.sort((a, b) => a.citations - b.citations);
                break;
        }

        // Clear and rebuild list
        papersList.innerHTML = '';
        sortedPapers.forEach(paper => papersList.appendChild(createPaperItem(paper)));
    }
});