from flask import render_template, jsonify, current_app
import pandas as pd
from app import data_processing, visualization


def init_routes(app):
    @app.route('/')
    def index():
        """Render main page with volcano plot"""
        return render_template('index.html')

    @app.route('/api/volcano-data')
    def get_volcano_data():
        """API endpoint to get volcano plot data"""
        volcano_data = data_processing.load_volcano_data()
        volcano_plot = visualization.create_volcano_plot(volcano_data)
        return jsonify({'plot': volcano_plot})

    @app.route('/api/gene/<gene_name>')
    def get_gene_data(gene_name):
        """API endpoint to get boxplot data for a specific gene"""
        gene_data = data_processing.get_gene_data(gene_name)

        if gene_data is None:
            return jsonify({'error': f'Gene {gene_name} not found'}), 404

        boxplot = visualization.create_boxplot(
            pd.DataFrame(gene_data['boxplot_data']),
            gene_name
        )

        return jsonify({
            'gene_info': gene_data['gene_info'],
            'boxplot': boxplot
        })