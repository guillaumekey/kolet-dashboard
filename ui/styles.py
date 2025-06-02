import streamlit as st


def apply_custom_styles():
    """Applique les styles CSS personnalisés à l'application"""

    st.markdown("""
    <style>
    /* Correction de l'espacement principal et suppression de la barre blanche */
    .main .block-container {
        padding-top: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
        max-width: 100%;
    }

    /* Correction de l'espacement entre sidebar et contenu principal */
    .css-1d391kg {
        padding-top: 1rem;
    }

    /* Suppression de l'espace blanc en haut */
    .css-18e3th9 {
        padding-top: 0rem;
    }

    /* Cartes de métriques */
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    /* Section funnel */
    .funnel-section {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 4px solid #3498db;
    }

    /* Container KPI principal */
    .kpi-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 1rem;
        color: white;
        margin: 2rem 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }

    /* Sections de comparaison */
    .comparison-section {
        background-color: #fafafa;
        padding: 1.5rem;
        border-radius: 0.8rem;
        margin: 1rem 0;
        border: 1px solid #e0e0e0;
    }

    /* Headers de section */
    .section-header {
        background: linear-gradient(90deg, #3498db, #2ecc71);
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1.5rem 0 1rem 0;
        font-weight: bold;
        text-align: center;
    }

    /* Debug panel */
    .debug-panel {
        background-color: #f8f9fa;
        border: 1px dashed #dee2e6;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }

    /* Alertes personnalisées */
    .alert-success {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }

    .alert-warning {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }

    .alert-info {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }

    /* Amélioration des métriques Streamlit */
    [data-testid="metric-container"] {
        background-color: white;
        border: 1px solid #e0e0e0;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    /* Suppression complète de l'espace blanc entre sidebar et contenu */
    [data-testid="stSidebar"] > div:first-child {
        width: 300px;
    }

    [data-testid="stSidebar"][aria-expanded="true"] > div:first-child {
        width: 300px;
        margin-left: 0px;
    }

    /* Ajustement du contenu principal pour éliminer la barre blanche */
    .css-1lcbmhc.e1fqkh3o0 {
        margin-left: 0px;
        padding-left: 1rem;
    }

    /* Hide Streamlit menu et footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
    }
    ::-webkit-scrollbar-thumb {
        background: #888;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #555;
    }
    </style>
    """, unsafe_allow_html=True)