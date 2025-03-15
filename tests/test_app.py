import sys
import os
import json
import pytest
import pandas as pd
import numpy as np
import tempfile
import shutil
from unittest import mock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, data_processing, visualization, mygene_client


@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
    })
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def mock_excel_file():
    temp_dir = tempfile.mkdtemp()

    volcano_df = pd.DataFrame({
        'EntrezGeneSymbol': ['GENE1', 'GENE2', 'GENE3', 'GENE4'],
        'logFC': [1.5, -2.0, 0.2, -0.3],
        'adj.P.Val': [0.01, 0.001, 0.2, 0.5]
    })

    boxplot_df = pd.DataFrame({
        'EntrezGeneSymbol': ['GENE1', 'GENE1', 'GENE2', 'GENE2'],
        'Set002.H4.YD12': [1.5, np.nan, 2.5, np.nan],
        'Set002.H4.YD13': [1.7, np.nan, 2.7, np.nan],
        'Set002.H4.OD12': [np.nan, 2.2, np.nan, 3.2],
        'Set002.H4.OD13': [np.nan, 2.4, np.nan, 3.4]
    })

    excel_path = os.path.join(temp_dir, 'test_data.xlsx')
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        volcano_df.to_excel(writer, sheet_name='S4B limma results', index=False)
        boxplot_df.to_excel(writer, sheet_name='S4A values', index=False)

    yield excel_path

    # Cleanup
    shutil.rmtree(temp_dir)


def test_get_sample_age_group():
    assert data_processing.get_sample_age_group('Set002.H4.YD12') == 'Young'
    assert data_processing.get_sample_age_group('Set002.H4.OD12') == 'Old'
    assert data_processing.get_sample_age_group('Other.Column') is None


@mock.patch('app.data_processing.get_data_file_path')
def test_load_volcano_data(mock_get_path, mock_excel_file):
    mock_get_path.return_value = mock_excel_file

    volcano_data = data_processing.load_volcano_data()

    assert isinstance(volcano_data, pd.DataFrame)
    assert 'EntrezGeneSymbol' in volcano_data.columns
    assert 'logFC' in volcano_data.columns
    assert 'adj.P.Val' in volcano_data.columns
    assert '-log10(adj.P.Val)' in volcano_data.columns
    assert 'regulation' in volcano_data.columns

    assert len(volcano_data) == 4

    assert 'up-regulated' in volcano_data['regulation'].values
    assert 'down-regulated' in volcano_data['regulation'].values


@mock.patch('app.data_processing.get_data_file_path')
def test_load_boxplot_data(mock_get_path, mock_excel_file):
    mock_get_path.return_value = mock_excel_file

    boxplot_data = data_processing.load_boxplot_data('GENE1')

    assert isinstance(boxplot_data, pd.DataFrame)
    assert 'age_group' in boxplot_data.columns
    assert 'value' in boxplot_data.columns
    assert 'sample' in boxplot_data.columns

    # There are only 'Old' and 'Young' groups
    assert len(boxplot_data['age_group'].unique()) == 2


def test_numpy_encoder():
    test_data = {
        'int': np.int64(42),
        'float': np.float64(3.14),
        'array': np.array([1, 2, 3]),
        'bool': np.bool_(True),
        'nan': np.nan
    }

    encoded = json.dumps(test_data, cls=visualization.NumpyEncoder)
    decoded = json.loads(encoded)

    assert decoded['int'] == 42
    assert decoded['float'] == 3.14
    assert decoded['array'] == [1, 2, 3]
    assert decoded['bool'] is True

    # NaN might be encoded differently
    assert 'nan' in decoded


