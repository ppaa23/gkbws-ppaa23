# app/visualization.py
import plotly.graph_objects as go
import json
import numpy as np
import pandas as pd


class NumpyEncoder(json.JSONEncoder):
    """JSON encoder that handles numpy types."""

    def default(self, obj):
        if isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif pd.isna(obj):
            return None
        return super().default(obj)


def create_volcano_plot(volcano_data):
    """Generate interactive volcano plot from processed data."""
    # Ensure we have data to plot
    if volcano_data is None or len(volcano_data) == 0:
        return json.dumps({"error": "No data available for volcano plot"})

    # Filter out NaN values in key columns
    clean_data = volcano_data.dropna(subset=['logFC', '-log10(adj.P.Val)', 'regulation', 'EntrezGeneSymbol'])

    # Print some diagnostic information
    print(f"Total data points: {len(clean_data)}")
    print(f"Regulation categories: {clean_data['regulation'].unique().tolist()}")
    print(f"Up-regulated: {len(clean_data[clean_data['regulation'] == 'up-regulated'])}")
    print(f"Down-regulated: {len(clean_data[clean_data['regulation'] == 'down-regulated'])}")
    print(f"Not significant: {len(clean_data[clean_data['regulation'] == 'not significant'])}")

    # Separate data by regulation category for different colors
    not_sig_data = clean_data[clean_data['regulation'] == 'not significant']
    up_reg_data = clean_data[clean_data['regulation'] == 'up-regulated']
    down_reg_data = clean_data[clean_data['regulation'] == 'down-regulated']

    # Create the plot with separate traces for each regulation type
    fig = go.Figure()

    # Add not significant points - IMPORTANT: Each gene name must be wrapped in an array to match main.js
    if len(not_sig_data) > 0:
        fig.add_trace(go.Scatter(
            x=not_sig_data['logFC'].tolist(),
            y=not_sig_data['-log10(adj.P.Val)'].tolist(),
            mode='markers',
            name='not significant',
            marker=dict(
                color='gray',
                size=6,
                opacity=0.6
            ),
            hovertemplate=
            '<b>%{customdata[0]}</b><br>' +
            'Log2 FC: %{x:.3f}<br>' +
            'p-value: %{text}<br>' +
            '<extra></extra>',
            text=not_sig_data['adj.P.Val'].apply(lambda p: f'{p:.2e}').tolist(),
            # Wrap each gene name in an array to match main.js expectation
            customdata=[[gene] for gene in not_sig_data['EntrezGeneSymbol'].tolist()]
        ))

    # Add up-regulated points with customdata as arrays
    if len(up_reg_data) > 0:
        fig.add_trace(go.Scatter(
            x=up_reg_data['logFC'].tolist(),
            y=up_reg_data['-log10(adj.P.Val)'].tolist(),
            mode='markers',
            name='up-regulated',
            marker=dict(
                color='red',
                size=8,
                opacity=0.8
            ),
            hovertemplate=
            '<b>%{customdata[0]}</b><br>' +
            'Log2 FC: %{x:.3f}<br>' +
            'p-value: %{text}<br>' +
            '<extra></extra>',
            text=up_reg_data['adj.P.Val'].apply(lambda p: f'{p:.2e}').tolist(),
            # Wrap each gene name in an array to match main.js expectation
            customdata=[[gene] for gene in up_reg_data['EntrezGeneSymbol'].tolist()]
        ))

    # Add down-regulated points with customdata as arrays
    if len(down_reg_data) > 0:
        fig.add_trace(go.Scatter(
            x=down_reg_data['logFC'].tolist(),
            y=down_reg_data['-log10(adj.P.Val)'].tolist(),
            mode='markers',
            name='down-regulated',
            marker=dict(
                color='blue',
                size=8,
                opacity=0.8
            ),
            hovertemplate=
            '<b>%{customdata[0]}</b><br>' +
            'Log2 FC: %{x:.3f}<br>' +
            'p-value: %{text}<br>' +
            '<extra></extra>',
            text=down_reg_data['adj.P.Val'].apply(lambda p: f'{p:.2e}').tolist(),
            # Wrap each gene name in an array to match main.js expectation
            customdata=[[gene] for gene in down_reg_data['EntrezGeneSymbol'].tolist()]
        ))

    # Calculate a symmetrical x-axis range to center the plot
    x_max = max(abs(float(clean_data['logFC'].min())), abs(float(clean_data['logFC'].max())))
    x_max = round(x_max * 1.1, 1)  # Add 10% padding and round to one decimal
    if x_max == 0 or pd.isna(x_max):  # Default if no range can be calculated
        x_max = 5
    x_range = [-x_max, x_max]

    # Max y value for vertical lines
    y_max = float(clean_data['-log10(adj.P.Val)'].max())

    # Update layout
    fig.update_layout(
        title='Volcano Plot of Protein Activity',
        xaxis=dict(
            title='Log2 Fold Change',
            gridcolor='lightgray',
            zeroline=True,
            zerolinecolor='black',
            zerolinewidth=1,
            range=x_range
        ),
        yaxis=dict(
            title='-log10(adjusted P-value)',
            gridcolor='lightgray'
        ),
        plot_bgcolor='white',
        hovermode='closest',
        margin=dict(l=50, r=50, b=80, t=100, pad=4),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        )
    )

    # Add a horizontal line at p-value = 0.05 (-log10(0.05) ≈ 1.3)
    fig.add_shape(
        type='line',
        x0=-x_max,
        x1=x_max,
        y0=-np.log10(0.05),
        y1=-np.log10(0.05),
        line=dict(color='darkgray', width=1, dash='dash')
    )

    # Add vertical lines at log2(FC) = 1 and log2(FC) = -1
    fig.add_shape(
        type='line',
        x0=1,
        x1=1,
        y0=0,
        y1=y_max,
        line=dict(color='darkgray', width=1, dash='dash')
    )

    fig.add_shape(
        type='line',
        x0=-1,
        x1=-1,
        y0=0,
        y1=y_max,
        line=dict(color='darkgray', width=1, dash='dash')
    )

    # Add annotations for the significance thresholds
    fig.add_annotation(
        x=0,
        y=-np.log10(0.05),
        text='p = 0.05',
        showarrow=False,
        yshift=10,
        font=dict(size=10)
    )

    # Use custom encoder to handle numpy values
    return json.dumps(fig.to_dict(), cls=NumpyEncoder)


