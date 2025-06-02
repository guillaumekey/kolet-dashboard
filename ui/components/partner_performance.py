import streamlit as st
import pandas as pd
from typing import Dict
from utils.helpers import format_currency, format_percentage


def render_partner_performance_table(processed_data: Dict[str, pd.DataFrame]):
    """
    Affiche un tableau simple de performance par partenaire avec segmentation type/canal

    Args:
        processed_data: Données traitées du dashboard
    """
    st.subheader("🎯 Performance par Partenaire Publicitaire")

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

    # Créer l'analyse par partenaire à partir des données brutes
    partner_table = _create_partner_table_from_raw(google_data, asa_data, branch_data)

    if partner_table.empty:
        st.info("📊 Aucune donnée publicitaire classifiée disponible")
        return

    # Afficher le tableau
    _render_partner_table(partner_table)


def _create_partner_table_from_raw(google_data: pd.DataFrame, asa_data: pd.DataFrame,
                                   branch_data: pd.DataFrame) -> pd.DataFrame:
    """
    Crée le tableau de performance par partenaire à partir des données brutes

    LOGIQUE CORRECTE :
    - Coût, Impressions, Clics : Google Ads et ASA (sources publicitaires)
    - Installs, Opens, Login, Purchases APP : Branch.io uniquement
    - Purchases WEB : Google Ads uniquement
    """
    partner_rows = []

    # === TRAITEMENT GOOGLE ADS ===
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
                    # CAMPAGNES APP : Récupérer les données Branch.io
                    google_app_installs = 0
                    google_app_opens = 0
                    google_app_login = 0
                    google_app_purchases = 0
                    google_app_revenue = 0

                    if not branch_data.empty:
                        # MÉTHODE 1 : Par source/ad_partner
                        google_branch = branch_data[
                            (branch_data['source'] == 'Google AdWords') |
                            (branch_data['ad_partner'] == 'Google AdWords') |
                            (branch_data['source'] == 'Google Ads') |
                            (branch_data['ad_partner'] == 'Google Ads')
                            ] if 'source' in branch_data.columns else pd.DataFrame()

                        # MÉTHODE 2 : Si pas de résultat, essayer par nom de campagne
                        if google_branch.empty and 'campaign_name' in branch_data.columns and 'campaign_name' in google_data.columns:
                            google_campaigns = google_data['campaign_name'].unique()
                            google_branch = branch_data[
                                branch_data['campaign_name'].isin(google_campaigns)
                            ]

                        # MÉTHODE 3 : Si toujours vide, prendre toutes les données Branch.io qui ne sont pas ASA
                        if google_branch.empty:
                            non_asa_branch = branch_data[
                                ~((branch_data['source'] == 'Apple Search Ads') |
                                  (branch_data['ad_partner'] == 'Apple Search Ads'))
                            ] if 'source' in branch_data.columns else branch_data

                            # Prendre une proportion basée sur les clics Google vs total
                            total_clicks_google = google_data['clicks'].sum()
                            total_clicks_all = total_clicks_google + (
                                asa_data['clicks'].sum() if not asa_data.empty else 0)
                            proportion = total_clicks_google / total_clicks_all if total_clicks_all > 0 else 0.5

                            google_branch = non_asa_branch.copy()

                        if not google_branch.empty:
                            # Filtrer les plateformes app
                            app_branch = google_branch[
                                google_branch['platform'].isin(['iOS', 'Android', 'App', 'IOS_APP', 'ANDROID_APP'])
                            ] if 'platform' in google_branch.columns else google_branch

                            if not app_branch.empty:
                                google_app_installs = app_branch['installs'].sum()
                                google_app_opens = app_branch['opens'].sum()
                                google_app_login = app_branch['login'].sum()
                                google_app_purchases = app_branch['purchases'].sum()
                                google_app_revenue = app_branch['revenue'].sum()

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

    # === TRAITEMENT APPLE SEARCH ADS ===
    if not asa_data.empty:
        if 'campaign_type' in asa_data.columns:
            asa_grouped = asa_data.groupby('campaign_type').agg({
                'campaign_name': 'nunique' if 'campaign_name' in asa_data.columns else lambda x: 1,
                'cost': 'sum',
                'impressions': 'sum',
                'clicks': 'sum'
            }).reset_index()

            for _, row in asa_grouped.iterrows():
                # ASA APP : Récupérer les données Branch.io
                asa_installs = 0
                asa_opens = 0
                asa_login = 0
                asa_purchases = 0
                asa_revenue = 0

                if not branch_data.empty:
                    # MÉTHODE 1 : Par source/ad_partner
                    asa_branch = branch_data[
                        (branch_data['source'] == 'Apple Search Ads') |
                        (branch_data['ad_partner'] == 'Apple Search Ads')
                        ] if 'source' in branch_data.columns else pd.DataFrame()

                    # MÉTHODE 2 : Si pas de résultat, essayer par nom de campagne
                    if asa_branch.empty and 'campaign_name' in branch_data.columns and 'campaign_name' in asa_data.columns:
                        asa_campaigns = asa_data[
                            'campaign_name'].unique() if 'campaign_name' in asa_data.columns else []
                        asa_branch = branch_data[
                            branch_data['campaign_name'].isin(asa_campaigns)
                        ]

                    # MÉTHODE 3 : Si toujours vide, prendre les données iOS par défaut (ASA = iOS)
                    if asa_branch.empty and 'platform' in branch_data.columns:
                        asa_branch = branch_data[
                            branch_data['platform'].isin(['iOS', 'IOS_APP'])
                        ]

                    if not asa_branch.empty:
                        asa_installs = asa_branch['installs'].sum()
                        asa_opens = asa_branch['opens'].sum()
                        asa_login = asa_branch['login'].sum()
                        asa_purchases = asa_branch['purchases'].sum()
                        asa_revenue = asa_branch['revenue'].sum()

                partner_rows.append({
                    'source': 'Apple Search Ads',
                    'campaign_type': row['campaign_type'],
                    'channel_type': 'app',
                    'nb_campaigns': row.get('campaign_name', 1),
                    'cost': row['cost'],
                    'impressions': row['impressions'],
                    'clicks': row['clicks'],
                    'installs': asa_installs,
                    'opens': asa_opens,
                    'login': asa_login,
                    'purchases': asa_purchases,
                    'revenue': asa_revenue
                })

    if not partner_rows:
        return pd.DataFrame()

    # Créer le DataFrame et calculer les métriques
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


