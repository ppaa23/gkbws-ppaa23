import os
import pandas as pd
import numpy as np
from flask import current_app


def get_data_file_path():
    """
    Returns the path to the data file.
    """
    # Use a more reliable way to get the path that doesn't depend on current_app
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, 'app', 'static', 'data', 'NIHMS1635539-supplement-1635539_Sup_tab_4.xlsx')


def load_volcano_data():
    """
    Load data for volcano plot from S4B limma results sheet.

    Returns:
        pandas.DataFrame: Data containing gene symbols, logFC, and p-values
    """
    file_path = get_data_file_path()
    df = pd.read_excel(file_path, sheet_name='S4B limma results')

    # Calculate -log10(p-value) for the y-axis of the volcano plot
    df['-log10(adj.P.Val)'] = -np.log10(df['adj.P.Val'])

    # Determine significance for coloring
    df['significant'] = df['adj.P.Val'] < 0.05
    df['regulation'] = 'not significant'
    df.loc[(df['significant']) & (df['logFC'] > 0), 'regulation'] = 'up-regulated'
    df.loc[(df['significant']) & (df['logFC'] < 0), 'regulation'] = 'down-regulated'

    return df


def get_sample_age_group(column_name):
    """
    Determine if a sample is from young or old donor based on column name.

    Args:
        column_name (str): Name of the column

    Returns:
        str: 'Young' if YD in column name, 'Old' if OD in column name, None otherwise
    """
    if 'YD' in column_name:
        return 'Young'
    elif 'OD' in column_name:
        return 'Old'
    return None


def load_boxplot_data(gene_name):
    """
    Load data for boxplot of a specific gene from S4A values sheet.

    Args:
        gene_name (str): Name of the gene

    Returns:
        pandas.DataFrame: Data for boxplot with age group and values
    """
    file_path = get_data_file_path()
    df = pd.read_excel(file_path, sheet_name='S4A values')

    # Filter by the gene name
    gene_data = df[df['EntrezGeneSymbol'] == gene_name]

    if gene_data.empty:
        return None

    # Get all donor columns (starting with 'Set')
    donor_columns = [col for col in gene_data.columns if col.startswith('Set')]

    # Create a new dataframe for the boxplot
    boxplot_data = []

    for col in donor_columns:
        age_group = get_sample_age_group(col)
        if age_group:
            value = gene_data[col].values[0]  # Get the value for this gene
            boxplot_data.append({
                'age_group': age_group,
                'value': value,
                'sample': col
            })

    return pd.DataFrame(boxplot_data)


def get_gene_data(gene_name):
    """
    Get combined gene data including both volcano plot info and boxplot data.

    Args:
        gene_name (str): Name of the gene

    Returns:
        dict: Dictionary containing gene information and boxplot data
    """
    volcano_data = load_volcano_data()
    gene_volcano_data = volcano_data[volcano_data['EntrezGeneSymbol'] == gene_name]

    if gene_volcano_data.empty:
        return None

    boxplot_data = load_boxplot_data(gene_name)

    if boxplot_data is None:
        return None

    # Extract gene information from the volcano data
    gene_info = gene_volcano_data.iloc[0].to_dict()

    # Convert the boxplot data to a format suitable for JSON
    boxplot_values = boxplot_data.to_dict(orient='records')

    # Combine all data
    result = {
        'gene_info': gene_info,
        'boxplot_data': boxplot_values
    }

    return result