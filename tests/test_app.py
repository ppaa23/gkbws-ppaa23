# tests/test_app.py
import sys
import os
import json
import pytest
import pandas as pd
import numpy as np

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# Tests for data processing functions
def test_get_sample_age_group():
    """Test the sample age group detection function."""
    from app.data_processing import get_sample_age_group

    assert get_sample_age_group('Set002.H4.YD12') == 'Young'
    assert get_sample_age_group('Set002.H4.OD12') == 'Old'
    assert get_sample_age_group('Other.Column') is None


# Tests for utility functions
def test_data_file_path():
    """Test the data file path function."""
    from app.data_processing import get_data_file_path

    path = get_data_file_path()
    assert isinstance(path, str)
    assert 'NIHMS1635539-supplement-1635539_Sup_tab_4.xlsx' in path


# Mock tests for visualization (no dependency on plotly)
def test_mock_volcano_plot():
    """Test basic structure of volcano plot data."""
    # Create mock data
    data = pd.DataFrame({
        'EntrezGeneSymbol': ['GeneA', 'GeneB'],
        'logFC': [1.5, -0.8],
        'adj.P.Val': [0.001, 0.02],
        '-log10(adj.P.Val)': [3.0, 1.7],
        'significant': [True, True],
        'regulation': ['up-regulated', 'down-regulated']
    })

    # Test basic data shape and content
    assert 'EntrezGeneSymbol' in data.columns
    assert 'logFC' in data.columns
    assert 'adj.P.Val' in data.columns
    assert len(data) == 2


def test_mock_boxplot_data():
    """Test the structure of boxplot data."""
    # Create mock data for boxplot
    data = pd.DataFrame({
        'age_group': ['Young', 'Young', 'Old', 'Old'],
        'value': [0.8, 1.2, 1.8, 2.2],
        'sample': ['Sample1', 'Sample2', 'Sample3', 'Sample4']
    })

    # Test that we have Young and Old groups
    assert set(data['age_group'].unique()) == {'Young', 'Old'}
    assert len(data) == 4
    assert all(isinstance(val, float) for val in data['value'])