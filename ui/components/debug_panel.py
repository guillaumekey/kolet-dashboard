import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Tuple


def render_debug_panel(data: pd.DataFrame, date_range: Tuple[datetime, datetime]):
    """
    Affiche le panel de debug avec les informations détaillées des données

    Args:
        data: DataFrame avec les données consolidées
        date_range: Tuple avec la période sélectionnée
    """

    # Panel de debug - FERMÉ par défaut
    with st.expander("🔍 Debug - Données chargées", expanded=False):
        st.write("**Répartition par source:**")
        source_counts = data['source'].value_counts()
        for source, count in source_counts.items():
            st.write(f"• {source}: {count:,} enregistrements")

        st.write("**Répartition par plateforme:**")
        platform_counts = data['platform'].value_counts()
        for platform, count in platform_counts.items():
            st.write(f"• {platform}: {count:,} enregistrements")

        st.write("**Répartition par campagne (Branch.io):**")
        branch_campaigns = data[data['source'] == 'Branch.io']['campaign_name'].value_counts()
        for campaign, count in branch_campaigns.items():
            st.write(f"• {campaign}: {count:,} enregistrements")

        st.write(f"• **Période sélectionnée**: {date_range[0]} à {date_range[1]}")
        st.write(f"• **Jours inclus**: {(date_range[1] - date_range[0]).days + 1}")

        st.write("**Colonnes disponibles dans les données:**")
        available_columns = list(data.columns)
        st.write(f"• Colonnes: {', '.join(available_columns)}")


def _render_overview_tab(data: pd.DataFrame, date_range: Tuple[datetime, datetime]):
    """Onglet vue d'ensemble"""

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**📊 Informations générales**")
        st.write(f"• **Total enregistrements**: {len(data):,}")
        st.write(f"• **Période sélectionnée**: {date_range[0]} à {date_range[1]}")
        st.write(f"• **Jours inclus**: {(date_range[1] - date_range[0]).days + 1}")

        # Vérification période Branch.io
        branch_start = datetime(2025, 5, 16).date()
        branch_end = datetime(2025, 5, 30).date()

        if date_range[0] != branch_start or date_range[1] != branch_end:
            st.warning(f"⚠️ Période différente de Branch.io original ({branch_start} à {branch_end})")
            st.info("💡 Pour correspondre aux données Branch.io, utilisez: 2025-05-16 à 2025-05-30")

    with col2:
        st.markdown("**🗂️ Colonnes disponibles**")
        available_columns = list(data.columns)
        st.write(f"• **Nombre de colonnes**: {len(available_columns)}")

        # Colonnes par catégorie
        core_columns = [col for col in available_columns if col in ['date', 'campaign_name', 'source', 'platform']]
        metric_columns = [col for col in available_columns if
                          col in ['cost', 'impressions', 'clicks', 'installs', 'purchases', 'revenue', 'opens',
                                  'login']]
        other_columns = [col for col in available_columns if col not in core_columns + metric_columns]

        with st.expander("Voir détail colonnes"):
            st.write(f"**Colonnes core**: {', '.join(core_columns)}")
            st.write(f"**Colonnes métriques**: {', '.join(metric_columns)}")
            if other_columns:
                st.write(f"**Autres**: {', '.join(other_columns)}")


