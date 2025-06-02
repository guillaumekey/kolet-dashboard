import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple


class DataProcessor:
    """Processeur de données pour l'analyse et la transformation avec logique métier Kolet"""

    def __init__(self):
        """Initialise le processeur de données"""
        pass

    def prepare_dashboard_data(self, df: pd.DataFrame, platforms: List[str] = None,
                               exclude_unpopulated: bool = True) -> Dict[str, pd.DataFrame]:
        """
        Prépare les données pour l'affichage dans le dashboard avec logique métier Kolet
        MODIFIÉ : Intègre la classification des campagnes pour les funnels

        Args:
            df: DataFrame avec les données brutes
            platforms: Liste des plateformes à inclure
            exclude_unpopulated: Exclure les données 'Unpopulated' de Branch.io

        Returns:
            Dictionnaire avec les DataFrames traités par source
        """
        if df.empty:
            return {'app': pd.DataFrame(), 'web': pd.DataFrame(), 'consolidated': pd.DataFrame()}

        print(f"🔍 DÉBUT - Données reçues: {len(df)} enregistrements")
        print(f"🔍 Installs totaux: {df['installs'].sum()}")

        # Filtrer les données unpopulated si demandé
        if exclude_unpopulated:
            data_before = len(df)
            installs_before = df['installs'].sum()
            df = df[~((df['source'] == 'Branch.io') & (df['campaign_name'] == 'Unpopulated'))]
            data_after = len(df)
            installs_after = df['installs'].sum()
            print(f"🔍 Filtrage Unpopulated: {data_before} → {data_after} enregistrements")
            print(f"🔍 Installs après Unpopulated: {installs_before} → {installs_after}")

        # Filtrer par plateformes si spécifié
        if platforms:
            data_before_platform = len(df)
            installs_before_platform = df['installs'].sum()
            df = df[df['platform'].isin(platforms)]
            data_after_platform = len(df)
            installs_after_platform = df['installs'].sum()
            print(f"🔍 Filtrage plateformes {platforms}: {data_before_platform} → {data_after_platform} enregistrements")
            print(f"🔍 Installs après plateformes: {installs_before_platform} → {installs_after_platform}")

        # Afficher les sources disponibles pour debug
        if not df.empty:
            sources = df['source'].value_counts()
            platforms_count = df['platform'].value_counts()
            print(f"📊 Sources disponibles: {sources.to_dict()}")
            print(f"📊 Plateformes disponibles: {platforms_count.to_dict()}")

        # Séparer les données par source (en tenant compte du mapping Branch.io)
        google_ads_data = df[df['source'].isin(['Google Ads', 'Google AdWords'])].copy()
        asa_data = df[df['source'].isin(['Apple Search Ads'])].copy()
        branch_data = df[df['source'] == 'Branch.io'].copy()

        print(f"🔍 Après séparation:")
        print(
            f"  • Google Ads: {len(google_ads_data)} enregistrements, {google_ads_data['installs'].sum() if not google_ads_data.empty else 0} installs")
        print(
            f"  • ASA: {len(asa_data)} enregistrements, {asa_data['installs'].sum() if not asa_data.empty else 0} installs")
        print(
            f"  • Branch.io: {len(branch_data)} enregistrements, {branch_data['installs'].sum() if not branch_data.empty else 0} installs")

        # Convertir les dates
        for data in [google_ads_data, asa_data, branch_data]:
            if not data.empty and 'date' in data.columns:
                data['date'] = pd.to_datetime(data['date'])

        # MODIFIÉ : Créer les données App et Web avec classification
        app_data = self._create_app_funnel_data_with_classification(asa_data, branch_data, google_ads_data)
        web_data = self._create_web_funnel_data_with_classification(google_ads_data)

        # Données consolidées pour les KPI globaux
        consolidated_data = self._create_consolidated_data(google_ads_data, asa_data, branch_data)

        # NOUVEAU : Données par type de campagne
        campaign_type_data = self._create_campaign_type_analysis(df)

        return {
            'app': app_data,
            'web': web_data,
            'consolidated': consolidated_data,
            'campaign_types': campaign_type_data,  # NOUVEAU
            'raw': {
                'google_ads': google_ads_data,
                'asa': asa_data,
                'branch': branch_data
            }
        }

    def _create_app_funnel_data_with_classification(self, asa_data: pd.DataFrame, branch_data: pd.DataFrame,
                                                    google_ads_data: pd.DataFrame) -> pd.DataFrame:
        """
        Crée les données du funnel App avec prise en compte de la classification des campagnes
        MODIFIÉ : Filtre les clics/impressions selon la classification (app seulement)

        Logique :
        - Impressions/Clics : ASA + Google Ads classifié "app"
        - Coûts : ASA + Google Ads classifié "app"
        - Installs/Opens/Logins/Purchases : Branch.io seulement
        """
        print(f"🔍 _create_app_funnel_data_with_classification:")
        print(f"  • ASA data: {len(asa_data)} lignes")
        print(f"  • Branch data: {len(branch_data)} lignes")
        print(f"  • Google Ads data: {len(google_ads_data)} lignes")

        if branch_data.empty:
            print("  ⚠️ Branch data vide, retour DataFrame vide")
            return pd.DataFrame()

        # Filtrer les données app de Branch.io
        app_branch = branch_data[
            ~branch_data['platform'].isin(['Web', 'WEB'])
        ].copy()

        print(f"  • Données app Branch après filtrage: {len(app_branch)} lignes")
        print(f"  • Installs app: {app_branch['installs'].sum() if not app_branch.empty else 0}")

        if app_branch.empty:
            print("  ⚠️ Aucune donnée app après filtrage")
            return pd.DataFrame()

        # Grouper Branch.io par date pour les métriques post-install
        branch_agg_dict = {
            'installs': 'sum',
            'opens': 'sum',
            'revenue': 'sum',
            'purchases': 'sum'
        }

        if 'login' in app_branch.columns:
            branch_agg_dict['login'] = 'sum'

        app_funnel = app_branch.groupby('date').agg(branch_agg_dict).reset_index()

        print(f"  • Après groupement Branch.io par date: {len(app_funnel)} lignes")
        print(f"  • Total installs agrégé: {app_funnel['installs'].sum()}")

        # Initialiser les colonnes publicitaires
        app_funnel['impressions'] = 0
        app_funnel['clicks'] = 0
        app_funnel['cost'] = 0

        # MODIFIÉ : Ajouter ASA (toujours app)
        if not asa_data.empty:
            asa_agg = asa_data.groupby('date').agg({
                'impressions': 'sum',
                'clicks': 'sum',
                'cost': 'sum'
            }).reset_index()

            print(f"  • ASA data agrégée: {len(asa_agg)} lignes")
            print(f"  • ASA impressions: {asa_agg['impressions'].sum():,}")
            print(f"  • ASA clicks: {asa_agg['clicks'].sum():,}")
            print(f"  • ASA costs: {asa_agg['cost'].sum():.2f}€")

            # Merger avec les données app
            app_funnel = app_funnel.merge(asa_agg, on='date', how='outer', suffixes=('', '_asa'))
            app_funnel['impressions'] = app_funnel['impressions'].fillna(0) + app_funnel['impressions_asa'].fillna(0)
            app_funnel['clicks'] = app_funnel['clicks'].fillna(0) + app_funnel['clicks_asa'].fillna(0)
            app_funnel['cost'] = app_funnel['cost'].fillna(0) + app_funnel['cost_asa'].fillna(0)

            # Nettoyer les colonnes temporaires
            app_funnel = app_funnel.drop(columns=[col for col in app_funnel.columns if col.endswith('_asa')])

        # NOUVEAU : Ajouter Google Ads classifié "app"
        if not google_ads_data.empty:
            google_app_data = google_ads_data[
                google_ads_data['channel_type'] == 'app'
                ].copy()

            if not google_app_data.empty:
                google_app_agg = google_app_data.groupby('date').agg({
                    'impressions': 'sum',
                    'clicks': 'sum',
                    'cost': 'sum'
                }).reset_index()

                print(f"  • Google Ads App classifiées: {len(google_app_agg)} lignes")
                print(f"  • Google App impressions: {google_app_agg['impressions'].sum():,}")
                print(f"  • Google App clicks: {google_app_agg['clicks'].sum():,}")
                print(f"  • Google App costs: {google_app_agg['cost'].sum():.2f}€")

                # Merger avec les données app
                app_funnel = app_funnel.merge(google_app_agg, on='date', how='outer', suffixes=('', '_google'))
                app_funnel['impressions'] = app_funnel['impressions'].fillna(0) + app_funnel[
                    'impressions_google'].fillna(0)
                app_funnel['clicks'] = app_funnel['clicks'].fillna(0) + app_funnel['clicks_google'].fillna(0)
                app_funnel['cost'] = app_funnel['cost'].fillna(0) + app_funnel['cost_google'].fillna(0)

                # Nettoyer les colonnes temporaires
                app_funnel = app_funnel.drop(columns=[col for col in app_funnel.columns if col.endswith('_google')])

        # Remplir les valeurs manquantes
        app_funnel = app_funnel.fillna(0)

        # Gérer la colonne login
        if 'login' not in app_funnel.columns:
            app_funnel['login'] = (app_funnel['opens'] * 0.25).round().astype(int)
            print(f"  • Logins estimés: {app_funnel['login'].sum():,}")
        else:
            print(f"  • Logins réels: {app_funnel['login'].sum():,}")

        # Calculer les métriques du funnel app
        app_funnel = self._calculate_app_funnel_metrics(app_funnel)
        app_funnel['channel'] = 'App'

        print(f"  ✅ Funnel app créé: {len(app_funnel)} lignes, {app_funnel['installs'].sum()} installs")
        print(f"  📊 Totaux finaux App:")
        print(f"    - Impressions: {app_funnel['impressions'].sum():,}")
        print(f"    - Clics: {app_funnel['clicks'].sum():,}")
        print(f"    - Installs: {app_funnel['installs'].sum():,}")
        print(f"    - Opens: {app_funnel['opens'].sum():,}")

        return app_funnel

    def _create_web_funnel_data_with_classification(self, google_ads_data: pd.DataFrame) -> pd.DataFrame:
        """
        Crée les données du funnel Web avec prise en compte de la classification des campagnes
        MODIFIÉ : Filtre seulement les campagnes classifiées "web"

        Logique :
        - Toutes les données viennent de Google Ads classifié "web"
        """
        if google_ads_data.empty:
            return pd.DataFrame()

        # MODIFIÉ : Filtrer seulement les campagnes classifiées "web"
        web_google_ads = google_ads_data[
            (google_ads_data['channel_type'] == 'web') |
            (google_ads_data['channel_type'].isna())  # Inclure les non-classifiées par défaut comme web
            ].copy()

        if web_google_ads.empty:
            print("  ⚠️ Aucune campagne Google Ads classifiée 'web'")
            return pd.DataFrame()

        print(f"  • Google Ads Web classifiées: {len(web_google_ads)} lignes")
        print(f"  • Google Web impressions: {web_google_ads['impressions'].sum():,}")
        print(f"  • Google Web clicks: {web_google_ads['clicks'].sum():,}")

        # Grouper par date pour le funnel web
        web_funnel = web_google_ads.groupby('date').agg({
            'impressions': 'sum',
            'clicks': 'sum',
            'cost': 'sum',
            'purchases': 'sum',
            'revenue': 'sum'
        }).reset_index()

        # Ajouter add_to_cart si pas présent (estimation)
        if 'add_to_cart' not in web_funnel.columns:
            web_funnel['add_to_cart'] = (web_funnel['purchases'] * 3).round().astype(int)

        # Calculer les métriques du funnel web
        web_funnel = self._calculate_web_funnel_metrics(web_funnel)
        web_funnel['channel'] = 'Web'

        print(f"  ✅ Funnel web créé: {len(web_funnel)} lignes")
        print(f"  📊 Totaux finaux Web:")
        print(f"    - Impressions: {web_funnel['impressions'].sum():,}")
        print(f"    - Clics: {web_funnel['clicks'].sum():,}")
        print(f"    - Purchases: {web_funnel['purchases'].sum():,}")

        return web_funnel

    def _create_app_funnel_data(self, asa_data: pd.DataFrame, branch_data: pd.DataFrame) -> pd.DataFrame:
        """
        Crée les données du funnel App : Impressions -> Clics -> Installs -> Opens -> Logins -> Purchases
        VERSION LEGACY - Conservée pour compatibilité

        MODIFIÉ : Logique corrigée pour clics et impressions
        - Impressions/Clics : ASA seulement (données publicitaires fiables)
        - Coûts : ASA seulement
        - Installs/Opens/Logins/Purchases : Branch.io seulement
        """
        print(f"🔍 _create_app_funnel_data:")
        print(f"  • ASA data: {len(asa_data)} lignes")
        print(f"  • Branch data: {len(branch_data)} lignes")

        if branch_data.empty:
            print("  ⚠️ Branch data vide, retour DataFrame vide")
            return pd.DataFrame()

        # Debug: analyser les plateformes dans branch_data
        print(f"  • Plateformes Branch disponibles: {branch_data['platform'].unique()}")

        # Filtrer les données app de Branch.io - ÉLARGI
        # Inclure TOUTES les plateformes sauf Web explicite
        app_branch = branch_data[
            ~branch_data['platform'].isin(['Web', 'WEB'])
        ].copy()

        print(f"  • Données app après filtrage: {len(app_branch)} lignes")
        print(f"  • Installs app: {app_branch['installs'].sum() if not app_branch.empty else 0}")

        if app_branch.empty:
            print("  ⚠️ Aucune donnée app après filtrage")
            return pd.DataFrame()

        # Debug: répartition par plateforme
        if not app_branch.empty:
            platform_breakdown = app_branch.groupby('platform')['installs'].sum()
            print(f"  • Répartition par plateforme:")
            for platform, installs in platform_breakdown.items():
                print(f"    - {platform}: {installs:,} installs")

        # MODIFIÉ : Grouper Branch.io par date pour les métriques post-install
        branch_agg_dict = {
            'installs': 'sum',  # Branch.io pour installs
            'opens': 'sum',  # Branch.io pour opens
            'revenue': 'sum',  # Branch.io pour revenue
            'purchases': 'sum'  # Branch.io pour purchases
        }

        # Ajouter les logins si la colonne existe
        if 'login' in app_branch.columns:
            branch_agg_dict['login'] = 'sum'

        app_funnel = app_branch.groupby('date').agg(branch_agg_dict).reset_index()

        print(f"  • Après groupement Branch.io par date: {len(app_funnel)} lignes")
        print(f"  • Total installs agrégé: {app_funnel['installs'].sum()}")

        # MODIFIÉ : Ajouter les données ASA (impressions, clics, coûts)
        if not asa_data.empty:
            asa_agg = asa_data.groupby('date').agg({
                'impressions': 'sum',
                'clicks': 'sum',
                'cost': 'sum'
            }).reset_index()

            print(f"  • ASA data agrégée: {len(asa_agg)} lignes")
            print(f"  • ASA impressions: {asa_agg['impressions'].sum():,}")
            print(f"  • ASA clicks: {asa_agg['clicks'].sum():,}")
            print(f"  • ASA costs: {asa_agg['cost'].sum():.2f}€")

            # Merger avec les données Branch.io
            app_funnel = app_funnel.merge(asa_agg, on='date', how='outer')

            # Remplir les valeurs manquantes
            app_funnel = app_funnel.fillna(0)

            print(f"  • Après merge ASA: {len(app_funnel)} lignes")
        else:
            print("  ⚠️ Aucune donnée ASA - ajout de colonnes vides")
            app_funnel['impressions'] = 0
            app_funnel['clicks'] = 0
            app_funnel['cost'] = 0

        # Gérer la colonne login
        if 'login' not in app_funnel.columns:
            # Estimer les logins comme un pourcentage des opens (estimation 25%)
            app_funnel['login'] = (app_funnel['opens'] * 0.25).round().astype(int)
            print(f"  • Logins estimés: {app_funnel['login'].sum():,}")
        else:
            print(f"  • Logins réels: {app_funnel['login'].sum():,}")

        # Calculer les métriques du funnel app
        app_funnel = self._calculate_app_funnel_metrics(app_funnel)
        app_funnel['channel'] = 'App'

        print(f"  ✅ Funnel app créé: {len(app_funnel)} lignes, {app_funnel['installs'].sum()} installs")
        print(f"  📊 Totaux finaux App:")
        print(f"    - Impressions: {app_funnel['impressions'].sum():,}")
        print(f"    - Clics: {app_funnel['clicks'].sum():,}")
        print(f"    - Installs: {app_funnel['installs'].sum():,}")
        print(f"    - Opens: {app_funnel['opens'].sum():,}")

        return app_funnel

    def _create_web_funnel_data(self, google_ads_data: pd.DataFrame) -> pd.DataFrame:
        """
        Crée les données du funnel Web : Impressions -> Clics -> Add to Cart -> Purchases

        Logique :
        - Toutes les données viennent de Google Ads
        """
        if google_ads_data.empty:
            return pd.DataFrame()

        # Grouper par date pour le funnel web
        web_funnel = google_ads_data.groupby('date').agg({
            'impressions': 'sum',
            'clicks': 'sum',
            'cost': 'sum',
            'purchases': 'sum',
            'revenue': 'sum'
        }).reset_index()

        # Ajouter add_to_cart si pas présent (estimation)
        if 'add_to_cart' not in web_funnel.columns:
            # Estimer add_to_cart comme 3x les purchases (taux de conversion estimé 33%)
            web_funnel['add_to_cart'] = (web_funnel['purchases'] * 3).round().astype(int)

        # Calculer les métriques du funnel web
        web_funnel = self._calculate_web_funnel_metrics(web_funnel)
        web_funnel['channel'] = 'Web'

        return web_funnel

    def _create_campaign_type_analysis(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        CORRIGÉ : Crée l'analyse par type de campagne avec données correctes

        Args:
            df: DataFrame avec les données consolidées

        Returns:
            DataFrame avec les performances par type de campagne
        """
        print(f"🔍 _create_campaign_type_analysis:")
        print(f"  • Données totales: {len(df)} lignes")

        if df.empty:
            return pd.DataFrame()

        # Vérifier si on a des classifications
        if 'campaign_type' not in df.columns:
            print("  ⚠️ Aucune classification de campagne trouvée")
            return pd.DataFrame()

        # Filtrer les campagnes classifiées
        classified_data = df[df['campaign_type'].notna()].copy()

        if classified_data.empty:
            print("  ⚠️ Aucune campagne classifiée")
            return pd.DataFrame()

        print(f"  • Campagnes classifiées: {len(classified_data)} lignes")

        # CORRECTION MAJEURE : Éviter le double comptage
        # Ne compter les coûts/impressions/clics que pour Google Ads et ASA (sources publicitaires)
        advertising_sources = ['Google Ads', 'Google AdWords', 'Apple Search Ads']

        # Séparer les données publicitaires des données de conversion
        advertising_data = classified_data[classified_data['source'].isin(advertising_sources)].copy()
        conversion_data = classified_data.copy()  # Toutes les données pour les conversions

        print(f"  • Données publicitaires (coûts/clics): {len(advertising_data)} lignes")
        print(f"  • Sources publicitaires: {advertising_data['source'].unique()}")

        # Agrégation des données publicitaires (coûts, impressions, clics)
        advertising_agg = advertising_data.groupby(['campaign_type', 'channel_type']).agg({
            'cost': 'sum',
            'impressions': 'sum',
            'clicks': 'sum',
            'campaign_name': 'nunique'
        }).reset_index()

        # Agrégation des données de conversion (installs, purchases, etc.)
        conversion_agg = conversion_data.groupby(['campaign_type', 'channel_type']).agg({
            'installs': 'sum',
            'purchases': 'sum',
            'revenue': 'sum',
            'opens': 'sum',
            'login': 'sum'
        }).reset_index()

        # NOUVEAU : Ajouter add_to_cart pour les campagnes web
        if 'add_to_cart' in conversion_data.columns:
            web_conversion_agg = conversion_data[conversion_data['channel_type'] == 'web'].groupby(
                ['campaign_type', 'channel_type']).agg({
                'add_to_cart': 'sum'
            }).reset_index()
            conversion_agg = conversion_agg.merge(web_conversion_agg, on=['campaign_type', 'channel_type'], how='left')
        else:
            # Estimer add_to_cart pour le web (3x les purchases)
            conversion_agg['add_to_cart'] = 0
            web_mask = conversion_agg['channel_type'] == 'web'
            conversion_agg.loc[web_mask, 'add_to_cart'] = conversion_agg.loc[web_mask, 'purchases'] * 3

        conversion_agg['add_to_cart'] = conversion_agg['add_to_cart'].fillna(0)

        # Merger les données publicitaires et de conversion
        campaign_analysis = advertising_agg.merge(conversion_agg, on=['campaign_type', 'channel_type'], how='outer')

        # Remplir les valeurs manquantes
        campaign_analysis = campaign_analysis.fillna(0)

        # Renommer la colonne campaign_name
        campaign_analysis = campaign_analysis.rename(columns={'campaign_name': 'nb_campaigns'})

        print(f"  • Coût total calculé: {campaign_analysis['cost'].sum():.2f}€")
        print(f"  • Clics total calculé: {campaign_analysis['clicks'].sum():,}")
        print(f"  • Installs total: {campaign_analysis['installs'].sum():,}")
        print(f"  • Purchases total: {campaign_analysis['purchases'].sum():,}")

        # CORRECTION : Calculer les métriques avec les bonnes formules
        campaign_analysis['ctr'] = self._safe_divide(campaign_analysis['clicks'],
                                                     campaign_analysis['impressions']) * 100

        # CORRECTION : Conversion rate = installs / clicks pour app, purchases / clicks pour web
        campaign_analysis['conversion_rate'] = 0.0

        # Pour les campagnes app : conversion_rate = installs / clicks
        app_mask = campaign_analysis['channel_type'] == 'app'
        campaign_analysis.loc[app_mask, 'conversion_rate'] = self._safe_divide(
            campaign_analysis.loc[app_mask, 'installs'],
            campaign_analysis.loc[app_mask, 'clicks']
        ) * 100

        # Pour les campagnes web : conversion_rate = purchases / clicks
        web_mask = campaign_analysis['channel_type'] == 'web'
        campaign_analysis.loc[web_mask, 'conversion_rate'] = self._safe_divide(
            campaign_analysis.loc[web_mask, 'purchases'],
            campaign_analysis.loc[web_mask, 'clicks']
        ) * 100

        # NOUVEAU : Taux d'achat DL = purchases / installs (pour app seulement)
        campaign_analysis['purchase_rate_dl'] = 0.0
        campaign_analysis.loc[app_mask, 'purchase_rate_dl'] = self._safe_divide(
            campaign_analysis.loc[app_mask, 'purchases'],
            campaign_analysis.loc[app_mask, 'installs']
        ) * 100

        # CORRECTION : Purchase rate = purchases / clicks (pour web)
        campaign_analysis['purchase_rate'] = 0.0
        campaign_analysis.loc[web_mask, 'purchase_rate'] = self._safe_divide(
            campaign_analysis.loc[web_mask, 'purchases'],
            campaign_analysis.loc[web_mask, 'clicks']
        ) * 100

        # Pour app, purchase_rate = purchases / installs
        campaign_analysis.loc[app_mask, 'purchase_rate'] = self._safe_divide(
            campaign_analysis.loc[app_mask, 'purchases'],
            campaign_analysis.loc[app_mask, 'installs']
        ) * 100

        # NOUVEAU : Métriques spécifiques par canal
        # App : open_rate = opens / installs, login_rate = logins / installs
        campaign_analysis['open_rate'] = 0.0
        campaign_analysis['login_rate'] = 0.0

        campaign_analysis.loc[app_mask, 'open_rate'] = self._safe_divide(
            campaign_analysis.loc[app_mask, 'opens'],
            campaign_analysis.loc[app_mask, 'installs']
        ) * 100

        campaign_analysis.loc[app_mask, 'login_rate'] = self._safe_divide(
            campaign_analysis.loc[app_mask, 'login'],
            campaign_analysis.loc[app_mask, 'installs']
        ) * 100

        # Web : cart_rate = add_to_cart / clicks, cart_to_purchase = purchases / add_to_cart
        campaign_analysis['cart_rate'] = 0.0
        campaign_analysis['cart_to_purchase_rate'] = 0.0

        campaign_analysis.loc[web_mask, 'cart_rate'] = self._safe_divide(
            campaign_analysis.loc[web_mask, 'add_to_cart'],
            campaign_analysis.loc[web_mask, 'clicks']
        ) * 100

        campaign_analysis.loc[web_mask, 'cart_to_purchase_rate'] = self._safe_divide(
            campaign_analysis.loc[web_mask, 'purchases'],
            campaign_analysis.loc[web_mask, 'add_to_cart']
        ) * 100

        # Autres métriques économiques
        campaign_analysis['cpc'] = self._safe_divide(campaign_analysis['cost'], campaign_analysis['clicks'])

        # CPA différent selon le canal
        campaign_analysis['cpa'] = 0.0
        campaign_analysis.loc[app_mask, 'cpa'] = self._safe_divide(
            campaign_analysis.loc[app_mask, 'cost'],
            campaign_analysis.loc[app_mask, 'installs']
        )
        campaign_analysis.loc[web_mask, 'cpa'] = self._safe_divide(
            campaign_analysis.loc[web_mask, 'cost'],
            campaign_analysis.loc[web_mask, 'purchases']
        )

        campaign_analysis['roas'] = self._safe_divide(campaign_analysis['revenue'], campaign_analysis['cost'])
        campaign_analysis['revenue_per_install'] = self._safe_divide(campaign_analysis['revenue'],
                                                                     campaign_analysis['installs'])

        print(f"  • Types de campagnes analysés: {campaign_analysis['campaign_type'].unique()}")
        print(f"  • Canaux analysés: {campaign_analysis['channel_type'].unique()}")

        # Debug par ligne
        for _, row in campaign_analysis.iterrows():
            print(
                f"  📊 {row['campaign_type']}-{row['channel_type']}: {row['clicks']:.0f} clics, {row['purchases']:.0f} achats, taux: {row['purchase_rate']:.2f}%")

        return campaign_analysis

    def get_campaign_type_summary(self, campaign_analysis: pd.DataFrame) -> Dict[str, Any]:
        """
        CORRIGÉ : Génère un résumé des performances par type de campagne

        Args:
            campaign_analysis: DataFrame avec l'analyse par type de campagne

        Returns:
            Dictionnaire avec le résumé
        """
        if campaign_analysis.empty:
            return {}

        summary = {}

        for campaign_type in campaign_analysis['campaign_type'].unique():
            type_data = campaign_analysis[campaign_analysis['campaign_type'] == campaign_type]

            # Agrégation totale pour ce type
            total_data = type_data.agg({
                'cost': 'sum',
                'impressions': 'sum',
                'clicks': 'sum',
                'installs': 'sum',
                'purchases': 'sum',
                'revenue': 'sum',
                'nb_campaigns': 'sum'
            })

            # Métriques calculées
            summary[campaign_type] = {
                'total_cost': total_data['cost'],
                'total_impressions': total_data['impressions'],
                'total_clicks': total_data['clicks'],
                'total_installs': total_data['installs'],
                'total_purchases': total_data['purchases'],
                'total_revenue': total_data['revenue'],
                'nb_campaigns': total_data['nb_campaigns'],
                'ctr': self._safe_divide(total_data['clicks'], total_data['impressions']) * 100,
                'conversion_rate': self._safe_divide(total_data['installs'], total_data['clicks']) * 100,
                'purchase_rate': self._safe_divide(total_data['purchases'], total_data['installs']) * 100,
                'cpa': self._safe_divide(total_data['cost'], total_data['installs']),
                'roas': self._safe_divide(total_data['revenue'], total_data['cost']),
                'cost_share': 0  # Sera calculé plus tard
                # SUPPRESSION du performance_score
            }

        # Calculer les parts de budget
        total_cost = sum(data['total_cost'] for data in summary.values())
        for campaign_type in summary:
            if total_cost > 0:
                summary[campaign_type]['cost_share'] = (summary[campaign_type]['total_cost'] / total_cost) * 100

        return summary

    def get_campaign_type_insights(self, summary: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        NOUVEAU : Génère des insights sur les performances par type de campagne

        Args:
            summary: Résumé des performances par type

        Returns:
            Liste d'insights
        """
        insights = []

        if not summary:
            return insights

        # Trouver le meilleur et le pire en ROAS
        roas_ranking = sorted(summary.items(), key=lambda x: x[1]['roas'], reverse=True)

        if len(roas_ranking) >= 2:
            best_roas = roas_ranking[0]
            worst_roas = roas_ranking[-1]

            insights.append({
                'type': 'success',
                'title': f'Meilleur ROAS: {best_roas[0].title()}',
                'message': f'ROAS de {best_roas[1]["roas"]:.2f} avec {best_roas[1]["nb_campaigns"]:.0f} campagnes'
            })

            if best_roas[1]['roas'] > worst_roas[1]['roas'] * 1.5:
                insights.append({
                    'type': 'warning',
                    'title': 'Écart de performance important',
                    'message': f'{best_roas[0].title()} performe {(best_roas[1]["roas"] / worst_roas[1]["roas"]):.1f}x mieux que {worst_roas[0].title()}'
                })

        # Analyse du budget allocation
        budget_ranking = sorted(summary.items(), key=lambda x: x[1]['cost_share'], reverse=True)

        if budget_ranking:
            biggest_spender = budget_ranking[0]
            insights.append({
                'type': 'info',
                'title': 'Répartition budget',
                'message': f'{biggest_spender[0].title()} représente {biggest_spender[1]["cost_share"]:.0f}% du budget total'
            })

        # Recommandations d'optimisation
        for campaign_type, data in summary.items():
            if data['roas'] < 1.5 and data['cost_share'] > 30:
                insights.append({
                    'type': 'warning',
                    'title': f'Optimisation {campaign_type.title()}',
                    'message': f'ROAS faible ({data["roas"]:.2f}) malgré {data["cost_share"]:.0f}% du budget'
                })

            if data['conversion_rate'] < 5 and data['total_clicks'] > 1000:
                insights.append({
                    'type': 'info',
                    'title': f'Conversion {campaign_type.title()}',
                    'message': f'Taux de conversion à améliorer: {data["conversion_rate"]:.1f}%'
                })

        return insights

    def _create_consolidated_data(self, google_ads_data: pd.DataFrame,
                                  asa_data: pd.DataFrame, branch_data: pd.DataFrame) -> pd.DataFrame:
        """
        CORRIGÉ : Crée les données consolidées pour les KPI globaux avec logique de coûts corrigée

        LOGIQUE CORRECTE :
        - Impressions/Clics : Google Ads + ASA seulement
        - Coûts : Google Ads + ASA seulement (PAS Branch.io car Branch.io n'a pas de coûts propres)
        - Installs : Branch.io seulement (TOUTES les plateformes)
        - Purchases : Branch.io (app) + Google Ads (web)
        """
        print(f"🔍 _create_consolidated_data:")
        print(f"  • Google Ads: {len(google_ads_data)} lignes")
        print(f"  • ASA: {len(asa_data)} lignes")
        print(f"  • Branch: {len(branch_data)} lignes")

        all_dates = set()

        # Collecter toutes les dates
        for data in [google_ads_data, asa_data, branch_data]:
            if not data.empty:
                all_dates.update(data['date'].dt.strftime('%Y-%m-%d'))

        if not all_dates:
            return pd.DataFrame()

        consolidated = pd.DataFrame({'date': sorted(list(all_dates))})
        consolidated['date'] = pd.to_datetime(consolidated['date'])

        # CORRECTION : Coûts uniquement Google Ads + ASA (pas Branch.io)
        cost_data = []
        if not google_ads_data.empty:
            google_costs = google_ads_data.groupby('date')['cost'].sum()
            cost_data.append(google_costs)
            print(f"  • Google Ads costs: {google_costs.sum():.2f}€")
        if not asa_data.empty:
            asa_costs = asa_data.groupby('date')['cost'].sum()
            cost_data.append(asa_costs)
            print(f"  • ASA costs: {asa_costs.sum():.2f}€")

        if cost_data:
            total_costs = pd.concat(cost_data).groupby(level=0).sum()
            consolidated = consolidated.merge(total_costs.reset_index(), on='date', how='left')
            consolidated['cost'] = consolidated['cost'].fillna(0)
            print(f"  • Total costs: {consolidated['cost'].sum():.2f}€")
        else:
            consolidated['cost'] = 0

        # Impressions et Clics : Google Ads + ASA seulement
        print(f"  📊 Calcul impressions/clics - Sources publicitaires uniquement:")

        # Impressions
        impression_data = []
        if not google_ads_data.empty:
            google_impressions = google_ads_data.groupby('date')['impressions'].sum()
            impression_data.append(google_impressions)
            print(f"  • Google Ads impressions: {google_impressions.sum():,}")
        if not asa_data.empty:
            asa_impressions = asa_data.groupby('date')['impressions'].sum()
            impression_data.append(asa_impressions)
            print(f"  • ASA impressions: {asa_impressions.sum():,}")

        if impression_data:
            total_impressions = pd.concat(impression_data).groupby(level=0).sum()
            consolidated = consolidated.merge(total_impressions.reset_index(), on='date', how='left')
            consolidated['impressions'] = consolidated['impressions'].fillna(0)
            print(f"  • Total impressions: {consolidated['impressions'].sum():,}")
        else:
            consolidated['impressions'] = 0

        # Clics
        click_data = []
        if not google_ads_data.empty:
            google_clicks = google_ads_data.groupby('date')['clicks'].sum()
            click_data.append(google_clicks)
            print(f"  • Google Ads clicks: {google_clicks.sum():,}")
        if not asa_data.empty:
            asa_clicks = asa_data.groupby('date')['clicks'].sum()
            click_data.append(asa_clicks)
            print(f"  • ASA clicks: {asa_clicks.sum():,}")

        if click_data:
            total_clicks = pd.concat(click_data).groupby(level=0).sum()
            consolidated = consolidated.merge(total_clicks.reset_index(), on='date', how='left')
            consolidated['clicks'] = consolidated['clicks'].fillna(0)
            print(f"  • Total clicks: {consolidated['clicks'].sum():,}")
        else:
            consolidated['clicks'] = 0

        # Installs : Branch.io seulement (TOUTES plateformes)
        if not branch_data.empty:
            branch_installs = branch_data.groupby('date')['installs'].sum()
            print(f"  • Branch installs total: {branch_installs.sum():,}")
            consolidated = consolidated.merge(branch_installs.reset_index(), on='date', how='left')
            consolidated['installs'] = consolidated['installs'].fillna(0)
        else:
            consolidated['installs'] = 0
            print("  ⚠️ Aucun install Branch.io")

        # Opens et Logins : Branch.io seulement
        for metric in ['opens', 'login']:
            if not branch_data.empty and metric in branch_data.columns:
                branch_metric = branch_data.groupby('date')[metric].sum()
                consolidated = consolidated.merge(branch_metric.reset_index(), on='date', how='left')
                consolidated[metric] = consolidated[metric].fillna(0)
                print(f"  • Total {metric}: {consolidated[metric].sum():,}")
            else:
                consolidated[metric] = 0
                print(f"  • {metric}: Aucune donnée trouvée")

        # Purchases : Branch.io + Google Ads
        purchase_data = []
        if not branch_data.empty:
            branch_purchases = branch_data.groupby('date')['purchases'].sum()
            purchase_data.append(branch_purchases)
            print(f"  • Branch purchases: {branch_purchases.sum():,}")

        if not google_ads_data.empty:
            google_purchases = google_ads_data.groupby('date')['purchases'].sum()
            purchase_data.append(google_purchases)
            print(f"  • Google purchases: {google_purchases.sum():,}")

        if purchase_data:
            total_purchases = pd.concat(purchase_data).groupby(level=0).sum()
            consolidated = consolidated.merge(total_purchases.reset_index(), on='date', how='left')
            consolidated['purchases'] = consolidated['purchases'].fillna(0)
            print(f"  • Total purchases: {consolidated['purchases'].sum():,}")
        else:
            consolidated['purchases'] = 0

        # Revenue : même logique que purchases
        revenue_data = []
        if not branch_data.empty:
            branch_revenue = branch_data.groupby('date')['revenue'].sum()
            revenue_data.append(branch_revenue)
            print(f"  • Branch revenue: ${branch_revenue.sum():,.2f}")

        if not google_ads_data.empty:
            google_revenue = google_ads_data.groupby('date')['revenue'].sum()
            revenue_data.append(google_revenue)
            print(f"  • Google revenue: ${google_revenue.sum():,.2f}")

        if revenue_data:
            total_revenue = pd.concat(revenue_data).groupby(level=0).sum()
            consolidated = consolidated.merge(total_revenue.reset_index(), on='date', how='left')
            consolidated['revenue'] = consolidated['revenue'].fillna(0)
            print(f"  • Total revenue: ${consolidated['revenue'].sum():,.2f}")
        else:
            consolidated['revenue'] = 0

        # Calculer les métriques globales
        consolidated = self._calculate_global_metrics(consolidated)

        print(f"  ✅ Consolidated créé: {len(consolidated)} lignes, {consolidated['installs'].sum():,} installs")
        print(f"  💰 Coût total consolidé: {consolidated['cost'].sum():.2f}€")

        return consolidated

    def _calculate_app_funnel_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule les métriques du funnel App"""
        data = df.copy()

        # Taux de passage du funnel App
        data['ctr'] = self._safe_divide(data['clicks'], data['impressions']) * 100  # Impressions -> Clics
        data['click_to_install_rate'] = self._safe_divide(data['installs'], data['clicks']) * 100  # Clics -> Installs
        data['install_to_open_rate'] = self._safe_divide(data['opens'], data['installs']) * 100  # Installs -> Opens
        data['open_to_login_rate'] = self._safe_divide(data['login'], data['opens']) * 100  # Opens -> Logins
        data['login_to_purchase_rate'] = self._safe_divide(data['purchases'],
                                                           data['login']) * 100  # Logins -> Purchases

        # Métriques globales
        data['overall_conversion_rate'] = self._safe_divide(data['installs'], data['impressions']) * 100
        data['purchase_conversion_rate'] = self._safe_divide(data['purchases'], data['installs']) * 100

        # Métriques économiques
        data['cpc'] = self._safe_divide(data['cost'], data['clicks'])
        data['cpa'] = self._safe_divide(data['cost'], data['installs'])
        data['cpm'] = self._safe_divide(data['cost'], data['impressions']) * 1000
        data['roas'] = self._safe_divide(data['revenue'], data['cost'])
        data['revenue_per_install'] = self._safe_divide(data['revenue'], data['installs'])

        return data

    def _calculate_web_funnel_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule les métriques du funnel Web"""
        data = df.copy()

        # Taux de passage du funnel Web
        data['ctr'] = self._safe_divide(data['clicks'], data['impressions']) * 100  # Impressions -> Clics
        data['click_to_cart_rate'] = self._safe_divide(data['add_to_cart'],
                                                       data['clicks']) * 100  # Clics -> Add to Cart
        data['cart_to_purchase_rate'] = self._safe_divide(data['purchases'],
                                                          data['add_to_cart']) * 100  # Add to Cart -> Purchases

        # Métriques globales
        data['overall_conversion_rate'] = self._safe_divide(data['purchases'], data['impressions']) * 100
        data['purchase_conversion_rate'] = self._safe_divide(data['purchases'], data['clicks']) * 100

        # Métriques économiques
        data['cpc'] = self._safe_divide(data['cost'], data['clicks'])
        data['cpa'] = self._safe_divide(data['cost'], data['purchases'])  # Pour web, CPA = cost per purchase
        data['cpm'] = self._safe_divide(data['cost'], data['impressions']) * 1000
        data['roas'] = self._safe_divide(data['revenue'], data['cost'])
        data['revenue_per_purchase'] = self._safe_divide(data['revenue'], data['purchases'])

        return data

    def _calculate_global_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule les métriques globales consolidées"""
        data = df.copy()

        # Métriques de base
        data['ctr'] = self._safe_divide(data['clicks'], data['impressions']) * 100
        data['conversion_rate'] = self._safe_divide(data['installs'], data['clicks']) * 100
        data['purchase_rate'] = self._safe_divide(data['purchases'], data['installs']) * 100

        # Métriques économiques
        data['cpc'] = self._safe_divide(data['cost'], data['clicks'])
        data['cpa'] = self._safe_divide(data['cost'], data['installs'])
        data['cpm'] = self._safe_divide(data['cost'], data['impressions']) * 1000
        data['roas'] = self._safe_divide(data['revenue'], data['cost'])

        return data

    def _safe_divide(self, numerator, denominator):
        """Division sécurisée qui évite la division par zéro"""
        return np.where(denominator != 0, numerator / denominator, 0)

    def calculate_funnel_summary(self, app_data: pd.DataFrame, web_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Calcule le résumé des funnels App vs Web
        """
        summary = {
            'app': self._calculate_funnel_totals(app_data, 'app'),
            'web': self._calculate_funnel_totals(web_data, 'web')
        }

        return summary

    def _calculate_funnel_totals(self, data: pd.DataFrame, channel: str) -> Dict[str, Any]:
        """Calcule les totaux pour un funnel donné"""
        if data.empty:
            return {}

        totals = {
            'impressions': data['impressions'].sum(),
            'clicks': data['clicks'].sum(),
            'cost': data['cost'].sum(),
            'revenue': data['revenue'].sum(),
            'purchases': data['purchases'].sum()
        }

        if channel == 'app':
            totals.update({
                'installs': data['installs'].sum(),
                'opens': data['opens'].sum(),
                'login': data.get('login', pd.Series([0])).sum(),
                'funnel_steps': ['Impressions', 'Clics', 'Installations', 'Ouvertures', 'Connexions', 'Achats'],
                'funnel_values': [
                    totals['impressions'],
                    totals['clicks'],
                    totals['installs'],
                    totals['opens'],
                    totals.get('login', 0),
                    totals['purchases']
                ]
            })
        else:  # web
            totals.update({
                'add_to_cart': data.get('add_to_cart', pd.Series([0])).sum(),
                'funnel_steps': ['Impressions', 'Clics', 'Ajouts Panier', 'Achats'],
                'funnel_values': [
                    totals['impressions'],
                    totals['clicks'],
                    totals.get('add_to_cart', 0),
                    totals['purchases']
                ]
            })

        # Calcul des taux
        if totals['impressions'] > 0:
            totals['ctr'] = (totals['clicks'] / totals['impressions']) * 100
        else:
            totals['ctr'] = 0

        if totals['cost'] > 0:
            totals['roas'] = totals['revenue'] / totals['cost']
        else:
            totals['roas'] = 0

        if channel == 'app' and totals['installs'] > 0:
            totals['cpa'] = totals['cost'] / totals['installs']
            totals['conversion_rate'] = (totals['installs'] / totals['clicks']) * 100 if totals['clicks'] > 0 else 0
        elif channel == 'web' and totals['purchases'] > 0:
            totals['cpa'] = totals['cost'] / totals['purchases']
            totals['conversion_rate'] = (totals['purchases'] / totals['clicks']) * 100 if totals['clicks'] > 0 else 0
        else:
            totals['cpa'] = 0
            totals['conversion_rate'] = 0

        return totals

    def get_performance_insights(self, app_data: pd.DataFrame, web_data: pd.DataFrame) -> List[Dict[str, str]]:
        """Génère des insights basés sur les performances App vs Web"""
        insights = []

        app_summary = self._calculate_funnel_totals(app_data, 'app')
        web_summary = self._calculate_funnel_totals(web_data, 'web')

        if not app_summary or not web_summary:
            return insights

        # Comparaison ROAS
        if app_summary['roas'] > web_summary['roas'] * 1.2:
            insights.append({
                'type': 'positive',
                'title': 'App plus rentable',
                'description': f"L'App génère un ROAS de {app_summary['roas']:.2f} vs {web_summary['roas']:.2f} pour le Web"
            })
        elif web_summary['roas'] > app_summary['roas'] * 1.2:
            insights.append({
                'type': 'positive',
                'title': 'Web plus rentable',
                'description': f"Le Web génère un ROAS de {web_summary['roas']:.2f} vs {app_summary['roas']:.2f} pour l'App"
            })

        # Comparaison CTR
        if app_summary['ctr'] > web_summary['ctr'] * 1.5:
            insights.append({
                'type': 'info',
                'title': 'CTR App supérieur',
                'description': f"L'App a un CTR de {app_summary['ctr']:.2f}% vs {web_summary['ctr']:.2f}% pour le Web"
            })

        # Analyse des volumes
        total_cost = app_summary['cost'] + web_summary['cost']
        if total_cost > 0:
            app_cost_share = (app_summary['cost'] / total_cost) * 100
            if app_cost_share > 70:
                insights.append({
                    'type': 'warning',
                    'title': 'Budget concentré sur App',
                    'description': f"L'App représente {app_cost_share:.0f}% du budget total"
                })
            elif app_cost_share < 30:
                insights.append({
                    'type': 'warning',
                    'title': 'Budget concentré sur Web',
                    'description': f"Le Web représente {100 - app_cost_share:.0f}% du budget total"
                })

        return insights

    def _calculate_derived_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcule les métriques dérivées

        Args:
            df: DataFrame source

        Returns:
            DataFrame avec métriques calculées
        """
        data = df.copy()

        # CTR (Click-Through Rate)
        data['ctr'] = np.where(
            data['impressions'] > 0,
            (data['clicks'] / data['impressions']) * 100,
            0
        )

        # Taux de conversion (Install Rate)
        data['conversion_rate'] = np.where(
            data['clicks'] > 0,
            (data['installs'] / data['clicks']) * 100,
            0
        )

        # CPC (Cost Per Click)
        data['cpc'] = np.where(
            data['clicks'] > 0,
            data['cost'] / data['clicks'],
            0
        )

        # CPA (Cost Per Acquisition/Install)
        data['cpa'] = np.where(
            data['installs'] > 0,
            data['cost'] / data['installs'],
            0
        )

        # CPM (Cost Per Mille)
        data['cpm'] = np.where(
            data['impressions'] > 0,
            (data['cost'] / data['impressions']) * 1000,
            0
        )

        # ROAS (Return on Ad Spend) - estimation basée sur revenue
        data['roas'] = np.where(
            data['cost'] > 0,
            data['revenue'] / data['cost'],
            0
        )

        # Taux d'achat (Purchase Rate)
        data['purchase_rate'] = np.where(
            data['installs'] > 0,
            (data['purchases'] / data['installs']) * 100,
            0
        )

        # Revenue per install
        data['rpi'] = np.where(
            data['installs'] > 0,
            data['revenue'] / data['installs'],
            0
        )

        return data

    def _add_analysis_segments(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ajoute des segments d'analyse

        Args:
            df: DataFrame source

        Returns:
            DataFrame avec segments ajoutés
        """
        data = df.copy()

        # Segment App vs Web
        data['channel_segment'] = data['platform'].apply(self._categorize_channel)

        # Segment de performance basé sur CPA
        data['performance_segment'] = data['cpa'].apply(self._categorize_performance)

        # Segment de volume basé sur les impressions
        data['volume_segment'] = pd.cut(
            data['impressions'],
            bins=[0, 100, 1000, 10000, float('inf')],
            labels=['Très faible', 'Faible', 'Moyen', 'Élevé'],
            include_lowest=True
        )

        # Jour de la semaine
        data['day_of_week'] = data['date'].dt.day_name()
        data['is_weekend'] = data['date'].dt.weekday >= 5

        # Semaine de l'année
        data['week'] = data['date'].dt.isocalendar().week

        return data

    def _categorize_channel(self, platform: str) -> str:
        """Catégorise le canal (App vs Web)"""
        if pd.isna(platform):
            return 'Unknown'

        platform_lower = platform.lower()
        if 'ios' in platform_lower or 'android' in platform_lower or 'app' in platform_lower:
            return 'App'
        else:
            return 'Web'

    def _categorize_performance(self, cpa: float) -> str:
        """Catégorise la performance basée sur le CPA"""
        if cpa == 0:
            return 'No Cost'
        elif cpa <= 5:
            return 'Excellent'
        elif cpa <= 15:
            return 'Good'
        elif cpa <= 30:
            return 'Average'
        else:
            return 'Poor'

    def aggregate_by_period(self, df: pd.DataFrame, period: str = 'D') -> pd.DataFrame:
        """
        Agrège les données par période

        Args:
            df: DataFrame source
            period: Période d'agrégation ('D', 'W', 'M')

        Returns:
            DataFrame agrégé
        """
        if df.empty:
            return df

        # Grouper par date et période
        grouper = pd.Grouper(key='date', freq=period)

        agg_dict = {
            'cost': 'sum',
            'impressions': 'sum',
            'clicks': 'sum',
            'installs': 'sum',
            'purchases': 'sum',
            'revenue': 'sum',
            'opens': 'sum'
        }

        aggregated = df.groupby(grouper).agg(agg_dict).reset_index()

        # Recalculer les métriques dérivées
        aggregated = self._calculate_derived_metrics(aggregated)

        return aggregated

    def calculate_funnel_metrics(self, df: pd.DataFrame, group_by: str = None) -> Dict[str, Any]:
        """
        Calcule les métriques du funnel de conversion

        Args:
            df: DataFrame source
            group_by: Colonne pour grouper les données

        Returns:
            Dictionnaire avec les métriques du funnel
        """
        if df.empty:
            return {}

        if group_by and group_by in df.columns:
            grouped = df.groupby(group_by)
            results = {}

            for name, group in grouped:
                results[name] = self._calculate_single_funnel(group)

            return results
        else:
            return {'overall': self._calculate_single_funnel(df)}

    def _calculate_single_funnel(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calcule le funnel pour un seul groupe de données"""
        total_impressions = df['impressions'].sum()
        total_clicks = df['clicks'].sum()
        total_installs = df['installs'].sum()
        total_purchases = df['purchases'].sum()
        total_cost = df['cost'].sum()
        total_revenue = df['revenue'].sum()

        # Taux de conversion du funnel
        impression_to_click = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        click_to_install = (total_installs / total_clicks * 100) if total_clicks > 0 else 0
        install_to_purchase = (total_purchases / total_installs * 100) if total_installs > 0 else 0
        impression_to_install = (total_installs / total_impressions * 100) if total_impressions > 0 else 0

        return {
            'impressions': total_impressions,
            'clicks': total_clicks,
            'installs': total_installs,
            'purchases': total_purchases,
            'cost': total_cost,
            'revenue': total_revenue,
            'impression_to_click_rate': impression_to_click,
            'click_to_install_rate': click_to_install,
            'install_to_purchase_rate': install_to_purchase,
            'impression_to_install_rate': impression_to_install,
            'cpa': total_cost / total_installs if total_installs > 0 else 0,
            'roas': total_revenue / total_cost if total_cost > 0 else 0
        }

    def compare_periods(self, df: pd.DataFrame, current_start: str, current_end: str,
                        previous_start: str, previous_end: str) -> Dict[str, Any]:
        """
        Compare les performances entre deux périodes

        Args:
            df: DataFrame source
            current_start: Début période actuelle
            current_end: Fin période actuelle
            previous_start: Début période précédente
            previous_end: Fin période précédente

        Returns:
            Dictionnaire avec la comparaison
        """
        current_data = df[
            (df['date'] >= current_start) &
            (df['date'] <= current_end)
            ]

        previous_data = df[
            (df['date'] >= previous_start) &
            (df['date'] <= previous_end)
            ]

        current_metrics = self._calculate_single_funnel(current_data)
        previous_metrics = self._calculate_single_funnel(previous_data)

        comparison = {}
        for metric in current_metrics:
            current_val = current_metrics[metric]
            previous_val = previous_metrics[metric]

            if previous_val > 0:
                change_pct = ((current_val - previous_val) / previous_val) * 100
            else:
                change_pct = 0 if current_val == 0 else 100

            comparison[metric] = {
                'current': current_val,
                'previous': previous_val,
                'change': current_val - previous_val,
                'change_percent': change_pct
            }

        return comparison

    def identify_top_performers(self, df: pd.DataFrame, metric: str = 'roas',
                                top_n: int = 10) -> pd.DataFrame:
        """
        Identifie les meilleures performances

        Args:
            df: DataFrame source
            metric: Métrique pour le classement
            top_n: Nombre d'éléments à retourner

        Returns:
            DataFrame avec les top performers
        """
        if df.empty or metric not in df.columns:
            return pd.DataFrame()

        # Grouper par campagne
        campaign_performance = df.groupby('campaign_name').agg({
            'cost': 'sum',
            'impressions': 'sum',
            'clicks': 'sum',
            'installs': 'sum',
            'purchases': 'sum',
            'revenue': 'sum'
        }).reset_index()

        # Recalculer les métriques
        campaign_performance = self._calculate_derived_metrics(campaign_performance)

        # Trier et retourner le top
        return campaign_performance.nlargest(top_n, metric)

    def detect_anomalies(self, df: pd.DataFrame, metric: str = 'cost',
                         threshold: float = 2.0) -> pd.DataFrame:
        """
        Détecte les anomalies dans les données

        Args:
            df: DataFrame source
            metric: Métrique à analyser
            threshold: Seuil de détection (écarts-types)

        Returns:
            DataFrame avec les anomalies détectées
        """
        if df.empty or metric not in df.columns:
            return pd.DataFrame()

        # Calculer la moyenne et l'écart-type
        mean_val = df[metric].mean()
        std_val = df[metric].std()

        # Identifier les anomalies
        upper_bound = mean_val + (threshold * std_val)
        lower_bound = mean_val - (threshold * std_val)

        anomalies = df[
            (df[metric] > upper_bound) |
            (df[metric] < lower_bound)
            ].copy()

        if not anomalies.empty:
            anomalies['anomaly_type'] = np.where(
                anomalies[metric] > upper_bound,
                'High',
                'Low'
            )
            anomalies['deviation'] = abs(anomalies[metric] - mean_val) / std_val

        return anomalies

    def calculate_cohort_analysis(self, df: pd.DataFrame,
                                  cohort_period: str = 'W') -> pd.DataFrame:
        """
        Calcule l'analyse de cohorte

        Args:
            df: DataFrame source
            cohort_period: Période de cohorte ('D', 'W', 'M')

        Returns:
            DataFrame avec l'analyse de cohorte
        """
        if df.empty:
            return pd.DataFrame()

        # Créer les cohortes basées sur la première date d'install
        df_cohort = df[df['installs'] > 0].copy()

        if df_cohort.empty:
            return pd.DataFrame()

        # Grouper par période
        df_cohort['period'] = df_cohort['date'].dt.to_period(cohort_period)

        # Calculer les métriques par cohorte
        cohort_data = df_cohort.groupby('period').agg({
            'installs': 'sum',
            'purchases': 'sum',
            'revenue': 'sum',
            'cost': 'sum'
        }).reset_index()

        # Calculer les taux
        cohort_data['purchase_rate'] = (
                cohort_data['purchases'] / cohort_data['installs'] * 100
        )
        cohort_data['revenue_per_install'] = (
                cohort_data['revenue'] / cohort_data['installs']
        )

        return cohort_data

    def generate_insights(self, df: pd.DataFrame) -> List[Dict[str, str]]:
        """
        Génère des insights automatiques basés sur les données

        Args:
            df: DataFrame source

        Returns:
            Liste d'insights
        """
        insights = []

        if df.empty:
            return insights

        # Insight sur la performance globale
        total_cost = df['cost'].sum()
        total_installs = df['installs'].sum()
        total_revenue = df['revenue'].sum()

        if total_cost > 0:
            overall_roas = total_revenue / total_cost
            if overall_roas > 3:
                insights.append({
                    'type': 'positive',
                    'title': 'ROAS Excellent',
                    'description': f'Votre ROAS global de {overall_roas:.2f} est excellent!'
                })
            elif overall_roas < 1:
                insights.append({
                    'type': 'warning',
                    'title': 'ROAS Faible',
                    'description': f'Votre ROAS global de {overall_roas:.2f} nécessite une optimisation.'
                })

        # Insight sur les meilleures plateformes
        platform_performance = df.groupby('platform').agg({
            'cost': 'sum',
            'installs': 'sum',
            'revenue': 'sum'
        })

        if not platform_performance.empty:
            platform_performance['roas'] = (
                    platform_performance['revenue'] /
                    platform_performance['cost'].replace(0, 1)
            )
            best_platform = platform_performance['roas'].idxmax()
            best_roas = platform_performance.loc[best_platform, 'roas']

            insights.append({
                'type': 'info',
                'title': 'Meilleure Plateforme',
                'description': f'{best_platform} performe le mieux avec un ROAS de {best_roas:.2f}'
            })

        # Insight sur les tendances
        if len(df) >= 7:  # Au moins une semaine de données
            recent_data = df.tail(7)
            older_data = df.head(7) if len(df) >= 14 else df.head(len(df) // 2)

            recent_cpa = recent_data['cost'].sum() / recent_data['installs'].sum() if recent_data[
                                                                                          'installs'].sum() > 0 else 0
            older_cpa = older_data['cost'].sum() / older_data['installs'].sum() if older_data[
                                                                                       'installs'].sum() > 0 else 0

            if recent_cpa > 0 and older_cpa > 0:
                cpa_change = ((recent_cpa - older_cpa) / older_cpa) * 100

                if cpa_change < -10:
                    insights.append({
                        'type': 'positive',
                        'title': 'CPA en Amélioration',
                        'description': f'Votre CPA s\'améliore de {abs(cpa_change):.1f}% récemment!'
                    })
                elif cpa_change > 10:
                    insights.append({
                        'type': 'warning',
                        'title': 'CPA en Dégradation',
                        'description': f'Votre CPA se dégrade de {cpa_change:.1f}% récemment.'
                    })

        return insights

    def export_summary_report(self, df: pd.DataFrame,
                              export_format: str = 'dict') -> Dict[str, Any]:
        """
        Exporte un rapport de synthèse

        Args:
            df: DataFrame source
            export_format: Format d'export

        Returns:
            Rapport de synthèse
        """
        if df.empty:
            return {}

        # Métriques globales
        global_metrics = self._calculate_single_funnel(df)

        # Performance par source
        source_performance = df.groupby('source').apply(
            lambda x: self._calculate_single_funnel(x)
        ).to_dict()

        # Performance par plateforme
        platform_performance = df.groupby('platform').apply(
            lambda x: self._calculate_single_funnel(x)
        ).to_dict()

        # Tendances journalières
        daily_trends = self.aggregate_by_period(df, 'D')

        # Top campagnes
        top_campaigns = self.identify_top_performers(df, 'roas', 5)

        # Insights
        insights = self.generate_insights(df)

        report = {
            'period': {
                'start_date': df['date'].min().strftime('%Y-%m-%d'),
                'end_date': df['date'].max().strftime('%Y-%m-%d'),
                'total_days': (df['date'].max() - df['date'].min()).days + 1
            },
            'global_metrics': global_metrics,
            'source_performance': source_performance,
            'platform_performance': platform_performance,
            'daily_trends': daily_trends.to_dict('records') if not daily_trends.empty else [],
            'top_campaigns': top_campaigns.to_dict('records') if not top_campaigns.empty else [],
            'insights': insights,
            'generated_at': datetime.now().isoformat()
        }

        return report