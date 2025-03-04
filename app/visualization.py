import plotly.graph_objects as go
import plotly.express as px
import json
import numpy as np


def create_volcano_plot(volcano_data):
    """
    Generate interactive volcano plot from processed data.

    Args:
        volcano_data (pandas.DataFrame): DataFrame containing volcano plot data

    Returns:
        str: JSON representation of the Plotly figure
    """
    # Color mapping for the different regulation categories
    color_map = {
        'up-regulated': 'red',
        'down-regulated': 'blue',
        'not significant': 'gray'
    }

    fig = px.scatter(
        volcano_data,
        x='logFC',
        y='-log10(adj.P.Val)',
        color='regulation',
        color_discrete_map=color_map,
        hover_name='EntrezGeneSymbol',
        hover_data={
            'logFC': True,
            'adj.P.Val': True,
            'regulation': True,
            '-log10(adj.P.Val)': False
        },
        labels={
            'logFC': 'Log2 Fold Change',
            '-log10(adj.P.Val)': '-log10(adjusted P-value)',
            'regulation': 'Regulation'
        },
        title='Volcano Plot of Protein Activity',
        custom_data=['EntrezGeneSymbol']  # Include gene name for click event
    )

    # Update layout for better visualization
    fig.update_layout(
        plot_bgcolor='white',
        margin=dict(l=20, r=20, t=60, b=20),
        legend_title_text='',
        xaxis=dict(
            title='Log2 Fold Change',
            gridcolor='lightgray',
            zeroline=True,
            zerolinecolor='black',
            zerolinewidth=1
        ),
        yaxis=dict(
            title='-log10(adjusted P-value)',
            gridcolor='lightgray'
        )
    )

    # Add a horizontal line at p-value = 0.05 (-log10(0.05) ≈ 1.3)
    fig.add_shape(
        type='line',
        x0=min(volcano_data['logFC']),
        x1=max(volcano_data['logFC']),
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
        y1=max(volcano_data['-log10(adj.P.Val)']),
        line=dict(color='darkgray', width=1, dash='dash')
    )

    fig.add_shape(
        type='line',
        x0=-1,
        x1=-1,
        y0=0,
        y1=max(volcano_data['-log10(adj.P.Val)']),
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

    return json.dumps(fig.to_dict())


def create_boxplot(boxplot_data, gene_name):
    """
    Generate boxplot comparing Young vs Old samples for a specific gene.

    Args:
        boxplot_data (pandas.DataFrame): DataFrame containing boxplot data
        gene_name (str): Name of the gene

    Returns:
        str: JSON representation of the Plotly figure
    """
    # Create figure
    fig = go.Figure()

    # Add boxplots for each age group
    for age_group in ['Young', 'Old']:
        group_data = boxplot_data[boxplot_data['age_group'] == age_group]

        # Add boxplot
        fig.add_trace(go.Box(
            y=group_data['value'],
            name=age_group,
            boxmean=True,  # Show mean
            marker_color='royalblue' if age_group == 'Young' else 'firebrick'
        ))

        # Add individual points
        fig.add_trace(go.Scatter(
            y=group_data['value'],
            x=[age_group] * len(group_data),
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
        margin=dict(l=20, r=20, t=60, b=20)
    )

    return json.dumps(fig.to_dict())