def _render_sources_tab(data: pd.DataFrame):
    """Onglet répartition par sources"""

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**📊 Répartition par source**")
        source_counts = data['source'].value_counts()
        for source, count in source_counts.items():
            percentage = (count / len(data)) * 100
            st.write(f"• **{source}**: {count:,} enregistrements ({percentage:.1f}%)")

    with col2:
        st.markdown("**🔧 Répartition par plateforme**")
        platform_counts = data['platform'].value_counts()
        for platform, count in platform_counts.items():
            percentage = (count / len(data)) * 100
            st.write(f"• **{platform}**: {count:,} enregistrements ({percentage:.1f}%)")

    # Détail Branch.io
    st.markdown("---")
    st.markdown("**🌿 Détail Branch.io**")

    branch_data = data[data['source'] == 'Branch.io']
    if not branch_data.empty:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Par campagne:**")
            branch_campaigns = branch_data['campaign_name'].value_counts().head(10)
            for campaign, count in branch_campaigns.items():
                st.write(f"• {campaign}: {count:,} enregistrements")

        with col2:
            st.markdown("**Par plateforme:**")
            branch_platforms = branch_data.groupby('platform')['installs'].sum().sort_values(ascending=False)
            for platform, installs in branch_platforms.items():
                st.write(f"• {platform}: {installs:,} installs")
    else:
        st.info("Aucune donnée Branch.io trouvée")


def _render_data_quality_tab(data: pd.DataFrame):
    """Onglet qualité des données"""

    # Analyse de complétude
    st.markdown("**📋 Complétude des données**")

    completeness_data = []
    important_columns = ['date', 'campaign_name', 'source', 'platform', 'cost', 'installs', 'clicks', 'impressions']

    for col in important_columns:
        if col in data.columns:
            non_null_count = data[col].notna().sum()
            completeness = (non_null_count / len(data)) * 100
            completeness_data.append({
                'Colonne': col,
                'Valeurs non-nulles': f"{non_null_count:,}",
                'Complétude': f"{completeness:.1f}%",
                'Status': "✅" if completeness > 95 else "⚠️" if completeness > 80 else "❌"
            })

    completeness_df = pd.DataFrame(completeness_data)
    st.dataframe(completeness_df, use_container_width=True)

    # Détection d'anomalies
    st.markdown("---")
    st.markdown("**🔍 Détection d'anomalies**")

    anomalies = []

    # Vérifier les valeurs négatives
    numeric_columns = ['cost', 'impressions', 'clicks', 'installs', 'purchases']
    for col in numeric_columns:
        if col in data.columns:
            negative_count = (data[col] < 0).sum()
            if negative_count > 0:
                anomalies.append(f"❌ {negative_count} valeurs négatives dans {col}")

    # Vérifier les dates invalides
    if 'date' in data.columns:
        invalid_dates = data['date'].isna().sum()
        if invalid_dates > 0:
            anomalies.append(f"⚠️ {invalid_dates} dates invalides")

    # Vérifier les campagnes sans nom
    if 'campaign_name' in data.columns:
        empty_campaigns = data['campaign_name'].isna().sum()
        if empty_campaigns > 0:
            anomalies.append(f"⚠️ {empty_campaigns} campagnes sans nom")

    if anomalies:
        for anomaly in anomalies:
            st.write(anomaly)
    else:
        st.success("✅ Aucune anomalie majeure détectée")

    # Score de qualité global
    quality_score = _calculate_overall_quality_score(data)

    if quality_score >= 90:
        st.success(f"🎯 Score de qualité: {quality_score:.0f}% - Excellent")
    elif quality_score >= 75:
        st.warning(f"📊 Score de qualité: {quality_score:.0f}% - Bon")
    else:
        st.error(f"⚠️ Score de qualité: {quality_score:.0f}% - À améliorer")


