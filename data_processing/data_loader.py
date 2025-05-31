import pandas as pd
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from database.db_manager import DatabaseManager
from io import StringIO


class DataLoader:
    """Chargeur et processeur de données pour les différentes sources"""

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialise le chargeur de données

        Args:
            db_manager: Instance du gestionnaire de base de données
        """
        self.db_manager = db_manager

        # Mapping des colonnes par source
        self.column_mappings = {
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
                'unified opens': 'opens',
                'unified login': 'login'  # Mapping correct pour les logins
            }
        }

    def detect_file_type(self, filename: str) -> str:
        """
        Détecte le type de fichier basé sur le nom

        Args:
            filename: Nom du fichier

        Returns:
            Type de fichier détecté
        """
        filename_lower = filename.lower()

        if 'asa' in filename_lower or 'apple' in filename_lower:
            return 'apple_search_ads'
        elif 'export' in filename_lower or 'branch' in filename_lower:
            return 'branch_io'
        elif 'dashboard' in filename_lower or 'google' in filename_lower:
            return 'google_ads'
        else:
            # Détection basée sur les colonnes
            return 'unknown'

    def detect_file_type_by_content(self, df: pd.DataFrame) -> str:
        """
        Détecte le type de fichier basé sur le contenu

        Args:
            df: DataFrame à analyser

        Returns:
            Type de fichier détecté
        """
        columns = [col.lower().strip() for col in df.columns]

        # Apple Search Ads
        if 'spend' in columns and 'taps' in columns and 'impressions' in columns:
            return 'apple_search_ads'

        # Branch.io
        if 'unified installs' in columns and 'ad partner' in columns:
            return 'branch_io'

        # Google Ads
        if 'campaign' in columns and 'cost' in columns and any('impr' in col for col in columns):
            return 'google_ads'

        return 'unknown'

    def preprocess_file(self, file_content: bytes, file_type: str, filename: str = "") -> pd.DataFrame:
        """
        Préprocesse le contenu du fichier avant parsing

        Args:
            file_content: Contenu brut du fichier (bytes)
            file_type: Type de fichier
            filename: Nom du fichier pour debug

        Returns:
            DataFrame nettoyé
        """
        # Détecter l'encodage et convertir en string
        content_str = self._decode_file_content(file_content, filename)
        lines = content_str.split('\n')

        if file_type == 'apple_search_ads':
            # Trouver la ligne d'en-tête pour ASA
            header_line = -1
            for i, line in enumerate(lines):
                if line.strip().startswith('Day,'):
                    header_line = i
                    break

            if header_line >= 0:
                csv_content = '\n'.join(lines[header_line:])
                return pd.read_csv(StringIO(csv_content), quoting=1)  # QUOTE_ALL

        elif file_type == 'branch_io':
            # Trouver la ligne d'en-tête pour Branch.io
            header_line = -1
            for i, line in enumerate(lines):
                if line.strip().startswith('campaign,'):
                    header_line = i
                    break

            if header_line >= 0:
                csv_content = '\n'.join(lines[header_line:])
                return pd.read_csv(StringIO(csv_content), quoting=1)  # QUOTE_ALL

        elif file_type == 'google_ads':
            # Pour Google Ads, ignorer les premières lignes de métadonnées
            data_start = 0
            for i, line in enumerate(lines):
                if 'Campaign' in line and ('Cost' in line or 'Clicks' in line):
                    data_start = i
                    break

            if data_start > 0:
                csv_content = '\n'.join(lines[data_start:])
            else:
                csv_content = content_str

            return pd.read_csv(StringIO(csv_content), sep='\t', quoting=1, encoding='utf-8')

        # Pour autres fichiers, lecture directe avec gestion d'erreurs
        return pd.read_csv(StringIO(content_str), quoting=1)

    def _decode_file_content(self, file_content: bytes, filename: str = "") -> str:
        """
        Décode le contenu du fichier avec gestion des encodages

        Args:
            file_content: Contenu en bytes
            filename: Nom du fichier pour debug

        Returns:
            Contenu décodé en string
        """
        # Essayer différents encodages
        encodings = ['utf-8', 'utf-16', 'cp1252', 'iso-8859-1', 'latin1']

        for encoding in encodings:
            try:
                return file_content.decode(encoding)
            except UnicodeDecodeError:
                continue

        # En dernier recours, utiliser utf-8 avec erreurs ignorées
        return file_content.decode('utf-8', errors='ignore')

    def clean_and_normalize_data(self, df: pd.DataFrame, file_type: str) -> pd.DataFrame:
        """
        Nettoie et normalise les données

        Args:
            df: DataFrame à nettoyer
            file_type: Type de fichier

        Returns:
            DataFrame nettoyé et normalisé
        """
        # Copie pour éviter les modifications sur l'original
        df_clean = df.copy()

        # Nettoyer les noms de colonnes
        df_clean.columns = df_clean.columns.str.lower().str.strip()

        # Supprimer les lignes vides
        df_clean = df_clean.dropna(how='all')

        # Normaliser les colonnes selon le type de fichier
        column_mapping = self.column_mappings.get(file_type, {})

        # Renommer les colonnes
        for old_col, new_col in column_mapping.items():
            if old_col in df_clean.columns:
                df_clean = df_clean.rename(columns={old_col: new_col})

        # Normaliser les dates
        if 'date' in df_clean.columns:
            # Convertir les dates MM/DD/YYYY vers YYYY-MM-DD
            df_clean['date'] = pd.to_datetime(df_clean['date'], errors='coerce')
            # Gérer spécifiquement le format MM/DD/YYYY de Branch.io
            if file_type == 'branch_io':
                # Convertir format américain 2025/05/23 vers 2025-05-23
                df_clean['date'] = pd.to_datetime(df_clean['date'], format='%Y/%m/%d', errors='coerce')

            df_clean['date'] = df_clean['date'].dt.strftime('%Y-%m-%d')

        # Nettoyer les valeurs numériques avec gestion spéciale pour Branch.io
        numeric_columns = ['cost', 'impressions', 'clicks', 'installs', 'purchases', 'revenue', 'opens']

        for col in numeric_columns:
            if col in df_clean.columns:
                if df_clean[col].dtype == 'object':
                    # Nettoyer les symboles monétaires, virgules et guillemets
                    df_clean[col] = df_clean[col].astype(str).str.replace(r'[\$,€"]', '', regex=True)

                    # Pour Branch.io, nettoyer spécifiquement les virgules comme séparateurs de milliers
                    if file_type == 'branch_io':
                        df_clean[col] = df_clean[col].str.replace(r',(\d{3})', r'\1', regex=True)

                # Convertir en numérique
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0)

        # Ajouter les colonnes manquantes avec des valeurs par défaut
        required_columns = ['campaign_name', 'source', 'platform', 'date', 'impressions',
                            'clicks', 'cost', 'installs', 'purchases', 'revenue', 'opens', 'login', 'ad_partner']

        for col in required_columns:
            if col not in df_clean.columns:
                if col in ['impressions', 'clicks', 'installs', 'purchases', 'opens', 'login']:
                    df_clean[col] = 0
                elif col in ['cost', 'revenue']:
                    df_clean[col] = 0.0
                else:
                    df_clean[col] = ''

        # Debug pour Branch.io
        if file_type == 'branch_io':
            print(f"🔍 Branch.io processing:")
            print(f"  • Lignes avant nettoyage: {len(df_clean)}")
            print(f"  • Colonnes détectées: {list(df_clean.columns)}")

            # Calculer les totaux AVANT et APRÈS nettoyage
            installs_before_clean = df_clean['installs'].sum() if 'installs' in df_clean.columns else 0
            print(f"  • Installs AVANT nettoyage: {installs_before_clean:,}")

            # Vérifier les conversions numériques APRÈS nettoyage
            for col in ['installs', 'purchases', 'revenue', 'opens']:
                if col in df_clean.columns:
                    # Compter les valeurs nulles/invalides
                    null_count = df_clean[col].isna().sum()
                    zero_count = (df_clean[col] == 0).sum()
                    non_zero_count = (df_clean[col] > 0).sum()

                    print(f"  • {col}: {null_count} nulls, {zero_count} zéros, {non_zero_count} non-zéros")

                    if col == 'installs':
                        # Vérifier les valeurs avant/après conversion
                        total_after = df_clean[col].sum()
                        print(f"  • Installs APRÈS conversion: {total_after:,}")

                        if installs_before_clean != total_after:
                            print(f"  ⚠️ PERTE LORS CONVERSION: {installs_before_clean - total_after:,} installs")

            # Vérifier les dates
            invalid_dates = df_clean['date'].isna().sum()
            if invalid_dates > 0:
                print(f"  ⚠️ Dates: {invalid_dates} dates invalides")
                # Montrer des exemples de dates problématiques
                invalid_date_examples = df_clean[df_clean['date'].isna()]['date'].head(3).tolist()
                print(f"  • Exemples dates invalides: {invalid_date_examples}")
            else:
                print(f"  ✅ Toutes les dates sont valides")

            # Vérifier les lignes supprimées par les filtres finaux
            lines_after_filters = len(df_clean)
            print(f"  • Lignes APRÈS tous les filtres: {lines_after_filters}")

            # Répartition Unpopulated vs Attributed
            unpopulated_installs = df_clean[df_clean['campaign_name'] == 'Unpopulated']['installs'].sum()
            attributed_installs = df_clean[df_clean['campaign_name'] != 'Unpopulated']['installs'].sum()
            print(f"  • Unpopulated installs: {unpopulated_installs:,}")
            print(f"  • Attributed installs: {attributed_installs:,}")
            print(f"  • Total installs final: {unpopulated_installs + attributed_installs:,}")

            # Debug spécifique : comparer avec fichier d'origine
            print(f"  🎯 COMPARAISON AVEC FICHIER ORIGINAL:")
            print(f"  • Fichier original: 7,920 installs")
            print(f"  • Après traitement: {df_clean['installs'].sum():,} installs")
            difference = 7920 - df_clean['installs'].sum()
            if difference != 0:
                print(f"  ❌ PERTE: {difference:,} installs ({difference / 7920 * 100:.1f}%)")
            else:
                print(f"  ✅ AUCUNE PERTE")

        # Définir la source et la plateforme selon le type de fichier
        if file_type == 'apple_search_ads':
            df_clean['source'] = 'Apple Search Ads'
            df_clean['platform'] = 'iOS'
            df_clean['campaign_name'] = 'Apple Search Ads Campaign'

        elif file_type == 'google_ads':
            df_clean['source'] = 'Google Ads'
            # Détecter la plateforme depuis le nom de campagne si possible
            if 'campaign_name' in df_clean.columns:
                df_clean['platform'] = df_clean['campaign_name'].apply(self._detect_platform_from_campaign)

        elif file_type == 'branch_io':
            df_clean['source'] = 'Branch.io'
            # Normaliser les plateformes Branch.io
            if 'platform' in df_clean.columns:
                df_clean['platform'] = df_clean['platform'].map({
                    'IOS_APP': 'iOS',
                    'ANDROID_APP': 'Android',
                    'WEB': 'Web',
                    'TV_APP': 'TV'
                }).fillna(df_clean['platform'])

            # Mapper correctement les partenaires publicitaires
            if 'ad partner' in df_clean.columns:
                # Conserver le partenaire publicitaire dans une colonne dédiée
                df_clean['ad_partner'] = df_clean['ad partner']
                # Garder "Branch.io" comme source principale mais noter le partenaire
                df_clean.loc[df_clean['ad partner'] == 'Apple Search Ads', 'source'] = 'Apple Search Ads'
                df_clean.loc[df_clean['ad partner'] == 'Google AdWords', 'source'] = 'Google AdWords'

        # Supprimer les lignes avec des dates invalides
        before_date_filter = len(df_clean)
        installs_before_date = df_clean['installs'].sum() if 'installs' in df_clean.columns else 0

        df_clean = df_clean.dropna(subset=['date'])

        after_date_filter = len(df_clean)
        installs_after_date = df_clean['installs'].sum() if 'installs' in df_clean.columns else 0

        if file_type == 'branch_io' and before_date_filter != after_date_filter:
            print(f"  🔍 Filtrage dates invalides:")
            print(f"    • Lignes avant: {before_date_filter}")
            print(f"    • Lignes après: {after_date_filter}")
            print(f"    • Lignes supprimées: {before_date_filter - after_date_filter}")
            print(f"    • Installs avant: {installs_before_date:,}")
            print(f"    • Installs après: {installs_after_date:,}")
            print(f"    • Installs perdus: {installs_before_date - installs_after_date:,}")

        # Filtrer les lignes avec des métriques valides
        before_metrics_filter = len(df_clean)
        installs_before_metrics = df_clean['installs'].sum() if 'installs' in df_clean.columns else 0

        df_clean = df_clean[
            (df_clean['cost'] >= 0) &
            (df_clean['impressions'] >= 0) &
            (df_clean['clicks'] >= 0)
            ]

        after_metrics_filter = len(df_clean)
        installs_after_metrics = df_clean['installs'].sum() if 'installs' in df_clean.columns else 0

        if file_type == 'branch_io' and before_metrics_filter != after_metrics_filter:
            print(f"  🔍 Filtrage métriques invalides:")
            print(f"    • Lignes avant: {before_metrics_filter}")
            print(f"    • Lignes après: {after_metrics_filter}")
            print(f"    • Lignes supprimées: {before_metrics_filter - after_metrics_filter}")
            print(f"    • Installs avant: {installs_before_metrics:,}")
            print(f"    • Installs après: {installs_after_metrics:,}")
            print(f"    • Installs perdus: {installs_before_metrics - installs_after_metrics:,}")

        return df_clean

    def _detect_platform_from_campaign(self, campaign_name: str) -> str:
        """
        Détecte la plateforme depuis le nom de campagne

        Args:
            campaign_name: Nom de la campagne

        Returns:
            Plateforme détectée
        """
        if pd.isna(campaign_name):
            return 'Web'

        campaign_lower = campaign_name.lower()

        if 'ios' in campaign_lower or 'iphone' in campaign_lower or 'app store' in campaign_lower:
            return 'iOS'
        elif 'android' in campaign_lower or 'google play' in campaign_lower:
            return 'Android'
        elif 'app' in campaign_lower:
            return 'App'
        else:
            return 'Web'

    def load_and_process_file(self, file_path: str = None, file_content: bytes = None,
                              filename: str = None, file_type: str = None) -> Tuple[pd.DataFrame, str]:
        """
        Charge et traite un fichier

        Args:
            file_path: Chemin vers le fichier (optionnel)
            file_content: Contenu du fichier en bytes (optionnel)
            filename: Nom du fichier
            file_type: Type de fichier (optionnel, sera détecté si non fourni)

        Returns:
            Tuple (DataFrame traité, type de fichier)
        """
        # Charger le contenu si nécessaire
        if file_content is None and file_path:
            with open(file_path, 'rb') as f:
                file_content = f.read()

        # Détecter le type de fichier si nécessaire
        if file_type is None and filename:
            file_type = self.detect_file_type(filename)

        # Préprocesser et charger
        df = self.preprocess_file(file_content, file_type, filename)

        # Si le type n'est toujours pas déterminé, l'identifier par le contenu
        if file_type == 'unknown':
            file_type = self.detect_file_type_by_content(df)

        # Nettoyer et normaliser
        df_processed = self.clean_and_normalize_data(df, file_type)

        return df_processed, file_type

    def insert_data(self, df: pd.DataFrame, file_type: str, filename: str = "") -> int:
        """
        Insère les données dans la base

        Args:
            df: DataFrame à insérer
            file_type: Type de fichier
            filename: Nom du fichier (pour logging)

        Returns:
            Nombre d'enregistrements insérés
        """
        try:
            # Convertir le DataFrame en liste de dictionnaires
            records = df.to_dict('records')

            # Insérer dans la base
            inserted_count = self.db_manager.insert_campaign_data(records)

            # Logger l'import
            self.db_manager.log_import(filename, file_type, len(records), True)

            return inserted_count

        except Exception as e:
            # Logger l'erreur
            self.db_manager.log_import(filename, file_type, 0, False, str(e))
            raise e

    def get_consolidated_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Récupère les données consolidées pour la période

        Args:
            start_date: Date de début
            end_date: Date de fin

        Returns:
            DataFrame avec les données consolidées
        """
        return self.db_manager.get_campaign_data(start_date, end_date)

    def get_unconfigured_campaigns(self) -> pd.DataFrame:
        """
        Récupère les campagnes non configurées

        Returns:
            DataFrame avec les campagnes sans classification
        """
        return self.db_manager.get_unclassified_campaigns()

    def update_campaign_classification(self, campaign_name: str, campaign_type: str,
                                       channel_type: str) -> bool:
        """
        Met à jour la classification d'une campagne

        Args:
            campaign_name: Nom de la campagne
            campaign_type: Type de campagne
            channel_type: Type de canal

        Returns:
            True si la mise à jour a réussi
        """
        return self.db_manager.classify_campaign(campaign_name, campaign_type, channel_type)

    def validate_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Valide la qualité des données

        Args:
            df: DataFrame à valider

        Returns:
            Rapport de validation
        """
        report = {
            'total_rows': len(df),
            'valid_rows': 0,
            'issues': [],
            'warnings': []
        }

        # Vérifier les colonnes requises
        required_columns = ['date', 'campaign_name', 'source']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            report['issues'].append(f"Colonnes manquantes: {missing_columns}")

        # Vérifier les dates
        if 'date' in df.columns:
            invalid_dates = df['date'].isna().sum()
            if invalid_dates > 0:
                report['warnings'].append(f"{invalid_dates} lignes avec des dates invalides")

        # Vérifier les valeurs négatives dans les métriques
        numeric_columns = ['cost', 'impressions', 'clicks', 'installs']
        for col in numeric_columns:
            if col in df.columns:
                negative_values = (df[col] < 0).sum()
                if negative_values > 0:
                    report['warnings'].append(f"{negative_values} valeurs négatives dans {col}")

        # Calculer les lignes valides
        valid_mask = True
        if 'date' in df.columns:
            valid_mask &= df['date'].notna()

        report['valid_rows'] = valid_mask.sum() if hasattr(valid_mask, 'sum') else len(df)

        return report

    def get_data_summary(self, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """
        Récupère un résumé des données

        Args:
            start_date: Date de début (optionnel)
            end_date: Date de fin (optionnel)

        Returns:
            Résumé des données
        """
        # Métriques consolidées
        metrics = self.db_manager.get_consolidated_metrics(start_date, end_date)

        # Performances par source
        source_performance = self.db_manager.get_source_performance(start_date, end_date)

        # Statistiques de la base
        db_stats = self.db_manager.get_database_stats()

        return {
            'metrics': metrics,
            'source_performance': source_performance.to_dict('records'),
            'database_stats': db_stats
        }