def _render_partner_table(partner_analysis: pd.DataFrame):
    """Affiche le tableau des performances par partenaire"""

    # Séparer App et Web pour un affichage plus clair
    app_data = partner_analysis[partner_analysis['channel_type'] == 'app'].copy()
    web_data = partner_analysis[partner_analysis['channel_type'] == 'web'].copy()
    non_classified = partner_analysis[partner_analysis['channel_type'] == 'Non classifié'].copy()

    # === TABLEAU APP ===
    if not app_data.empty:
        st.markdown("#### 📱 Campagnes App")

        app_columns = [
            'source', 'campaign_type', 'nb_campaigns', 'cost', 'impressions', 'clicks',
            'installs', 'opens', 'login', 'purchases', 'revenue',
            'ctr', 'conversion_rate', 'open_rate', 'login_rate', 'purchase_rate_dl', 'cpa', 'roas'
        ]

        available_app_columns = [col for col in app_columns if col in app_data.columns]
        app_display = app_data[available_app_columns]

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

        st.dataframe(
            app_display,
            column_config=app_column_config,
            use_container_width=True,
            hide_index=True
        )

    # === TABLEAU WEB ===
    if not web_data.empty:
        st.markdown("#### 🌐 Campagnes Web")

        web_columns = [
            'source', 'campaign_type', 'nb_campaigns', 'cost', 'impressions', 'clicks',
            'purchases', 'revenue', 'ctr', 'conversion_rate', 'purchase_rate', 'cpa', 'roas'
        ]

        available_web_columns = [col for col in web_columns if col in web_data.columns]
        web_display = web_data[available_web_columns]

        web_column_config = {
            "source": st.column_config.TextColumn("Partenaire", width="medium"),
            "campaign_type": st.column_config.TextColumn("Type", width="small"),
            "nb_campaigns": st.column_config.NumberColumn("Nb Camp.", format="%d"),
            "cost": st.column_config.NumberColumn("Coût", format="%.2f €"),
            "impressions": st.column_config.NumberColumn("Impressions", format="%d"),
            "clicks": st.column_config.NumberColumn("Clics", format="%d"),
            "purchases": st.column_config.NumberColumn("Achats", format="%d"),
            "revenue": st.column_config.NumberColumn("Revenus", format="%.2f €"),
            "ctr": st.column_config.NumberColumn("CTR", format="%.2f%%"),
            "conversion_rate": st.column_config.NumberColumn("Taux Conv.", format="%.2f%%", help="Achats / Clics"),
            "purchase_rate": st.column_config.NumberColumn("Taux Achat", format="%.2f%%", help="Achats / Clics"),
            "cpa": st.column_config.NumberColumn("CPA", format="%.2f €"),
            "roas": st.column_config.NumberColumn("ROAS", format="%.2f")
        }

        st.dataframe(
            web_display,
            column_config=web_column_config,
            use_container_width=True,
            hide_index=True
        )

    # === TABLEAU NON CLASSIFIÉ ===
    if not non_classified.empty:
        st.markdown("#### ❓ Campagnes Non Classifiées")
        st.info("💡 Configurez vos campagnes pour les voir dans les tableaux App/Web ci-dessus")

        basic_columns = [
            'source', 'nb_campaigns', 'cost', 'impressions', 'clicks', 'installs', 'purchases', 'revenue', 'ctr', 'roas'
        ]

        available_basic_columns = [col for col in basic_columns if col in non_classified.columns]
        basic_display = non_classified[available_basic_columns]

        basic_column_config = {
            "source": st.column_config.TextColumn("Partenaire", width="medium"),
            "nb_campaigns": st.column_config.NumberColumn("Nb Camp.", format="%d"),
            "cost": st.column_config.NumberColumn("Coût", format="%.2f €"),
            "impressions": st.column_config.NumberColumn("Impressions", format="%d"),
            "clicks": st.column_config.NumberColumn("Clics", format="%d"),
            "installs": st.column_config.NumberColumn("Installs", format="%d"),
            "purchases": st.column_config.NumberColumn("Achats", format="%d"),
            "revenue": st.column_config.NumberColumn("Revenus", format="%.2f €"),
            "ctr": st.column_config.NumberColumn("CTR", format="%.2f%%"),
            "roas": st.column_config.NumberColumn("ROAS", format="%.2f")
        }

        st.dataframe(
            basic_display,
            column_config=basic_column_config,
            use_container_width=True,
            hide_index=True
        )

    # Bouton d'export
    if st.button("📥 Exporter les tableaux partenaires", key="export_partners_simple"):
        # Combiner tous les tableaux pour l'export
        all_data = pd.concat([app_data, web_data, non_classified], ignore_index=True)
        csv = all_data.to_csv(index=False)
        st.download_button(
            label="Télécharger CSV",
            data=csv,
            file_name="performance_partenaires_detaille.csv",
            mime="text/csv"
        )


