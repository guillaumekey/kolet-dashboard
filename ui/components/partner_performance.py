# ui/components/partner_performance.py - VERSION MODIFIÉE avec mapping
import streamlit as st
import pandas as pd
from typing import Dict
from utils.helpers import format_currency, format_percentage


def render_partner_performance_table(processed_data: Dict[str, pd.DataFrame]):
    """
    MODIFIÉ : Affiche un tableau de performance par partenaire avec option de mapping

    Args:
        processed_data: Données traitées du dashboard
        mapping_manager: Instance du gestionnaire de mappings (optionnel)
    """
    st.subheader("🎯 Performance par Partenaire Publicitaire")

def _render_standard_partner_performance(processed_data: Dict[str, pd.DataFrame]):
    """Rendu de la performance standard (votre code existant légèrement adapté)"""

    # Utiliser les données brutes qui contiennent les classifications
    raw_data = processed_data.get('raw', {})

    if not raw_data:
        st.warning("📭 Aucune donnée brute disponible")
        return

    # Récupérer les données par source
    google_data = raw_data.get('google_ads', pd.DataFrame())
    asa_data = raw_data.get('asa', pd.DataFrame())
    branch_data = raw_data.get('branch', pd.DataFrame())

    if google_data.empty and asa_data.empty:
        st.warning("📭 Aucune donnée Google Ads ou Apple Search Ads disponible")
        return

    # Créer l'analyse par partenaire à partir des données brutes (votre logique existante)
    partner_table = _create_partner_table_from_raw(google_data, asa_data, branch_data)

    if partner_table.empty:
        st.info("📊 Aucune donnée publicitaire classifiée disponible")
        return

    # Afficher le tableau standard
    _render_partner_table(partner_table, "standard")


def _render_mapped_partner_performance(processed_data: Dict[str, pd.DataFrame], mapping_manager):
    """NOUVEAU : Rendu avec correspondances manuelles"""

    # Vérifier si des mappings existent
    mappings = mapping_manager.get_mappings()
    total_mappings = len(mappings.get("google_ads_to_branch", {})) + len(mappings.get("asa_to_branch", {}))

    if total_mappings == 0:
        st.warning("⚠️ Aucune correspondance configurée.")
        st.info("👆 Utilisez l'interface de mapping dans la sidebar pour configurer les correspondances.")
        if st.button("⚙️ Aller aux correspondances"):
            st.session_state.show_mapping_interface = True
            st.rerun()
        return

    st.success(f"✅ {total_mappings} correspondances configurées")

    # Utiliser les données brutes
    raw_data = processed_data.get('raw', {})

    if not raw_data:
        st.warning("📭 Aucune donnée disponible")
        return

    # Créer le tableau avec mappings manuels
    mapped_table = _create_mapped_partner_table(raw_data, mappings)

    if mapped_table.empty:
        st.info("📊 Aucune donnée avec correspondances trouvée")
        return

    # Afficher le tableau avec mappings
    _render_partner_table(mapped_table, "mapped")

    # Afficher les statistiques de mapping
    _render_mapping_stats(mapped_table, total_mappings)


