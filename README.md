# Testing assignment for Gene Knowledge Base Web Service

## Description
This is a Flask-based web application that visualizes protein activity levels with interactive volcano plots, boxplots, and related scientific publications.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/ppaa23/gkbws-ppaa23.git
   cd gkbws-ppaa23
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
- Python 3.11+
- Flask
- Werkzeug
- pandas
- numpy
- plotly = 5.16.1
- openpyxl
- requests
- pytest

All the required packages (with the appropriate versions) are specified in the `requirements.txt` file.

## Features
- **Interactive Volcano Plot**: The app uses Plotly to create an interactive volcano plot (with standard level of critical p-value = 0.5).
- **Gene-Specific Boxplots**: The app displays boxplots showing the distribution of expression among different age groups.
- **Related Publications**: The app displays research papers with mentioning of gene name (obtained through MyGene.info API). For better user experience, related papers are paginated, and can be sorted (but sorting is working for each page separately, since the loading of all papers might be too slow). Loading this data is also bounded by the timeout of 100 seconds to avoid long waiting times.
- **Caching of gene-specific information**: The app caches volcano plot data and gene-specific information to reduce the number of API calls and improve time and memory efficiency.
- **Logging**: The app uses Singleton pattern to avoid multiple instances of logger.
- **Testing**: The app uses pytest to test the application (including negative tests, e.g. 404 error).

## API Endpoints
- `/` (GET) - Displays the main page with the volcano plot
- `/api/volcano-data` (GET) - Returns JSON data for the volcano plot
- `/api/gene/<gene_name>` (GET) - Returns gene data, boxplot, and papers for a specific gene
- `/api/papers/<gene_name>` (GET) - Returns paginated papers for a specific gene

API endpoints are used for creating plots and tables, user accesses all the information via the main page.

## Project structure
```
gene-expression-explorer/
│
├── app/
│   ├── static/
│   │   ├── data/NIHMS1635539-supplement-1635539_Sup_tab_4.xlsx  # Dataset
│   │   ├── css/style.css                                        # CSS styles
│   │   └── js/ main.js                                          # Frontend JavaScript
│   ├── templates/
│   │   └── index.html                                           
│   ├── __init__.py                                              
│   ├── data_processing.py                                       # Data loading and processing
│   ├── logger.py                                                # Singleton logger implementation
│   ├── mygene_client.py                                         # API client for MyGene.info
│   ├── routes.py                                                
│   └── visualization.py                                         # Plotting functions
├── tests/                                                       # Tests directory
│
├── README.md                                                    
├── requirements.txt                                             
└── run.py                                                       # Application entry point
```

It is important to mention that the above tree doesn't contain all files (e.g., .gitignore, pytest.ini, etc.).