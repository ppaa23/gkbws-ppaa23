import os
import pandas as pd
import numpy as np
import warnings
from openpyxl import load_workbook


def get_data_file_path():
    """Returns the path to the data file"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, 'app', 'static', 'data', 'NIHMS1635539-supplement-1635539_Sup_tab_4.xlsx')


def load_volcano_data():
    """Load data for volcano plot from S4B limma results sheet."""
    file_path = get_data_file_path()

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Excel file not found at {file_path}")

    # First, check the Excel structure to understand the header row
    wb = load_workbook(filename=file_path, read_only=True)
    sheet = wb['S4B limma results']

    # Find the actual header row - iterate through the first 10 rows to find a row with column names
    header_row = None
    for i in range(1, 10):  # Check first 10 rows
        if 'EntrezGeneSymbol' in [str(cell.value).strip() for cell in list(sheet.rows)[i - 1]]:
            header_row = i - 1
            break

    wb.close()

    # If we found a header row, use it
    if header_row is not None:
        df = pd.read_excel(file_path, sheet_name='S4B limma results', header=header_row)
    else:
        # Fallback to original approach, but with explicit warning
        warnings.warn("Could not find 'EntrezGeneSymbol' in the first 10 rows. Falling back to header=2.")
        df = pd.read_excel(file_path, sheet_name='S4B limma results', header=2)

    # Check if we have the expected columns
    if 'EntrezGeneSymbol' not in df.columns:
        raise ValueError(f"Expected column 'EntrezGeneSymbol' not found. Available columns: {df.columns.tolist()}")

    if 'adj.P.Val' not in df.columns and 'P.Value' in df.columns:
        # Rename column if needed
        df.rename(columns={'P.Value': 'adj.P.Val'}, inplace=True)

    if 'logFC' not in df.columns:
        # Try to find a column that might contain log fold change values
        fc_col = next((col for col in df.columns if 'FC' in col or 'fold' in col.lower()), None)
        if fc_col:
            df.rename(columns={fc_col: 'logFC'}, inplace=True)
        else:
            raise ValueError(f"No column related to fold change found. Available columns: {df.columns.tolist()}")

    # Calculate -log10(p-value) for the y-axis of the volcano plot
    # Handle possible zeros in p-values (replace with minimum non-zero value)
    min_pval = df['adj.P.Val'][df['adj.P.Val'] > 0].min() / 10 if any(df['adj.P.Val'] > 0) else 1e-10
    df['adj.P.Val'] = df['adj.P.Val'].replace(0, min_pval)
    df['-log10(adj.P.Val)'] = -np.log10(df['adj.P.Val'])

    # Determine significance for coloring (with a safer approach)
    df['significant'] = df['adj.P.Val'] < 0.05

    # Create a new regulation column
    df['regulation'] = 'not significant'
    df.loc[(df['significant']) & (df['logFC'] > 0), 'regulation'] = 'up-regulated'
    df.loc[(df['significant']) & (df['logFC'] < 0), 'regulation'] = 'down-regulated'

    # Drop rows with missing values in key columns
    df = df.dropna(subset=['EntrezGeneSymbol', 'logFC', 'adj.P.Val'])

    # Ensure the data types are correct
    df['logFC'] = pd.to_numeric(df['logFC'], errors='coerce')
    df['adj.P.Val'] = pd.to_numeric(df['adj.P.Val'], errors='coerce')
    df['-log10(adj.P.Val)'] = pd.to_numeric(df['-log10(adj.P.Val)'], errors='coerce')

    # Drop rows with NaN after conversion
    df = df.dropna(subset=['logFC', 'adj.P.Val', '-log10(adj.P.Val)'])

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

    try:
        # Find the correct header row
        wb = load_workbook(filename=file_path, read_only=True)
        sheet = wb['S4A values']

        # Find the header row
        header_row = None
        for i in range(1, 10):  # Check first 10 rows
            if 'EntrezGeneSymbol' in [str(cell.value).strip() for cell in list(sheet.rows)[i - 1]]:
                header_row = i - 1
                break

        wb.close()

        # Read the Excel sheet with the correct header
        if header_row is not None:
            df = pd.read_excel(file_path, sheet_name='S4A values', header=header_row)
        else:
            warnings.warn("Could not find 'EntrezGeneSymbol' in the first 10 rows. Falling back to header=2.")
            df = pd.read_excel(file_path, sheet_name='S4A values', header=2)

        # Filter by the gene name
        gene_data = df[df['EntrezGeneSymbol'] == gene_name]

        if gene_data.empty:
            print(f"No data found for gene {gene_name} in S4A values sheet")
            return None

        # Get all donor columns (containing OD or YD)
        donor_columns = [col for col in df.columns if ('OD' in str(col).upper() or 'YD' in str(col).upper())]

        if not donor_columns:
            print(f"No donor columns found (containing 'OD' or 'YD')")
            return None

        print(f"Found {len(donor_columns)} donor columns")

        # Create boxplot data
        boxplot_data = []

        for col in donor_columns:
            age_group = get_sample_age_group(col)
            if age_group and not gene_data[col].isnull().all():
                value = gene_data[col].values[0]
                # Convert numpy types to Python types for JSON serialization
                boxplot_data.append({
                    'age_group': age_group,
                    'value': float(value) if not pd.isna(value) else 0.0,
                    'sample': str(col)
                })

        print(f"Created boxplot data with {len(boxplot_data)} points")
        return pd.DataFrame(boxplot_data)

    except Exception as e:
        print(f"Error in load_boxplot_data: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def get_gene_data(gene_name):
    """Get combined gene data including both volcano plot info and boxplot data."""
    volcano_data = load_volcano_data()

    # Ensure the gene name exists in the volcano data
    gene_volcano_data = volcano_data[volcano_data['EntrezGeneSymbol'] == gene_name]

    if gene_volcano_data.empty:
        print(f"Gene {gene_name} not found in volcano data")
        return None

    # Get boxplot data
    boxplot_data = load_boxplot_data(gene_name)

    if boxplot_data is None or boxplot_data.empty:
        print(f"No boxplot data available for gene {gene_name}")
        return None

    # Convert numpy values to native Python types for JSON serialization
    gene_info = {}
    for key, value in gene_volcano_data.iloc[0].to_dict().items():
        if isinstance(value, (np.integer, np.floating)):
            gene_info[key] = float(value)
        elif isinstance(value, np.bool_):
            gene_info[key] = bool(value)
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