import streamlit as st
import pandas as pd
from utils.helpers import format_currency, format_percentage
from typing import Dict, Any


def render_campaign_type_comparison(campaign_analysis: pd.DataFrame, summary: Dict[str, Any]):
    """
    Affiche la comparaison des performances par type de campagne
    VERSION CORRIGÉE avec nouvelles métriques

    Args:
        campaign_analysis: DataFrame avec l'analyse détaillée
        summary: Dictionnaire avec le résumé par type de campagne
    """
    st.subheader("🎯 Performance par Type de Campagne")

    if campaign_analysis.empty:
        st.warning(
            "📭 Aucune campagne classifiée trouvée. Utilisez la configuration des campagnes pour classifier vos campagnes.")
        return

    # Vue d'ensemble
    _render_campaign_type_overview(summary)

    # Tableau détaillé
    _render_campaign_type_detailed_table(campaign_analysis)


def _render_campaign_type_overview(summary: Dict[str, Any]):
    """Affiche la vue d'ensemble des types de campagne"""

    st.markdown("### 📊 Vue d'Ensemble par Type")

    if not summary:
        st.info("Aucune donnée de résumé disponible")
        return

    # Métriques principales par type
    cols = st.columns(len(summary))

    for i, (campaign_type, data) in enumerate(summary.items()):
        with cols[i]:
            st.markdown(f"#### 🏷️ {campaign_type.title()}")

            # Métriques clés
            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "Budget",
                    format_currency(data['total_cost']),
                    help=f"{data['cost_share']:.1f}% du budget total"
                )
                st.metric(
                    "Campaigns",
                    f"{data['nb_campaigns']:.0f}",
                    help="Nombre de campagnes actives"
                )

            with col2:
                st.metric(
                    "ROAS",
                    f"{data['roas']:.2f}",
                    help="Return on Ad Spend"
                )
                st.metric(
                    "Conv. Rate",
                    format_percentage(data['conversion_rate']),
                    help="Taux de conversion"
                )