def test_create_boxplot():
    data = pd.DataFrame({
        'age_group': ['Young', 'Young', 'Old', 'Old'],
        'value': [1.5, 1.7, 2.2, 2.4],
        'sample': ['Sample1', 'Sample2', 'Sample3', 'Sample4']
    })

    boxplot_json = visualization.create_boxplot(data, 'GENE1')
    boxplot_data = json.loads(boxplot_json)

    # Check if data structure is correct
    assert 'data' in boxplot_data
    assert 'layout' in boxplot_data

    assert len(boxplot_data['data']) == 4

    # Check the title contains the gene name
    title = boxplot_data['layout']['title']
    if isinstance(title, dict) and 'text' in title:
        assert 'GENE1' in title['text']
    else:
        assert 'GENE1' in title


@mock.patch('app.data_processing.get_data_file_path')
def test_get_gene_data(mock_get_path, mock_excel_file):
    # Set the mock to return our test file path
    mock_get_path.return_value = mock_excel_file

    gene_data = data_processing.get_gene_data('GENE1')

    # Check if data structure is correct
    assert isinstance(gene_data, dict)
    assert 'gene_info' in gene_data
    assert 'boxplot_data' in gene_data

    # Check gene info
    assert gene_data['gene_info']['EntrezGeneSymbol'] == 'GENE1'

    # Check boxplot data
    assert isinstance(gene_data['boxplot_data'], list)
    assert len(gene_data['boxplot_data']) > 0
    assert 'age_group' in gene_data['boxplot_data'][0]
    assert 'value' in gene_data['boxplot_data'][0]


def test_create_volcano_plot():
    data = pd.DataFrame({
        'EntrezGeneSymbol': ['Gene1', 'Gene2', 'Gene3', 'Gene4'],
        'logFC': [1.5, -2.0, 0.2, -0.3],
        'adj.P.Val': [0.01, 0.001, 0.2, 0.5],
        '-log10(adj.P.Val)': [2.0, 3.0, 0.7, 0.3],
        'regulation': ['up-regulated', 'down-regulated', 'not significant', 'not significant']
    })

    plot_json = visualization.create_volcano_plot(data)

    plot_data = json.loads(plot_json)

    # Check if data structure is correct
    assert 'data' in plot_data
    assert 'layout' in plot_data

    # Check for traces (up-regulated, down-regulated or not significant)
    trace_names = [trace.get('name', '') for trace in plot_data['data']]
    assert 'up-regulated' in trace_names
    assert 'down-regulated' in trace_names
    assert 'not significant' in trace_names


@mock.patch('app.mygene_client.requests.get')
def test_search_gene_by_symbol(mock_get):
    # Mock the API response
    mock_response = mock.Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        'hits': [
            {
                '_id': '1017',
                'symbol': 'CDK2',
                'name': 'cyclin dependent kinase 2'
            }
        ]
    }
    mock_get.return_value = mock_response

    result = mygene_client.search_gene_by_symbol('CDK2')

    assert result['_id'] == '1017'
    assert result['symbol'] == 'CDK2'

    # Check that the API was called correctly
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert 'mygene.info/v3/query' in args[0]
    assert 'symbol:CDK2' in args[0]


@mock.patch('app.mygene_client.requests.get')
@mock.patch('app.mygene_client.get_publication_details')
def test_get_gene_publications(mock_get_pub_details, mock_get):
    # Mock the API response for gene data
    mock_response = mock.Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        '_id': '1017',
        'symbol': 'CDK2',
        'generif': [
            {'pubmed': 12345},
            {'pubmed': 67890}
        ],
        'reporter': {
            'publications': [54321, 98765]
        }
    }
    mock_get.return_value = mock_response

    # Mock the publication details function
    mock_get_pub_details.side_effect = lambda pmid: {
        'pmid': pmid,
        'title': f'Publication {pmid}',
        'url': f'https://pubmed.ncbi.nlm.nih.gov/{pmid}',
        'date': '2020 Jan',
        'citations': int(pmid) % 10
    }

    result = mygene_client.get_gene_publications('1017', max_papers=4)

    assert len(result) == 4  # We asked for a maximum of 4 papers
    assert result[0]['pmid'] in ['12345', '67890', '54321', '98765']

    # Check that the API was called correctly
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert 'mygene.info/v3/gene/1017' in args[0]


