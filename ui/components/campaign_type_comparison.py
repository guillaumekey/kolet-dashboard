import streamlit as st
import pandas as pd
from utils.helpers import format_currency, format_percentage
from typing import Dict, Any


def render_campaign_type_comparison(campaign_analysis: pd.DataFrame, summary: Dict[str, Any],
                                    raw_data: Dict[str, pd.DataFrame] = None):
    """
    Affiche la comparaison des performances par type de campagne
    VERSION AMÉLIORÉE avec détail des campagnes

    Args:
        campaign_analysis: DataFrame avec l'analyse détaillée
        summary: Dictionnaire avec le résumé par type de campagne
        raw_data: Données brutes pour le détail des campagnes
    """
    st.subheader("🎯 Performance par Type de Campagne")

    if campaign_analysis.empty:
        st.warning(
            "📭 Aucune campagne classifiée trouvée. Utilisez la configuration des campagnes pour classifier vos campagnes.")
        return

    # Vue d'ensemble
    _render_campaign_type_overview(summary)

    # Tableau détaillé avec boutons d'expansion
    _render_campaign_type_detailed_table_with_drill_down(campaign_analysis, raw_data)


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


def _render_campaign_type_detailed_table_with_drill_down(campaign_analysis: pd.DataFrame,
                                                         raw_data: Dict[str, pd.DataFrame] = None):
    """Affiche le tableau détaillé avec possibilité d'expansion pour voir les campagnes"""

    st.markdown("### 📋 Tableau Détaillé des Performances")

    # Préparer les données pour l'affichage
    display_data = campaign_analysis.copy()

    # Séparer App et Web pour affichage différencié
    app_data = display_data[display_data['channel_type'] == 'app'].copy()
    web_data = display_data[display_data['channel_type'] == 'web'].copy()

    if not app_data.empty:
        st.markdown("#### 📱 Campagnes App")
        _render_app_campaigns_with_detail(app_data, raw_data)

    if not web_data.empty:
        st.markdown("#### 🌐 Campagnes Web")
        _render_web_campaigns_with_detail(web_data, raw_data)

    # Bouton d'export global
    if st.button("📥 Exporter le tableau complet", key="export_campaign_types"):
        csv = display_data.to_csv(index=False)
        st.download_button(
            label="Télécharger CSV",
            data=csv,
            file_name="campaign_types_performance.csv",
            mime="text/csv"
        )


def _render_app_campaigns_with_detail(app_data: pd.DataFrame, raw_data: Dict[str, pd.DataFrame] = None):
    """Affiche les campagnes App avec boutons de détail"""

    app_columns = [
        'campaign_type', 'channel_type', 'nb_campaigns', 'cost', 'impressions',
        'clicks', 'installs', 'opens', 'login', 'purchases', 'revenue',
        'ctr', 'conversion_rate', 'open_rate', 'login_rate', 'purchase_rate_dl', 'cpa', 'roas'
    ]

    # Filtrer les colonnes disponibles
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
        "purchase_rate_dl": st.column_config.NumberColumn("Taux Achat DL", format="%.2f%%", help="Achats / Installs"),
        "cpa": st.column_config.NumberColumn("CPA", format="%.2f €"),
        "roas": st.column_config.NumberColumn("ROAS", format="%.2f")
    }

    st.dataframe(
        app_display,
        column_config=app_column_config,
        use_container_width=True,
        hide_index=True
    )

    # Boutons de détail pour chaque type de campagne App
    for campaign_type in app_data['campaign_type'].unique():
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"**{campaign_type.title()} App** - Détail des campagnes")

        with col2:
            if st.button(f"📊 Voir détail", key=f"detail_app_{campaign_type}"):
                st.session_state[f'show_detail_app_{campaign_type}'] = not st.session_state.get(
                    f'show_detail_app_{campaign_type}', False)

        # Afficher le détail si demandé
        if st.session_state.get(f'show_detail_app_{campaign_type}', False):
            _render_campaign_detail_merged(campaign_type, 'app', raw_data)


