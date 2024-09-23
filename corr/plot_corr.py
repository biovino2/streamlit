"""Plot correlation scatterplots between ATAC and RNA data.

Ben Iovino  08/08/24    CZ-Biohub
"""

import matplotlib.pyplot as plt
import pickle as pkl
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import scanpy as sc
from scipy.stats import pearsonr
import streamlit as st
import sys
from preprocess import define_color_dict


def st_setup(gene_names: 'list[str]'):
    """Initializes streamlit session.

    Args:
        gene_names: The list of gene names.
    """

    st.set_page_config(layout="wide")
    st.sidebar.markdown('# Settings')
    st.title('ATAC and RNA Correlation')
    st.write('For each time point, we plot plot time-resolved scatter plots of ATAC (x-axis) and RNA expression (y-axis) ' \
             'for any gene. Each point represents a metacell (SEACell), colored by cell type. The correlation between ' \
              'chromatin accessbility and gene expression is also calculated for each time point.')
    
    # Remove extra space at top of the page
    st.markdown(
    """
    <style>
        /* Remove padding from main block */
        .block-container {
            padding-top: 2rem;
        }
    </style>
    """,
    unsafe_allow_html=True
    )

    # Initialize drop down boxes
    if "selectboxes" not in st.session_state:
        st.session_state.selectboxes = [0]

    # Set up buttons for adding/removing genes
    with st.sidebar:
        add, reset = st.columns([1, 1])
        with add:
            if st.button('Add Gene'):
                st.session_state.selectboxes.append(len(st.session_state.selectboxes))
        with reset:
            if st.button('Reset'):
                st.session_state.selectboxes = [0]

    # Create selectboxes
    selected_genes = []
    default = gene_names.index('slc4a1a')
    for key in st.session_state.selectboxes:
        st.sidebar.selectbox(
            'Select a gene to plot',
            gene_names,
            key=key,
            index=default
        )
        selected_genes.append(st.session_state[key])

    return selected_genes


def save_config() -> dict:
    """Returns a config to save plotly figure as SVG.

    Returns:
        config (dict): The configuration.
    """

    config = {
    'toImageButtonOptions': {
        'format': 'svg', # one of png, svg, jpeg, webp
        'filename': 'correlation_scatterplot',
        'height': None,
        'width': None,
        'scale': 1 # Multiply title/legend/axis/canvas sizes by this factor
    },
    'displayModeBar': True
    }

    return config


def plot_genes(gene: str, gene_dict: 'dict[str:sc.AnnData]') -> plt.Figure:
    """Returns one figure containing scatter plots for each gene.

    Args:
        genes (str): Gene to plot
        dict_meta (dict[str:sc.AnnData]): The dictionary of adata objects.

    Returns:
        plt.Figure: The figure object.
    """

    timepoints = {'TDR126': '10 hours post fertilization',
                    'TDR127': '12 hours post fertilization',
                    'TDR128': '14 hours post fertilization',
                    'TDR118': '16 hours post fertilization',
                    'TDR125': '19 hours post fertilization',
                    'TDR124': '24 hours post fertilization'}
    fig = make_subplots(rows=2, cols=3, subplot_titles=list(timepoints.values()))

    # Loop over all timepoints
    corr_scores = []
    rna_max, atac_max = 0, 0
    for index, sample_id in enumerate(list(timepoints.keys())):

        # Get data for timepoint
        expr_rna = gene_dict[gene][sample_id][0]
        expr_atac = gene_dict[gene][sample_id][1]
        colors = gene_dict[gene][sample_id][2]

        # Calculate correlation
        if np.all(expr_rna == expr_rna[0]) or np.all(expr_atac== expr_atac[0]):
            corr_scores.append(np.nan)
        else:
            correlation, _ = pearsonr(expr_rna, expr_atac)
            corr_scores.append(correlation)

        # Map colors to cell types
        color_dict = define_color_dict()
        inv_color_dict = {v: k for k, v in color_dict.items()}
        type_colors = [inv_color_dict[color] for color in colors]

        # Plot scatter plot with plotly
        scatter = go.Scatter(
                        x=expr_atac,
                        y=expr_rna,
                        mode='markers',
                        marker=dict(color=colors),
                        hoverinfo='text',
                        text=type_colors,
                    )
        
        # Update margins of the plot
        if np.max(expr_rna) > rna_max:
            rna_max = np.max(expr_rna)
        if np.max(expr_atac) > atac_max:
            atac_max = np.max(expr_atac)

        # Add go.Scatter object to figure
        fig.add_trace(scatter, row=(index//3)+1, col=(index%3)+1)

    # Update layout
    fig.update_layout(
        margin=dict(l=10, r=10, t=70, b=0),
        showlegend=False,
        xaxis=dict(title_standoff=5)
    )

    # Update titles
    for i, annotation in enumerate(fig.layout.annotations):
        annotation.text = f"{list(timepoints.values())[i]}<br>Correlation: {corr_scores[i]:.2f}"
        annotation.font.size = 14

    # Update axes labels and titles
    for i in range (0, len(corr_scores)):
        fig.update_xaxes(title='ATAC', row=i//3+1, col=i%3+1, title_font=dict(size=10), range=[0, atac_max], title_standoff=4)
        fig.update_yaxes(title='RNA', row=i//3+1, col=i%3+1, title_font=dict(size=10), range=[0, rna_max], title_standoff=5)

    return fig


def main():
    """
    """

    # Get path to data from command line
    arg: 'list[str]' = sys.argv[0].split('/')[:-1]
    path = '/'.join(arg) + '/data'

    # Load data and set up streamlit
    gene_dict = pkl.load(open(f"{path}/gene_dict.pkl", "rb"))
    gene_names = list(gene_dict.keys())
    selected_genes = st_setup(gene_names)

    # Plot each figure
    for gene in selected_genes:
        fig = plot_genes(gene, gene_dict)
        st.markdown(f'### {gene}')
        st.plotly_chart(fig, config=save_config())


if __name__ == "__main__":
    main()
