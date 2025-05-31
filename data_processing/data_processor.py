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

        # Créer les données App et Web selon la logique métier
        app_data = self._create_app_funnel_data(asa_data, branch_data)
        web_data = self._create_web_funnel_data(google_ads_data)

        # Données consolidées pour les KPI globaux
        consolidated_data = self._create_consolidated_data(google_ads_data, asa_data, branch_data)

        return {
            'app': app_data,
            'web': web_data,
            'consolidated': consolidated_data,
            'raw': {
                'google_ads': google_ads_data,
                'asa': asa_data,
                'branch': branch_data
            }
        }

    def _create_app_funnel_data(self, asa_data: pd.DataFrame, branch_data: pd.DataFrame) -> pd.DataFrame:
        """
        Crée les données du funnel App : Impressions -> Clics -> Installs -> Opens -> Logins -> Purchases

        Logique :
        - Coûts : ASA seulement (pas de double comptage)
        - Impressions/Clics : Branch.io (données consolidées)
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

        # Grouper par date pour le funnel app
        agg_dict = {
            'impressions': 'sum',  # Branch.io pour impressions
            'clicks': 'sum',  # Branch.io pour clics
            'installs': 'sum',  # Branch.io pour installs
            'opens': 'sum',  # Branch.io pour opens
            'cost': 'sum',  # On va remplacer par ASA
            'revenue': 'sum',  # Branch.io pour revenue
            'purchases': 'sum'  # Branch.io pour purchases
        }

        # Ajouter les logins si la colonne existe
        if 'login' in app_branch.columns:
            agg_dict['login'] = 'sum'

        app_funnel = app_branch.groupby('date').agg(agg_dict).reset_index()

        print(f"  • Après groupement par date: {len(app_funnel)} lignes")
        print(f"  • Total installs agrégé: {app_funnel['installs'].sum()}")

        # Ajouter les coûts ASA (remplacer les coûts Branch)
        if not asa_data.empty:
            asa_costs = asa_data.groupby('date')['cost'].sum().reset_index()
            print(f"  • ASA costs: {len(asa_costs)} lignes, total: {asa_costs['cost'].sum():.2f}€")
            app_funnel = app_funnel.merge(asa_costs, on='date', how='left', suffixes=('', '_asa'))
            app_funnel['cost'] = app_funnel['cost_asa'].fillna(0)
            app_funnel.drop(columns=['cost_asa'], inplace=True)
        else:
            print("  ⚠️ Aucune donnée ASA pour les coûts")

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

    def _create_consolidated_data(self, google_ads_data: pd.DataFrame,
                                  asa_data: pd.DataFrame, branch_data: pd.DataFrame) -> pd.DataFrame:
        """
        Crée les données consolidées pour les KPI globaux

        Logique :
        - Coûts : Google Ads + ASA (pas Branch.io)
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

        # Coûts : Google Ads + ASA
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

        # Installs : Branch.io seulement (TOUTES plateformes)
        if not branch_data.empty:
            branch_installs = branch_data.groupby('date')['installs'].sum()
            print(f"  • Branch installs total: {branch_installs.sum():,}")
            consolidated = consolidated.merge(branch_installs.reset_index(), on='date', how='left')
            consolidated['installs'] = consolidated['installs'].fillna(0)
        else:
            consolidated['installs'] = 0
            print("  ⚠️ Aucun install Branch.io")

        # Impressions, Clics, Opens et Logins : somme de toutes les sources
        for metric in ['impressions', 'clicks', 'opens', 'login']:
            metric_data = []
            for data in [google_ads_data, asa_data, branch_data]:
                if not data.empty and metric in data.columns:
                    metric_sum = data.groupby('date')[metric].sum()
                    metric_data.append(metric_sum)
                    print(
                        f"  • {data['source'].iloc[0] if 'source' in data.columns else 'Unknown'} {metric}: {metric_sum.sum():,}")

            if metric_data:
                total_metric = pd.concat(metric_data).groupby(level=0).sum()
                consolidated = consolidated.merge(total_metric.reset_index(), on='date', how='left')
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