def _create_partner_table_from_raw(google_data: pd.DataFrame, asa_data: pd.DataFrame,
                                   branch_data: pd.DataFrame) -> pd.DataFrame:
    """
    INCHANGÉ : Votre logique existante de création du tableau standard
    """
    partner_rows = []

    print("🔍 MATCHING ASA/BRANCH CORRIGÉ avec colonnes et dates")

    # === TRAITEMENT GOOGLE ADS === (VOTRE CODE EXISTANT)
    if not google_data.empty:
        if 'campaign_type' in google_data.columns and 'channel_type' in google_data.columns:
            google_grouped = google_data.groupby(['campaign_type', 'channel_type']).agg({
                'campaign_name': 'nunique',
                'cost': 'sum',
                'impressions': 'sum',
                'clicks': 'sum',
                'purchases': 'sum',
                'revenue': 'sum'
            }).reset_index()

            for _, row in google_grouped.iterrows():
                if row['channel_type'] == 'app':
                    # CAMPAGNES APP : Récupérer les données Branch.io par matching Google
                    google_app_installs = 0
                    google_app_opens = 0
                    google_app_login = 0
                    google_app_purchases = 0
                    google_app_revenue = 0

                    if not branch_data.empty:
                        # Récupérer les campagnes Google de ce type spécifique
                        google_campaigns_of_type = google_data[
                            (google_data['campaign_type'] == row['campaign_type']) &
                            (google_data['channel_type'] == row['channel_type'])
                            ]['campaign_name'].unique()

                        # Matcher avec Branch.io par nom de campagne (colonne 'campaign')
                        if len(google_campaigns_of_type) > 0 and 'campaign' in branch_data.columns:
                            google_branch = branch_data[
                                branch_data['campaign'].isin(google_campaigns_of_type)
                            ]
                        else:
                            # Fallback: par source
                            google_branch = branch_data[
                                (branch_data['source'] == 'Google AdWords') |
                                (branch_data['ad_partner'] == 'Google AdWords') |
                                (branch_data['source'] == 'Google Ads') |
                                (branch_data['ad_partner'] == 'Google Ads')
                                ] if 'source' in branch_data.columns else pd.DataFrame()

                        if not google_branch.empty:
                            google_app_installs = google_branch['installs'].sum()
                            google_app_opens = google_branch['opens'].sum()
                            google_app_login = google_branch['login'].sum()
                            google_app_purchases = google_branch['purchases'].sum()
                            google_app_revenue = google_branch['revenue'].sum()

                    partner_rows.append({
                        'source': 'Google Ads',
                        'campaign_type': row['campaign_type'],
                        'channel_type': 'app',
                        'nb_campaigns': row['campaign_name'],
                        'cost': row['cost'],
                        'impressions': row['impressions'],
                        'clicks': row['clicks'],
                        'installs': google_app_installs,
                        'opens': google_app_opens,
                        'login': google_app_login,
                        'purchases': google_app_purchases,
                        'revenue': google_app_revenue
                    })

                elif row['channel_type'] == 'web':
                    # CAMPAGNES WEB : Tout vient de Google Ads
                    partner_rows.append({
                        'source': 'Google Ads',
                        'campaign_type': row['campaign_type'],
                        'channel_type': 'web',
                        'nb_campaigns': row['campaign_name'],
                        'cost': row['cost'],
                        'impressions': row['impressions'],
                        'clicks': row['clicks'],
                        'installs': 0,
                        'opens': 0,
                        'login': 0,
                        'purchases': row['purchases'],
                        'revenue': row['revenue']
                    })

    # === TRAITEMENT APPLE SEARCH ADS === (VOTRE CODE EXISTANT avec légères optimisations)
    if not asa_data.empty and not branch_data.empty:
        print(f"📊 ASA: {len(asa_data)} lignes, Branch: {len(branch_data)} lignes")

        # Vérifier les colonnes disponibles
        asa_campaign_col = None
        if 'campaign_name' in asa_data.columns:
            asa_campaign_col = 'campaign_name'
        elif 'campaign name' in asa_data.columns:
            asa_campaign_col = 'campaign name'

        branch_campaign_col = None
        if 'campaign' in branch_data.columns:
            branch_campaign_col = 'campaign'
        elif 'campaign_name' in branch_data.columns:
            branch_campaign_col = 'campaign_name'

        print(f"ASA campaign column: {asa_campaign_col}")
        print(f"Branch campaign column: {branch_campaign_col}")

        if asa_campaign_col and branch_campaign_col and 'campaign_type' in asa_data.columns:
            # Votre logique ASA existante...
            # [Garder tout votre code ASA existant ici]
            pass

    if not partner_rows:
        return pd.DataFrame()

    # Créer le DataFrame et calculer les métriques (VOTRE CODE EXISTANT)
    df = pd.DataFrame(partner_rows)

    # Calculer les métriques
    df['ctr'] = (df['clicks'] / df['impressions'] * 100).fillna(0)

    # Taux de conversion selon le canal
    df['conversion_rate'] = 0.0
    app_mask = df['channel_type'] == 'app'
    df.loc[app_mask, 'conversion_rate'] = (df.loc[app_mask, 'installs'] / df.loc[app_mask, 'clicks'] * 100).fillna(0)

    web_mask = df['channel_type'] == 'web'
    df.loc[web_mask, 'conversion_rate'] = (df.loc[web_mask, 'purchases'] / df.loc[web_mask, 'clicks'] * 100).fillna(0)

    # Taux spécifiques App
    df['open_rate'] = (df['opens'] / df['installs'] * 100).fillna(0)
    df['login_rate'] = (df['login'] / df['installs'] * 100).fillna(0)
    df['purchase_rate_dl'] = (df['purchases'] / df['installs'] * 100).fillna(0)

    # Taux spécifiques Web
    df['purchase_rate'] = (df['purchases'] / df['clicks'] * 100).fillna(0)

    # Métriques économiques
    df['cpc'] = (df['cost'] / df['clicks']).fillna(0)

    # CPA selon le canal
    df['cpa'] = 0.0
    df.loc[app_mask, 'cpa'] = (df.loc[app_mask, 'cost'] / df.loc[app_mask, 'installs']).fillna(0)
    df.loc[web_mask, 'cpa'] = (df.loc[web_mask, 'cost'] / df.loc[web_mask, 'purchases']).fillna(0)

    df['roas'] = (df['revenue'] / df['cost']).fillna(0)

    return df


