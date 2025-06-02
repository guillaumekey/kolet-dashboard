import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Imports des modules personnalisés
from database.db_manager import DatabaseManager
from data_processing.data_loader import DataLoader
from data_processing.data_processor import DataProcessor

# Imports des composants UI
from ui.styles import apply_custom_styles
from ui.components.partner_performance import render_partner_performance_table
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

        # Bouton pour supprimer complètement la base de données
        if st.button("🗑️ Reset DB Complet", type="secondary"):
            if st.session_state.get('confirm_full_reset', False):
                try:
                    # Supprimer la base de données
                    if os.path.exists("data/kolet_dashboard.db"):
                        os.remove("data/kolet_dashboard.db")

                    # Vider le cache
                    st.cache_data.clear()
                    if hasattr(st, 'cache_resource'):
                        st.cache_resource.clear()

                    # Vider le session state
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]

                    st.success("✅ Base de données et cache complètement vidés!")
                    st.rerun()

                except Exception as e:
                    st.error(f"Erreur: {e}")
            else:
                st.session_state.confirm_full_reset = True
                st.warning("⚠️ Cliquez à nouveau pour confirmer la suppression complète")

        # Afficher les informations de debug
        if st.checkbox("🔍 Mode Debug Avancé"):
            st.write("**📊 Diagnostic Base de Données:**")
            try:
                db_exists = os.path.exists("data/kolet_dashboard.db")
                st.write(f"• Base existe: {'✅' if db_exists else '❌'}")

                if db_exists:
                    db_size = os.path.getsize("data/kolet_dashboard.db")
                    st.write(f"• Taille DB: {db_size:,} bytes")

                    # Tester la connexion à la DB
                    try:
                        import sqlite3
                        with sqlite3.connect("data/kolet_dashboard.db") as conn:
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
    """Fonction principale de l'application avec cache management"""

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

    # Toujours afficher la sidebar, même sans base de données
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

        # Section Comparaison par Type de Campagne (SIMPLIFIÉE)
        try:
            if not processed_data.get('campaign_types', pd.DataFrame()).empty:
                st.markdown("---")

                # Générer seulement le résumé (pas d'insights ni recommandations)
                campaign_summary = data_processor.get_campaign_type_summary(processed_data['campaign_types'])

                # Afficher seulement la comparaison (pas les autres sections)
                render_campaign_type_comparison(
                    processed_data['campaign_types'],
                    campaign_summary
                )
            else:
                st.info("💡 Configurez vos campagnes pour voir l'analyse par type (branding, acquisition, retargeting)")
        except Exception as e:
            st.error(f"❌ Erreur comparaison campagnes: {str(e)}")

        # AJOUTER CETTE NOUVELLE SECTION (ne pas remplacer l'ancienne)
        try:
            st.markdown("---")
            render_partner_performance_table(processed_data)
        except Exception as e:
            st.error(f"❌ Erreur performance partenaires: {str(e)}")

        # Section Funnel d'acquisition
        try:
            render_acquisition_funnel(processed_data['app'], processed_data['web'])
        except Exception as e:
            st.error(f"❌ Erreur funnel d'acquisition: {str(e)}")

        # Section Performance temporelle
        try:
            render_temporal_performance(processed_data['consolidated'])
        except Exception as e:
            st.error(f"❌ Erreur performance temporelle: {str(e)}")

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