def _render_web_campaigns_with_detail(web_data: pd.DataFrame, raw_data: Dict[str, pd.DataFrame] = None):
    """Affiche les campagnes Web avec boutons de détail"""

    web_columns = [
        'campaign_type', 'channel_type', 'nb_campaigns', 'cost', 'impressions',
        'clicks', 'add_to_cart', 'purchases', 'revenue',
        'ctr', 'conversion_rate', 'cart_rate', 'cart_to_purchase_rate', 'cpa', 'roas'
    ]

    # Filtrer les colonnes disponibles
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

    # Boutons de détail pour chaque type de campagne Web
    for campaign_type in web_data['campaign_type'].unique():
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"**{campaign_type.title()} Web** - Détail des campagnes")

        with col2:
            if st.button(f"📊 Voir détail", key=f"detail_web_{campaign_type}"):
                st.session_state[f'show_detail_web_{campaign_type}'] = not st.session_state.get(
                    f'show_detail_web_{campaign_type}', False)

        # Afficher le détail si demandé
        if st.session_state.get(f'show_detail_web_{campaign_type}', False):
            _render_campaign_detail_merged(campaign_type, 'web', raw_data)


def _render_campaign_detail_merged(campaign_type: str, channel_type: str, raw_data: Dict[str, pd.DataFrame] = None):
    """
    CORRIGÉ : Affiche le détail des campagnes avec fusion correcte des données
    Coût/Impressions/Clics depuis Google Ads + ASA
    Installs/Opens/Logins/Achats/Revenus depuis Branch.io
    """

    st.markdown(f"#### 🔍 Détail - {campaign_type.title()} {channel_type.title()}")

    if not raw_data:
        st.warning("❌ Données détaillées non disponibles")
        return

    print(f"🔍 FUSION DONNÉES CORRIGÉE - {campaign_type} {channel_type}")

    # Collecter les données par source
    all_classified_data = pd.DataFrame()

    for source_name, source_data in raw_data.items():
        if source_data.empty:
            continue

        # Filtrer exactement comme dans le tableau global
        filtered = source_data[
            (source_data.get('campaign_type', '') == campaign_type) &
            (source_data.get('channel_type', '') == channel_type)
            ].copy()

        if not filtered.empty:
            filtered['data_source'] = source_name
            all_classified_data = pd.concat([all_classified_data, filtered], ignore_index=True)
            print(f"  • {source_name}: {len(filtered)} lignes pour {campaign_type}/{channel_type}")

    if all_classified_data.empty:
        st.info(f"📭 Aucune campagne classifiée trouvée pour {campaign_type} {channel_type}")
        return

    # LOGIQUE CORRIGÉE : Fusion par nom de campagne selon la règle
    # Coût/Impressions/Clics : Google Ads + ASA
    # Installs/Opens/Logins/Achats/Revenus : Branch.io

    if channel_type == 'app':
        campaign_totals = _process_app_campaign_fusion_corrected(all_classified_data)
    else:  # web
        # Pour Web : tout vient de Google Ads
        campaign_totals = all_classified_data.groupby('campaign_name').agg({
            'cost': 'sum',
            'impressions': 'sum',
            'clicks': 'sum',
            'purchases': 'sum',
            'revenue': 'sum',
            'data_source': 'first'
        }).reset_index()

        # Ajouter colonnes manquantes pour Web
        for col in ['installs', 'opens', 'login']:
            campaign_totals[col] = 0

    if campaign_totals.empty:
        st.info(f"📭 Aucune campagne trouvée pour {campaign_type} {channel_type}")
        return

    # Debug final
    total_installs_detail = campaign_totals['installs'].sum() if 'installs' in campaign_totals.columns else 0
    total_cost_detail = campaign_totals['cost'].sum() if 'cost' in campaign_totals.columns else 0

    print(f"  ✅ RÉSULTAT FINAL:")
    print(f"    • Campagnes uniques: {len(campaign_totals)}")
    print(f"    • Total coût: {total_cost_detail:.2f}€")
    print(f"    • Total installs: {total_installs_detail}")

    # Affichage du tableau avec les données corrigées
    _display_merged_campaign_table(campaign_totals, channel_type, campaign_type)


