import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from .base_processor import BaseProcessor
from .funnel_processor import FunnelProcessor
from .campaign_processor import CampaignProcessor
from .consolidation_processor import ConsolidationProcessor
from .analytics_processor import AnalyticsProcessor


class DataProcessor(BaseProcessor):
    """
    Processeur principal de données - Orchestrateur des différents modules
    Version modulaire et maintenable
    """

    def __init__(self):
        """Initialise le processeur principal avec tous les sous-processeurs"""
        super().__init__()

        # Initialisation des processeurs spécialisés
        self.funnel_processor = FunnelProcessor()
        self.campaign_processor = CampaignProcessor()
        self.consolidation_processor = ConsolidationProcessor()
        self.analytics_processor = AnalyticsProcessor()

    def prepare_dashboard_data(self, df: pd.DataFrame, platforms: List[str] = None,
                               exclude_unpopulated: bool = True) -> Dict[str, pd.DataFrame]:
        """
        Prépare les données pour l'affichage dans le dashboard - Fonction principale

        Args:
            df: DataFrame avec les données brutes
            platforms: Liste des plateformes à inclure
            exclude_unpopulated: Exclure les données 'Unpopulated' de Branch.io

        Returns:
            Dictionnaire avec les DataFrames traités par source
        """
        if df.empty:
            return self._get_empty_dashboard_data()

        print(f"🔍 DÉBUT - Préparation dashboard avec {len(df)} enregistrements")
        print(f"🔧 Exclude unpopulated: {exclude_unpopulated}")

        # 1. Consolidation et séparation des données
        consolidation_result = self.consolidation_processor.process(df, platforms, exclude_unpopulated)
        consolidated_data = consolidation_result['consolidated']
        separated_data = consolidation_result['separated']

        # 2. Création des funnels App et Web
        funnel_result = self.funnel_processor.process(
            separated_data['asa'],
            separated_data['branch'],
            separated_data['google_ads']
        )

        # 3. Analyse par type de campagne - MODIFIÉ : Passer le paramètre exclude_unpopulated
        campaign_type_data = self.campaign_processor.process(df, exclude_unpopulated)

        # 4. Affichage des résultats pour debug
        self._log_processing_results(funnel_result, consolidated_data, campaign_type_data)

        return {
            'app': funnel_result['app'],
            'web': funnel_result['web'],
            'consolidated': consolidated_data,
            'campaign_types': campaign_type_data,
            'raw': separated_data
        }

    def _get_empty_dashboard_data(self) -> Dict[str, pd.DataFrame]:
        """Retourne une structure vide pour le dashboard"""
        return {
            'app': pd.DataFrame(),
            'web': pd.DataFrame(),
            'consolidated': pd.DataFrame(),
            'campaign_types': pd.DataFrame(),
            'raw': {
                'google_ads': pd.DataFrame(),
                'asa': pd.DataFrame(),
                'branch': pd.DataFrame()
            }
        }

    def _log_processing_results(self, funnel_result: Dict, consolidated_data: pd.DataFrame,
                                campaign_type_data: pd.DataFrame):
        """Log les résultats du traitement pour debug"""
        app_installs = funnel_result['app']['installs'].sum() if not funnel_result['app'].empty else 0
        web_purchases = funnel_result['web']['purchases'].sum() if not funnel_result['web'].empty else 0

        print(f"✅ RÉSULTATS FINAUX:")
        print(f"  • App installs: {app_installs:,}")
        print(f"  • Web purchases: {web_purchases:,}")
        print(f"  • Consolidated records: {len(consolidated_data)}")
        print(f"  • Campaign types analyzed: {len(campaign_type_data)}")

    # Délégation vers les processeurs spécialisés
    def get_campaign_type_summary(self, campaign_analysis: pd.DataFrame) -> Dict[str, Any]:
        """Délègue vers le processeur de campagnes"""
        return self.campaign_processor.get_campaign_type_summary(campaign_analysis)

    def get_campaign_type_insights(self, summary: Dict[str, Any]) -> List[Dict[str, str]]:
        """Délègue vers le processeur de campagnes"""
        return self.campaign_processor.get_campaign_type_insights(summary)

    def calculate_funnel_summary(self, app_data: pd.DataFrame, web_data: pd.DataFrame) -> Dict[str, Any]:
        """Délègue vers le processeur de funnels"""
        return self.funnel_processor.calculate_funnel_summary(app_data, web_data)

    def get_performance_insights(self, app_data: pd.DataFrame, web_data: pd.DataFrame) -> List[Dict[str, str]]:
        """Délègue vers le processeur d'analytics"""
        return self.analytics_processor.get_performance_insights(app_data, web_data)

    def calculate_funnel_metrics(self, df: pd.DataFrame, group_by: str = None) -> Dict[str, Any]:
        """Délègue vers le processeur d'analytics"""
        return self.analytics_processor.calculate_funnel_metrics(df, group_by)

    def compare_periods(self, df: pd.DataFrame, current_start: str, current_end: str,
                        previous_start: str, previous_end: str) -> Dict[str, Any]:
        """Délègue vers le processeur d'analytics"""
        return self.analytics_processor.compare_periods(df, current_start, current_end,
                                                        previous_start, previous_end)

    def identify_top_performers(self, df: pd.DataFrame, metric: str = 'roas',
                                top_n: int = 10) -> pd.DataFrame:
        """Délègue vers le processeur d'analytics"""
        return self.analytics_processor.identify_top_performers(df, metric, top_n)

    def detect_anomalies(self, df: pd.DataFrame, metric: str = 'cost',
                         threshold: float = 2.0) -> pd.DataFrame:
        """Délègue vers le processeur d'analytics"""
        return self.analytics_processor.detect_anomalies(df, metric, threshold)

    def calculate_cohort_analysis(self, df: pd.DataFrame,
                                  cohort_period: str = 'W') -> pd.DataFrame:
        """Délègue vers le processeur d'analytics"""
        return self.analytics_processor.calculate_cohort_analysis(df, cohort_period)

    def aggregate_by_period(self, df: pd.DataFrame, period: str = 'D') -> pd.DataFrame:
        """Délègue vers le processeur d'analytics"""
        return self.analytics_processor.aggregate_by_period(df, period)

    def generate_insights(self, df: pd.DataFrame) -> List[Dict[str, str]]:
        """Délègue vers le processeur d'analytics"""
        return self.analytics_processor.generate_insights(df)

    def export_summary_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Délègue vers le processeur d'analytics"""
        return self.analytics_processor.export_summary_report(df)

    # Méthodes utilitaires conservées pour compatibilité
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

    def process(self, df: pd.DataFrame, processing_type: str = 'dashboard', **kwargs) -> Any:
        """
        Méthode générale de traitement selon le type demandé

        Args:
            df: DataFrame à traiter
            processing_type: Type de traitement ('dashboard', 'funnel', 'campaign', etc.)
            **kwargs: Arguments supplémentaires selon le type

        Returns:
            Résultat selon le type de traitement
        """
        if processing_type == 'dashboard':
            return self.prepare_dashboard_data(
                df,
                kwargs.get('platforms'),
                kwargs.get('exclude_unpopulated', True)
            )
        elif processing_type == 'funnel':
            return self.funnel_processor.process(
                kwargs.get('asa_data', pd.DataFrame()),
                kwargs.get('branch_data', pd.DataFrame()),
                kwargs.get('google_ads_data', pd.DataFrame())
            )
        elif processing_type == 'campaign':
            # MODIFIÉ : Passer le paramètre exclude_unpopulated
            return self.campaign_processor.process(
                df,
                kwargs.get('exclude_unpopulated', True)
            )
        elif processing_type == 'consolidation':
            return self.consolidation_processor.process(
                df,
                kwargs.get('platforms'),
                kwargs.get('exclude_unpopulated', True)
            )
        elif processing_type == 'analytics':
            return self.analytics_processor.process(
                df,
                kwargs.get('analysis_type', 'insights')
            )
        else:
            # Par défaut, préparation du dashboard
            return self.prepare_dashboard_data(df)

    # Méthodes legacy conservées pour la compatibilité ascendante
    def _create_app_funnel_data_with_classification(self, asa_data: pd.DataFrame,
                                                    branch_data: pd.DataFrame,
                                                    google_ads_data: pd.DataFrame) -> pd.DataFrame:
        """LEGACY: Délègue vers le nouveau processeur de funnels"""
        return self.funnel_processor.create_app_funnel_data(asa_data, branch_data, google_ads_data)

    def _create_web_funnel_data_with_classification(self, google_ads_data: pd.DataFrame) -> pd.DataFrame:
        """LEGACY: Délègue vers le nouveau processeur de funnels"""
        return self.funnel_processor.create_web_funnel_data(google_ads_data)

    def _create_campaign_type_analysis(self, df: pd.DataFrame, exclude_unpopulated: bool = True) -> pd.DataFrame:
        """LEGACY: Délègue vers le nouveau processeur de campagnes avec le filtre"""
        return self.campaign_processor.create_campaign_type_analysis(df, exclude_unpopulated)

    def _create_consolidated_data(self, google_ads_data: pd.DataFrame,
                                  asa_data: pd.DataFrame, branch_data: pd.DataFrame) -> pd.DataFrame:
        """LEGACY: Délègue vers le nouveau processeur de consolidation"""
        return self.consolidation_processor.create_consolidated_data(google_ads_data, asa_data, branch_data)