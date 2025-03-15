from flask import render_template, jsonify, request
import pandas as pd
import traceback
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
            logger.info("Fetching volcano plot data")
            volcano_data = data_processing.load_volcano_data()
            volcano_plot = visualization.create_volcano_plot(volcano_data)
            logger.info(f"Successfully created volcano plot with {len(volcano_data)} data points")
            return jsonify({'plot': volcano_plot})
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error in get_volcano_data: {error_message}")
            logger.error(traceback.format_exc())
            return jsonify({'error': error_message}), 500

    @app.route('/api/gene/<gene_name>')
    def get_gene_data(gene_name):
        """API endpoint to get boxplot and paper data for a specific gene"""
        try:
            logger.info(f"Fetching data for gene: {gene_name}")
            gene_data = data_processing.get_gene_data(gene_name)

            if gene_data is None:
                error_msg = f'Gene {gene_name} not found or no data available'
                logger.warning(error_msg)
                return jsonify({'error': error_msg}), 404

            boxplot_df = pd.DataFrame(gene_data['boxplot_data'])
            logger.info(f"Creating boxplot with {len(boxplot_df)} data points for gene {gene_name}")
            boxplot = visualization.create_boxplot(boxplot_df, gene_name)

            # Get related papers in background thread with timeout
            papers = []

            def fetch_papers():
                nonlocal papers
                try:
                    logger.info(f"Background thread: fetching papers for gene {gene_name}")
                    papers = mygene_client.get_papers_for_gene(gene_name, max_papers=100, timeout=100)
                    logger.info(f"Background thread: found {len(papers)} papers for gene {gene_name}")
                except Exception as e:
                    logger.error(f"Background thread: error fetching papers for gene {gene_name}: {str(e)}")
                    papers = []

            paper_thread = threading.Thread(target=fetch_papers)
            paper_thread.daemon = True
            paper_thread.start()
            paper_thread.join(timeout=3.0)

            if paper_thread.is_alive():
                logger.info(f"Paper fetching still running for {gene_name}, returning without papers")
                papers = []

            response = {
                'gene_info': gene_data['gene_info'],
                'boxplot': boxplot,
                'papers': papers,
                'total_papers': len(papers),
                'has_more_papers': len(papers) >= 8
            }

            logger.info(f"Successfully prepared response for gene: {gene_name} with {len(papers)} papers")
            return jsonify(response)
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error in get_gene_data for gene {gene_name}: {error_message}")
            logger.error(traceback.format_exc())
            return jsonify({'error': error_message}), 500

    @app.route('/api/papers/<gene_name>')
    def get_gene_papers(gene_name):
        """Endpoint to get papers for a gene with pagination"""
        try:
            page = int(request.args.get('page', 1))
            page_size = int(request.args.get('page_size', 5))
            skip = (page - 1) * page_size

            logger.info(f"Fetching papers for gene: {gene_name} (page {page}, size {page_size})")

            all_papers = mygene_client.get_papers_for_gene(gene_name, max_papers=100, timeout=100)
            total_papers = len(all_papers)

            # Apply pagination
            paginated_papers = all_papers[skip:skip + page_size]
            has_more = total_papers > skip + page_size

            logger.info(
                f"Found {total_papers} papers for gene {gene_name}, returning {len(paginated_papers)} for page {page}")

            return jsonify({
                'papers': paginated_papers,
                'page': page,
                'page_size': page_size,
                'total_papers': total_papers,
                'has_more': has_more
            })
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error fetching papers for gene {gene_name}: {error_message}")
            return jsonify({'error': error_message}), 500