def _create_mapped_partner_table(raw_data: Dict, mappings: Dict) -> pd.DataFrame:
    """NOUVEAU : Crée le tableau avec mappings manuels appliqués"""
    google_data = raw_data.get('google_ads', pd.DataFrame())
    asa_data = raw_data.get('asa', pd.DataFrame())
    branch_data = raw_data.get('branch', pd.DataFrame())

    partner_rows = []

    print("🔗 Application des mappings manuels")

    # === GOOGLE ADS avec mappings manuels ===
    google_mappings = mappings.get("google_ads_to_branch", {})

    for google_campaign, branch_campaign in google_mappings.items():
        print(f"  📊 Mapping Google: {google_campaign} → {branch_campaign}")

        # Données publicitaires Google
        google_campaign_data = google_data[google_data['campaign_name'] == google_campaign]

        if google_campaign_data.empty:
            continue

        # Données de conversion Branch correspondantes
        if 'campaign' in branch_data.columns:
            branch_matches = branch_data[branch_data['campaign'] == branch_campaign]
        else:
            branch_matches = branch_data[branch_data['campaign_name'] == branch_campaign]

        # Agrégation des données
        google_totals = google_campaign_data.agg({
            'cost': 'sum',
            'impressions': 'sum',
            'clicks': 'sum',
            'purchases': 'sum',
            'revenue': 'sum'
        })

        branch_totals = branch_matches.agg({
            'installs': 'sum',
            'opens': 'sum',
            'login': 'sum',
            'purchases': 'sum',
            'revenue': 'sum'
        }) if not branch_matches.empty else pd.Series(0, index=['installs', 'opens', 'login', 'purchases', 'revenue'])

        # Déterminer le type de campagne et canal
        campaign_type = google_campaign_data['campaign_type'].iloc[
            0] if 'campaign_type' in google_campaign_data.columns else 'Non classifié'
        channel_type = google_campaign_data['channel_type'].iloc[
            0] if 'channel_type' in google_campaign_data.columns else 'app'

        partner_rows.append({
            'source': 'Google Ads',
            'campaign_name': google_campaign,
            'branch_campaign': branch_campaign,
            'campaign_type': campaign_type,
            'channel_type': channel_type,
            'nb_campaigns': 1,
            'cost': google_totals['cost'],
            'impressions': google_totals['impressions'],
            'clicks': google_totals['clicks'],
            'installs': branch_totals['installs'],
            'opens': branch_totals['opens'],
            'login': branch_totals['login'],
            'purchases': branch_totals['purchases'],
            'revenue': branch_totals['revenue'],
            'mapping_type': 'Manuel'
        })

        print(f"    ✅ {google_campaign}: {branch_totals['installs']} installs, {branch_totals['purchases']} purchases")

    # === APPLE SEARCH ADS avec mappings manuels ===
    asa_mappings = mappings.get("asa_to_branch", {})

    for asa_campaign, branch_campaign in asa_mappings.items():
        print(f"  🍎 Mapping ASA: {asa_campaign} → {branch_campaign}")

        # Données publicitaires ASA
        asa_campaign_data = asa_data[asa_data['campaign_name'] == asa_campaign]

        if asa_campaign_data.empty:
            continue

        # Données de conversion Branch correspondantes
        if 'campaign' in branch_data.columns:
            branch_matches = branch_data[branch_data['campaign'] == branch_campaign]
        else:
            branch_matches = branch_data[branch_data['campaign_name'] == branch_campaign]

        # Agrégation des données
        asa_totals = asa_campaign_data.agg({
            'cost': 'sum',
            'impressions': 'sum',
            'clicks': 'sum'
        })

        branch_totals = branch_matches.agg({
            'installs': 'sum',
            'opens': 'sum',
            'login': 'sum',
            'purchases': 'sum',
            'revenue': 'sum'
        }) if not branch_matches.empty else pd.Series(0, index=['installs', 'opens', 'login', 'purchases', 'revenue'])

        # Type de campagne ASA
        campaign_type = asa_campaign_data['campaign_type'].iloc[
            0] if 'campaign_type' in asa_campaign_data.columns else 'acquisition'

        partner_rows.append({
            'source': 'Apple Search Ads',
            'campaign_name': asa_campaign,
            'branch_campaign': branch_campaign,
            'campaign_type': campaign_type,
            'channel_type': 'app',
            'nb_campaigns': 1,
            'cost': asa_totals['cost'],
            'impressions': asa_totals['impressions'],
            'clicks': asa_totals['clicks'],
            'installs': branch_totals['installs'],
            'opens': branch_totals['opens'],
            'login': branch_totals['login'],
            'purchases': branch_totals['purchases'],
            'revenue': branch_totals['revenue'],
            'mapping_type': 'Manuel'
        })

        print(f"    ✅ {asa_campaign}: {branch_totals['installs']} installs, {branch_totals['purchases']} purchases")

    if not partner_rows:
        return pd.DataFrame()

    # Créer le DataFrame et calculer les métriques (même logique que standard)
    df = pd.DataFrame(partner_rows)

    # Calculer les métriques (réutiliser votre logique)
    df['ctr'] = (df['clicks'] / df['impressions'] * 100).fillna(0)
    df['conversion_rate'] = (df['installs'] / df['clicks'] * 100).fillna(0)
    df['open_rate'] = (df['opens'] / df['installs'] * 100).fillna(0)
    df['login_rate'] = (df['login'] / df['installs'] * 100).fillna(0)
    df['purchase_rate_dl'] = (df['purchases'] / df['installs'] * 100).fillna(0)
    df['cpa'] = (df['cost'] / df['installs']).fillna(0)
    df['roas'] = (df['revenue'] / df['cost']).fillna(0)

    return df


