import sqlite3
import pandas as pd
import os
from datetime import datetime
from typing import List, Dict, Any, Optional


class DatabaseManager:
    """Gestionnaire de base de données SQLite pour le dashboard Kolet"""

    def __init__(self, db_path: str = "data/kolet_dashboard.db"):
        """
        Initialise le gestionnaire de base de données

        Args:
            db_path: Chemin vers la base de données SQLite
        """
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """MODIFIÉ : Initialise la base de données avec support ASA campagnes"""
        with sqlite3.connect(self.db_path) as conn:
            # Table pour les données consolidées - COLONNES AJOUTÉES
            conn.execute("""
                CREATE TABLE IF NOT EXISTS campaign_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_name TEXT NOT NULL,
                    source TEXT NOT NULL,  -- 'google_ads', 'apple_search_ads', 'branch_io'
                    platform TEXT,  -- 'iOS', 'Android', 'Web'
                    date DATE NOT NULL,
                    impressions INTEGER DEFAULT 0,
                    clicks INTEGER DEFAULT 0,
                    cost REAL DEFAULT 0,
                    installs INTEGER DEFAULT 0,
                    purchases INTEGER DEFAULT 0,
                    revenue REAL DEFAULT 0,
                    opens INTEGER DEFAULT 0,
                    login INTEGER DEFAULT 0,
                    add_to_cart INTEGER DEFAULT 0,
                    ad_partner TEXT DEFAULT '',  -- Pour Branch.io et ASA
                    campaign_status TEXT DEFAULT '',  -- NOUVEAU : Pour ASA
                    ad_group_name TEXT DEFAULT '',    -- NOUVEAU : Pour ASA  
                    new_downloads INTEGER DEFAULT 0,  -- NOUVEAU : Pour ASA
                    redownloads INTEGER DEFAULT 0,    -- NOUVEAU : Pour ASA
                    import_batch TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Ajouter les nouvelles colonnes si elles n'existent pas (pour migration)
            try:
                conn.execute("ALTER TABLE campaign_data ADD COLUMN campaign_status TEXT DEFAULT ''")
            except sqlite3.OperationalError:
                pass  # Colonne existe déjà

            try:
                conn.execute("ALTER TABLE campaign_data ADD COLUMN ad_group_name TEXT DEFAULT ''")
            except sqlite3.OperationalError:
                pass

            try:
                conn.execute("ALTER TABLE campaign_data ADD COLUMN new_downloads INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass

            try:
                conn.execute("ALTER TABLE campaign_data ADD COLUMN redownloads INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass

            # Table pour la classification des campagnes
            conn.execute("""
                CREATE TABLE IF NOT EXISTS campaign_classification (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_name TEXT UNIQUE NOT NULL,
                    campaign_type TEXT NOT NULL,  -- 'branding', 'acquisition', 'retargeting'
                    channel_type TEXT NOT NULL,   -- 'app', 'web'
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Table pour l'historique des imports
            conn.execute("""
                CREATE TABLE IF NOT EXISTS import_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    records_count INTEGER NOT NULL,
                    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    success BOOLEAN DEFAULT TRUE,
                    error_message TEXT
                )
            """)

            # Index pour améliorer les performances
            conn.execute("CREATE INDEX IF NOT EXISTS idx_campaign_date ON campaign_data(date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_campaign_source ON campaign_data(source)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_campaign_name ON campaign_data(campaign_name)")

            conn.commit()

    def insert_campaign_data(self, data: List[Dict[str, Any]]) -> int:
        """
        MODIFIÉ : Insère les données de campagne avec nouvelles colonnes ASA

        Args:
            data: Liste de dictionnaires contenant les données

        Returns:
            Nombre d'enregistrements insérés
        """
        if not data:
            return 0

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Import batch ID pour traçabilité
            import_batch = f"import_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # MODIFIÉ : Requête d'insertion avec nouvelles colonnes
            query = """
                INSERT INTO campaign_data 
                (campaign_name, source, platform, date, impressions, clicks, cost, 
                 installs, purchases, revenue, opens, login, ad_partner, 
                 campaign_status,add_to_cart, ad_group_name, new_downloads, redownloads, import_batch)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            records = []
            for row in data:
                records.append((
                    row.get('campaign_name', ''),
                    row.get('source', ''),
                    row.get('platform', ''),
                    row.get('date'),
                    row.get('impressions', 0),
                    row.get('clicks', 0),
                    row.get('cost', 0.0),
                    row.get('installs', 0),
                    row.get('purchases', 0),
                    row.get('revenue', 0.0),
                    row.get('opens', 0),
                    row.get('login', 0),
                    row.get('ad_partner', ''),
                    row.get('campaign_status', ''),
                    row.get('add_to_cart', 0),# NOUVEAU
                    row.get('ad_group_name', ''),  # NOUVEAU
                    row.get('new_downloads', 0),  # NOUVEAU
                    row.get('redownloads', 0),  # NOUVEAU
                    import_batch
                ))

            cursor.executemany(query, records)
            conn.commit()

            print(f"✅ Inserted {len(records)} records with batch ID: {import_batch}")

            # Debug pour ASA
            asa_records = [r for r in records if r[1] == 'Apple Search Ads']
            if asa_records:
                print(f"🍎 ASA records inserted: {len(asa_records)}")
                total_asa_cost = sum(r[6] for r in asa_records)  # cost est à l'index 6
                print(f"🍎 ASA total cost: {total_asa_cost:.2f}€")

            return cursor.rowcount

    def get_campaign_data(self, start_date: str = None, end_date: str = None,
                          sources: List[str] = None) -> pd.DataFrame:
        """
        Récupère les données de campagne avec filtres

        Args:
            start_date: Date de début (format YYYY-MM-DD)
            end_date: Date de fin (format YYYY-MM-DD)
            sources: Liste des sources à inclure

        Returns:
            DataFrame avec les données filtrées
        """
        query = """
            SELECT 
                cd.*,
                cc.campaign_type,
                cc.channel_type
            FROM campaign_data cd
            LEFT JOIN campaign_classification cc ON cd.campaign_name = cc.campaign_name
            WHERE 1=1
        """

        params = []

        if start_date:
            query += " AND cd.date >= ?"
            params.append(start_date)

        if end_date:
            query += " AND cd.date <= ?"
            params.append(end_date)

        if sources:
            placeholders = ','.join(['?'] * len(sources))
            query += f" AND cd.source IN ({placeholders})"
            params.extend(sources)

        query += " ORDER BY cd.date DESC, cd.campaign_name"

        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query(query, conn, params=params)

            # Debug : vérifier les colonnes retournées
            print(f"🔍 DB Query Result:")
            print(f"  • Colonnes retournées: {list(df.columns)}")
            print(f"  • Nombre de lignes: {len(df)}")

            if len(df) > 0:
                # Vérifier les totaux par colonne
                for col in ['installs', 'opens', 'login', 'purchases']:
                    if col in df.columns:
                        total = df[col].sum()
                        print(f"  • Total {col}: {total:,}")
                    else:
                        print(f"  • Colonne {col}: NON TROUVÉE")

            return df

    def get_consolidated_metrics(self, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """
        Récupère les métriques consolidées pour la période

        Args:
            start_date: Date de début
            end_date: Date de fin

        Returns:
            Dictionnaire avec les métriques agrégées
        """
        query = """
            SELECT 
                SUM(cost) as total_cost,
                SUM(impressions) as total_impressions,
                SUM(clicks) as total_clicks,
                SUM(installs) as total_installs,
                SUM(purchases) as total_purchases,
                SUM(revenue) as total_revenue,
                COUNT(DISTINCT campaign_name) as total_campaigns,
                COUNT(DISTINCT date) as total_days
            FROM campaign_data
            WHERE 1=1
        """

        params = []
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            result = cursor.fetchone()

            if result:
                return {
                    'total_cost': result[0] or 0,
                    'total_impressions': result[1] or 0,
                    'total_clicks': result[2] or 0,
                    'total_installs': result[3] or 0,
                    'total_purchases': result[4] or 0,
                    'total_revenue': result[5] or 0,
                    'total_campaigns': result[6] or 0,
                    'total_days': result[7] or 0
                }
            return {}

    def classify_campaign(self, campaign_name: str, campaign_type: str, channel_type: str) -> bool:
        """
        Classifie une campagne

        Args:
            campaign_name: Nom de la campagne
            campaign_type: Type de campagne (branding, acquisition, retargeting)
            channel_type: Type de canal (app, web)

        Returns:
            True si la classification a réussi
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO campaign_classification 
                    (campaign_name, campaign_type, channel_type, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, (campaign_name, campaign_type, channel_type))
                conn.commit()
                return True
        except Exception as e:
            print(f"Erreur lors de la classification: {e}")
            return False

    def get_unclassified_campaigns(self) -> pd.DataFrame:
        """
        Récupère les campagnes non classifiées

        Returns:
            DataFrame avec les campagnes sans classification
        """
        query = """
            SELECT DISTINCT cd.campaign_name, cd.source
            FROM campaign_data cd
            LEFT JOIN campaign_classification cc ON cd.campaign_name = cc.campaign_name
            WHERE cc.campaign_name IS NULL
            ORDER BY cd.campaign_name
        """

        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(query, conn)

    def get_daily_performance(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        Récupère les performances journalières agrégées

        Args:
            start_date: Date de début
            end_date: Date de fin

        Returns:
            DataFrame avec les métriques par jour
        """
        query = """
            SELECT 
                date,
                SUM(cost) as daily_cost,
                SUM(impressions) as daily_impressions,
                SUM(clicks) as daily_clicks,
                SUM(installs) as daily_installs,
                SUM(purchases) as daily_purchases,
                SUM(revenue) as daily_revenue,
                CASE 
                    WHEN SUM(impressions) > 0 THEN ROUND(SUM(clicks) * 100.0 / SUM(impressions), 2)
                    ELSE 0 
                END as ctr,
                CASE 
                    WHEN SUM(clicks) > 0 THEN ROUND(SUM(installs) * 100.0 / SUM(clicks), 2)
                    ELSE 0 
                END as conversion_rate,
                CASE 
                    WHEN SUM(installs) > 0 THEN ROUND(SUM(cost) / SUM(installs), 2)
                    ELSE 0 
                END as cpa
            FROM campaign_data
            WHERE 1=1
        """

        params = []
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)

        query += " GROUP BY date ORDER BY date"

        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(query, conn, params=params)

    def get_source_performance(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        Récupère les performances par source

        Args:
            start_date: Date de début
            end_date: Date de fin

        Returns:
            DataFrame avec les métriques par source
        """
        query = """
            SELECT 
                source,
                COUNT(DISTINCT campaign_name) as campaigns_count,
                SUM(cost) as total_cost,
                SUM(impressions) as total_impressions,
                SUM(clicks) as total_clicks,
                SUM(installs) as total_installs,
                SUM(purchases) as total_purchases,
                CASE 
                    WHEN SUM(impressions) > 0 THEN ROUND(SUM(clicks) * 100.0 / SUM(impressions), 2)
                    ELSE 0 
                END as ctr,
                CASE 
                    WHEN SUM(clicks) > 0 THEN ROUND(SUM(installs) * 100.0 / SUM(clicks), 2)
                    ELSE 0 
                END as conversion_rate,
                CASE 
                    WHEN SUM(installs) > 0 THEN ROUND(SUM(cost) / SUM(installs), 2)
                    ELSE 0 
                END as cpa
            FROM campaign_data
            WHERE 1=1
        """

        params = []
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)

        query += " GROUP BY source ORDER BY total_cost DESC"

        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(query, conn, params=params)

    def log_import(self, filename: str, file_type: str, records_count: int,
                   success: bool = True, error_message: str = None):
        """
        Enregistre l'historique d'un import

        Args:
            filename: Nom du fichier importé
            file_type: Type de fichier
            records_count: Nombre d'enregistrements traités
            success: Succès de l'import
            error_message: Message d'erreur si échec
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO import_history 
                (filename, file_type, records_count, success, error_message)
                VALUES (?, ?, ?, ?, ?)
            """, (filename, file_type, records_count, success, error_message))
            conn.commit()

    def get_import_history(self, limit: int = 50) -> pd.DataFrame:
        """
        Récupère l'historique des imports

        Args:
            limit: Nombre maximum d'enregistrements à retourner

        Returns:
            DataFrame avec l'historique des imports
        """
        query = """
            SELECT filename, file_type, records_count, success, 
                   error_message, import_date
            FROM import_history
            ORDER BY import_date DESC
            LIMIT ?
        """

        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(query, conn, params=[limit])

    def cleanup_old_data(self, days_to_keep: int = 90):
        """
        Nettoie les anciennes données

        Args:
            days_to_keep: Nombre de jours de données à conserver
        """
        cutoff_date = (datetime.now() - pd.Timedelta(days=days_to_keep)).strftime('%Y-%m-%d')

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM campaign_data WHERE date < ?", (cutoff_date,))
            deleted_count = cursor.rowcount
            conn.commit()

            return deleted_count

    def backup_database(self, backup_path: str = None):
        """
        Sauvegarde la base de données

        Args:
            backup_path: Chemin de sauvegarde (optionnel)
        """
        if not backup_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f"kolet_dashboard_backup_{timestamp}.db"

        import shutil
        shutil.copy2(self.db_path, backup_path)
        return backup_path

    def get_database_stats(self) -> Dict[str, Any]:
        """
        Récupère les statistiques de la base de données

        Returns:
            Dictionnaire avec les statistiques
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Nombre total d'enregistrements
            cursor.execute("SELECT COUNT(*) FROM campaign_data")
            total_records = cursor.fetchone()[0]

            # Plage de dates
            cursor.execute("SELECT MIN(date), MAX(date) FROM campaign_data")
            date_range = cursor.fetchone()

            # Nombre de campagnes uniques
            cursor.execute("SELECT COUNT(DISTINCT campaign_name) FROM campaign_data")
            unique_campaigns = cursor.fetchone()[0]

            # Nombre de sources
            cursor.execute("SELECT COUNT(DISTINCT source) FROM campaign_data")
            unique_sources = cursor.fetchone()[0]

            # Taille de la base
            cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
            db_size = cursor.fetchone()[0]

            return {
                'total_records': total_records,
                'date_range': date_range,
                'unique_campaigns': unique_campaigns,
                'unique_sources': unique_sources,
                'database_size_bytes': db_size,
                'database_size_mb': round(db_size / (1024 * 1024), 2)
            }

    def get_all_campaigns_with_classification(self) -> pd.DataFrame:
        """
        Récupère toutes les campagnes avec leur classification

        Returns:
            DataFrame avec toutes les campagnes et leur statut de classification
        """
        query = """
            SELECT DISTINCT 
                cd.campaign_name, 
                cd.source, 
                cc.campaign_type, 
                cc.channel_type,
                COUNT(cd.id) as records_count,
                SUM(cd.cost) as total_cost,
                SUM(cd.installs) as total_installs,
                SUM(cd.purchases) as total_purchases,
                SUM(cd.revenue) as total_revenue,
                MIN(cd.date) as first_date,
                MAX(cd.date) as last_date
            FROM campaign_data cd
            LEFT JOIN campaign_classification cc ON cd.campaign_name = cc.campaign_name
            GROUP BY cd.campaign_name, cd.source, cc.campaign_type, cc.channel_type
            ORDER BY cd.campaign_name
        """

        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(query, conn)

    def get_configured_campaigns(self) -> pd.DataFrame:
        """
        Récupère toutes les campagnes qui ont une classification

        Returns:
            DataFrame avec les campagnes configurées uniquement
        """
        query = """
            SELECT DISTINCT 
                cd.campaign_name, 
                cd.source, 
                cc.campaign_type, 
                cc.channel_type,
                cc.created_at,
                cc.updated_at,
                COUNT(cd.id) as records_count,
                SUM(cd.cost) as total_cost,
                SUM(cd.installs) as total_installs
            FROM campaign_data cd
            INNER JOIN campaign_classification cc ON cd.campaign_name = cc.campaign_name
            GROUP BY cd.campaign_name, cd.source, cc.campaign_type, cc.channel_type
            ORDER BY cc.updated_at DESC
        """

        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(query, conn)

    def search_campaigns(self, search_term: str = "", campaign_type: str = "",
                         channel_type: str = "") -> pd.DataFrame:
        """
        Recherche des campagnes selon différents critères

        Args:
            search_term: Terme de recherche dans le nom de campagne
            campaign_type: Type de campagne à filtrer
            channel_type: Canal à filtrer

        Returns:
            DataFrame avec les campagnes correspondant aux critères
        """
        query = """
            SELECT DISTINCT 
                cd.campaign_name, 
                cd.source, 
                cc.campaign_type, 
                cc.channel_type,
                COUNT(cd.id) as records_count,
                SUM(cd.cost) as total_cost,
                SUM(cd.installs) as total_installs
            FROM campaign_data cd
            LEFT JOIN campaign_classification cc ON cd.campaign_name = cc.campaign_name
            WHERE 1=1
        """

        params = []

        if search_term:
            query += " AND cd.campaign_name LIKE ?"
            params.append(f"%{search_term}%")

        if campaign_type:
            query += " AND cc.campaign_type = ?"
            params.append(campaign_type)

        if channel_type:
            query += " AND cc.channel_type = ?"
            params.append(channel_type)

        query += " GROUP BY cd.campaign_name, cd.source, cc.campaign_type, cc.channel_type ORDER BY cd.campaign_name"

        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(query, conn, params=params)

    def update_campaign_classification(self, campaign_name: str, campaign_type: str,
                                       channel_type: str) -> bool:
        """
        Met à jour ou crée la classification d'une campagne
        MODIFIÉ : Version améliorée avec gestion des erreurs

        Args:
            campaign_name: Nom de la campagne
            campaign_type: Type de campagne (branding, acquisition, retargeting)
            channel_type: Type de canal (app, web)

        Returns:
            True si la mise à jour a réussi
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Vérifier si la campagne existe dans les données
                cursor.execute(
                    "SELECT COUNT(*) FROM campaign_data WHERE campaign_name = ?",
                    (campaign_name,)
                )
                if cursor.fetchone()[0] == 0:
                    print(f"⚠️ Campagne '{campaign_name}' non trouvée dans les données")
                    return False

                # Insérer ou mettre à jour la classification
                cursor.execute("""
                    INSERT OR REPLACE INTO campaign_classification 
                    (campaign_name, campaign_type, channel_type, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, (campaign_name, campaign_type, channel_type))

                conn.commit()
                print(f"✅ Classification mise à jour: {campaign_name} -> {campaign_type}/{channel_type}")
                return True

        except Exception as e:
            print(f"❌ Erreur lors de la classification de '{campaign_name}': {e}")
            return False

    def delete_campaign_classification(self, campaign_name: str) -> bool:
        """
        Supprime la classification d'une campagne

        Args:
            campaign_name: Nom de la campagne

        Returns:
            True si la suppression a réussi
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM campaign_classification WHERE campaign_name = ?",
                    (campaign_name,)
                )
                conn.commit()

                if cursor.rowcount > 0:
                    print(f"✅ Classification supprimée pour: {campaign_name}")
                    return True
                else:
                    print(f"⚠️ Aucune classification trouvée pour: {campaign_name}")
                    return False

        except Exception as e:
            print(f"❌ Erreur lors de la suppression de '{campaign_name}': {e}")
            return False

    def delete_all_classifications(self) -> bool:
        """
        Supprime toutes les classifications

        Returns:
            True si la suppression a réussi
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM campaign_classification")
                conn.commit()

                print(f"✅ {cursor.rowcount} classifications supprimées")
                return True

        except Exception as e:
            print(f"❌ Erreur lors de la suppression massive: {e}")
            return False

    def get_classification_history(self, campaign_name: str = None) -> pd.DataFrame:
        """
        Récupère l'historique des modifications de classification

        Args:
            campaign_name: Nom de campagne spécifique (optionnel)

        Returns:
            DataFrame avec l'historique des modifications
        """
        query = """
            SELECT 
                campaign_name,
                campaign_type,
                channel_type,
                created_at,
                updated_at
            FROM campaign_classification
            WHERE 1=1
        """

        params = []
        if campaign_name:
            query += " AND campaign_name = ?"
            params.append(campaign_name)

        query += " ORDER BY updated_at DESC"

        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(query, conn, params=params)

    def get_classification_stats(self) -> Dict[str, Any]:
        """
        Récupère les statistiques des classifications

        Returns:
            Dictionnaire avec les statistiques
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Total des campagnes
            cursor.execute("SELECT COUNT(DISTINCT campaign_name) FROM campaign_data")
            total_campaigns = cursor.fetchone()[0]

            # Campagnes classifiées
            cursor.execute("SELECT COUNT(*) FROM campaign_classification")
            classified_campaigns = cursor.fetchone()[0]

            # Répartition par type
            cursor.execute("""
                SELECT campaign_type, COUNT(*) 
                FROM campaign_classification 
                GROUP BY campaign_type
            """)
            type_distribution = dict(cursor.fetchall())

            # Répartition par canal
            cursor.execute("""
                SELECT channel_type, COUNT(*) 
                FROM campaign_classification 
                GROUP BY channel_type
            """)
            channel_distribution = dict(cursor.fetchall())

            # Dernière modification
            cursor.execute("""
                SELECT MAX(updated_at) 
                FROM campaign_classification
            """)
            last_update = cursor.fetchone()[0]

            return {
                'total_campaigns': total_campaigns,
                'classified_campaigns': classified_campaigns,
                'unclassified_campaigns': total_campaigns - classified_campaigns,
                'classification_rate': (classified_campaigns / total_campaigns * 100) if total_campaigns > 0 else 0,
                'type_distribution': type_distribution,
                'channel_distribution': channel_distribution,
                'last_update': last_update
            }

    def batch_update_classifications(self, updates: List[Dict[str, str]]) -> Dict[str, int]:
        """
        Met à jour plusieurs classifications en une fois

        Args:
            updates: Liste de dictionnaires avec 'campaign_name', 'campaign_type', 'channel_type'

        Returns:
            Dictionnaire avec le nombre de succès et d'échecs
        """
        success_count = 0
        error_count = 0
        errors = []

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                for update in updates:
                    try:
                        cursor.execute("""
                            INSERT OR REPLACE INTO campaign_classification 
                            (campaign_name, campaign_type, channel_type, updated_at)
                            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                        """, (update['campaign_name'], update['campaign_type'], update['channel_type']))

                        success_count += 1

                    except Exception as e:
                        error_count += 1
                        errors.append(f"{update['campaign_name']}: {str(e)}")

                conn.commit()
                print(f"✅ Mise à jour en lot: {success_count} succès, {error_count} erreurs")

        except Exception as e:
            print(f"❌ Erreur lors de la mise à jour en lot: {e}")

        return {
            'success': success_count,
            'errors': error_count,
            'error_details': errors
        }

    def export_classifications_to_csv(self, file_path: str = None) -> str:
        """
        Exporte toutes les classifications vers un fichier CSV

        Args:
            file_path: Chemin du fichier (optionnel)

        Returns:
            Chemin du fichier créé ou contenu CSV
        """
        from datetime import datetime

        # Récupérer toutes les données
        campaigns_data = self.get_all_campaigns_with_classification()

        if file_path:
            campaigns_data.to_csv(file_path, index=False)
            return file_path
        else:
            # Retourner le contenu CSV
            return campaigns_data.to_csv(index=False)

    def import_classifications_from_csv(self, csv_content: str) -> Dict[str, int]:
        """
        Importe des classifications depuis un contenu CSV

        Args:
            csv_content: Contenu du fichier CSV

        Returns:
            Dictionnaire avec les résultats de l'import
        """
        try:
            from io import StringIO
            df = pd.read_csv(StringIO(csv_content))

            # Vérifier les colonnes requises
            required_columns = ['campaign_name', 'campaign_type', 'channel_type']
            if not all(col in df.columns for col in required_columns):
                return {'success': 0, 'errors': 1, 'error_details': ['Colonnes requises manquantes']}

            # Préparer les mises à jour
            updates = []
            for _, row in df.iterrows():
                if pd.notna(row['campaign_type']) and pd.notna(row['channel_type']):
                    updates.append({
                        'campaign_name': row['campaign_name'],
                        'campaign_type': row['campaign_type'],
                        'channel_type': row['channel_type']
                    })

            # Effectuer la mise à jour en lot
            return self.batch_update_classifications(updates)

        except Exception as e:
            return {'success': 0, 'errors': 1, 'error_details': [str(e)]}