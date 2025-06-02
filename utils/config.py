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

    # MODIFIÉ : Configuration des colonnes par source avec ASA campagnes
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
            # NOUVEAU : Support ASA avec campagnes détaillées
            'day': 'date',
            'campaign name': 'campaign_name',  # AJOUTÉ
            'spend': 'cost',
            'impressions': 'impressions',
            'taps': 'clicks',
            'installs (tap-through)': 'installs',
            # Colonnes supplémentaires ASA
            'campaign status': 'campaign_status',  # AJOUTÉ
            'ad group name': 'ad_group_name',  # AJOUTÉ
            'new downloads (tap-through)': 'new_downloads',  # AJOUTÉ
            'redownloads (tap-through)': 'redownloads'  # AJOUTÉ
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
            'unified opens': 'opens',
            'unified login': 'login'
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

    # MODIFIÉ : Métriques principales avec nouvelles métriques ASA
    MAIN_METRICS: List[Dict[str, str]] = field(default_factory=lambda: [
        {'key': 'cost', 'label': 'Coût Total', 'icon': '💰', 'format': 'currency'},
        {'key': 'impressions', 'label': 'Impressions', 'icon': '👁️', 'format': 'number'},
        {'key': 'clicks', 'label': 'Clics', 'icon': '🖱️', 'format': 'number'},
        {'key': 'installs', 'label': 'Installations', 'icon': '📱', 'format': 'number'},
        {'key': 'new_downloads', 'label': 'Nouveaux téléchargements', 'icon': '⬇️', 'format': 'number'},  # NOUVEAU
        {'key': 'redownloads', 'label': 'Retéléchargements', 'icon': '🔄', 'format': 'number'},  # NOUVEAU
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
        'campaign_configured': "Campagne configurée avec succès!",
        'asa_campaigns_detected': "Campagnes ASA détectées avec succès!",  # NOUVEAU
        'asa_classification_available': "Classification des campagnes ASA disponible"  # NOUVEAU
    })

    # Configuration de l'export
    EXPORT_FORMATS: List[str] = field(default_factory=lambda: ['CSV', 'Excel', 'PDF'])

    # Limite de requêtes par source
    API_RATE_LIMITS: Dict[str, int] = field(default_factory=lambda: {
        'google_ads': 1000,
        'apple_search_ads': 500,
        'branch_io': 2000
    })

    # NOUVEAU : Configuration spécifique ASA
    ASA_CONFIG: Dict[str, Any] = field(default_factory=lambda: {
        'supported_formats': ['campaign', 'summary'],  # Formats de fichiers ASA supportés
        'default_currency': 'EUR',
        'campaign_status_mapping': {
            'RUNNING': 'Actif',
            'PAUSED': 'En pause',
            'CAMPAIGN_ON_HOLD': 'En attente'
        },
        'metrics_mapping': {
            'spend': 'Coût',
            'taps': 'Clics',
            'impressions': 'Impressions',
            'installs': 'Installations',
            'new_downloads': 'Nouveaux téléchargements',
            'redownloads': 'Retéléchargements'
        }
    })

    # NOUVEAU : Configuration de validation des données
    DATA_VALIDATION: Dict[str, Any] = field(default_factory=lambda: {
        'required_columns': {
            'google_ads': ['campaign', 'day', 'cost'],
            'apple_search_ads': ['day', 'spend'],  # Flexible pour ancien/nouveau format
            'branch_io': ['campaign', 'day', 'unified installs']
        },
        'numeric_columns': ['cost', 'spend', 'impressions', 'clicks', 'taps', 'installs', 'purchases', 'revenue'],
        'date_formats': ['%Y-%m-%d', '%Y/%m/%d', '%d/%m/%Y', '%m/%d/%Y'],
        'max_cost_threshold': 10000,  # Alerte si coût journalier > 10k€
        'min_date': '2024-01-01',  # Date minimum acceptable
        'max_future_days': 30  # Jours maximum dans le futur
    })

    # NOUVEAU : Configuration des alertes
    ALERT_CONFIG: Dict[str, Any] = field(default_factory=lambda: {
        'cost_spike_threshold': 200,  # % d'augmentation pour alerte
        'performance_drop_threshold': 50,  # % de baisse pour alerte
        'data_gap_threshold': 3,  # Jours sans données pour alerte
        'notification_channels': ['dashboard', 'log'],
        'alert_levels': {
            'info': '#3498db',
            'warning': '#f39c12',
            'error': '#e74c3c',
            'success': '#2ecc71'
        }
    })

    # NOUVEAU : Configuration de cache
    CACHE_CONFIG: Dict[str, Any] = field(default_factory=lambda: {
        'enable_caching': True,
        'cache_ttl_seconds': 300,  # 5 minutes
        'cache_max_size': 100,  # Nombre max d'éléments en cache
        'cache_strategy': 'lru',  # Least Recently Used
        'cacheable_operations': [
            'get_campaign_data',
            'get_consolidated_metrics',
            'get_source_performance'
        ]
    })

    # NOUVEAU : Configuration de performance
    PERFORMANCE_CONFIG: Dict[str, Any] = field(default_factory=lambda: {
        'batch_size': 1000,  # Taille des lots pour traitement
        'parallel_processing': True,  # Traitement en parallèle
        'max_workers': 4,  # Nombre max de workers
        'memory_limit_mb': 512,  # Limite mémoire par processus
        'query_timeout_seconds': 30,  # Timeout des requêtes DB
        'file_processing_timeout': 120  # Timeout traitement fichiers
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

    def get_column_mapping(self, source_type: str) -> Dict[str, str]:
        """
        Récupère le mapping des colonnes pour une source donnée

        Args:
            source_type: Type de source (google_ads, apple_search_ads, branch_io)

        Returns:
            Dictionnaire de mapping des colonnes
        """
        return self.COLUMN_MAPPINGS.get(source_type, {})

    def get_required_columns(self, source_type: str) -> List[str]:
        """
        Récupère les colonnes requises pour une source

        Args:
            source_type: Type de source

        Returns:
            Liste des colonnes requises
        """
        return self.DATA_VALIDATION['required_columns'].get(source_type, [])

    def get_asa_status_label(self, status_code: str) -> str:
        """
        Convertit un code de statut ASA en libellé français

        Args:
            status_code: Code de statut ASA

        Returns:
            Libellé en français
        """
        return self.ASA_CONFIG['campaign_status_mapping'].get(status_code, status_code)

    def get_metric_label(self, metric_key: str) -> str:
        """
        Récupère le libellé d'une métrique

        Args:
            metric_key: Clé de la métrique

        Returns:
            Libellé de la métrique
        """
        # Chercher dans les métriques principales
        for metric in self.MAIN_METRICS:
            if metric['key'] == metric_key:
                return metric['label']

        # Chercher dans le mapping ASA
        return self.ASA_CONFIG['metrics_mapping'].get(metric_key, metric_key.title())

    def get_color_palette(self, palette_name: str = 'default') -> List[str]:
        """
        Récupère une palette de couleurs

        Args:
            palette_name: Nom de la palette

        Returns:
            Liste des couleurs
        """
        return self.COLOR_PALETTES.get(palette_name, self.COLOR_PALETTES['default'])

    def is_valid_campaign_type(self, campaign_type: str) -> bool:
        """
        Vérifie si un type de campagne est valide

        Args:
            campaign_type: Type de campagne à vérifier

        Returns:
            True si valide
        """
        return campaign_type in self.CAMPAIGN_TYPES

    def is_valid_channel_type(self, channel_type: str) -> bool:
        """
        Vérifie si un type de canal est valide

        Args:
            channel_type: Type de canal à vérifier

        Returns:
            True si valide
        """
        return channel_type in self.CHANNEL_TYPES

    def get_alert_color(self, level: str) -> str:
        """
        Récupère la couleur d'une alerte selon son niveau

        Args:
            level: Niveau d'alerte

        Returns:
            Code couleur hexadécimal
        """
        return self.ALERT_CONFIG['alert_levels'].get(level, self.COLORS['info'])

    def should_cache_operation(self, operation_name: str) -> bool:
        """
        Détermine si une opération doit être mise en cache

        Args:
            operation_name: Nom de l'opération

        Returns:
            True si l'opération doit être cachée
        """
        return (self.CACHE_CONFIG['enable_caching'] and
                operation_name in self.CACHE_CONFIG['cacheable_operations'])

    def validate_file_size(self, file_size_mb: float) -> bool:
        """
        Valide la taille d'un fichier

        Args:
            file_size_mb: Taille du fichier en MB

        Returns:
            True si la taille est acceptable
        """
        return file_size_mb <= self.MAX_FILE_SIZE_MB

    def get_processing_batch_size(self) -> int:
        """
        Récupère la taille de lot pour le traitement

        Returns:
            Taille de lot
        """
        return self.PERFORMANCE_CONFIG['batch_size']


# Instance globale de configuration
config = Config.from_env()