def _process_app_campaign_fusion_corrected(all_classified_data: pd.DataFrame) -> pd.DataFrame:
    """
    CORRIGÉ : Fusion correcte en incluant TOUTES les campagnes
    """

    # Identifier TOUTES les campagnes uniques d'abord
    all_campaign_names = all_classified_data['campaign_name'].unique()
    print(f"    🎯 TOUTES LES CAMPAGNES TROUVÉES: {len(all_campaign_names)}")

    # Créer le DataFrame final avec toutes les campagnes
    campaign_totals = pd.DataFrame({'campaign_name': all_campaign_names})

    # Initialiser toutes les colonnes à zéro
    for col in ['cost', 'impressions', 'clicks', 'installs', 'opens', 'login', 'purchases', 'revenue']:
        campaign_totals[col] = 0

    campaign_totals['data_source'] = 'unknown'

    # 1. AJOUTER LES DONNÉES PUBLICITAIRES (Google Ads + ASA)
    advertising_sources = ['google_ads', 'asa']
    pub_data = all_classified_data[
        all_classified_data['data_source'].isin(advertising_sources)
    ]

    if not pub_data.empty:
        pub_totals = pub_data.groupby('campaign_name').agg({
            'cost': 'sum',
            'impressions': 'sum',
            'clicks': 'sum',
            'data_source': 'first'  # Garder la source
        }).reset_index()

        print(f"      • Données pub: {len(pub_totals)} campagnes, coût total: {pub_totals['cost'].sum():.2f}€")

        # Mettre à jour les campagnes avec données pub
        for _, pub_row in pub_totals.iterrows():
            mask = campaign_totals['campaign_name'] == pub_row['campaign_name']
            campaign_totals.loc[mask, 'cost'] = pub_row['cost']
            campaign_totals.loc[mask, 'impressions'] = pub_row['impressions']
            campaign_totals.loc[mask, 'clicks'] = pub_row['clicks']
            campaign_totals.loc[mask, 'data_source'] = pub_row['data_source']

    # 2. AJOUTER LES DONNÉES DE CONVERSION (Branch.io)
    conv_data = all_classified_data[
        all_classified_data['data_source'] == 'branch'
        ]

    if not conv_data.empty:
        conv_totals = conv_data.groupby('campaign_name').agg({
            'installs': 'sum',
            'opens': 'sum',
            'login': 'sum',
            'purchases': 'sum',
            'revenue': 'sum'
        }).reset_index()

        print(f"      • Données conv: {len(conv_totals)} campagnes, installs total: {conv_totals['installs'].sum()}")

        # Mettre à jour les campagnes avec données conversion
        for _, conv_row in conv_totals.iterrows():
            mask = campaign_totals['campaign_name'] == conv_row['campaign_name']
            campaign_totals.loc[mask, 'installs'] = conv_row['installs']
            campaign_totals.loc[mask, 'opens'] = conv_row['opens']
            campaign_totals.loc[mask, 'login'] = conv_row['login']
            campaign_totals.loc[mask, 'purchases'] = conv_row['purchases']
            campaign_totals.loc[mask, 'revenue'] = conv_row['revenue']

            # Si pas de source pub, marquer comme branch_only
            if campaign_totals.loc[mask, 'data_source'].iloc[0] == 'unknown':
                campaign_totals.loc[mask, 'data_source'] = 'branch_only'

    # 3. VÉRIFICATION FINALE
    total_installs_final = campaign_totals['installs'].sum()
    total_cost_final = campaign_totals['cost'].sum()

    print(f"      ✅ FUSION FINALE:")
    print(f"         - Campagnes totales: {len(campaign_totals)}")
    print(f"         - Installs totaux: {total_installs_final}")
    print(f"         - Coût total: {total_cost_final:.2f}€")

    # Debug par source
    source_counts = campaign_totals['data_source'].value_counts()
    for source, count in source_counts.items():
        installs_source = campaign_totals[campaign_totals['data_source'] == source]['installs'].sum()
        print(f"         - {source}: {count} campagnes, {installs_source} installs")

    return campaign_totals


