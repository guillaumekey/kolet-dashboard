import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from .base_processor import BaseProcessor


class ConsolidationProcessor(BaseProcessor):
    """Processeur spécialisé pour la consolidation des données multi-sources"""

    def __init__(self):
        super().__init__()

    def create_consolidated_data(self, google_ads_data: pd.DataFrame,
                                 asa_data: pd.DataFrame, branch_data: pd.DataFrame) -> pd.DataFrame:
        """
        Crée les données consolidées pour les KPI globaux avec logique de coûts corrigée

        LOGIQUE :
        - Impressions/Clics : Google Ads + ASA seulement
        - Coûts : Google Ads + ASA seulement
        - Installs : Branch.io seulement (TOUTES les plateformes)
        - Purchases : Branch.io (app) + Google Ads (web)
        """
        print(f"🔍 Consolidation des données:")
        print(f"  • Google Ads: {len(google_ads_data)} lignes")
        print(f"  • ASA: {len(asa_data)} lignes")
        print(f"  • Branch: {len(branch_data)} lignes")

        # Collecter toutes les dates
        all_dates = self._collect_all_dates([google_ads_data, asa_data, branch_data])

        if not all_dates:
            return pd.DataFrame()

        # Créer le DataFrame de base avec toutes les dates
        consolidated = pd.DataFrame({'date': sorted(list(all_dates))})
        consolidated['date'] = pd.to_datetime(consolidated['date'])

        # Consolider chaque type de métrique
        consolidated = self._consolidate_costs(consolidated, google_ads_data, asa_data)
        consolidated = self._consolidate_advertising_metrics(consolidated, google_ads_data, asa_data)
        consolidated = self._consolidate_installs_metrics(consolidated, branch_data)
        consolidated = self._consolidate_purchase_metrics(consolidated, branch_data, google_ads_data)
        consolidated = self._consolidate_revenue_metrics(consolidated, branch_data, google_ads_data)

        # Calculer les métriques globales
        consolidated = self._calculate_global_metrics(consolidated)

        print(f"  ✅ Consolidation terminée: {len(consolidated)} lignes")
        print(f"  💰 Coût total: {consolidated['cost'].sum():.2f}€")

        return consolidated

    def _collect_all_dates(self, dataframes: List[pd.DataFrame]) -> set:
        """Collecte toutes les dates uniques des DataFrames"""
        all_dates = set()

        for data in dataframes:
            if not data.empty and 'date' in data.columns:
                dates = pd.to_datetime(data['date']).dt.strftime('%Y-%m-%d')
                all_dates.update(dates)

        return all_dates

    def _consolidate_costs(self, consolidated: pd.DataFrame,
                           google_ads_data: pd.DataFrame, asa_data: pd.DataFrame) -> pd.DataFrame:
        """Consolide les coûts depuis Google Ads et ASA uniquement"""
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
        else:
            consolidated['cost'] = 0

        return consolidated

    def _consolidate_advertising_metrics(self, consolidated: pd.DataFrame,
                                         google_ads_data: pd.DataFrame, asa_data: pd.DataFrame) -> pd.DataFrame:
        """Consolide les impressions et clics depuis les sources publicitaires"""
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
        else:
            consolidated['clicks'] = 0

        return consolidated

    def _consolidate_installs_metrics(self, consolidated: pd.DataFrame,
                                      branch_data: pd.DataFrame) -> pd.DataFrame:
        """Consolide les installs et métriques post-install depuis Branch.io"""
        if not branch_data.empty:
            branch_metrics = branch_data.groupby('date').agg({
                'installs': 'sum',
                'opens': 'sum',
                'login': 'sum'
            })

            print(f"  • Branch installs: {branch_metrics['installs'].sum():,}")
            print(f"  • Branch opens: {branch_metrics['opens'].sum():,}")
            print(f"  • Branch logins: {branch_metrics['login'].sum():,}")

            for metric in ['installs', 'opens', 'login']:
                consolidated = consolidated.merge(
                    branch_metrics[metric].reset_index(), on='date', how='left'
                )
                consolidated[metric] = consolidated[metric].fillna(0)
        else:
            for metric in ['installs', 'opens', 'login']:
                consolidated[metric] = 0
                print(f"  • {metric}: Aucune donnée trouvée")

        return consolidated

    def _consolidate_purchase_metrics(self, consolidated: pd.DataFrame,
                                      branch_data: pd.DataFrame, google_ads_data: pd.DataFrame) -> pd.DataFrame:
        """Consolide les purchases depuis Branch.io + Google Ads"""
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
        else:
            consolidated['purchases'] = 0

        return consolidated

    def _consolidate_revenue_metrics(self, consolidated: pd.DataFrame,
                                     branch_data: pd.DataFrame, google_ads_data: pd.DataFrame) -> pd.DataFrame:
        """Consolide les revenus depuis Branch.io + Google Ads"""
        revenue_data = []

        if not branch_data.empty:
            branch_revenue = branch_data.groupby('date')['revenue'].sum()
            revenue_data.append(branch_revenue)
            print(f"  • Branch revenue: {branch_revenue.sum():,.2f}€")

        if not google_ads_data.empty:
            google_revenue = google_ads_data.groupby('date')['revenue'].sum()
            revenue_data.append(google_revenue)
            print(f"  • Google revenue: {google_revenue.sum():,.2f}€")

        if revenue_data:
            total_revenue = pd.concat(revenue_data).groupby(level=0).sum()
            consolidated = consolidated.merge(total_revenue.reset_index(), on='date', how='left')
            consolidated['revenue'] = consolidated['revenue'].fillna(0)
        else:
            consolidated['revenue'] = 0

        return consolidated

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

    def separate_data_by_source(self, df: pd.DataFrame, platforms: List[str] = None,
                                exclude_unpopulated: bool = True) -> Dict[str, pd.DataFrame]:
        """Sépare les données par source avec filtrage optionnel"""
        print(f"🔍 Séparation des données par source:")
        print(f"  • Données reçues: {len(df)} enregistrements")

        # Filtrer les données unpopulated si demandé
        if exclude_unpopulated:
            data_before = len(df)
            df = df[~((df['source'] == 'Branch.io') & (df['campaign_name'] == 'Unpopulated'))]
            print(f"  • Après filtrage Unpopulated: {data_before} → {len(df)} enregistrements")

        # Filtrer par plateformes si spécifié
        if platforms:
            data_before = len(df)
            df = df[df['platform'].isin(platforms)]
            print(f"  • Après filtrage plateformes: {data_before} → {len(df)} enregistrements")

        # Séparer par source
        separated_data = {
            'google_ads': df[df['source'].isin(['Google Ads', 'Google AdWords'])].copy(),
            'asa': df[df['source'].isin(['Apple Search Ads'])].copy(),
            'branch': df[df['source'] == 'Branch.io'].copy()
        }

        # Convertir les dates
        for source, data in separated_data.items():
            if not data.empty and 'date' in data.columns:
                data['date'] = pd.to_datetime(data['date'])
                print(f"  • {source}: {len(data)} enregistrements")

        return separated_data

    def process(self, df: pd.DataFrame, platforms: List[str] = None,
                exclude_unpopulated: bool = True) -> Dict[str, pd.DataFrame]:
        """Traite et consolide les données"""
        # Séparer les données par source
        separated_data = self.separate_data_by_source(df, platforms, exclude_unpopulated)

        # Créer les données consolidées
        consolidated = self.create_consolidated_data(
            separated_data['google_ads'],
            separated_data['asa'],
            separated_data['branch']
        )

        return {
            'consolidated': consolidated,
            'separated': separated_data
        }