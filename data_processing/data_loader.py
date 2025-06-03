import pandas as pd
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from database.db_manager import DatabaseManager
from io import StringIO
import numpy as np


class DataLoader:
    """Chargeur et processeur de données pour les différentes sources - VERSION COMPLÈTE ET ROBUSTE"""

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialise le chargeur de données

        Args:
            db_manager: Instance du gestionnaire de base de données
        """
        self.db_manager = db_manager

        # MAPPING ÉTENDU pour tous les formats possibles
        self.column_mappings = {
            'google_ads': {
                # Formats standards Google Ads
                'campaign': 'campaign_name',
                'day': 'date',
                'cost': 'cost',
                'impr.': 'impressions',
                'clicks': 'clicks',
                'installs': 'installs',
                'purchase': 'purchases',
                'conv. value': 'revenue',

                # Variantes courantes
                'impressions': 'impressions',
                'conversions': 'installs',
                'conversion value': 'revenue',
                'cost (eur)': 'cost',
                'cost (€)': 'cost',
                'purchases': 'purchases',
                'date': 'date',
                'campaign name': 'campaign_name',
                'total cost': 'cost',
                'total impressions': 'impressions',
                'total clicks': 'clicks',

                # Formats français
                'campagne': 'campaign_name',
                'jour': 'date',
                'coût': 'cost',
                'impressions': 'impressions',
                'clics': 'clicks',
                'conversions': 'installs',
                'valeur de conversion': 'revenue',
            },
            'apple_search_ads': {
                # Nouveau format avec campagnes détaillées
                'day': 'date',
                'campaign name': 'campaign_name',
                'spend': 'cost',
                'impressions': 'impressions',
                'taps': 'clicks',
                'installs (tap-through)': 'installs',
                'campaign status': 'campaign_status',
                'ad group name': 'ad_group_name',
                'new downloads (tap-through)': 'new_downloads',
                'redownloads (tap-through)': 'redownloads'
            },
            'branch_io': {
                'campaign': 'campaign_name',
                'day': 'date',
                'platform': 'platform',
                'ad partner': 'ad_partner',
                'unified installs': 'installs',
                'unified purchases': 'purchases',
                'clicks': 'clicks',
                'cost': 'cost',
                'unified revenue': 'revenue',
                'unified opens': 'opens',
                'unified login': 'login'
            }
        }

    def detect_file_type(self, filename: str) -> str:
        """
        Détecte le type de fichier basé sur le nom avec meilleure détection

        Args:
            filename: Nom du fichier

        Returns:
            Type de fichier détecté
        """
        filename_lower = filename.lower().replace(' ', '').replace('-', '')

        print(f"🔍 Détection type fichier pour: {filename}")

        # Détection ASA - TRÈS SPÉCIFIQUE
        if 'asa' in filename_lower or ('apple' in filename_lower and 'search' in filename_lower):
            print(f"  → ASA détecté")
            return 'apple_search_ads'

        # Détection Branch.io - TRÈS SPÉCIFIQUE
        elif 'export' in filename_lower or 'branch' in filename_lower or 'reporting' in filename_lower:
            print(f"  → Branch.io détecté")
            return 'branch_io'

        # TOUT LE RESTE = Google Ads (approche sûre)
        else:
            print(f"  → Google Ads détecté (par défaut)")
            return 'google_ads'

    def detect_file_type_by_content(self, df: pd.DataFrame) -> str:
        """
        Détecte le type de fichier basé sur le contenu avec logique améliorée

        Args:
            df: DataFrame à analyser

        Returns:
            Type de fichier détecté
        """
        if df.empty:
            return 'unknown'

        columns = [col.lower().strip() for col in df.columns]
        print(f"🔍 Analyse contenu - Colonnes: {columns[:8]}...")

        # ASA - Nouveau format avec campagnes
        if ('campaign name' in columns and 'spend' in columns and 'taps' in columns):
            print(f"  → ASA par contenu (nouveau format)")
            return 'apple_search_ads'

        # ASA - Ancien format
        elif ('spend' in columns and 'taps' in columns and 'impressions' in columns):
            print(f"  → ASA par contenu (ancien format)")
            return 'apple_search_ads'

        # Branch.io - Très spécifique
        elif ('unified installs' in columns and 'ad partner' in columns):
            print(f"  → Branch.io par contenu")
            return 'branch_io'

        # Google Ads - Patterns typiques
        elif any(col in columns for col in ['campaign', 'day']) and any(
                col in columns for col in ['cost', 'impr.', 'impressions']):
            print(f"  → Google Ads par contenu")
            return 'google_ads'

        # Fallback
        else:
            print(f"  → Google Ads par contenu (défaut)")
            return 'google_ads'

    def preprocess_file(self, file_content: bytes, file_type: str, filename: str = "") -> pd.DataFrame:
        """
        ULTRA-ROBUSTE : Préprocesse le contenu du fichier avec gestion complète des erreurs CSV

        Args:
            file_content: Contenu brut du fichier (bytes)
            file_type: Type de fichier
            filename: Nom du fichier pour debug

        Returns:
            DataFrame nettoyé
        """
        print(f"🔄 Preprocessing {filename} (type: {file_type})")

        # Détecter l'encodage et convertir en string
        content_str = self._decode_file_content(file_content, filename)
        lines = content_str.split('\n')

        print(f"  • Total lignes: {len(lines)}")

        if file_type == 'google_ads':
            return self._preprocess_google_ads(lines, filename)
        elif file_type == 'apple_search_ads':
            return self._preprocess_apple_search_ads(lines, content_str)
        elif file_type == 'branch_io':
            return self._preprocess_branch_io(lines, content_str)
        else:
            # Fallback générique
            return self._preprocess_generic(content_str)

    def _preprocess_google_ads(self, lines: List[str], filename: str) -> pd.DataFrame:
        """Preprocessing spécialisé Google Ads ultra-robuste"""
        print(f"  🎯 TRAITEMENT GOOGLE ADS ULTRA-ROBUSTE")

        # ÉTAPE 1: Analyser la structure du fichier
        non_empty_lines = [line for line in lines if line.strip()]
        print(f"    • Lignes non-vides: {len(non_empty_lines)}")

        if len(non_empty_lines) < 2:
            print(f"    ❌ Fichier trop petit")
            return pd.DataFrame()

        # ÉTAPE 2: Détecter les métadonnées et trouver les données
        data_start_line = self._find_google_ads_header(lines)

        # ÉTAPE 3: Préparer le contenu CSV
        if data_start_line > 0:
            csv_lines = lines[data_start_line:]
        else:
            csv_lines = lines

        # Nettoyer les lignes vides
        csv_lines = [line for line in csv_lines if line.strip()]
        csv_content = '\n'.join(csv_lines)

        print(f"    • Lignes à parser: {len(csv_lines)}")

        # ÉTAPE 4: Essayer différentes stratégies de parsing
        return self._parse_google_ads_with_strategies(csv_content)

    def _find_google_ads_header(self, lines: List[str]) -> int:
        """Trouve la ligne d'en-tête Google Ads"""
        data_start_line = 0

        # Chercher des patterns typiques Google Ads
        for i, line in enumerate(lines[:50]):  # Chercher dans les 50 premières lignes
            line_lower = line.lower().strip()

            # Skip les lignes de métadonnées courantes Google Ads
            if any(skip in line_lower for skip in [
                'account currency', 'time zone', 'date range',
                'downloaded', 'report', 'summary', 'account:', 'currency:'
            ]):
                continue

            # Chercher la ligne de header avec des colonnes
            google_indicators = ['campaign', 'cost', 'impressions', 'impr.', 'clicks', 'day', 'date']
            found_indicators = sum(1 for indicator in google_indicators if indicator in line_lower)

            if found_indicators >= 3:  # Au moins 3 indicateurs
                data_start_line = i
                print(f"    ✅ Header trouvé ligne {i} ({found_indicators} indicateurs): {line[:60]}...")
                break

        # Si pas de header trouvé, chercher une ligne avec beaucoup de séparateurs
        if data_start_line == 0:
            max_separators = 0
            best_line = 0

            for i, line in enumerate(lines[:20]):
                sep_count = max(line.count('\t'), line.count(','), line.count(';'))
                if sep_count > max_separators and sep_count >= 5:
                    max_separators = sep_count
                    best_line = i

            if max_separators > 0:
                data_start_line = best_line
                print(f"    🔍 Ligne avec séparateurs trouvée: {best_line} ({max_separators} séparateurs)")

        return data_start_line

    def _parse_google_ads_with_strategies(self, csv_content: str) -> pd.DataFrame:
        """Parse Google Ads avec différentes stratégies robustes"""

        # Stratégies de parsing ordonnées par probabilité de succès
        parsing_strategies = [
            # Stratégies standard avec gestion d'erreurs
            {'sep': '\t', 'quoting': 1, 'on_bad_lines': 'skip', 'encoding': 'utf-8'},
            {'sep': ',', 'quoting': 1, 'on_bad_lines': 'skip', 'encoding': 'utf-8'},
            {'sep': '\t', 'quoting': 1, 'on_bad_lines': 'skip', 'encoding': 'cp1252'},
            {'sep': ',', 'quoting': 1, 'on_bad_lines': 'skip', 'encoding': 'cp1252'},

            # Stratégies sans guillemets
            {'sep': '\t', 'quoting': 3, 'on_bad_lines': 'skip', 'encoding': 'utf-8'},  # QUOTE_NONE
            {'sep': ',', 'quoting': 3, 'on_bad_lines': 'skip', 'encoding': 'utf-8'},

            # Stratégies alternatives
            {'sep': ';', 'quoting': 1, 'on_bad_lines': 'skip', 'encoding': 'utf-8'},
            {'sep': '|', 'quoting': 1, 'on_bad_lines': 'skip', 'encoding': 'utf-8'},

            # Stratégies de derniers recours
            {'sep': '\t', 'quoting': 0, 'on_bad_lines': 'skip', 'encoding': 'utf-8'},  # QUOTE_MINIMAL
            {'sep': ',', 'quoting': 0, 'on_bad_lines': 'skip', 'encoding': 'utf-8'},
        ]

        best_df = pd.DataFrame()
        best_strategy = None
        best_score = 0

        for i, strategy in enumerate(parsing_strategies):
            try:
                print(f"    🧪 Stratégie {i + 1}: sep='{strategy['sep']}', quoting={strategy['quoting']}")

                # Essayer le parsing avec la stratégie
                df_test = pd.read_csv(StringIO(csv_content), **strategy)

                print(f"      • Résultat: {len(df_test)} lignes, {len(df_test.columns)} colonnes")

                if len(df_test.columns) > 1 and len(df_test) > 0:
                    # Évaluer la qualité du parsing
                    score = self._evaluate_google_ads_quality(df_test)
                    print(f"      • Score qualité: {score}")

                    # Si c'est le meilleur score, garder ce DataFrame
                    if score > best_score:
                        best_df = df_test
                        best_strategy = strategy
                        best_score = score
                        print(f"      ✅ NOUVEAU MEILLEUR: score={score}")

            except Exception as e:
                print(f"      ❌ Erreur: {str(e)[:50]}...")

        # Résultat final
        if not best_df.empty and best_score > 15:
            print(f"  ✅ SUCCÈS Google Ads parsing!")
            print(f"    • Stratégie gagnante: {best_strategy}")
            print(f"    • Score final: {best_score}")
            print(f"    • Résultat: {len(best_df)} lignes, {len(best_df.columns)} colonnes")
            return best_df
        else:
            print(f"  ❌ ÉCHEC parsing Google Ads (meilleur score: {best_score})")
            return pd.DataFrame()

    def _evaluate_google_ads_quality(self, df: pd.DataFrame) -> int:
        """Évalue la qualité d'un DataFrame Google Ads parsé"""
        score = 0
        cols_lower = [str(c).lower() for c in df.columns]

        # Points pour colonnes Google Ads typiques
        if any('campaign' in c for c in cols_lower): score += 10
        if any('cost' in c for c in cols_lower): score += 10
        if any('impression' in c or 'impr' in c for c in cols_lower): score += 10
        if any('click' in c for c in cols_lower): score += 5
        if any('day' in c or 'date' in c for c in cols_lower): score += 5

        # Points pour le nombre de lignes et colonnes
        if len(df) > 10: score += 5
        if len(df) > 50: score += 5
        if 5 <= len(df.columns) <= 30: score += 3

        # Vérifier s'il y a des données numériques
        numeric_data_found = False
        for col in df.columns:
            if any(keyword in str(col).lower() for keyword in ['cost', 'impression', 'click']):
                try:
                    numeric_values = pd.to_numeric(df[col], errors='coerce')
                    if numeric_values.sum() > 0:
                        numeric_data_found = True
                        score += 15
                        break
                except:
                    pass

        return score

    def _preprocess_apple_search_ads(self, lines: List[str], content_str: str) -> pd.DataFrame:
        """Preprocessing spécialisé Apple Search Ads"""
        header_line = -1
        header_patterns = [
            'Day,Campaign Name,',  # Nouveau format avec campagnes
            'Day,Spend,',  # Ancien format sans campagnes
            'Day,'  # Pattern général
        ]

        for i, line in enumerate(lines):
            for pattern in header_patterns:
                if line.strip().startswith(pattern):
                    header_line = i
                    print(f"  • ASA header trouvé ligne {i}: {line[:100]}...")
                    break
            if header_line >= 0:
                break

        if header_line >= 0:
            csv_content = '\n'.join(lines[header_line:])
            return pd.read_csv(StringIO(csv_content), quoting=1)
        else:
            print("  ⚠️ Aucun en-tête ASA trouvé, essai parsing direct")
            return pd.read_csv(StringIO(content_str), quoting=1)

    def _preprocess_branch_io(self, lines: List[str], content_str: str) -> pd.DataFrame:
        """Preprocessing spécialisé Branch.io"""
        header_line = -1
        for i, line in enumerate(lines):
            if line.strip().startswith('campaign,'):
                header_line = i
                break

        if header_line >= 0:
            csv_content = '\n'.join(lines[header_line:])
            return pd.read_csv(StringIO(csv_content), quoting=1)
        else:
            return pd.read_csv(StringIO(content_str), quoting=1)

    def _preprocess_generic(self, content_str: str) -> pd.DataFrame:
        """Preprocessing générique pour fichiers non identifiés"""
        try:
            return pd.read_csv(StringIO(content_str), quoting=1, on_bad_lines='skip')
        except:
            try:
                return pd.read_csv(StringIO(content_str), sep='\t', on_bad_lines='skip')
            except:
                return pd.DataFrame()

    def clean_and_normalize_data(self, df: pd.DataFrame, file_type: str) -> pd.DataFrame:
        """
        Nettoie et normalise les données avec support ASA campagnes

        Args:
            df: DataFrame à nettoyer
            file_type: Type de fichier

        Returns:
            DataFrame nettoyé et normalisé
        """
        if df.empty:
            print(f"  ⚠️ DataFrame vide pour {file_type}")
            return df

        print(f"🧹 Nettoyage {file_type}: {len(df)} lignes, {len(df.columns)} colonnes")

        # Copie pour éviter les modifications sur l'original
        df_clean = df.copy()

        # Nettoyer les noms de colonnes
        df_clean.columns = df_clean.columns.str.lower().str.strip()

        # Supprimer les lignes vides
        df_clean = df_clean.dropna(how='all')

        # Appliquer le mapping selon le type de fichier
        if file_type == 'google_ads':
            df_clean = self._apply_google_ads_mapping(df_clean)
        else:
            # Mapping standard pour autres types
            column_mapping = self.column_mappings.get(file_type, {})
            rename_dict = {old: new for old, new in column_mapping.items() if old in df_clean.columns}
            df_clean = df_clean.rename(columns=rename_dict)

        print(f"  • Colonnes après mapping: {list(df_clean.columns)}")

        # Normaliser les dates
        df_clean = self._normalize_dates(df_clean, file_type)

        # Nettoyer les valeurs numériques
        df_clean = self._clean_numeric_values(df_clean, file_type)

        # Ajouter les colonnes manquantes avec des valeurs par défaut
        df_clean = self._add_missing_columns(df_clean)

        # Définir la source et la plateforme
        df_clean = self._set_source_and_platform(df_clean, file_type)

        # Supprimer les lignes avec des dates invalides
        before_filter = len(df_clean)
        df_clean = df_clean.dropna(subset=['date'])
        after_filter = len(df_clean)

        if before_filter != after_filter:
            print(f"  • Lignes supprimées (dates invalides): {before_filter - after_filter}")

        # Filtrer les lignes avec des métriques valides
        df_clean = df_clean[
            (df_clean['cost'] >= 0) &
            (df_clean['impressions'] >= 0) &
            (df_clean['clicks'] >= 0)
            ]

        print(f"  ✅ Nettoyage terminé: {len(df_clean)} lignes finales")

        return df_clean

    def _apply_google_ads_mapping(self, df_clean: pd.DataFrame) -> pd.DataFrame:
        """Applique un mapping intelligent pour Google Ads"""
        print(f"  🎯 MAPPING GOOGLE ADS INTELLIGENT")

        available_cols = df_clean.columns.tolist()
        print(f"    • Colonnes disponibles: {available_cols}")

        # Mapping intelligent par similarité
        smart_mapping = {}

        # Chercher campaign_name
        for col in available_cols:
            if 'campaign' in col and 'campaign_name' not in smart_mapping.values():
                smart_mapping[col] = 'campaign_name'
                print(f"    • {col} → campaign_name")
                break

        # Chercher date
        for col in available_cols:
            if ('day' in col or 'date' in col) and 'date' not in smart_mapping.values():
                smart_mapping[col] = 'date'
                print(f"    • {col} → date")
                break

        # Chercher cost
        for col in available_cols:
            if ('cost' in col or 'coût' in col) and 'cost' not in smart_mapping.values():
                smart_mapping[col] = 'cost'
                print(f"    • {col} → cost")
                break

        # Chercher impressions
        for col in available_cols:
            if ('impression' in col or 'impr' in col) and 'impressions' not in smart_mapping.values():
                smart_mapping[col] = 'impressions'
                print(f"    • {col} → impressions")
                break

        # Chercher clicks
        for col in available_cols:
            if ('click' in col or 'clic' in col) and 'clicks' not in smart_mapping.values():
                smart_mapping[col] = 'clicks'
                print(f"    • {col} → clicks")
                break

        # Chercher conversions/installs
        for col in available_cols:
            if ('conversion' in col or 'install' in col) and 'installs' not in smart_mapping.values():
                smart_mapping[col] = 'installs'
                print(f"    • {col} → installs")
                break

        # Chercher purchases
        for col in available_cols:
            if ('purchase' in col or 'achat' in col) and 'purchases' not in smart_mapping.values():
                smart_mapping[col] = 'purchases'
                print(f"    • {col} → purchases")
                break

        # Chercher revenue
        for col in available_cols:
            if ('value' in col or 'valeur' in col or 'revenue' in col) and 'revenue' not in smart_mapping.values():
                smart_mapping[col] = 'revenue'
                print(f"    • {col} → revenue")
                break

        # Appliquer le mapping
        df_clean = df_clean.rename(columns=smart_mapping)
        print(f"    ✅ Mapping appliqué: {smart_mapping}")

        return df_clean

    def _normalize_dates(self, df: pd.DataFrame, file_type: str) -> pd.DataFrame:
        """Normalise les dates selon le type de fichier"""
        if 'date' in df.columns:
            print(f"  📅 Normalisation des dates...")

            df['date'] = pd.to_datetime(df['date'], errors='coerce')

            if file_type == 'apple_search_ads':
                # Format ASA : "2025-05-23"
                df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d', errors='coerce')
            elif file_type == 'branch_io':
                # Format Branch.io : 2025/05/23
                df['date'] = pd.to_datetime(df['date'], format='%Y/%m/%d', errors='coerce')

            df['date'] = df['date'].dt.strftime('%Y-%m-%d')

            valid_dates = df['date'].notna().sum()
            print(f"    • Dates valides: {valid_dates}/{len(df)}")

        return df

    def _clean_numeric_values(self, df: pd.DataFrame, file_type: str) -> pd.DataFrame:
        """Nettoie les valeurs numériques"""
        numeric_columns = ['cost', 'impressions', 'clicks', 'installs', 'purchases', 'revenue', 'opens',
                           'new_downloads', 'redownloads', 'login']

        for col in numeric_columns:
            if col in df.columns:
                if df[col].dtype == 'object':
                    # Nettoyer les symboles monétaires, virgules et guillemets
                    df[col] = df[col].astype(str).str.replace(r'[\$,€"\\]', '', regex=True)

                    # Pour Branch.io, nettoyer spécifiquement les virgules comme séparateurs de milliers
                    if file_type == 'branch_io':
                        df[col] = df[col].str.replace(r',(\d{3})', r'\1', regex=True)

                # Convertir en numérique
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        return df

    def _add_missing_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ajoute les colonnes manquantes avec des valeurs par défaut"""
        required_columns = ['campaign_name', 'source', 'platform', 'date', 'impressions',
                            'clicks', 'cost', 'installs', 'purchases', 'revenue', 'opens', 'login', 'ad_partner',
                            'campaign_status', 'ad_group_name', 'new_downloads', 'redownloads']

        for col in required_columns:
            if col not in df.columns:
                if col in ['impressions', 'clicks', 'installs', 'purchases', 'opens', 'login', 'new_downloads',
                           'redownloads']:
                    df[col] = 0
                elif col in ['cost', 'revenue']:
                    df[col] = 0.0
                else:
                    df[col] = ''

        return df

    def _set_source_and_platform(self, df: pd.DataFrame, file_type: str) -> pd.DataFrame:
        """Définit la source et la plateforme selon le type de fichier"""
        if file_type == 'apple_search_ads':
            df['source'] = 'Apple Search Ads'
            df['platform'] = 'iOS'

            # Garder le nom de campagne s'il existe
            if 'campaign_name' not in df.columns or df['campaign_name'].isna().all():
                df['campaign_name'] = 'Apple Search Ads Campaign'

            # Debug pour ASA avec campagnes
            print(f"  🔍 ASA processing:")
            print(f"    • Lignes après nettoyage: {len(df)}")
            print(f"    • Campagnes uniques: {df['campaign_name'].nunique()}")
            print(f"    • Coût total: {df['cost'].sum():.2f}€")
            print(f"    • Installs total: {df['installs'].sum():,}")

        elif file_type == 'google_ads':
            df['source'] = 'Google Ads'
            # Détecter la plateforme depuis le nom de campagne si possible
            if 'campaign_name' in df.columns:
                df['platform'] = df['campaign_name'].apply(self._detect_platform_from_campaign)
            else:
                df['platform'] = 'Web'  # Par défaut pour Google Ads

            # VALIDATION GOOGLE ADS
            total_cost = df['cost'].sum()
            total_impressions = df['impressions'].sum()
            total_clicks = df['clicks'].sum()

            print(f"  🎯 VALIDATION GOOGLE ADS:")
            print(f"    • Coût total: {total_cost:,.2f}€")
            print(f"    • Impressions totales: {total_impressions:,}")
            print(f"    • Clics totaux: {total_clicks:,}")

            if total_cost == 0 and total_impressions == 0:
                print(f"    ❌ ALERTE: Aucune donnée détectée dans Google Ads!")
            else:
                print(f"    ✅ Données Google Ads détectées")

        elif file_type == 'branch_io':
            df['source'] = 'Branch.io'
            # Normaliser les plateformes Branch.io
            if 'platform' in df.columns:
                df['platform'] = df['platform'].map({
                    'IOS_APP': 'iOS',
                    'ANDROID_APP': 'Android',
                    'WEB': 'Web',
                    'TV_APP': 'TV'
                }).fillna(df['platform'])

            # Mapper correctement les partenaires publicitaires
            if 'ad partner' in df.columns:
                df['ad_partner'] = df['ad partner']
                # Garder "Branch.io" comme source principale mais noter le partenaire
                df.loc[df['ad partner'] == 'Apple Search Ads', 'source'] = 'Apple Search Ads'
                df.loc[df['ad partner'] == 'Google AdWords', 'source'] = 'Google AdWords'

        return df

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

        campaign_lower = str(campaign_name).lower()

        if 'ios' in campaign_lower or 'iphone' in campaign_lower or 'app store' in campaign_lower:
            return 'iOS'
        elif 'android' in campaign_lower or 'google play' in campaign_lower:
            return 'Android'
        elif 'app' in campaign_lower:
            return 'App'
        else:
            return 'Web'

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
                content = file_content.decode(encoding)
                print(f"  • Encodage réussi: {encoding}")
                return content
            except UnicodeDecodeError:
                continue

        # En dernier recours, utiliser utf-8 avec erreurs ignorées
        print(f"  ⚠️ Utilisation utf-8 avec erreurs ignorées")
        return file_content.decode('utf-8', errors='ignore')

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
        return self.db_manager.update_campaign_classification(campaign_name, campaign_type, channel_type)

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