# AUSSI : Modifiez la fonction principale pour garder le diagnostic
def _render_campaign_detail_merged(campaign_type: str, channel_type: str, raw_data: Dict[str, pd.DataFrame] = None):
    """
    CORRIGÉ : Affiche le détail des campagnes avec fusion correcte des données
    """

    st.markdown(f"#### 🔍 Détail - {campaign_type.title()} {channel_type.title()}")

    if not raw_data:
        st.warning("❌ Données détaillées non disponibles")
        return

    print(f"🔍 FUSION DONNÉES CORRIGÉE - {campaign_type} {channel_type}")

    # GARDER LE DIAGNOSTIC POUR VÉRIFIER
    st.write("🔍 **DIAGNOSTIC RAPIDE**")
    total_installs_by_source = {}

    for source_name, source_data in raw_data.items():
        if source_data.empty:
            continue

        filtered = source_data[
            (source_data.get('campaign_type', '') == campaign_type) &
            (source_data.get('channel_type', '') == channel_type)
            ]

        if not filtered.empty:
            total_installs = filtered['installs'].sum()
            total_installs_by_source[source_name] = total_installs
            st.write(f"**{source_name}:** {total_installs:,} installs")

    total_installs_diagnostic = sum(total_installs_by_source.values())
    st.write(f"**TOTAL ATTENDU:** {total_installs_diagnostic:,} installs")

    # Collecter les données par source
    all_classified_data = pd.DataFrame()

    for source_name, source_data in raw_data.items():
        if source_data.empty:
            continue

        filtered = source_data[
            (source_data.get('campaign_type', '') == campaign_type) &
            (source_data.get('channel_type', '') == channel_type)
            ].copy()

        if not filtered.empty:
            filtered['data_source'] = source_name
            all_classified_data = pd.concat([all_classified_data, filtered], ignore_index=True)

    if all_classified_data.empty:
        st.info(f"📭 Aucune campagne classifiée trouvée pour {campaign_type} {channel_type}")
        return

    # LOGIQUE CORRIGÉE
    if channel_type == 'app':
        campaign_totals = _process_app_campaign_fusion_corrected(all_classified_data)
    else:  # web
        campaign_totals = all_classified_data.groupby('campaign_name').agg({
            'cost': 'sum',
            'impressions': 'sum',
            'clicks': 'sum',
            'purchases': 'sum',
            'revenue': 'sum',
            'data_source': 'first'
        }).reset_index()

        for col in ['installs', 'opens', 'login']:
            campaign_totals[col] = 0

    if campaign_totals.empty:
        st.info(f"📭 Aucune campagne trouvée pour {campaign_type} {channel_type}")
        return

    # Vérification finale
    total_installs_tableau = campaign_totals['installs'].sum()
    st.success(f"✅ **TABLEAU FINAL:** {total_installs_tableau:,} installs")

    if total_installs_tableau != total_installs_diagnostic:
        st.error(f"❌ ERREUR: Différence de {total_installs_diagnostic - total_installs_tableau:,} installs!")

    # Affichage du tableau
    _display_merged_campaign_table(campaign_totals, channel_type, campaign_type)

