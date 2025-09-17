import streamlit as st
import pandas as pd
from datetime import datetime
import os
import time
import gc

# Imports des modules personnalisés
from database.db_manager import DatabaseManager
from data_processing.data_loader import DataLoader
from data_processing.data_processor import DataProcessor

# Imports des composants UI
from ui.styles import apply_custom_styles
from ui.components.sidebar import render_sidebar
from ui.components.debug_panel import render_debug_panel
from ui.components.kpi_dashboard import render_main_kpis
from ui.components.funnel_charts import render_acquisition_funnel
from ui.components.temporal_charts import render_temporal_performance
from ui.components.comparison_charts import render_app_vs_web_comparison
from ui.components.campaign_performance import render_campaign_performance
from ui.components.campaign_config import show_campaign_configuration
from ui.components.campaign_type_comparison import (
    render_campaign_type_comparison
)
from ui.components.weekly_performance import render_weekly_performance_table

# SUPPRIMÉ : Import de partner_performance


# Configuration de la page
st.set_page_config(
    page_title="Kolet - Dashboard Marketing",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded"
)

def add_debug_controls():
    """Ajoute des contrôles de debug pour vider le cache et reset l'application"""
    with st.sidebar:
        st.markdown("---")
        st.subheader("🛠️ Debug & Reset")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🧹 Vider Cache", help="Vide le cache Streamlit"):
                st.cache_data.clear()
                if hasattr(st, 'cache_resource'):
                    st.cache_resource.clear()
                st.success("Cache vidé!")
                st.rerun()

        with col2:
            if st.button("🔄 Reset App", help="Reset complet de l'application"):
                # Vider le cache
                st.cache_data.clear()
                if hasattr(st, 'cache_resource'):
                    st.cache_resource.clear()

                # Vider le session state
                for key in list(st.session_state.keys()):
                    del st.session_state[key]

                st.success("Application reset!")
                st.rerun()

        # CORRIGÉ : Bouton pour supprimer complètement la base de données
        if st.button("🗑️ Reset DB Complet", type="secondary"):
            if st.session_state.get('confirm_full_reset', False):
                try:
                    # NOUVEAU : Fermer toutes les connexions DB avant suppression
                    gc.collect()  # Force garbage collection

                    # NOUVEAU : Essayer de fermer les connexions explicitement
                    try:
                        # Si on a une instance db_manager globale, la fermer
                        if 'db_manager' in globals():
                            db_manager.close_connections()
                    except:
                        pass

                    # NOUVEAU : Attendre un peu pour que les connexions se ferment
                    time.sleep(0.5)

                    # Supprimer la base de données avec gestion d'erreur améliorée
                    db_path = "data/kolet_dashboard.db"
                    if os.path.exists(db_path):
                        try:
                            os.remove(db_path)
                            st.success("✅ Base de données supprimée avec succès!")
                        except PermissionError:
                            # NOUVEAU : Méthode alternative si fichier verrouillé
                            st.warning("⚠️ Fichier verrouillé. Essai méthode alternative...")

                            # Essayer de renommer le fichier d'abord
                            backup_path = f"{db_path}.backup_{int(time.time())}"
                            try:
                                os.rename(db_path, backup_path)
                                st.info(f"📁 Base renommée vers: {backup_path}")
                                st.success("✅ Reset effectué! Redémarrez l'application pour supprimer complètement.")
                            except Exception as e:
                                st.error(f"❌ Impossible de reset la DB: {e}")
                                return
                        except Exception as e:
                            st.error(f"❌ Erreur lors de la suppression: {e}")
                            return
                    else:
                        st.info("📭 Aucune base de données trouvée")

                    # Vider le cache après suppression DB
                    st.cache_data.clear()
                    if hasattr(st, 'cache_resource'):
                        st.cache_resource.clear()

                    # Vider le session state
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]

                    st.session_state.confirm_full_reset = False
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Erreur inattendue: {e}")
                    st.info("💡 Redémarrez l'application Streamlit pour un reset complet")
            else:
                st.session_state.confirm_full_reset = True
                st.warning("⚠️ Cliquez à nouveau pour confirmer la suppression complète")

        # NOUVEAU : Bouton alternatif pour forcer le reset
        if st.button("⚡ Force Reset (Redémarrage requis)", type="secondary"):
            try:
                # Créer un fichier signal pour indiquer qu'il faut supprimer la DB au prochain démarrage
                os.makedirs("data", exist_ok=True)
                with open("data/.reset_signal", "w") as f:
                    f.write("DELETE_DB")

                st.warning("🔄 Redémarrez l'application Streamlit pour appliquer le reset complet")
                st.info("La base sera supprimée au prochain démarrage")

            except Exception as e:
                st.error(f"Erreur: {e}")

        # Afficher les informations de debug
        if st.checkbox("🔍 Mode Debug Avancé"):
            st.write("**📊 Diagnostic Base de Données:**")
            try:
                db_path = "data/kolet_dashboard.db"
                db_exists = os.path.exists(db_path)
                st.write(f"• Base existe: {'✅' if db_exists else '❌'}")

                if db_exists:
                    db_size = os.path.getsize(db_path)
                    st.write(f"• Taille DB: {db_size:,} bytes")

                    # NOUVEAU : Vérifier si le fichier est verrouillé
                    try:
                        # Essayer d'ouvrir en mode écriture pour tester le verrouillage
                        with open(db_path, 'a'):
                            st.write("• Statut fichier: ✅ Accessible")
                    except PermissionError:
                        st.write("• Statut fichier: 🔒 Verrouillé par un processus")
                    except Exception as e:
                        st.write(f"• Statut fichier: ❓ Erreur - {e}")

                    # Tester la connexion à la DB
                    try:
                        import sqlite3
                        with sqlite3.connect(db_path, timeout=1) as conn:
                            cursor = conn.cursor()
                            cursor.execute("SELECT COUNT(*) FROM campaign_data")
                            count = cursor.fetchone()[0]
                            st.write(f"• Enregistrements: {count:,}")
                    except Exception as e:
                        st.write(f"• Erreur DB: {e}")
                else:
                    st.write("• Base de données non trouvée")

            except Exception as e:
                st.write(f"• Erreur diagnostic: {e}")

            st.write("**🎯 Session State:**")
            if st.session_state:
                st.json(dict(st.session_state))
            else:
                st.write("Session state vide")