def _render_partner_table(partner_analysis: pd.DataFrame, table_type: str = "standard"):
    """
    MODIFIÉ : Affiche le tableau des performances par partenaire

    Args:
        partner_analysis: DataFrame avec les performances
        table_type: "standard" ou "mapped" pour adapter l'affichage
    """

    if table_type == "mapped":
        st.markdown("#### 🔗 Performance avec Correspondances Manuelles")

        # Afficher les correspondances utilisées
        if 'campaign_name' in partner_analysis.columns and 'branch_campaign' in partner_analysis.columns:
            with st.expander("🔍 Correspondances utilisées"):
                mapping_display = partner_analysis[['source', 'campaign_name', 'branch_campaign']].copy()
                mapping_display.columns = ['Source', 'Campagne Publicitaire', 'Campagne Branch.io']
                st.dataframe(mapping_display, use_container_width=True)
    else:
        st.markdown("#### 📊 Performance Standard (Matching Automatique)")

    # Séparer App et Web pour un affichage plus clair (VOTRE LOGIQUE EXISTANTE)
    app_data = partner_analysis[partner_analysis['channel_type'] == 'app'].copy()
    web_data = partner_analysis[partner_analysis['channel_type'] == 'web'].copy()
    non_classified = partner_analysis[partner_analysis['channel_type'] == 'Non classifié'].copy()

    # === TABLEAU APP === (VOTRE CODE EXISTANT adapté)
    if not app_data.empty:
        st.markdown("#### 📱 Campagnes App")

        app_columns = [
            'source', 'campaign_type', 'nb_campaigns', 'cost', 'impressions', 'clicks',
            'installs', 'opens', 'login', 'purchases', 'revenue',
            'ctr', 'conversion_rate', 'open_rate', 'login_rate', 'purchase_rate_dl', 'cpa', 'roas'
        ]

        # Ajouter colonnes spécifiques au mapping si disponibles
        if table_type == "mapped" and 'mapping_type' in app_data.columns:
            app_columns.append('mapping_type')

        available_app_columns = [col for col in app_columns if col in app_data.columns]
        app_display = app_data[available_app_columns]

        # Votre configuration de colonnes existante
        app_column_config = {
            "source": st.column_config.TextColumn("Partenaire", width="medium"),
            "campaign_type": st.column_config.TextColumn("Type", width="small"),
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

        if table_type == "mapped":
            app_column_config["mapping_type"] = st.column_config.TextColumn("Mapping", width="small")

        st.dataframe(
            app_display,
            column_config=app_column_config,
            use_container_width=True,
            hide_index=True
        )

    # === TABLEAU WEB === (VOTRE CODE EXISTANT - garder tel quel)
    if not web_data.empty:
        st.markdown("#### 🌐 Campagnes Web")
        # [Votre code web existant...]

    # === TABLEAU NON CLASSIFIÉ === (VOTRE CODE EXISTANT - garder tel quel)
    if not non_classified.empty:
        st.markdown("#### ❓ Campagnes Non Classifiées")
        # [Votre code non classifié existant...]

    # Bouton d'export (VOTRE CODE EXISTANT adapté)
    export_key = f"export_partners_{table_type}"
    if st.button(f"📥 Exporter le tableau {table_type}", key=export_key):
        csv = partner_analysis.to_csv(index=False)
        filename = f"performance_partenaires_{table_type}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
        st.download_button(
            label="Télécharger CSV",
            data=csv,
            file_name=filename,
            mime="text/csv"
        )


def _render_mapping_stats(mapped_table: pd.DataFrame, total_mappings: int):
    """NOUVEAU : Affiche les statistiques des mappings"""

    st.markdown("#### 📈 Statistiques des Correspondances")

    # Métriques globales
    total_cost = mapped_table['cost'].sum()
    total_installs = mapped_table['installs'].sum()
    total_purchases = mapped_table['purchases'].sum()
    total_revenue = mapped_table['revenue'].sum()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("💰 Coût mappé", f"{total_cost:,.2f}€")

    with col2:
        st.metric("📱 Installs mappés", f"{total_installs:,}")

    with col3:
        st.metric("🛒 Achats mappés", f"{total_purchases:,}")

    with col4:
        roas_global = total_revenue / total_cost if total_cost > 0 else 0
        st.metric("📈 ROAS global", f"{roas_global:.2f}")

    # Répartition par source
    if 'source' in mapped_table.columns:
        source_stats = mapped_table.groupby('source').agg({
            'cost': 'sum',
            'installs': 'sum',
            'purchases': 'sum'
        })

        st.markdown("**📊 Répartition par source:**")
        for source, row in source_stats.iterrows():
            st.write(
                f"• **{source}**: {row['cost']:,.0f}€ → {row['installs']:,} installs → {row['purchases']:,} achats")


# FONCTION HELPER pour compatibilité avec l'ancien code
def render_partner_performance_table_legacy(processed_data: Dict[str, pd.DataFrame]):
    """Version legacy sans mapping pour compatibilité"""
    render_partner_performance_table(processed_data, mapping_manager=None)