import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from .base_processor import BaseProcessor


class AnalyticsProcessor(BaseProcessor):
    """Processeur spécialisé pour les analyses avancées et insights"""

    def __init__(self):
        super().__init__()

    def get_performance_insights(self, app_data: pd.DataFrame, web_data: pd.DataFrame) -> List[Dict[str, str]]:
        """Génère des insights basés sur les performances App vs Web"""
        insights = []

        app_summary = self._calculate_channel_totals(app_data, 'app')
        web_summary = self._calculate_channel_totals(web_data, 'web')

        if not app_summary or not web_summary:
            return insights

        # Comparaison ROAS
        insights.extend(self._analyze_roas_comparison(app_summary, web_summary))

        # Comparaison CTR
        insights.extend(self._analyze_ctr_comparison(app_summary, web_summary))

        # Analyse des volumes budgétaires
        insights.extend(self._analyze_budget_allocation(app_summary, web_summary))

        return insights

    def _calculate_channel_totals(self, data: pd.DataFrame, channel: str) -> Dict[str, Any]:
        """Calcule les totaux pour un canal donné"""
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
                'login': data.get('login', pd.Series([0])).sum()
            })
        else:  # web
            totals.update({
                'add_to_cart': data.get('add_to_cart', pd.Series([0])).sum()
            })

        # Calcul des taux
        totals['ctr'] = self._calculate_percentage(totals['clicks'], totals['impressions'])
        totals['roas'] = self._safe_divide(totals['revenue'], totals['cost'])

        if channel == 'app' and totals['installs'] > 0:
            totals['conversion_rate'] = self._calculate_percentage(totals['installs'], totals['clicks'])
        elif channel == 'web' and totals['purchases'] > 0:
            totals['conversion_rate'] = self._calculate_percentage(totals['purchases'], totals['clicks'])
        else:
            totals['conversion_rate'] = 0

        return totals

    def _analyze_roas_comparison(self, app_summary: Dict, web_summary: Dict) -> List[Dict[str, str]]:
        """Analyse la comparaison ROAS entre App et Web"""
        insights = []

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

        return insights

    def _analyze_ctr_comparison(self, app_summary: Dict, web_summary: Dict) -> List[Dict[str, str]]:
        """Analyse la comparaison CTR entre App et Web"""
        insights = []

        if app_summary['ctr'] > web_summary['ctr'] * 1.5:
            insights.append({
                'type': 'info',
                'title': 'CTR App supérieur',
                'description': f"L'App a un CTR de {app_summary['ctr']:.2f}% vs {web_summary['ctr']:.2f}% pour le Web"
            })

        return insights

    def _analyze_budget_allocation(self, app_summary: Dict, web_summary: Dict) -> List[Dict[str, str]]:
        """Analyse l'allocation budgétaire"""
        insights = []

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

    def calculate_funnel_metrics(self, df: pd.DataFrame, group_by: str = None) -> Dict[str, Any]:
        """Calcule les métriques du funnel de conversion"""
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
        totals = {
            'impressions': df['impressions'].sum(),
            'clicks': df['clicks'].sum(),
            'installs': df['installs'].sum(),
            'purchases': df['purchases'].sum(),
            'cost': df['cost'].sum(),
            'revenue': df['revenue'].sum()
        }

        # Taux de conversion du funnel
        metrics = {
            **totals,
            'impression_to_click_rate': self._calculate_percentage(totals['clicks'], totals['impressions']),
            'click_to_install_rate': self._calculate_percentage(totals['installs'], totals['clicks']),
            'install_to_purchase_rate': self._calculate_percentage(totals['purchases'], totals['installs']),
            'impression_to_install_rate': self._calculate_percentage(totals['installs'], totals['impressions']),
            'cpa': self._safe_divide(totals['cost'], totals['installs']),
            'roas': self._safe_divide(totals['revenue'], totals['cost'])
        }

        return metrics

    def compare_periods(self, df: pd.DataFrame, current_start: str, current_end: str,
                        previous_start: str, previous_end: str) -> Dict[str, Any]:
        """Compare les performances entre deux périodes"""
        current_data = df[
            (df['date'] >= current_start) & (df['date'] <= current_end)
            ]

        previous_data = df[
            (df['date'] >= previous_start) & (df['date'] <= previous_end)
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
        """Identifie les meilleures performances"""
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

    def _calculate_derived_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule les métriques dérivées pour une analyse"""
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
        data['rpi'] = self._safe_divide(data['revenue'], data['installs'])

        return data

    def detect_anomalies(self, df: pd.DataFrame, metric: str = 'cost',
                         threshold: float = 2.0) -> pd.DataFrame:
        """Détecte les anomalies dans les données"""
        if df.empty or metric not in df.columns:
            return pd.DataFrame()

        # Calculer la moyenne et l'écart-type
        mean_val = df[metric].mean()
        std_val = df[metric].std()

        if std_val == 0:  # Éviter la division par zéro
            return pd.DataFrame()

        # Identifier les anomalies
        upper_bound = mean_val + (threshold * std_val)
        lower_bound = mean_val - (threshold * std_val)

        anomalies = df[
            (df[metric] > upper_bound) | (df[metric] < lower_bound)
            ].copy()

        if not anomalies.empty:
            anomalies['anomaly_type'] = np.where(
                anomalies[metric] > upper_bound, 'High', 'Low'
            )
            anomalies['deviation'] = abs(anomalies[metric] - mean_val) / std_val

        return anomalies

    def calculate_cohort_analysis(self, df: pd.DataFrame,
                                  cohort_period: str = 'W') -> pd.DataFrame:
        """Calcule l'analyse de cohorte"""
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
        cohort_data['purchase_rate'] = self._calculate_percentage(
            cohort_data['purchases'], cohort_data['installs']
        )
        cohort_data['revenue_per_install'] = self._safe_divide(
            cohort_data['revenue'], cohort_data['installs']
        )

        return cohort_data

    def aggregate_by_period(self, df: pd.DataFrame, period: str = 'D') -> pd.DataFrame:
        """Agrège les données par période"""
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

    def generate_insights(self, df: pd.DataFrame) -> List[Dict[str, str]]:
        """Génère des insights automatiques basés sur les données"""
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
        if 'platform' in df.columns:
            platform_performance = df.groupby('platform').agg({
                'cost': 'sum',
                'installs': 'sum',
                'revenue': 'sum'
            })

            if not platform_performance.empty:
                platform_performance['roas'] = self._safe_divide(
                    platform_performance['revenue'], platform_performance['cost']
                )
                best_platform = platform_performance['roas'].idxmax()
                best_roas = platform_performance.loc[best_platform, 'roas']

                insights.append({
                    'type': 'info',
                    'title': 'Meilleure Plateforme',
                    'description': f'{best_platform} performe le mieux avec un ROAS de {best_roas:.2f}'
                })

        # Insight sur les tendances
        insights.extend(self._analyze_trends(df))

        return insights

    def _analyze_trends(self, df: pd.DataFrame) -> List[Dict[str, str]]:
        """Analyse les tendances dans les données"""
        insights = []

        if len(df) >= 7:  # Au moins une semaine de données
            recent_data = df.tail(7)
            older_data = df.head(7) if len(df) >= 14 else df.head(len(df) // 2)

            recent_cpa = self._safe_divide(recent_data['cost'].sum(), recent_data['installs'].sum())
            older_cpa = self._safe_divide(older_data['cost'].sum(), older_data['installs'].sum())

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

    def export_summary_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Exporte un rapport de synthèse"""
        if df.empty:
            return {}

        # Métriques globales
        global_metrics = self._calculate_single_funnel(df)

        # Performance par source
        source_performance = {}
        if 'source' in df.columns:
            for source in df['source'].unique():
                source_data = df[df['source'] == source]
                source_performance[source] = self._calculate_single_funnel(source_data)

        # Performance par plateforme
        platform_performance = {}
        if 'platform' in df.columns:
            for platform in df['platform'].unique():
                platform_data = df[df['platform'] == platform]
                platform_performance[platform] = self._calculate_single_funnel(platform_data)

        # Tendances journalières
        daily_trends = self.aggregate_by_period(df, 'D')

        # Top campagnes
        top_campaigns = self.identify_top_performers(df, 'roas', 5)

        # Insights
        insights = self.generate_insights(df)

        report = {
            'period': {
                'start_date': df['date'].min().strftime('%Y-%m-%d') if 'date' in df.columns else None,
                'end_date': df['date'].max().strftime('%Y-%m-%d') if 'date' in df.columns else None,
                'total_days': (df['date'].max() - df['date'].min()).days + 1 if 'date' in df.columns else 0
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

    def process(self, df: pd.DataFrame, analysis_type: str = 'insights') -> Any:
        """Traite les données selon le type d'analyse demandé"""
        if analysis_type == 'insights':
            return self.generate_insights(df)
        elif analysis_type == 'top_performers':
            return self.identify_top_performers(df)
        elif analysis_type == 'anomalies':
            return self.detect_anomalies(df)
        elif analysis_type == 'cohort':
            return self.calculate_cohort_analysis(df)
        elif analysis_type == 'report':
            return self.export_summary_report(df)
        else:
            return self.generate_insights(df)