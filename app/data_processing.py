# app/data_processing.py - simplified version
import os
import pandas as pd
import numpy as np


def get_data_file_path():
    """Returns the path to the data file"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, 'app', 'static', 'data', 'NIHMS1635539-supplement-1635539_Sup_tab_4.xlsx')


def load_volcano_data():
    """Load data for volcano plot from S4B limma results sheet."""
    file_path = get_data_file_path()

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Excel file not found at {file_path}")

    # Read with header in the third row (index 2)
    df = pd.read_excel(file_path, sheet_name='S4B limma results', header=2)

    # Calculate -log10(p-value) for the y-axis of the volcano plot
    df['-log10(adj.P.Val)'] = -np.log10(df['adj.P.Val'])

    # Determine significance for coloring
    df['significant'] = df['adj.P.Val'] < 0.05
    df['regulation'] = 'not significant'
    df.loc[(df['significant']) & (df['logFC'] > 0), 'regulation'] = 'up-regulated'
    df.loc[(df['significant']) & (df['logFC'] < 0), 'regulation'] = 'down-regulated'

    return df


def get_sample_age_group(column_name):
    """Determine if a sample is from young or old donor based on column name."""
    col_str = str(column_name).upper()
    if 'YD' in col_str:
        return 'Young'
    elif 'OD' in col_str:
        return 'Old'
    return None


def load_boxplot_data(gene_name):
    """Load data for boxplot of a specific gene from S4A values sheet."""
    file_path = get_data_file_path()

    # Read with header in the third row (index 2)
    df = pd.read_excel(file_path, sheet_name='S4A values', header=2)

    # Filter by the gene name
    gene_data = df[df['EntrezGeneSymbol'] == gene_name]

    if gene_data.empty:
        return None

    # Get all donor columns (containing OD or YD)
    donor_columns = [col for col in df.columns if 'OD' in str(col) or 'YD' in str(col)]

    if not donor_columns:
        print("No donor columns found with OD/YD patterns")
        return None

    # Create boxplot data
    boxplot_data = []

    for col in donor_columns:
        age_group = get_sample_age_group(col)
        if age_group:
            value = gene_data[col].values[0]
            boxplot_data.append({
                'age_group': age_group,
                'value': float(value),  # Convert to Python float for JSON
                'sample': str(col)  # Convert to string for JSON
            })

    return pd.DataFrame(boxplot_data)


def get_gene_data(gene_name):
    """Get combined gene data including both volcano plot info and boxplot data."""
    volcano_data = load_volcano_data()
    gene_volcano_data = volcano_data[volcano_data['EntrezGeneSymbol'] == gene_name]

    if gene_volcano_data.empty:
        return None

    boxplot_data = load_boxplot_data(gene_name)

    if boxplot_data is None:
        return None

    # Convert numpy values to native Python types for JSON serialization
    gene_info = {}
    for key, value in gene_volcano_data.iloc[0].to_dict().items():
        if isinstance(value, (np.integer, np.floating)):
            gene_info[key] = float(value)
        else:
            gene_info[key] = value

    # Convert the boxplot data to a format suitable for JSON
    boxplot_values = boxplot_data.to_dict(orient='records')

    # Combine all data
    result = {
        'gene_info': gene_info,
        'boxplot_data': boxplot_values
    }

    return result