def _display_merged_campaign_table(campaign_data: pd.DataFrame, channel_type: str, campaign_type: str):
    """MODIFIÉ : Affiche le tableau des campagnes avec données cohérentes"""

    # Calculer les métriques
    campaign_data['ctr'] = (campaign_data['clicks'] / campaign_data['impressions'] * 100).fillna(0)
    campaign_data['roas'] = (campaign_data['revenue'] / campaign_data['cost']).fillna(0)

    if channel_type == 'app':
        campaign_data['cpa'] = (campaign_data['cost'] / campaign_data['installs']).fillna(0)
        campaign_data['conversion_rate'] = (campaign_data['installs'] / campaign_data['clicks'] * 100).fillna(0)
        campaign_data['open_rate'] = (campaign_data['opens'] / campaign_data['installs'] * 100).fillna(0)
        campaign_data['purchase_rate'] = (campaign_data['purchases'] / campaign_data['installs'] * 100).fillna(0)

        # Colonnes App (AVEC LOGINS)
        display_columns = ['campaign_name', 'data_source', 'cost', 'impressions', 'clicks',
                           'installs', 'opens', 'login', 'purchases', 'revenue', 'ctr', 'conversion_rate',
                           'open_rate', 'purchase_rate', 'cpa', 'roas']

        column_config = {
            "campaign_name": st.column_config.TextColumn("Nom Campagne", width="large"),
            "data_source": st.column_config.TextColumn("Source", width="small"),
            "cost": st.column_config.NumberColumn("Coût", format="%.2f €"),
            "impressions": st.column_config.NumberColumn("Impressions", format="%d"),
            "clicks": st.column_config.NumberColumn("Clics", format="%d"),
            "installs": st.column_config.NumberColumn("Installs", format="%d"),
            "opens": st.column_config.NumberColumn("Opens", format="%d"),
            "login": st.column_config.NumberColumn("Logins", format="%d"),
            "purchases": st.column_config.NumberColumn("Achats", format="%d"),
            "revenue": st.column_config.NumberColumn("Revenus", format="%.2f €"),
            "ctr": st.column_config.NumberColumn("CTR", format="%.2f%%"),
            "conversion_rate": st.column_config.NumberColumn("Taux Conv.", format="%.2f%%"),
            "open_rate": st.column_config.NumberColumn("Taux Open", format="%.2f%%"),
            "purchase_rate": st.column_config.NumberColumn("Taux Achat", format="%.2f%%"),
            "cpa": st.column_config.NumberColumn("CPA", format="%.2f €"),
            "roas": st.column_config.NumberColumn("ROAS", format="%.2f")
        }
    else:  # web
        campaign_data['cpa'] = (campaign_data['cost'] / campaign_data['purchases']).fillna(0)
        campaign_data['conversion_rate'] = (campaign_data['purchases'] / campaign_data['clicks'] * 100).fillna(0)

        # Colonnes Web
        display_columns = ['campaign_name', 'data_source', 'cost', 'impressions', 'clicks',
                           'purchases', 'revenue', 'ctr', 'conversion_rate', 'cpa', 'roas']

        column_config = {
            "campaign_name": st.column_config.TextColumn("Nom Campagne", width="large"),
            "data_source": st.column_config.TextColumn("Source", width="small"),
            "cost": st.column_config.NumberColumn("Coût", format="%.2f €"),
            "impressions": st.column_config.NumberColumn("Impressions", format="%d"),
            "clicks": st.column_config.NumberColumn("Clics", format="%d"),
            "purchases": st.column_config.NumberColumn("Achats", format="%d"),
            "revenue": st.column_config.NumberColumn("Revenus", format="%.2f €"),
            "ctr": st.column_config.NumberColumn("CTR", format="%.2f%%"),
            "conversion_rate": st.column_config.NumberColumn("Taux Conv.", format="%.2f%%"),
            "cpa": st.column_config.NumberColumn("CPA", format="%.2f €"),
            "roas": st.column_config.NumberColumn("ROAS", format="%.2f")
        }

    # Filtrer les colonnes disponibles et TRIER PAR COÛT DÉCROISSANT
    available_columns = [col for col in display_columns if col in campaign_data.columns]
    display_data = campaign_data[available_columns].sort_values('cost', ascending=False)

    # DEBUG : Afficher les totaux calculés
    total_installs_detail = display_data['installs'].sum() if 'installs' in display_data.columns else 0
    print(f"🔍 DEBUG AFFICHAGE:")
    print(f"  • Campagnes affichées: {len(display_data)}")
    print(f"  • Total installs affiché: {total_installs_detail}")

    st.dataframe(
        display_data,
        column_config=column_config,
        use_container_width=True,
        hide_index=True
    )

    # Statistiques consolidées MODIFIÉES
    if channel_type == 'app':
        col1, col2, col3, col4, col5, col6 = st.columns(6)

        with col1:
            st.metric("📊 Campagnes", len(display_data))

        with col2:
            total_cost = display_data['cost'].sum()
            st.metric("💰 Coût Total", f"{total_cost:,.2f}€")

        with col3:
            total_installs = display_data['installs'].sum()
            st.metric("📱 Total Installs", f"{total_installs:,}")

        with col4:
            total_purchases = display_data['purchases'].sum()
            st.metric("🛒 Total Achats", f"{total_purchases:,}")

        with col5:
            total_revenue = display_data['revenue'].sum()
            st.metric("💵 Revenus Total", f"{total_revenue:,.2f}€")

        with col6:
            avg_roas = display_data['roas'].mean()
            st.metric("📈 ROAS Moyen", f"{avg_roas:.2f}")

    else:  # web
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric("📊 Campagnes", len(display_data))

        with col2:
            total_cost = display_data['cost'].sum()
            st.metric("💰 Coût Total", f"{total_cost:,.2f}€")

        with col3:
            total_purchases = display_data['purchases'].sum()
            st.metric("🛒 Total Achats", f"{total_purchases:,}")

        with col4:
            total_revenue = display_data['revenue'].sum()
            st.metric("💵 Revenus Total", f"{total_revenue:,.2f}€")

        with col5:
            avg_roas = display_data['roas'].mean()
            st.metric("📈 ROAS Moyen", f"{avg_roas:.2f}")

    # Message d'information sur la consolidation
    st.info(f"📅 **Données consolidées** sur la période sélectionnée - Une ligne par campagne avec totaux agrégés")

    # Bouton d'export
    if st.button(f"📥 Exporter {campaign_type} {channel_type}", key=f"export_{campaign_type}_{channel_type}"):
        csv = display_data.to_csv(index=False)
        st.download_button(
            label="Télécharger CSV consolidé",
            data=csv,
            file_name=f"detail_consolide_{campaign_type}_{channel_type}.csv",
            mime="text/csv",
            key=f"download_{campaign_type}_{channel_type}"
        )

    # Bouton pour masquer
    if st.button(f"🔼 Masquer le détail", key=f"hide_{campaign_type}_{channel_type}"):
        st.session_state[f'show_detail_{channel_type}_{campaign_type}'] = False
        st.rerun()


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