def create_boxplot(boxplot_data, gene_name):
    """Generate boxplot comparing Young vs Old samples for a specific gene."""
    # Check if we have data
    if boxplot_data is None or len(boxplot_data) == 0:
        return json.dumps({"error": "No data available for boxplot"})

    # Create figure
    fig = go.Figure()

    # Add boxplots for each age group
    for age_group in ['Young', 'Old']:
        group_data = boxplot_data[boxplot_data['age_group'] == age_group]

        if len(group_data) > 0:
            # Convert values to numeric and filter out NaN
            values = pd.to_numeric(group_data['value'], errors='coerce').dropna().tolist()

            if values:  # Only add trace if we have values
                # Add boxplot
                fig.add_trace(go.Box(
                    y=values,
                    name=age_group,
                    boxmean=True,  # Show mean
                    marker_color='royalblue' if age_group == 'Young' else 'firebrick'
                ))

                # Add individual points
                fig.add_trace(go.Scatter(
                    y=values,
                    x=[age_group] * len(values),
                    mode='markers',
                    name=f'{age_group} samples',
                    marker=dict(
                        color='navy' if age_group == 'Young' else 'darkred',
                        size=8,
                        opacity=0.6
                    ),
                    showlegend=False
                ))

    # Update layout
    fig.update_layout(
        title=f'Protein levels of {gene_name} in Young vs Old samples',
        yaxis_title='Protein level',
        xaxis_title='Age group',
        boxmode='group',
        plot_bgcolor='white',
        margin=dict(l=50, r=50, b=80, t=100, pad=4)
    )

    # Use custom encoder to handle numpy values
    return json.dumps(fig.to_dict(), cls=NumpyEncoder)