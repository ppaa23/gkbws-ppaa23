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
                Plotly.newPlot('volcano-plot', plotData.data, plotData.layout);

                // Add click event to the plot
                document.getElementById('volcano-plot').on('plotly_click', function(data) {
                    // Get the gene name from the point's custom data
                    const point = data.points[0];
                    const geneName = point.customdata[0];

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
                infoHTML += `<tr><td>Log2 Fold Change:</td><td>${geneInfo.logFC.toFixed(4)}</td></tr>`;
                infoHTML += `<tr><td>Adjusted P-value:</td><td>${geneInfo.adj.P.Val.toExponential(4)}</td></tr>`;
                infoHTML += `<tr><td>Regulation:</td><td>${geneInfo.regulation}</td></tr>`;
                infoHTML += '</table>';

                geneInfoElement.innerHTML = infoHTML;

                // Create boxplot
                const boxplotData = JSON.parse(data.boxplot);
                Plotly.newPlot('boxplot', boxplotData.data, boxplotData.layout);

                boxplotLoading.classList.add('hidden');
                boxplotElement.classList.remove('hidden');
            })
            .catch(error => {
                console.error('Error loading gene data:', error);
                geneTitleElement.textContent = 'Error';
                geneInfoElement.innerHTML = `<p>Error loading data for ${geneName}. ${error}</p>`;
                boxplotLoading.classList.add('hidden');
            });
    }
});