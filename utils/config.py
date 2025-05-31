"""
Configuration du dashboard Kolet
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Config:
    """Configuration principale de l'application"""

    # Base de données
    DATABASE_PATH: str = "data/kolet_dashboard.db"

    # Chemins des données
    DATA_DIR: str = "data"
    UPLOAD_DIR: str = "uploads"
    BACKUP_DIR: str = "backups"

    # Configuration Streamlit
    PAGE_TITLE: str = "Kolet - Dashboard Marketing"
    PAGE_ICON: str = "📱"
    LAYOUT: str = "wide"

    # Métriques par défaut
    DEFAULT_CURRENCY: str = "EUR"
    DEFAULT_DATE_FORMAT: str = "%Y-%m-%d"

    # Seuils d'alerte
    CPA_EXCELLENT_THRESHOLD: float = 5.0
    CPA_GOOD_THRESHOLD: float = 15.0
    CPA_AVERAGE_THRESHOLD: float = 30.0

    ROAS_EXCELLENT_THRESHOLD: float = 3.0
    ROAS_GOOD_THRESHOLD: float = 2.0
    ROAS_POOR_THRESHOLD: float = 1.0

    # Configuration des fichiers
    MAX_FILE_SIZE_MB: int = 50

    # Rétention des données (en jours)
    DATA_RETENTION_DAYS: int = 365

    # Configuration de sauvegarde automatique
    AUTO_BACKUP: bool = True
    BACKUP_FREQUENCY_DAYS: int = 7
    MAX_BACKUPS: int = 10

    # Configuration des fichiers
    SUPPORTED_FILE_TYPES: List[str] = field(default_factory=lambda: ['csv'])

    # Mapping des sources de données
    DATA_SOURCE_MAPPING: Dict[str, str] = field(default_factory=lambda: {
        'google_ads': 'Google Ads',
        'apple_search_ads': 'Apple Search Ads',
        'branch_io': 'Branch.io',
        'facebook_ads': 'Facebook Ads',
        'tiktok_ads': 'TikTok Ads'
    })

    # Configuration des colonnes par source
    COLUMN_MAPPINGS: Dict[str, Dict[str, str]] = field(default_factory=lambda: {
        'google_ads': {
            'campaign': 'campaign_name',
            'day': 'date',
            'cost': 'cost',
            'impr.': 'impressions',
            'clicks': 'clicks',
            'installs': 'installs',
            'purchase': 'purchases',
            'conv. value': 'revenue'
        },
        'apple_search_ads': {
            'day': 'date',
            'spend': 'cost',
            'impressions': 'impressions',
            'taps': 'clicks',
            'installs (tap-through)': 'installs'
        },
        'branch_io': {
            'campaign': 'campaign_name',
            'day': 'date',
            'platform': 'platform',
            'ad partner': 'source',
            'unified installs': 'installs',
            'unified purchases': 'purchases',
            'clicks': 'clicks',
            'cost': 'cost',
            'unified revenue': 'revenue',
            'unified opens': 'opens'
        }
    })

    # Types de campagnes
    CAMPAIGN_TYPES: List[str] = field(default_factory=lambda: ['branding', 'acquisition', 'retargeting'])
    CHANNEL_TYPES: List[str] = field(default_factory=lambda: ['app', 'web'])

    # Plateformes supportées
    PLATFORMS: List[str] = field(default_factory=lambda: ['iOS', 'Android', 'Web', 'App'])

    # Configuration des couleurs pour les graphiques
    COLORS: Dict[str, str] = field(default_factory=lambda: {
        'primary': '#3498db',
        'secondary': '#2ecc71',
        'warning': '#f39c12',
        'danger': '#e74c3c',
        'info': '#9b59b6',
        'success': '#27ae60',
        'dark': '#34495e',
        'light': '#ecf0f1'
    })

    COLOR_PALETTES: Dict[str, List[str]] = field(default_factory=lambda: {
        'default': ['#3498db', '#2ecc71', '#f39c12', '#e74c3c', '#9b59b6'],
        'funnel': ['#3498db', '#2ecc71', '#e74c3c'],
        'performance': ['#27ae60', '#f39c12', '#e74c3c'],
        'sources': ['#3498db', '#9b59b6', '#e67e22', '#2ecc71']
    })

    # Configuration des métriques affichées
    MAIN_METRICS: List[Dict[str, str]] = field(default_factory=lambda: [
        {'key': 'cost', 'label': 'Coût Total', 'icon': '💰', 'format': 'currency'},
        {'key': 'impressions', 'label': 'Impressions', 'icon': '👁️', 'format': 'number'},
        {'key': 'clicks', 'label': 'Clics', 'icon': '🖱️', 'format': 'number'},
        {'key': 'installs', 'label': 'Installations', 'icon': '📱', 'format': 'number'},
        {'key': 'conversion_rate', 'label': 'Taux de conversion', 'icon': '📈', 'format': 'percentage'}
    ])

    # Configuration des graphiques
    CHART_CONFIG: Dict[str, Dict] = field(default_factory=lambda: {
        'funnel': {
            'height': 400,
            'show_values': True,
            'connector_style': 'dot'
        },
        'time_series': {
            'height': 500,
            'show_legend': True,
            'line_width': 2
        },
        'bar_chart': {
            'height': 400,
            'orientation': 'vertical'
        },
        'pie_chart': {
            'height': 400,
            'show_percentages': True
        }
    })

    # Messages et textes
    MESSAGES: Dict[str, str] = field(default_factory=lambda: {
        'welcome': "Bienvenue sur le dashboard marketing de Kolet",
        'no_data': "Aucune donnée disponible pour la période sélectionnée",
        'upload_success': "Fichiers chargés avec succès!",
        'upload_error': "Erreur lors du chargement des fichiers",
        'processing': "Traitement des données en cours...",
        'campaign_configured': "Campagne configurée avec succès!"
    })

    # Configuration de l'export
    EXPORT_FORMATS: List[str] = field(default_factory=lambda: ['CSV', 'Excel', 'PDF'])

    # Limite de requêtes par source
    API_RATE_LIMITS: Dict[str, int] = field(default_factory=lambda: {
        'google_ads': 1000,
        'apple_search_ads': 500,
        'branch_io': 2000
    })

    def __post_init__(self):
        """Initialisation post-création"""
        # Créer les dossiers si nécessaire
        os.makedirs(self.DATA_DIR, exist_ok=True)
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        os.makedirs(self.BACKUP_DIR, exist_ok=True)

        # Créer le dossier pour la base de données
        db_dir = os.path.dirname(self.DATABASE_PATH)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

    @classmethod
    def from_env(cls):
        """Crée la configuration à partir des variables d'environnement"""
        return cls(
            DATABASE_PATH=os.getenv('KOLET_DB_PATH', cls.DATABASE_PATH),
            DATA_DIR=os.getenv('KOLET_DATA_DIR', cls.DATA_DIR),
            DEFAULT_CURRENCY=os.getenv('KOLET_CURRENCY', cls.DEFAULT_CURRENCY),
            MAX_FILE_SIZE_MB=int(os.getenv('KOLET_MAX_FILE_SIZE', cls.MAX_FILE_SIZE_MB)),
            DATA_RETENTION_DAYS=int(os.getenv('KOLET_RETENTION_DAYS', cls.DATA_RETENTION_DAYS))
        )


# Instance globale de configuration
config = Config.from_env()