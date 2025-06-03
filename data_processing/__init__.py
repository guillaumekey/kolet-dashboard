"""
Module de traitement des données - Architecture modulaire

Ce module contient tous les processeurs de données spécialisés pour le dashboard Kolet:
- BaseProcessor: Classe de base avec méthodes communes
- FunnelProcessor: Traitement des funnels App vs Web
- CampaignProcessor: Analyse des campagnes par type
- ConsolidationProcessor: Consolidation multi-sources
- AnalyticsProcessor: Analyses avancées et insights
- DataProcessor: Orchestrateur principal
"""

from .base_processor import BaseProcessor
from .funnel_processor import FunnelProcessor
from .campaign_processor import CampaignProcessor
from .consolidation_processor import ConsolidationProcessor
from .analytics_processor import AnalyticsProcessor
from .data_processor import DataProcessor

__all__ = [
    'BaseProcessor',
    'FunnelProcessor',
    'CampaignProcessor',
    'ConsolidationProcessor',
    'AnalyticsProcessor',
    'DataProcessor'
]

# Version du module
__version__ = '2.0.0'

# Configuration par défaut
DEFAULT_CONFIG = {
    'safe_division_default': 0,
    'percentage_precision': 2,
    'currency_precision': 2,
    'anomaly_threshold': 2.0,
    'top_performers_default': 10
}


def get_processor(processor_type: str = 'main'):
    """
    Factory function pour obtenir le bon processeur

    Args:
        processor_type: Type de processeur ('main', 'funnel', 'campaign', 'consolidation', 'analytics')

    Returns:
        Instance du processeur demandé
    """
    processors = {
        'main': DataProcessor,
        'funnel': FunnelProcessor,
        'campaign': CampaignProcessor,
        'consolidation': ConsolidationProcessor,
        'analytics': AnalyticsProcessor,
        'base': BaseProcessor
    }

    processor_class = processors.get(processor_type, DataProcessor)
    return processor_class()