// app/static/js/main.js
document.addEventListener('DOMContentLoaded', function() {
    // Load volcano plot on page load
    loadVolcanoPlot();

    // Function to load the volcano plot
    function loadVolcanoPlot() {
        const loadingElement = document.getElementById('volcano-loading');
        const plotElement = document.getElementById('volcano-plot');

        loadingElement.classList.remove('hidden');
        plotElement.classList.add('hidden');

        fetch('/api/volcano-data')
            .then(response => response.json())
            .then(data => {
                const plotData = JSON.parse(data.plot);

                // Update layout for better centering
                const updatedLayout = {
                    ...plotData.layout,
                    autosize: true,
                    margin: {
                        l: 70,
                        r: 70,
                        b: 70,
                        t: 70,
                        pad: 10
                    }
                };

                Plotly.newPlot('volcano-plot', plotData.data, updatedLayout, {
                    responsive: true,
                    displayModeBar: true
                });

                // Add click event to the plot
                document.getElementById('volcano-plot').on('plotly_click', function(data) {
                    // Get the gene name from the point's custom data
                    const point = data.points[0];
                    const geneName = point.customdata[0];
                    console.log("Clicked on gene:", geneName);  // Debug output

                    // Load gene data and boxplot
                    loadGeneData(geneName);
                });

                loadingElement.classList.add('hidden');
                plotElement.classList.remove('hidden');
            })
            .catch(error => {
                console.error('Error loading volcano plot:', error);
                loadingElement.textContent = 'Error loading volcano plot. Please try again.';
            });
    }

    // Function to load gene data and create boxplot
    function loadGeneData(geneName) {
        const boxplotContainer = document.getElementById('boxplot-container');
        const boxplotLoading = document.getElementById('boxplot-loading');
        const boxplotElement = document.getElementById('boxplot');
        const geneInfoElement = document.getElementById('gene-info');
        const geneTitleElement = document.getElementById('gene-title');

        // Clear any existing paper information
        const existingPapersContainer = boxplotContainer.querySelector('.papers-container');
        if (existingPapersContainer) {
            existingPapersContainer.remove();
        }

        const existingNoPapers = boxplotContainer.querySelector('.no-papers');
        if (existingNoPapers) {
            existingNoPapers.remove();
        }

        boxplotContainer.classList.remove('hidden');
        boxplotLoading.classList.remove('hidden');
        boxplotElement.classList.add('hidden');
        geneInfoElement.innerHTML = '';
        geneTitleElement.textContent = `Loading data for ${geneName}...`;

        // Scroll to boxplot
        boxplotContainer.scrollIntoView({ behavior: 'smooth' });

        fetch(`/api/gene/${geneName}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Gene not found');
                }
                return response.json();
            })
            .then(data => {
                // Update gene title and info
                geneTitleElement.textContent = `${geneName} Information`;

                // Display gene information
                const geneInfo = data.gene_info;
                let infoHTML = '<table>';
                infoHTML += `<tr><td>Gene Symbol:</td><td>${geneInfo.EntrezGeneSymbol}</td></tr>`;
                infoHTML += `<tr><td>Log2 Fold Change:</td><td>${typeof geneInfo.logFC === 'number' ? geneInfo.logFC.toFixed(4) : geneInfo.logFC}</td></tr>`;
                infoHTML += `<tr><td>Adjusted P-value:</td><td>${typeof geneInfo['adj.P.Val'] === 'number' ? geneInfo['adj.P.Val'].toExponential(4) : geneInfo['adj.P.Val']}</td></tr>`;
                infoHTML += `<tr><td>Regulation:</td><td>${geneInfo.regulation}</td></tr>`;
                infoHTML += '</table>';

                geneInfoElement.innerHTML = infoHTML;

                // Create boxplot
                const boxplotData = JSON.parse(data.boxplot);

                const updatedBoxplotLayout = {
                    ...boxplotData.layout,
                    autosize: true,
                    margin: {
                        l: 70,
                        r: 70,
                        b: 70,
                        t: 70,
                        pad: 10
                    }
                };

                Plotly.newPlot('boxplot', boxplotData.data, updatedBoxplotLayout, {
                    responsive: true,
                    displayModeBar: true
                });

                boxplotLoading.classList.add('hidden');
                boxplotElement.classList.remove('hidden');

                // Create papers section with loading indicator
                createPapersSection(geneName, boxplotContainer, data.papers || []);
            })
            .catch(error => {
                console.error('Error loading gene data:', error);
                geneTitleElement.textContent = 'Error';
                geneInfoElement.innerHTML = `<p>Error loading data for ${geneName}. ${error}</p>`;
                boxplotLoading.classList.add('hidden');
            });
    }

    // Function to create papers section with lazy loading
    function createPapersSection(geneName, container, initialPapers) {
        // Create papers container
        const papersContainer = document.createElement('div');
        papersContainer.className = 'papers-container';

        // Create header with title and loading indicator
        const headerDiv = document.createElement('div');
        headerDiv.className = 'papers-header';

        const papersTitle = document.createElement('h3');
        papersTitle.textContent = 'Related Scientific Papers';
        headerDiv.appendChild(papersTitle);

        const loadingSpan = document.createElement('span');
        loadingSpan.className = 'papers-loading';
        loadingSpan.innerHTML = initialPapers.length > 0 ? '' : 'Loading papers...';
        headerDiv.appendChild(loadingSpan);

        papersContainer.appendChild(headerDiv);

        // Create papers list
        const papersList = document.createElement('ul');
        papersList.className = 'papers-list';

        // Add initial papers if any
        if (initialPapers.length > 0) {
            initialPapers.forEach(paper => {
                papersList.appendChild(createPaperItem(paper));
            });
        } else {
            // If no initial papers, show placeholder
            const loadingItem = document.createElement('li');
            loadingItem.className = 'paper-loading';
            loadingItem.textContent = 'Searching for publications...';
            papersList.appendChild(loadingItem);

            // Try to load papers from separate endpoint
            fetchAdditionalPapers(geneName, papersContainer);
        }

        papersContainer.appendChild(papersList);

        // Add sort controls if we have papers
        if (initialPapers.length > 0) {
            addSortControls(papersContainer, initialPapers);
        }

        // Add papers container to the main container
        container.appendChild(papersContainer);
    }

    // Function to fetch additional papers
    function fetchAdditionalPapers(geneName, papersContainer) {
        fetch(`/api/papers/${geneName}`)
            .then(response => response.json())
            .then(data => {
                const papers = data.papers || [];
                const papersList = papersContainer.querySelector('.papers-list');
                const loadingSpan = papersContainer.querySelector('.papers-loading');

                // Clear loading indicators
                loadingSpan.textContent = '';
                papersList.innerHTML = '';

                if (papers.length > 0) {
                    // Add papers to list
                    papers.forEach(paper => {
                        papersList.appendChild(createPaperItem(paper));
                    });

                    // Add sort controls
                    addSortControls(papersContainer, papers);
                } else {
                    // No papers found
                    const noDataElement = document.createElement('li');
                    noDataElement.className = 'no-papers';
                    noDataElement.textContent = 'No scientific papers found for this gene.';
                    papersList.appendChild(noDataElement);
                }
            })
            .catch(error => {
                console.error('Error loading papers:', error);
                const papersList = papersContainer.querySelector('.papers-list');
                const loadingSpan = papersContainer.querySelector('.papers-loading');

                loadingSpan.textContent = '';
                papersList.innerHTML = '';

                const errorElement = document.createElement('li');
                errorElement.className = 'papers-error';
                errorElement.textContent = 'Error loading papers. Please try again later.';
                papersList.appendChild(errorElement);
            });
    }

    // Function to create a paper list item
    function createPaperItem(paper) {
        const paperItem = document.createElement('li');

        const paperLink = document.createElement('a');
        paperLink.href = paper.url;
        paperLink.target = '_blank';
        paperLink.textContent = paper.title || `PubMed ID: ${paper.pmid}`;
        paperItem.appendChild(paperLink);

        const paperMeta = document.createElement('div');
        paperMeta.className = 'paper-meta';

        if (paper.date && paper.date !== "Unknown") {
            const dateSpan = document.createElement('span');
            dateSpan.className = 'paper-date';
            dateSpan.textContent = `Published: ${paper.date}`;
            paperMeta.appendChild(dateSpan);
        }

        const citationsSpan = document.createElement('span');
        citationsSpan.className = 'paper-citations';
        citationsSpan.textContent = `Citations: ${paper.citations}`;
        paperMeta.appendChild(citationsSpan);

        paperItem.appendChild(paperMeta);
        return paperItem;
    }

    // Function to add sort controls to papers container
    function addSortControls(papersContainer, papers) {
        // Remove existing sort controls if any
        const existingSortControls = papersContainer.querySelector('.sort-controls');
        if (existingSortControls) {
            existingSortControls.remove();
        }

        // Create sort controls
        const headerDiv = papersContainer.querySelector('.papers-header');
        const sortDiv = document.createElement('div');
        sortDiv.className = 'sort-controls';

        const sortLabel = document.createElement('span');
        sortLabel.textContent = 'Sort by: ';
        sortDiv.appendChild(sortLabel);

        const sortSelect = document.createElement('select');
        sortSelect.id = 'paper-sort';

        const options = [
            { value: 'default', text: 'Default' },
            { value: 'date-desc', text: 'Date (newest first)' },
            { value: 'date-asc', text: 'Date (oldest first)' },
            { value: 'citations-desc', text: 'Citations (high to low)' },
            { value: 'citations-asc', text: 'Citations (low to high)' }
        ];

        options.forEach(option => {
            const optElement = document.createElement('option');
            optElement.value = option.value;
            optElement.textContent = option.text;
            sortSelect.appendChild(optElement);
        });

        sortDiv.appendChild(sortSelect);
        headerDiv.appendChild(sortDiv);

        // Store papers data
        papersContainer.dataset.allPapers = JSON.stringify(papers);
        papersContainer.dataset.visibleCount = papers.length.toString();

        // Add event listener
        sortSelect.addEventListener('change', function() {
            renderPapers(papersContainer);
        });
    }

    // Function to render papers based on current sort settings
    function renderPapers(container) {
        const papersList = container.querySelector('.papers-list');
        const sortSelect = container.querySelector('#paper-sort');

        // Get data
        const allPapers = JSON.parse(container.dataset.allPapers);
        const visibleCount = parseInt(container.dataset.visibleCount);

        // Sort papers
        const sortedPapers = [...allPapers];

        switch (sortSelect.value) {
            case 'date-desc':
                sortedPapers.sort((a, b) => {
                    // Handle "Unknown" dates
                    if (a.date === "Unknown") return 1;
                    if (b.date === "Unknown") return -1;
                    return new Date(b.date) - new Date(a.date);
                });
                break;
            case 'date-asc':
                sortedPapers.sort((a, b) => {
                    // Handle "Unknown" dates
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

        // Clear current list
        papersList.innerHTML = '';

        // Add papers (limited by visible count)
        const papersToShow = sortedPapers.slice(0, visibleCount);

        papersToShow.forEach(paper => {
            papersList.appendChild(createPaperItem(paper));
        });
    }
});