def _render_detailed_metrics_tab(data: pd.DataFrame):
    """Onglet métriques détaillées"""

    st.markdown("**📈 Métriques par source**")

    # Calcul des métriques par source
    sources = data['source'].unique()

    for source in sources:
        source_data = data[data['source'] == source]

        with st.expander(f"📊 {source} ({len(source_data):,} enregistrements)"):

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("**💰 Financier**")
                total_cost = source_data['cost'].sum() if 'cost' in source_data.columns else 0
                total_revenue = source_data['revenue'].sum() if 'revenue' in source_data.columns else 0
                roas = total_revenue / total_cost if total_cost > 0 else 0

                st.write(f"• Coût total: {total_cost:,.2f}€")
                st.write(f"• Revenus: {total_revenue:,.2f}€")
                st.write(f"• ROAS: {roas:.2f}")

            with col2:
                st.markdown("**👥 Acquisition**")
                total_impressions = source_data['impressions'].sum() if 'impressions' in source_data.columns else 0
                total_clicks = source_data['clicks'].sum() if 'clicks' in source_data.columns else 0
                total_installs = source_data['installs'].sum() if 'installs' in source_data.columns else 0

                st.write(f"• Impressions: {total_impressions:,}")
                st.write(f"• Clics: {total_clicks:,}")
                st.write(f"• Installs: {total_installs:,}")

                if total_impressions > 0:
                    ctr = (total_clicks / total_impressions) * 100
                    st.write(f"• CTR: {ctr:.2f}%")

            with col3:
                st.markdown("**🔄 Conversion**")
                total_opens = source_data['opens'].sum() if 'opens' in source_data.columns else 0
                total_logins = source_data['login'].sum() if 'login' in source_data.columns else 0
                total_purchases = source_data['purchases'].sum() if 'purchases' in source_data.columns else 0

                st.write(f"• Opens: {total_opens:,}")
                st.write(f"• Logins: {total_logins:,}")
                st.write(f"• Purchases: {total_purchases:,}")

                if total_installs > 0:
                    purchase_rate = (total_purchases / total_installs) * 100
                    st.write(f"• Taux achat: {purchase_rate:.2f}%")

    # Comparaison cross-source
    st.markdown("---")
    st.markdown("**🔀 Comparaison cross-source**")

    comparison_data = []
    for source in sources:
        source_data = data[data['source'] == source]

        comparison_data.append({
            'Source': source,
            'Enregistrements': len(source_data),
            'Coût total': f"{source_data['cost'].sum():,.0f}€" if 'cost' in source_data.columns else "N/A",
            'Installs': f"{source_data['installs'].sum():,}" if 'installs' in source_data.columns else "N/A",
            'Purchases': f"{source_data['purchases'].sum():,}" if 'purchases' in source_data.columns else "N/A"
        })

    comparison_df = pd.DataFrame(comparison_data)
    st.dataframe(comparison_df, use_container_width=True)


def _calculate_overall_quality_score(data: pd.DataFrame) -> float:
    """Calcule un score de qualité global des données"""

    score = 0
    max_score = 0

    # Complétude des colonnes importantes
    important_columns = ['date', 'campaign_name', 'source', 'cost', 'installs']
    for col in important_columns:
        max_score += 20
        if col in data.columns:
            completeness = data[col].notna().sum() / len(data)
            score += completeness * 20

    # Absence de valeurs négatives dans les métriques
    max_score += 20
    numeric_columns = ['cost', 'impressions', 'clicks', 'installs']
    negative_penalty = 0
    for col in numeric_columns:
        if col in data.columns:
            negative_count = (data[col] < 0).sum()
            if negative_count > 0:
                negative_penalty += negative_count / len(data)

    score += max(0, 20 - (negative_penalty * 100))

    return (score / max_score) * 100 if max_score > 0 else 0


def render_debug_summary():
    """Affiche un résumé rapide pour le debug en bas de page"""

    if st.checkbox("🔧 Mode debug avancé"):
        st.markdown("---")
        st.markdown("### 🛠️ Informations techniques")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**Session State**")
            st.json(dict(st.session_state))

        with col2:
            st.markdown("**Cache Info**")
            cache_stats = st.cache_data.clear.__doc__ if hasattr(st.cache_data, 'clear') else "N/A"
            st.write(f"Cache status: {cache_stats}")

        with col3:
            st.markdown("**Performance**")
            import time
            st.write(f"Timestamp: {time.time()}")

        # Bouton pour vider le cache
        if st.button("🧹 Vider le cache"):
            st.cache_data.clear()
            st.success("Cache vidé!")
            st.rerun()