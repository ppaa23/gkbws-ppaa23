# Gene Expression Explorer

## Description
This is a Flask-based web application that visualizes protein activity levels in aging studies. The application provides an interactive volcano plot to explore differentially expressed genes between young and old donors, with detailed boxplots for individual genes and references to relevant scientific publications.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/gene-expression-explorer.git
   cd gene-expression-explorer
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python run.py
   ```

4. (Optional) Run the tests:
   ```bash
   python -m pytest
   ```

## Requirements
- Python 3.8+
- Flask
- Pandas
- Plotly
- NumPy
- Openpyxl
- Requests

All the required packages are specified in the `requirements.txt` file.

## Features
- **Interactive Volcano Plot**: Visualize differentially expressed genes with statistical significance
- **Gene-Specific Boxplots**: Compare protein levels between young and old donors for selected genes
- **Scientific Publications**: Retrieve and display relevant research papers for each gene
- **Efficient Data Processing**: Optimized data loading and caching for faster performance
- **Singleton Logger**: Centralized logging system with file rotation
- **Comprehensive Testing**: Extensive test coverage for all components

## Project Structure
```
gene-expression-explorer/
│
├── app/
│   ├── static/
│   │   ├── data/
│   │   │   └── NIHMS1635539-supplement-1635539_Sup_tab_4.xlsx   # Dataset
│   │   ├── css/
│   │   │   └── styles.css                                       # CSS styles
│   │   └── js/
│   │       └── main.js                                          # Frontend JavaScript
│   ├── templates/
│   │   └── index.html                                           # Main HTML template
│   ├── __init__.py                                              # App initialization
│   ├── data_processing.py                                       # Data loading and processing
│   ├── logger.py                                                # Singleton logger implementation
│   ├── mygene_client.py                                         # API client for MyGene.info
│   ├── routes.py                                                # Flask routes
│   └── visualization.py                                         # Plotting functions
│
├── logs/                                                        # Log files directory
│
├── tests/
│   └── test_app.py                                              # Tests for the application
│
├── README.md                                                    # This file
├── requirements.txt                                             # Dependencies
└── run.py                                                       # Application entry point
```

## API Endpoints
- `/` (GET) - Displays the main page with the volcano plot
- `/api/volcano-data` (GET) - Returns JSON data for the volcano plot
- `/api/gene/<gene_name>` (GET) - Returns gene data, boxplot, and papers for a specific gene
- `/api/papers/<gene_name>` (GET) - Returns only papers for a specific gene
- `/api/test-gene/<gene_name>` (GET) - Test endpoint for API diagnostics

## Usage
1. Open your browser and navigate to `http://localhost:5000/`
2. Explore the volcano plot - red points represent up-regulated genes, blue points represent down-regulated genes
3. Click on any point to view detailed information about the selected gene
4. The boxplot shows protein levels in young vs. old samples
5. Below the boxplot, you'll find relevant scientific publications related to the gene

## Note
This application uses the MyGene.info API to retrieve scientific publications. There are rate limits on this API, so occasionally the paper retrieval might timeout if too many requests are made in a short period.