@mock.patch('app.mygene_client.search_gene_by_symbol')
@mock.patch('app.mygene_client.get_gene_publications')
def test_get_papers_for_gene(mock_get_pubs, mock_search):
    # Mock the search function
    mock_search.return_value = {
        '_id': '1017',
        'symbol': 'CDK2'
    }

    # Mock the publications function
    mock_get_pubs.return_value = [
        {
            'pmid': '12345',
            'title': 'Publication 12345',
            'url': 'https://pubmed.ncbi.nlm.nih.gov/12345',
            'date': '2020 Jan',
            'citations': 5
        },
        {
            'pmid': '67890',
            'title': 'Publication 67890',
            'url': 'https://pubmed.ncbi.nlm.nih.gov/67890',
            'date': '2019 Dec',
            'citations': 10
        }
    ]

    result = mygene_client.get_papers_for_gene('CDK2', max_papers=2)

    assert len(result) == 2
    assert result[0]['pmid'] == '12345'
    assert result[1]['pmid'] == '67890'

    # Check that the mocked functions were called correctly
    mock_search.assert_called_once_with('CDK2', timeout=5)
    mock_get_pubs.assert_called_once()
    args, kwargs = mock_get_pubs.call_args
    assert args[0] == '1017'
    assert kwargs['max_papers'] == 2


def test_index_route(client):
    response = client.get('/')
    assert response.status_code == 200 # Normal response


@mock.patch('app.data_processing.load_volcano_data')
@mock.patch('app.visualization.create_volcano_plot')
def test_volcano_data_route(mock_create_plot, mock_load_data, client):
    # Mock the data loading
    mock_df = pd.DataFrame({
        'EntrezGeneSymbol': ['Gene1', 'Gene2'],
        'logFC': [1.5, -2.0],
        'adj.P.Val': [0.01, 0.001],
        '-log10(adj.P.Val)': [2.0, 3.0],
        'regulation': ['up-regulated', 'down-regulated']
    })
    mock_load_data.return_value = mock_df

    mock_create_plot.return_value = json.dumps({'data': [], 'layout': {}})

    response = client.get('/api/volcano-data')

    assert response.status_code == 200 # Normal response
    data = json.loads(response.data)
    assert 'plot' in data

    mock_load_data.assert_called_once()
    mock_create_plot.assert_called_once_with(mock_df)


@mock.patch('app.data_processing.get_gene_data')
@mock.patch('app.visualization.create_boxplot')
@mock.patch('app.mygene_client.get_papers_for_gene')
def test_gene_data_route(mock_get_papers, mock_create_boxplot, mock_get_gene_data, client):
    # Mock the gene data
    mock_get_gene_data.return_value = {
        'gene_info': {
            'EntrezGeneSymbol': 'GENE1',
            'logFC': 1.5,
            'adj.P.Val': 0.01,
            'regulation': 'up-regulated'
        },
        'boxplot_data': [
            {'age_group': 'Young', 'value': 1.5, 'sample': 'Sample1'},
            {'age_group': 'Old', 'value': 2.2, 'sample': 'Sample3'}
        ]
    }

    mock_create_boxplot.return_value = json.dumps({'data': [], 'layout': {}})

    mock_get_papers.return_value = [
        {
            'pmid': '12345',
            'title': 'Publication 12345',
            'url': 'https://pubmed.ncbi.nlm.nih.gov/12345',
            'date': '2020 Jan',
            'citations': 5
        }
    ]

    response = client.get('/api/gene/GENE1')

    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'gene_info' in data
    assert 'boxplot' in data
    assert data['gene_info']['EntrezGeneSymbol'] == 'GENE1'

    # Check that the mocked functions were called
    mock_get_gene_data.assert_called_once_with('GENE1')
    mock_create_boxplot.assert_called_once()


def test_missing_gene_route(client):
    """Negative test for missing gene."""
    response = client.get('/api/gene/NONEXISTENTGENE')

    assert response.status_code == 404 # Not found
    data = json.loads(response.data)
    assert 'error' in data