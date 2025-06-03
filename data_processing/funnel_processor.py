import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from .base_processor import BaseProcessor


class FunnelProcessor(BaseProcessor):
    """Processeur spécialisé pour les funnels d'acquisition App et Web"""

    def __init__(self):
        super().__init__()

    def create_app_funnel_data(self, asa_data: pd.DataFrame, branch_data: pd.DataFrame,
                               google_ads_data: pd.DataFrame) -> pd.DataFrame:
        """
        Crée les données du funnel App avec prise en compte de la classification des campagnes

        Logique :
        - Impressions/Clics : ASA + Google Ads classifié "app"
        - Coûts : ASA + Google Ads classifié "app"
        - Installs/Opens/Logins/Purchases : Branch.io seulement
        """
        print(f"🔍 Creating App funnel data:")
        print(f"  • ASA data: {len(asa_data)} lignes")
        print(f"  • Branch data: {len(branch_data)} lignes")
        print(f"  • Google Ads data: {len(google_ads_data)} lignes")

        if branch_data.empty:
            print("  ⚠️ Branch data vide, retour DataFrame vide")
            return pd.DataFrame()

        # Filtrer les données app de Branch.io
        app_branch = branch_data[~branch_data['platform'].isin(['Web', 'WEB'])].copy()

        if app_branch.empty:
            print("  ⚠️ Aucune donnée app après filtrage")
            return pd.DataFrame()

        # Agrégation des données Branch.io
        app_funnel = self._aggregate_branch_data(app_branch)

        # Ajouter les données publicitaires
        app_funnel = self._add_advertising_data(app_funnel, asa_data, google_ads_data)

        # Calculer les métriques du funnel
        app_funnel = self._calculate_app_funnel_metrics(app_funnel)
        app_funnel['channel'] = 'App'

        print(f"  ✅ Funnel app créé: {len(app_funnel)} lignes, {app_funnel['installs'].sum()} installs")
        return app_funnel

    def create_web_funnel_data(self, google_ads_data: pd.DataFrame) -> pd.DataFrame:
        """
        Crée les données du funnel Web avec prise en compte de la classification des campagnes

        Logique :
        - Toutes les données viennent de Google Ads classifié "web"
        """
        if google_ads_data.empty:
            return pd.DataFrame()

        # Filtrer seulement les campagnes classifiées "web"
        web_google_ads = google_ads_data[
            (google_ads_data['channel_type'] == 'web') |
            (google_ads_data['channel_type'].isna())  # Inclure les non-classifiées par défaut
            ].copy()

        if web_google_ads.empty:
            print("  ⚠️ Aucune campagne Google Ads classifiée 'web'")
            return pd.DataFrame()

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
        return web_funnel

    def _aggregate_branch_data(self, app_branch: pd.DataFrame) -> pd.DataFrame:
        """Agrège les données Branch.io par date"""
        branch_agg_dict = {
            'installs': 'sum',
            'opens': 'sum',
            'revenue': 'sum',
            'purchases': 'sum'
        }

        if 'login' in app_branch.columns:
            branch_agg_dict['login'] = 'sum'

        app_funnel = app_branch.groupby('date').agg(branch_agg_dict).reset_index()

        # Gérer la colonne login
        if 'login' not in app_funnel.columns:
            app_funnel['login'] = (app_funnel['opens'] * 0.25).round().astype(int)

        return app_funnel

    def _add_advertising_data(self, app_funnel: pd.DataFrame, asa_data: pd.DataFrame,
                              google_ads_data: pd.DataFrame) -> pd.DataFrame:
        """Ajoute les données publicitaires au funnel app"""
        # Initialiser les colonnes publicitaires
        app_funnel['impressions'] = 0
        app_funnel['clicks'] = 0
        app_funnel['cost'] = 0

        # Ajouter ASA (toujours app)
        if not asa_data.empty:
            app_funnel = self._merge_asa_data(app_funnel, asa_data)

        # Ajouter Google Ads classifié "app"
        if not google_ads_data.empty:
            app_funnel = self._merge_google_app_data(app_funnel, google_ads_data)

        return app_funnel.fillna(0)

    def _merge_asa_data(self, app_funnel: pd.DataFrame, asa_data: pd.DataFrame) -> pd.DataFrame:
        """Merge les données ASA avec le funnel app"""
        asa_agg = asa_data.groupby('date').agg({
            'impressions': 'sum',
            'clicks': 'sum',
            'cost': 'sum'
        }).reset_index()

        print(f"  • ASA data agrégée: {len(asa_agg)} lignes")
        print(f"  • ASA impressions: {asa_agg['impressions'].sum():,}")
        print(f"  • ASA clicks: {asa_agg['clicks'].sum():,}")

        # Merger avec les données app
        app_funnel = app_funnel.merge(asa_agg, on='date', how='outer', suffixes=('', '_asa'))
        app_funnel['impressions'] = app_funnel['impressions'].fillna(0) + app_funnel['impressions_asa'].fillna(0)
        app_funnel['clicks'] = app_funnel['clicks'].fillna(0) + app_funnel['clicks_asa'].fillna(0)
        app_funnel['cost'] = app_funnel['cost'].fillna(0) + app_funnel['cost_asa'].fillna(0)

        # Nettoyer les colonnes temporaires
        return app_funnel.drop(columns=[col for col in app_funnel.columns if col.endswith('_asa')])

    def _merge_google_app_data(self, app_funnel: pd.DataFrame, google_ads_data: pd.DataFrame) -> pd.DataFrame:
        """Merge les données Google Ads App avec le funnel"""
        google_app_data = google_ads_data[google_ads_data['channel_type'] == 'app'].copy()

        if not google_app_data.empty:
            google_app_agg = google_app_data.groupby('date').agg({
                'impressions': 'sum',
                'clicks': 'sum',
                'cost': 'sum'
            }).reset_index()

            print(f"  • Google Ads App classifiées: {len(google_app_agg)} lignes")

            # Merger avec les données app
            app_funnel = app_funnel.merge(google_app_agg, on='date', how='outer', suffixes=('', '_google'))
            app_funnel['impressions'] = app_funnel['impressions'].fillna(0) + app_funnel['impressions_google'].fillna(0)
            app_funnel['clicks'] = app_funnel['clicks'].fillna(0) + app_funnel['clicks_google'].fillna(0)
            app_funnel['cost'] = app_funnel['cost'].fillna(0) + app_funnel['cost_google'].fillna(0)

            # Nettoyer les colonnes temporaires
            app_funnel = app_funnel.drop(columns=[col for col in app_funnel.columns if col.endswith('_google')])

        return app_funnel

    def _calculate_app_funnel_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule les métriques du funnel App"""
        data = df.copy()

        # Taux de passage du funnel App
        data['ctr'] = self._safe_divide(data['clicks'], data['impressions']) * 100
        data['click_to_install_rate'] = self._safe_divide(data['installs'], data['clicks']) * 100
        data['install_to_open_rate'] = self._safe_divide(data['opens'], data['installs']) * 100
        data['open_to_login_rate'] = self._safe_divide(data['login'], data['opens']) * 100
        data['login_to_purchase_rate'] = self._safe_divide(data['purchases'], data['login']) * 100

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
        data['ctr'] = self._safe_divide(data['clicks'], data['impressions']) * 100
        data['click_to_cart_rate'] = self._safe_divide(data['add_to_cart'], data['clicks']) * 100
        data['cart_to_purchase_rate'] = self._safe_divide(data['purchases'], data['add_to_cart']) * 100

        # Métriques globales
        data['overall_conversion_rate'] = self._safe_divide(data['purchases'], data['impressions']) * 100
        data['purchase_conversion_rate'] = self._safe_divide(data['purchases'], data['clicks']) * 100

        # Métriques économiques
        data['cpc'] = self._safe_divide(data['cost'], data['clicks'])
        data['cpa'] = self._safe_divide(data['cost'], data['purchases'])
        data['cpm'] = self._safe_divide(data['cost'], data['impressions']) * 1000
        data['roas'] = self._safe_divide(data['revenue'], data['cost'])
        data['revenue_per_purchase'] = self._safe_divide(data['revenue'], data['purchases'])

        return data

    def calculate_funnel_summary(self, app_data: pd.DataFrame, web_data: pd.DataFrame) -> Dict[str, Any]:
        """Calcule le résumé des funnels App vs Web"""
        return {
            'app': self._calculate_funnel_totals(app_data, 'app'),
            'web': self._calculate_funnel_totals(web_data, 'web')
        }

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
        totals['ctr'] = self._calculate_percentage(totals['clicks'], totals['impressions'])
        totals['roas'] = self._safe_divide(totals['revenue'], totals['cost'])

        if channel == 'app' and totals['installs'] > 0:
            totals['cpa'] = totals['cost'] / totals['installs']
            totals['conversion_rate'] = self._calculate_percentage(totals['installs'], totals['clicks'])
        elif channel == 'web' and totals['purchases'] > 0:
            totals['cpa'] = totals['cost'] / totals['purchases']
            totals['conversion_rate'] = self._calculate_percentage(totals['purchases'], totals['clicks'])
        else:
            totals['cpa'] = 0
            totals['conversion_rate'] = 0

        return totals

    def process(self, asa_data: pd.DataFrame, branch_data: pd.DataFrame,
                google_ads_data: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """Traite les données pour créer les funnels App et Web"""
        return {
            'app': self.create_app_funnel_data(asa_data, branch_data, google_ads_data),
            'web': self.create_web_funnel_data(google_ads_data)
        }