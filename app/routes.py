# app/routes.py
from flask import render_template, jsonify
import pandas as pd
import traceback
import json
import threading
from app import data_processing, visualization, mygene_client
from app.logger import get_logger

logger = get_logger()


def init_routes(app):
    @app.route('/')
    def index():
        """Render main page with volcano plot"""
        logger.info("Rendering index page")
        return render_template('index.html')

    @app.route('/api/volcano-data')
    def get_volcano_data():
        """API endpoint to get volcano plot data"""
        try:
            logger.info("Fetching volcano plot data...")

            # Load the data
            volcano_data = data_processing.load_volcano_data()

            # Create the plot
            volcano_plot = visualization.create_volcano_plot(volcano_data)

            # Return the data
            logger.info(f"Successfully created volcano plot with {len(volcano_data)} data points")
            return jsonify({'plot': volcano_plot})
        except Exception as e:
            error_message = str(e)
            stack_trace = traceback.format_exc()
            logger.error(f"Error in get_volcano_data: {error_message}")
            logger.error(stack_trace)
            return jsonify({'error': error_message}), 500

    @app.route('/api/gene/<gene_name>')
    def get_gene_data(gene_name):
        """API endpoint to get boxplot and paper data for a specific gene"""
        try:
            logger.info(f"Fetching data for gene: {gene_name}")

            # Get the combined gene data
            gene_data = data_processing.get_gene_data(gene_name)

            if gene_data is None:
                error_msg = f'Gene {gene_name} not found or no data available'
                logger.warning(error_msg)
                return jsonify({'error': error_msg}), 404

            # Create the boxplot
            boxplot_df = pd.DataFrame(gene_data['boxplot_data'])
            logger.info(f"Creating boxplot with {len(boxplot_df)} data points for gene {gene_name}")

            boxplot = visualization.create_boxplot(boxplot_df, gene_name)

            # Get related papers with a timeout
            papers = []
            paper_thread = None

            def fetch_papers():
                """Fetch papers in a separate thread with timeout"""
                nonlocal papers
                try:
                    logger.info(f"Fetching papers for gene: {gene_name} in background thread")
                    papers = mygene_client.get_papers_for_gene(gene_name, max_papers=5, timeout=10)
                    logger.info(f"Found {len(papers)} papers for gene {gene_name}")
                except Exception as e:
                    logger.error(f"Error fetching papers for gene {gene_name}: {str(e)}")
                    papers = []

            # Start background paper fetching thread
            paper_thread = threading.Thread(target=fetch_papers)
            paper_thread.daemon = True  # Thread will terminate when main thread ends
            paper_thread.start()

            # Wait for a short time for papers to be fetched, but don't block indefinitely
            paper_thread.join(timeout=3.0)  # Wait max 3 seconds

            if paper_thread.is_alive():
                logger.info(f"Paper fetching still running for {gene_name}, returning without papers")
                # Paper fetching is still running, but we won't wait
                papers = []

            # Build the response
            response = {
                'gene_info': gene_data['gene_info'],
                'boxplot': boxplot,
                'papers': papers
            }

            logger.info(f"Successfully prepared response for gene: {gene_name} with {len(papers)} papers")
            return jsonify(response)
        except Exception as e:
            error_message = str(e)
            stack_trace = traceback.format_exc()
            logger.error(f"Error in get_gene_data for gene {gene_name}: {error_message}")
            logger.error(stack_trace)
            return jsonify({'error': error_message}), 500

    @app.route('/api/papers/<gene_name>')
    def get_gene_papers(gene_name):
        """Separate endpoint to get papers for a gene"""
        try:
            logger.info(f"Fetching papers for gene: {gene_name} (dedicated endpoint)")
            papers = mygene_client.get_papers_for_gene(gene_name, max_papers=10, timeout=20)
            logger.info(f"Found {len(papers)} papers for gene {gene_name}")
            return jsonify({'papers': papers})
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error fetching papers for gene {gene_name}: {error_message}")
            return jsonify({'error': error_message}), 500

    @app.route('/api/test-gene/<gene_name>')
    def test_gene_data(gene_name):
        """Test endpoint to verify API functionality"""
        try:
            logger.info(f"Testing API for gene: {gene_name}")

            # Test the volcano data loading
            volcano_data = data_processing.load_volcano_data()
            logger.info(f"Loaded volcano data with {len(volcano_data)} points")

            # Test finding the gene in volcano data
            gene_volcano_data = volcano_data[volcano_data['EntrezGeneSymbol'] == gene_name]
            if gene_volcano_data.empty:
                logger.warning(f"Gene {gene_name} not found in volcano data")
                return jsonify({
                    'status': 'error',
                    'message': f'Gene {gene_name} not found in volcano data'
                })

            logger.info(f"Found gene {gene_name} in volcano data")

            # Test loading boxplot data
            boxplot_data = data_processing.load_boxplot_data(gene_name)
            if boxplot_data is None or boxplot_data.empty:
                logger.warning(f"No boxplot data available for gene {gene_name}")
                return jsonify({
                    'status': 'error',
                    'message': f'No boxplot data available for gene {gene_name}'
                })

            logger.info(f"Loaded boxplot data with {len(boxplot_data)} points")

            # Return success with gene info
            return jsonify({
                'status': 'success',
                'gene': gene_name,
                'volcano_data_found': True,
                'boxplot_data_points': len(boxplot_data),
                'gene_info': {
                    'logFC': float(gene_volcano_data['logFC'].iloc[0]),
                    'adj_P_Val': float(gene_volcano_data['adj.P.Val'].iloc[0]),
                    'regulation': gene_volcano_data['regulation'].iloc[0]
                }
            })
        except Exception as e:
            error_message = str(e)
            stack_trace = traceback.format_exc()
            logger.error(f"Error in test endpoint for gene {gene_name}: {error_message}")
            logger.error(stack_trace)
            return jsonify({
                'status': 'error',
                'message': error_message,
                'traceback': stack_trace
            }), 500