def check_database_status():
    """Vérifie le statut de la base de données et affiche des informations"""
    db_path = "data/kolet_dashboard.db"

    if not os.path.exists(db_path):
        return False

    try:
        import sqlite3
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Vérifier si la table existe
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='campaign_data'
            """)
            table_exists = cursor.fetchone() is not None

            if not table_exists:
                return False

            # Vérifier le nombre d'enregistrements
            cursor.execute("SELECT COUNT(*) FROM campaign_data")
            count = cursor.fetchone()[0]

            return count > 0

    except Exception as e:
        return False


def render_welcome_screen():
    """Affiche l'écran d'accueil quand aucune donnée n'est disponible"""

    # Message principal
    st.info("📭 Aucune base de données trouvée. Importez des fichiers pour commencer.")

    # Instructions détaillées
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        ### 🚀 Pour commencer :

        1. **📁 Utilisez la sidebar** pour importer vos fichiers CSV
        2. **📊 Formats supportés** :
           - Google Ads (Dashboard export)
           - Apple Search Ads (Campaign reports)  
           - Branch.io (Export reporting)
        3. **⚙️ Configurez vos campagnes** après l'import
        4. **📈 Analysez vos performances** App vs Web

        ### 📋 Fichiers attendus :
        - `Kolet - Dashboard.csv` → Google Ads
        - `Kolet - Dashboard - ASA.csv` → Apple Search Ads  
        - `kolet-export-reporting.csv` → Branch.io

        ### 🔧 Fonctionnalités disponibles :
        - **KPI globaux** : Coût, impressions, clics, installations
        - **Funnel d'acquisition** : App vs Web avec taux de conversion
        - **Classification campagnes** : Branding, acquisition, retargeting
        - **Comparaisons temporelles** : Évolution des performances
        - **Analyse par canal** : Optimisation App vs Web
        """)

    with col2:
        st.markdown("""
        ### 📊 Métriques suivies :

        **📱 Funnel App :**
        - Impressions → Clics
        - Clics → Installations  
        - Installations → Ouvertures
        - Ouvertures → Connexions
        - Connexions → Achats

        **🌐 Funnel Web :**
        - Impressions → Clics
        - Clics → Ajouts panier
        - Ajouts panier → Achats

        **💡 Classifications :**
        - Types : Branding, Acquisition, Retargeting
        - Canaux : App, Web
        """)

    # Zone d'aide rapide
    with st.expander("❓ Aide rapide", expanded=False):
        st.markdown("""
        **🔍 Résolution de problèmes :**

        - **Fichier non reconnu ?** Vérifiez le format et les colonnes
        - **Données manquantes ?** Utilisez les filtres de date
        - **Cache persistant ?** Utilisez les boutons de reset dans la sidebar
        - **Erreur d'import ?** Consultez les détails d'erreur affichés

        **📞 Support :**

        Cette application analyse les performances marketing de Kolet en comparant l'efficacité des campagnes App vs Web avec des données provenant de Google Ads, Apple Search Ads et Branch.io.
        """)


def main():
    """Fonction principale de l'application avec gestion reset DB"""

    # NOUVEAU : Vérifier le signal de reset au démarrage
    reset_signal_path = "data/.reset_signal"
    if os.path.exists(reset_signal_path):
        try:
            db_path = "data/kolet_dashboard.db"
            if os.path.exists(db_path):
                os.remove(db_path)
                st.success("✅ Base de données supprimée au démarrage!")

            # Supprimer le fichier signal
            os.remove(reset_signal_path)

        except Exception as e:
            st.error(f"Erreur lors du reset au démarrage: {e}")

    # Configuration supplémentaire pour éliminer les espaces blancs
    st.markdown("""
    <style>
        /* Suppression complète des marges et padding par défaut */
        .reportview-container .main .block-container{
            padding-top: 0rem;
            padding-right: 0rem;
            padding-left: 0rem;
            padding-bottom: 0rem;
            margin-left: 0rem;
        }

        /* Container principal sans marge */
        .main .block-container {
            padding-top: 1rem;
            padding-left: 0rem;
            padding-right: 1rem;
            max-width: 100%;
            margin-left: 0rem;
        }

        /* Correction spécifique pour la barre blanche à gauche */
        .css-1lcbmhc.e1fqkh3o0 {
            margin-left: -1rem !important;
            padding-left: 1rem !important;
        }

        .css-k1vhr4.e1fqkh3o3 {
            margin-left: 0rem !important;
            padding-left: 0rem !important;
        }

        /* Sidebar ajustements */
        [data-testid="stSidebar"] > div:first-child {
            width: 300px;
            margin-left: 0px;
        }

        [data-testid="stSidebar"][aria-expanded="true"] > div:first-child {
            width: 300px;
            margin-left: 0px;
        }

        /* Force le contenu à prendre toute la largeur */
        .css-18e3th9 {
            padding-left: 0rem !important;
            margin-left: 0rem !important;
        }

        /* Container App principal */
        .css-1y4p8pa {
            padding-left: 0rem !important;
            margin-left: 0rem !important;
        }

        /* Dernière tentative - Force tous les containers */
        .stApp > div:first-child {
            margin-left: 0rem !important;
            padding-left: 0rem !important;
        }

        /* Si rien ne marche, on cache complètement la marge */
        .main {
            padding-left: 0rem !important;
            margin-left: -1rem !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # Appliquer les styles CSS
    apply_custom_styles()

    # Titre principal
    st.title("📱 Dashboard Campagnes Marketing - Kolet")
    st.markdown("*Analyse des performances App vs Web avec classification des campagnes*")

    # Initialiser les services même sans base de données
    try:
        db_manager = DatabaseManager()
        data_loader = DataLoader(db_manager)
        data_processor = DataProcessor()
    except Exception as e:
        st.error(f"❌ Erreur d'initialisation: {str(e)}")
        st.info("💡 Erreur critique - impossible d'initialiser les services")
        with st.expander("Détails de l'erreur"):
            import traceback
            st.code(traceback.format_exc())
        return

    # Ajouter les contrôles de debug
    add_debug_controls()

    # Render sidebar
    try:
        sidebar_params = render_sidebar(data_loader)
    except Exception as e:
        st.error(f"❌ Erreur dans la sidebar: {str(e)}")
        st.info("💡 Erreur lors du rendu de la sidebar")
        with st.expander("Détails de l'erreur sidebar"):
            import traceback
            st.code(traceback.format_exc())
        return

    # Vérifier si on a des données
    has_data = check_database_status()

    if not has_data:
        # Affichage d'accueil quand pas de données
        render_welcome_screen()
        return

    # Configuration des campagnes (modal)
    if st.session_state.get('show_campaign_config', False):
        try:
            show_campaign_configuration(data_loader)
        except Exception as e:
            st.error(f"❌ Erreur configuration campagnes: {str(e)}")
            with st.expander("Détails erreur configuration"):
                import traceback
                st.code(traceback.format_exc())

    # Récupération des données consolidées
    try:
        data = data_loader.get_consolidated_data(
            sidebar_params['date_range'][0],
            sidebar_params['date_range'][1]
        )

        if data.empty:
            st.warning("📭 Aucune donnée disponible pour la période sélectionnée.")
            st.info("💡 Vérifiez vos filtres de date dans la sidebar")

            # Afficher les données disponibles
            with st.expander("🔍 Diagnostic des données disponibles"):
                try:
                    import sqlite3
                    with sqlite3.connect("data/kolet_dashboard.db") as conn:
                        # Vérifier les dates disponibles
                        cursor = conn.cursor()
                        cursor.execute("SELECT MIN(date), MAX(date), COUNT(*) FROM campaign_data")
                        min_date, max_date, total_records = cursor.fetchone()

                        st.write(f"**Données en base :**")
                        st.write(f"• Total enregistrements : {total_records:,}")
                        st.write(f"• Période disponible : {min_date} à {max_date}")
                        st.write(
                            f"• Période sélectionnée : {sidebar_params['date_range'][0]} à {sidebar_params['date_range'][1]}")

                        # Vérifier par source
                        cursor.execute(
                            "SELECT source, COUNT(*), MIN(date), MAX(date) FROM campaign_data GROUP BY source")
                        sources_info = cursor.fetchall()

                        st.write(f"**Par source :**")
                        for source, count, min_d, max_d in sources_info:
                            st.write(f"• {source}: {count:,} enregistrements ({min_d} à {max_d})")

                except Exception as e:
                    st.write(f"Erreur diagnostic: {e}")

            return

        # Mise à jour des statistiques dans la sidebar
        total_records = len(data)
        unpopulated_records = len(data[(data['source'] == 'Branch.io') & (data['campaign_name'] == 'Unpopulated')])
        classified_campaigns = len(data[data['campaign_type'].notna()])

        st.sidebar.success(f"📊 Total: {total_records:,} enregistrements | Unpopulated: {unpopulated_records:,}")
        st.sidebar.info(f"🏷️ Campagnes classifiées: {classified_campaigns:,}")

        # Panel de debug (fermé par défaut)
        render_debug_panel(data, sidebar_params['date_range'])

        # Traitement des données pour l'affichage
        try:
            processed_data = data_processor.prepare_dashboard_data(
                data,
                sidebar_params['platforms'],
                sidebar_params['exclude_unpopulated']
            )
        except Exception as e:
            st.error(f"❌ Erreur lors du traitement des données: {str(e)}")
            with st.expander("Détails erreur traitement"):
                import traceback
                st.code(traceback.format_exc())
            return

        # =================== SECTIONS DU DASHBOARD ===================

        # Section KPI principaux
        try:
            render_main_kpis(processed_data)
        except Exception as e:
            st.error(f"❌ Erreur KPI principaux: {str(e)}")

        # 🆕 SECTION HEBDOMADAIRE - DEBUG VERSION
        st.write("🔍 DEBUG: Tentative d'affichage de la section hebdomadaire...")

        try:
            st.markdown("---")
            render_weekly_performance_table(
                processed_data=processed_data,  # Même données que les KPIs globaux
                date_range=sidebar_params['date_range'],
                exclude_unpopulated=sidebar_params['exclude_unpopulated']
            )
        except Exception as e:
            st.error(f"❌ Erreur performances hebdomadaires: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

        # Section Comparaison par Type de Campagne
        try:
            if not processed_data.get('campaign_types', pd.DataFrame()).empty:
                st.markdown("---")

                # Générer seulement le résumé (pas d'insights ni recommandations)
                campaign_summary = data_processor.get_campaign_type_summary(processed_data['campaign_types'])

                render_campaign_type_comparison(
                    processed_data['campaign_types'],
                    campaign_summary,
                    processed_data['raw']  # NOUVEAU : Ajouter les données brutes
                )
            else:
                st.info("💡 Configurez vos campagnes pour voir l'analyse par type (branding, acquisition, retargeting)")
        except Exception as e:
            st.error(f"❌ Erreur comparaison campagnes: {str(e)}")

        # SUPPRIMÉ : Section Performance par Partenaire
        # Cette section a été complètement retirée

        st.markdown("---")

        # Section Funnel d'acquisition
        try:
            render_acquisition_funnel(processed_data['app'], processed_data['web'], processed_data)
        except Exception as e:
            st.error(f"❌ Erreur funnel d'acquisition: {str(e)}")

        # Section Performance temporelle
        # CORRECTION FINALE DANS app.py - Section Performance temporelle
        # ===============================================================
        # Respecte TOUTE la logique métier :
        # - Coûts/Impressions/Clics : Google Ads + ASA
        # - App : Installs/Opens/Login/Purchases/Revenue depuis Branch
        # - Web : Purchases/Revenue/Add_to_cart depuis Google Ads

        try:
            # Reproduire EXACTEMENT la logique métier du tableau détaillé
            google_ads_data = pd.DataFrame()
            asa_data = pd.DataFrame()
            branch_data = pd.DataFrame()

            if 'raw' in processed_data and processed_data['raw']:
                if 'google_ads' in processed_data['raw']:
                    google_ads_data = processed_data['raw']['google_ads'].copy()
                if 'asa' in processed_data['raw']:
                    asa_data = processed_data['raw']['asa'].copy()
                if 'branch' in processed_data['raw']:
                    branch_data = processed_data['raw']['branch'].copy()

            # Filtrer seulement les campagnes classifiées
            if not google_ads_data.empty and 'campaign_type' in google_ads_data.columns:
                google_ads_data = google_ads_data[
                    google_ads_data['campaign_type'].notna() &
                    google_ads_data['channel_type'].notna()
                    ]

            if not asa_data.empty and 'campaign_type' in asa_data.columns:
                asa_data = asa_data[
                    asa_data['campaign_type'].notna() &
                    asa_data['channel_type'].notna()
                    ]

            if not branch_data.empty and 'campaign_type' in branch_data.columns:
                branch_data = branch_data[
                    branch_data['campaign_type'].notna() &
                    branch_data['channel_type'].notna()
                    ]

            # Collecter toutes les dates
            all_dates = set()
            for df in [google_ads_data, asa_data, branch_data]:
                if not df.empty and 'date' in df.columns:
                    all_dates.update(pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d'))

            # Construire les données consolidées jour par jour
            consolidated_data = []

            for date in sorted(all_dates):
                # === DONNÉES PUBLICITAIRES (Coûts/Impressions/Clics) ===
                daily_campaigns = {}

                # Google Ads
                if not google_ads_data.empty:
                    google_daily = google_ads_data[google_ads_data['date'] == date]
                    for _, row in google_daily.iterrows():
                        campaign = row.get('campaign_name', 'Unknown')
                        channel = row.get('channel_type', 'unknown')

                        if campaign not in daily_campaigns:
                            daily_campaigns[campaign] = {
                                'date': date,
                                'campaign_name': campaign,
                                'campaign_type': row.get('campaign_type'),
                                'channel_type': channel,
                                'cost': 0,
                                'impressions': 0,
                                'clicks': 0,
                                'installs': 0,
                                'opens': 0,
                                'login': 0,
                                'purchases': 0,
                                'revenue': 0,
                                'add_to_cart': 0
                            }

                        # Toujours ajouter coûts/impressions/clics
                        daily_campaigns[campaign]['cost'] += row.get('cost', 0)
                        daily_campaigns[campaign]['impressions'] += row.get('impressions', 0)
                        daily_campaigns[campaign]['clicks'] += row.get('clicks', 0)

                        # Si WEB : ajouter purchases/revenue/add_to_cart depuis Google Ads
                        if channel == 'web':
                            daily_campaigns[campaign]['purchases'] += row.get('purchases', 0)
                            daily_campaigns[campaign]['revenue'] += row.get('revenue', 0)
                            daily_campaigns[campaign]['add_to_cart'] += row.get('add_to_cart', 0)

                # ASA (toujours App)
                if not asa_data.empty:
                    asa_daily = asa_data[asa_data['date'] == date]
                    for _, row in asa_daily.iterrows():
                        campaign = row.get('campaign_name', row.get('Campaign Name', 'Unknown'))

                        if campaign not in daily_campaigns:
                            daily_campaigns[campaign] = {
                                'date': date,
                                'campaign_name': campaign,
                                'campaign_type': row.get('campaign_type'),
                                'channel_type': 'app',  # ASA est toujours App
                                'cost': 0,
                                'impressions': 0,
                                'clicks': 0,
                                'installs': 0,
                                'opens': 0,
                                'login': 0,
                                'purchases': 0,
                                'revenue': 0,
                                'add_to_cart': 0
                            }

                        # Normaliser les colonnes ASA
                        cost = row.get('cost', row.get('Spend', row.get('spend', 0)))
                        impressions = row.get('impressions', row.get('Impressions', 0))
                        clicks = row.get('clicks', row.get('Taps', row.get('taps', 0)))

                        daily_campaigns[campaign]['cost'] += cost
                        daily_campaigns[campaign]['impressions'] += impressions
                        daily_campaigns[campaign]['clicks'] += clicks

                # === DONNÉES DE CONVERSION APP (Branch.io) ===
                if not branch_data.empty:
                    branch_daily = branch_data[branch_data['date'] == date]
                    for _, row in branch_daily.iterrows():
                        campaign = row.get('campaign_name', 'Unknown')
                        channel = row.get('channel_type', 'unknown')

                        # Branch fournit les données de conversion pour APP uniquement
                        if channel == 'app':
                            if campaign not in daily_campaigns:
                                daily_campaigns[campaign] = {
                                    'date': date,
                                    'campaign_name': campaign,
                                    'campaign_type': row.get('campaign_type'),
                                    'channel_type': channel,
                                    'cost': 0,
                                    'impressions': 0,
                                    'clicks': 0,
                                    'installs': 0,
                                    'opens': 0,
                                    'login': 0,
                                    'purchases': 0,
                                    'revenue': 0,
                                    'add_to_cart': 0
                                }

                            # Pour APP : les métriques de conversion viennent de Branch
                            daily_campaigns[campaign]['installs'] += row.get('installs', 0)
                            daily_campaigns[campaign]['opens'] += row.get('opens', 0)
                            daily_campaigns[campaign]['login'] += row.get('login', 0)
                            daily_campaigns[campaign]['purchases'] += row.get('purchases', 0)
                            daily_campaigns[campaign]['revenue'] += row.get('revenue', 0)

                # Ajouter toutes les campagnes du jour
                consolidated_data.extend(daily_campaigns.values())

            # Convertir en DataFrame
            temporal_data = pd.DataFrame(consolidated_data)

            # S'assurer que toutes les colonnes numériques sont bien typées
            numeric_cols = ['cost', 'impressions', 'clicks', 'installs', 'opens', 'login', 'purchases', 'revenue',
                            'add_to_cart']
            for col in numeric_cols:
                if col in temporal_data.columns:
                    temporal_data[col] = pd.to_numeric(temporal_data[col], errors='coerce').fillna(0)

            # Stats de vérification
            print(f"📊 Données temporelles (logique métier complète):")
            print(f"   - Total lignes: {len(temporal_data)}")
            print(f"   - Campagnes uniques: {temporal_data['campaign_name'].nunique()}")

            # Séparer App et Web pour vérification
            app_data = temporal_data[temporal_data['channel_type'] == 'app']
            web_data = temporal_data[temporal_data['channel_type'] == 'web']

            print(f"\n   📱 APP:")
            print(f"   - Coût (Google Ads + ASA): {app_data['cost'].sum():.2f}€")
            print(f"   - Installs (Branch): {app_data['installs'].sum():.0f}")
            print(f"   - Revenue (Branch): {app_data['revenue'].sum():.2f}€")

            print(f"\n   🌐 WEB:")
            print(f"   - Coût (Google Ads): {web_data['cost'].sum():.2f}€")
            print(f"   - Purchases (Google Ads): {web_data['purchases'].sum():.0f}")
            print(f"   - Revenue (Google Ads): {web_data['revenue'].sum():.2f}€")
            print(f"   - Add to cart (Google Ads): {web_data['add_to_cart'].sum():.0f}")

            print(f"\n   💰 TOTAL:")
            print(f"   - Coût total: {temporal_data['cost'].sum():.2f}€")
            print(f"   - Revenue total: {temporal_data['revenue'].sum():.2f}€")

            render_temporal_performance(
                temporal_data,
                date_range=sidebar_params['date_range'],
                campaign_types_data=processed_data.get('campaign_types', pd.DataFrame())
            )

        except Exception as e:
            st.error(f"❌ Erreur performance temporelle: {str(e)}")
            with st.expander("Détails de l'erreur"):
                import traceback
                st.code(traceback.format_exc())

        # Section Comparaison App vs Web
        try:
            render_app_vs_web_comparison(processed_data['app'], processed_data['web'])
        except Exception as e:
            st.error(f"❌ Erreur comparaison App vs Web: {str(e)}")

        # Section Performance des campagnes
        try:
            render_campaign_performance(processed_data['raw'])
        except Exception as e:
            st.error(f"❌ Erreur performance campagnes: {str(e)}")

        # Section informations de classification
        try:
            _render_classification_status(data)
        except Exception as e:
            st.error(f"❌ Erreur statut classification: {str(e)}")

    except Exception as e:
        st.error(f"❌ Erreur lors du chargement des données: {str(e)}")

        # Affichage détaillé de l'erreur en mode debug
        if st.checkbox("🔍 Afficher les détails de l'erreur"):
            import traceback
            st.code(traceback.format_exc())

        st.info("💡 Essayez de vider le cache ou faire un reset complet via la sidebar.")


def _render_classification_status(data: pd.DataFrame):
    """Affiche le statut de classification des campagnes"""

    st.markdown("---")
    st.subheader("🏷️ Statut de Classification des Campagnes")

    # Statistiques de classification
    total_campaigns = data['campaign_name'].nunique()
    classified_campaigns = data[data['campaign_type'].notna()]['campaign_name'].nunique()
    unclassified_campaigns = total_campaigns - classified_campaigns

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Campagnes", total_campaigns)

    with col2:
        st.metric("Classifiées", classified_campaigns)

    with col3:
        st.metric("Non-classifiées", unclassified_campaigns)

    with col4:
        classification_rate = (classified_campaigns / total_campaigns * 100) if total_campaigns > 0 else 0
        st.metric("Taux Classification", f"{classification_rate:.1f}%")

    # Détail par type de campagne et canal
    if classified_campaigns > 0:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Par Type de Campagne:**")
            campaign_type_counts = data[data['campaign_type'].notna()]['campaign_type'].value_counts()
            for campaign_type, count in campaign_type_counts.items():
                st.write(f"• {campaign_type.title()}: {count:,} enregistrements")

        with col2:
            st.markdown("**Par Canal:**")
            channel_type_counts = data[data['channel_type'].notna()]['channel_type'].value_counts()
            for channel_type, count in channel_type_counts.items():
                st.write(f"• {channel_type.title()}: {count:,} enregistrements")

    # Bouton de configuration rapide
    if unclassified_campaigns > 0:
        st.warning(f"⚠️ {unclassified_campaigns} campagnes ne sont pas classifiées")
        if st.button("⚙️ Configurer les campagnes maintenant"):
            st.session_state.show_campaign_config = True
            st.rerun()
    else:
        st.success("✅ Toutes les campagnes sont classifiées !")


if __name__ == "__main__":
    main()