def _render_campaign_type_detailed_table(campaign_analysis: pd.DataFrame):
    """Affiche le tableau détaillé des performances par type de campagne avec nouvelles métriques"""

    st.markdown("### 📋 Tableau Détaillé des Performances")

    # Préparer les données pour l'affichage
    display_data = campaign_analysis.copy()

    # NOUVEAU : Colonnes différentes selon le canal
    app_columns = [
        'campaign_type', 'channel_type', 'nb_campaigns', 'cost', 'impressions',
        'clicks', 'installs', 'opens', 'login', 'purchases', 'revenue',
        'ctr', 'conversion_rate', 'open_rate', 'login_rate', 'purchase_rate_dl', 'cpa', 'roas'
    ]

    web_columns = [
        'campaign_type', 'channel_type', 'nb_campaigns', 'cost', 'impressions',
        'clicks', 'add_to_cart', 'purchases', 'revenue',
        'ctr', 'conversion_rate', 'cart_rate', 'cart_to_purchase_rate', 'cpa', 'roas'
    ]

    # Séparer App et Web pour affichage différencié
    app_data = display_data[display_data['channel_type'] == 'app'].copy()
    web_data = display_data[display_data['channel_type'] == 'web'].copy()

    if not app_data.empty:
        st.markdown("#### 📱 Campagnes App")

        # Filtrer les colonnes disponibles pour App
        available_app_columns = [col for col in app_columns if col in app_data.columns]
        app_display = app_data[available_app_columns]

        # Configuration des colonnes pour App
        app_column_config = {
            "campaign_type": st.column_config.TextColumn("Type", width="medium"),
            "channel_type": st.column_config.TextColumn("Canal", width="small"),
            "nb_campaigns": st.column_config.NumberColumn("Nb Camp.", format="%d"),
            "cost": st.column_config.NumberColumn("Coût", format="%.2f €"),
            "impressions": st.column_config.NumberColumn("Impressions", format="%d"),
            "clicks": st.column_config.NumberColumn("Clics", format="%d"),
            "installs": st.column_config.NumberColumn("Installs", format="%d"),
            "opens": st.column_config.NumberColumn("Opens", format="%d"),
            "login": st.column_config.NumberColumn("Logins", format="%d"),
            "purchases": st.column_config.NumberColumn("Achats", format="%d"),
            "revenue": st.column_config.NumberColumn("Revenus", format="%.2f €"),
            "ctr": st.column_config.NumberColumn("CTR", format="%.2f%%"),
            "conversion_rate": st.column_config.NumberColumn("Taux Conv.", format="%.2f%%", help="Installs / Clics"),
            "open_rate": st.column_config.NumberColumn("Taux Open", format="%.2f%%", help="Opens / Installs"),
            "login_rate": st.column_config.NumberColumn("Taux Login", format="%.2f%%", help="Logins / Installs"),
            "purchase_rate_dl": st.column_config.NumberColumn("Taux Achat DL", format="%.2f%%",
                                                              help="Achats / Installs"),
            "cpa": st.column_config.NumberColumn("CPA", format="%.2f €"),
            "roas": st.column_config.NumberColumn("ROAS", format="%.2f")
        }

        st.dataframe(
            app_display,
            column_config=app_column_config,
            use_container_width=True,
            hide_index=True
        )

    if not web_data.empty:
        st.markdown("#### 🌐 Campagnes Web")

        # Filtrer les colonnes disponibles pour Web
        available_web_columns = [col for col in web_columns if col in web_data.columns]
        web_display = web_data[available_web_columns]

        # Configuration des colonnes pour Web
        web_column_config = {
            "campaign_type": st.column_config.TextColumn("Type", width="medium"),
            "channel_type": st.column_config.TextColumn("Canal", width="small"),
            "nb_campaigns": st.column_config.NumberColumn("Nb Camp.", format="%d"),
            "cost": st.column_config.NumberColumn("Coût", format="%.2f €"),
            "impressions": st.column_config.NumberColumn("Impressions", format="%d"),
            "clicks": st.column_config.NumberColumn("Clics", format="%d"),
            "add_to_cart": st.column_config.NumberColumn("Ajouts Panier", format="%d"),
            "purchases": st.column_config.NumberColumn("Achats", format="%d"),
            "revenue": st.column_config.NumberColumn("Revenus", format="%.2f €"),
            "ctr": st.column_config.NumberColumn("CTR", format="%.2f%%"),
            "conversion_rate": st.column_config.NumberColumn("Taux Achat", format="%.2f%%", help="Achats / Clics"),
            "cart_rate": st.column_config.NumberColumn("Taux Panier", format="%.2f%%", help="Paniers / Clics"),
            "cart_to_purchase_rate": st.column_config.NumberColumn("Finalisation", format="%.2f%%",
                                                                   help="Achats / Paniers"),
            "cpa": st.column_config.NumberColumn("CPA", format="%.2f €"),
            "roas": st.column_config.NumberColumn("ROAS", format="%.2f")
        }

        st.dataframe(
            web_display,
            column_config=web_column_config,
            use_container_width=True,
            hide_index=True
        )

    # Bouton d'export global
    if st.button("📥 Exporter le tableau", key="export_campaign_types"):
        csv = display_data.to_csv(index=False)
        st.download_button(
            label="Télécharger CSV",
            data=csv,
            file_name="campaign_types_performance.csv",
            mime="text/csv"
        )


def render_campaign_type_insights(insights: list):
    """
    Fonction vide pour compatibilité - ne fait rien
    Conservée pour éviter les erreurs d'import dans app.py
    """
    pass


def render_campaign_type_recommendations(summary: Dict[str, Any]):
    """
    Fonction vide pour compatibilité - ne fait rien
    Conservée pour éviter les erreurs d'import dans app.py
    """
    pass