def _render_raw_partner_data(google_data: pd.DataFrame, asa_data: pd.DataFrame):
    """Affiche les données brutes par partenaire en cas d'absence de données consolidées"""

    st.info("📊 Affichage simplifié basé sur les données brutes")

    # Tableau Google Ads
    if not google_data.empty:
        st.markdown("#### 🔍 Google Ads")

        google_summary = google_data.groupby('campaign_name').agg({
            'cost': 'sum',
            'impressions': 'sum',
            'clicks': 'sum',
            'purchases': 'sum',
            'revenue': 'sum'
        }).reset_index()

        # Calcul des métriques Google Ads
        google_summary['ctr'] = (google_summary['clicks'] / google_summary['impressions'] * 100).fillna(0)
        google_summary['conversion_rate'] = (google_summary['purchases'] / google_summary['clicks'] * 100).fillna(0)
        google_summary['cpa'] = (google_summary['cost'] / google_summary['purchases']).fillna(0)
        google_summary['roas'] = (google_summary['revenue'] / google_summary['cost']).fillna(0)

        st.dataframe(google_summary, use_container_width=True)

    # Tableau ASA
    if not asa_data.empty:
        st.markdown("#### 🍎 Apple Search Ads")

        asa_summary = asa_data.groupby('date' if 'campaign_name' not in asa_data.columns else 'campaign_name').agg({
            'cost': 'sum',
            'impressions': 'sum',
            'clicks': 'sum',
            'installs': 'sum' if 'installs' in asa_data.columns else 'new_downloads'
        }).reset_index()

        # Calcul des métriques ASA
        asa_summary['ctr'] = (asa_summary['clicks'] / asa_summary['impressions'] * 100).fillna(0)
        asa_summary['conversion_rate'] = (asa_summary['installs'] / asa_summary['clicks'] * 100).fillna(0)
        asa_summary['cpi'] = (asa_summary['cost'] / asa_summary['installs']).fillna(0)

        st.dataframe(asa_summary, use_container_width=True)