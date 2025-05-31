import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List, Any
import os

# Imports des modules personnalisés
from database.db_manager import DatabaseManager
from data_processing.data_loader import DataLoader
from data_processing.data_processor import DataProcessor
from utils.config import Config
from utils.helpers import format_currency, format_percentage, calculate_funnel_metrics

# Configuration de la page
st.set_page_config(
    page_title="Kolet - Dashboard Marketing",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé
st.markdown("""
<style>
.metric-card {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 0.5rem 0;
}
.funnel-section {
    background-color: #ffffff;
    padding: 1.5rem;
    border-radius: 0.5rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin: 1rem 0;
}
.kpi-container {
    display: flex;
    justify-content: space-around;
    align-items: center;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 2rem;
    border-radius: 1rem;
    color: white;
    margin: 2rem 0;
}
</style>
""", unsafe_allow_html=True)


def main():
    st.title("📱 Dashboard Campagnes Marketing - Kolet")
    st.markdown("*Analyse des performances App vs Web*")

    # Initialisation de la base de données
    db_manager = DatabaseManager()
    data_loader = DataLoader(db_manager)
    data_processor = DataProcessor()

    # Sidebar pour les contrôles
    with st.sidebar:
        st.header("⚙️ Configuration")

        # Upload de fichiers
        st.subheader("📁 Import de données")

        uploaded_files = st.file_uploader(
            "Sélectionner les fichiers CSV",
            type=['csv'],
            accept_multiple_files=True,
            help="Formats acceptés: Google Ads, Apple Search Ads, Branch.io"
        )

        # Bouton pour supprimer la base de données
        if st.button("🗑️ Supprimer toutes les données", type="secondary"):
            if st.session_state.get('confirm_delete', False):
                try:
                    import os
                    if os.path.exists("data/kolet_dashboard.db"):
                        os.remove("data/kolet_dashboard.db")
                        st.success("✅ Base de données supprimée ! Rechargez vos fichiers.")
                        st.session_state.confirm_delete = False
                        st.rerun()
                    else:
                        st.warning("Aucune base de données trouvée")
                except Exception as e:
                    st.error(f"Erreur: {e}")
            else:
                st.session_state.confirm_delete = True
                st.warning("⚠️ Cliquez à nouveau pour confirmer la suppression")

        if uploaded_files:
            if st.button("🔄 Charger les données"):
                with st.spinner("Chargement des données..."):
                    success_count = 0
                    for file in uploaded_files:
                        try:
                            # Lire le contenu du fichier en bytes
                            file_content = file.read()

                            # Afficher info sur le fichier
                            st.info(f"🔄 Traitement de {file.name} ({len(file_content)} bytes)")

                            # Traiter le fichier
                            processed_data, file_type = data_loader.load_and_process_file(
                                file_content=file_content,
                                filename=file.name
                            )

                            # Afficher les résultats du traitement
                            st.info(f"📊 Type détecté: {file_type}")
                            st.info(f"📊 Lignes traitées: {len(processed_data)}")
                            if 'installs' in processed_data.columns:
                                total_installs = processed_data['installs'].sum()
                                st.info(f"📊 Total installs: {total_installs:,}")

                            # Insérer en base
                            inserted_count = data_loader.insert_data(processed_data, file_type, file.name)
                            success_count += 1

                            st.success(f"✅ {file.name}: {inserted_count} enregistrements traités ({file_type})")

                        except Exception as e:
                            st.error(f"❌ Erreur avec {file.name}: {str(e)}")
                            import traceback
                            st.error(f"Détails: {traceback.format_exc()}")

                    if success_count > 0:
                        st.success(f"🎉 {success_count} fichier(s) traité(s) avec succès!")
                        st.rerun()

        # Filtres
        st.subheader("🔍 Filtres")

        # Sélection de la période
        date_range = st.date_input(
            "Période d'analyse",
            value=(datetime(2025, 5, 16), datetime(2025, 5, 30)),  # Période exacte de Branch.io
            max_value=datetime.now(),
            help="Sélectionner la période à analyser - Par défaut: période des données Branch.io"
        )

        # Filtre par plateforme
        platforms = st.multiselect(
            "Plateformes",
            options=["App", "Web", "iOS", "Android"],
            default=["App", "Web", "iOS", "Android"]
        )

        # Filtre pour exclure les données "Unpopulated"
        exclude_unpopulated = st.checkbox(
            "Exclure les données 'Unpopulated' de Branch.io",
            value=False,  # Changé à False par défaut
            help="Exclure les campagnes non attribuées dans Branch.io"
        )

        # Affichage des statistiques de données
        st.info("📊 Chargement des données...")

        # Classification des campagnes
        st.subheader("🏷️ Classification")
        if st.button("⚙️ Configurer les campagnes"):
            st.session_state.show_campaign_config = True

    # Configuration des campagnes (modal)
    if st.session_state.get('show_campaign_config', False):
        show_campaign_configuration(data_loader)

    # Récupération des données consolidées
    try:
        data = data_loader.get_consolidated_data(date_range[0], date_range[1])

        if data.empty:
            st.warning("📭 Aucune donnée disponible pour la période sélectionnée. Veuillez importer des fichiers.")
            return

        # Affichage des statistiques de données (mise à jour)
        total_records = len(data)
        unpopulated_records = len(data[(data['source'] == 'Branch.io') & (data['campaign_name'] == 'Unpopulated')])
        st.sidebar.success(f"📊 Total: {total_records:,} enregistrements | Unpopulated: {unpopulated_records:,}")

        # Debug : afficher les sources et comptes
        with st.expander("🔍 Debug - Données chargées", expanded=True):
            st.write("**Répartition par source:**")
            source_counts = data['source'].value_counts()
            for source, count in source_counts.items():
                st.write(f"• {source}: {count:,} enregistrements")

            st.write("**Répartition par plateforme:**")
            platform_counts = data['platform'].value_counts()
            for platform, count in platform_counts.items():
                st.write(f"• {platform}: {count:,} enregistrements")

            st.write("**Répartition par campagne (Branch.io):**")
            branch_campaigns = data[data['source'] == 'Branch.io']['campaign_name'].value_counts()
            for campaign, count in branch_campaigns.items():
                st.write(f"• {campaign}: {count:,} enregistrements")

            st.write(f"• **Période sélectionnée**: {date_range[0]} à {date_range[1]}")
            st.write(f"• **Jours inclus**: {(date_range[1] - date_range[0]).days + 1}")

            # Comparer avec la période Branch.io d'origine
            branch_start = datetime(2025, 5, 16).date()
            branch_end = datetime(2025, 5, 30).date()

            if date_range[0] != branch_start or date_range[1] != branch_end:
                st.warning(f"⚠️ Période différente de Branch.io original ({branch_start} à {branch_end})")
                st.info("💡 Pour correspondre aux données Branch.io, utilisez: 2025-05-16 à 2025-05-30")

            st.write("**Colonnes disponibles dans les données:**")
            available_columns = list(data.columns)
            st.write(f"• Colonnes: {', '.join(available_columns)}")

            st.write("**Métriques totales (AVANT filtrage):**")
            total_installs = data['installs'].sum()
            total_installs_branch = data[data['source'] == 'Branch.io']['installs'].sum()
            total_unpopulated = data[(data['source'] == 'Branch.io') & (data['campaign_name'] == 'Unpopulated')][
                'installs'].sum()

            st.write(f"• **Total Installs toutes sources**: {total_installs:,}")
            st.write(f"• **Branch.io Installs**: {total_installs_branch:,}")
            st.write(f"• **Unpopulated Installs**: {total_unpopulated:,}")
            st.write(f"• **Branch.io sans Unpopulated**: {total_installs_branch - total_unpopulated:,}")

            # Vérifier spécifiquement Opens et Logins
            if 'opens' in data.columns:
                total_opens = data['opens'].sum()
                branch_opens = data[data['source'] == 'Branch.io']['opens'].sum()
                st.write(f"• **Total Opens**: {total_opens:,}")
                st.write(f"• **Branch.io Opens**: {branch_opens:,}")
            else:
                st.write("• **Opens**: Colonne non trouvée ❌")

            if 'login' in data.columns:
                total_logins = data['login'].sum()
                branch_logins = data[data['source'] == 'Branch.io']['login'].sum()
                st.write(f"• **Total Logins**: {total_logins:,}")
                st.write(f"• **Branch.io Logins**: {branch_logins:,}")
            else:
                st.write("• **Logins**: Colonne non trouvée ❌")

            # Filtrage par plateformes
            if platforms:
                st.write(f"**Impact du filtre plateformes {platforms}:**")
                before_platform_filter = data['installs'].sum()

                # Détail par plateforme AVANT filtrage
                platform_breakdown_before = data.groupby('platform')['installs'].sum().sort_values(ascending=False)
                st.write("Installs par plateforme (AVANT filtrage):")
                for platform, installs in platform_breakdown_before.items():
                    included = "✅" if platform in platforms else "❌"
                    st.write(f"  {included} {platform}: {installs:,} installs")

                filtered_data = data[data['platform'].isin(platforms)] if platforms else data
                after_platform_filter = filtered_data['installs'].sum()
                st.write(f"• **Total AVANT filtre plateformes**: {before_platform_filter:,}")
                st.write(f"• **Total APRÈS filtre plateformes**: {after_platform_filter:,}")
                st.write(f"• **Différence**: {before_platform_filter - after_platform_filter:,} installs exclus")
            else:
                filtered_data = data
                st.write("• Aucun filtre plateforme appliqué")

            # Détail par plateforme et campagne
            st.write("**Détail Branch.io par plateforme:**")
            branch_detail = data[data['source'] == 'Branch.io'].groupby(['platform', 'campaign_name'])[
                'installs'].sum().reset_index()
            branch_detail = branch_detail.sort_values('installs', ascending=False)
            st.dataframe(branch_detail)

            # Vérifier qu'on a bien toutes les données
            branch_total_detail = branch_detail['installs'].sum()
            branch_total_direct = data[data['source'] == 'Branch.io']['installs'].sum()
            st.write(f"**Vérification totaux Branch.io:**")
            st.write(f"• Somme du détail: {branch_total_detail:,} installs")
            st.write(f"• Total direct: {branch_total_direct:,} installs")

            if branch_total_detail != branch_total_direct:
                st.error(f"⚠️ PROBLÈME: Les totaux ne correspondent pas!")

            # Afficher TOUTES les lignes Branch.io (sans groupement)
            st.write("**TOUTES les lignes Branch.io (top 20):**")
            all_branch = data[data['source'] == 'Branch.io'][
                ['date', 'platform', 'campaign_name', 'installs', 'purchases', 'opens']].sort_values('installs',
                                                                                                     ascending=False)
            st.dataframe(all_branch.head(20))

        # Traitement des données pour l'affichage
        processed_data = data_processor.prepare_dashboard_data(data, platforms, exclude_unpopulated)

        # SECTION MÉTRIQUES PRINCIPALES
        display_main_kpis(processed_data['consolidated'])

        # SECTION FUNNEL D'ACQUISITION
        display_acquisition_funnel(processed_data['app'], processed_data['web'])

        # SECTION PERFORMANCE TEMPORELLE
        display_temporal_performance(processed_data['consolidated'])

        # SECTION COMPARAISON APP VS WEB
        display_app_vs_web_comparison(processed_data['app'], processed_data['web'])

        # SECTION PERFORMANCE DES CAMPAGNES
        display_campaign_performance(processed_data['raw'])

    except Exception as e:
        st.error(f"Erreur lors du chargement des données: {str(e)}")


def display_main_kpis(data):
    """Affichage des KPI principaux avec toutes les métriques"""
    st.markdown("<div class='kpi-container'>", unsafe_allow_html=True)

    # Première ligne de métriques
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        total_spend = data['cost'].sum() if 'cost' in data.columns else 0
        st.metric(
            label="💰 Coût Total",
            value=format_currency(total_spend),
            delta=None
        )

    with col2:
        total_impressions = data['impressions'].sum() if 'impressions' in data.columns else 0
        st.metric(
            label="👁️ Impressions",
            value=f"{int(total_impressions):,}".replace(",", " "),
            delta=None
        )

    with col3:
        total_clicks = data['clicks'].sum() if 'clicks' in data.columns else 0
        st.metric(
            label="🖱️ Clics",
            value=f"{int(total_clicks):,}".replace(",", " "),
            delta=None
        )

    with col4:
        total_installs = data['installs'].sum() if 'installs' in data.columns else 0
        st.metric(
            label="📱 Installations",
            value=f"{int(total_installs):,}".replace(",", " "),
            delta=None
        )

    with col5:
        total_revenue = data['revenue'].sum() if 'revenue' in data.columns else 0
        st.metric(
            label="💵 Revenus",
            value=format_currency(total_revenue),
            delta=None
        )

    # Deuxième ligne de métriques
    col6, col7, col8, col9, col10 = st.columns(5)

    with col6:
        total_opens = data['opens'].sum() if 'opens' in data.columns else 0
        st.metric(
            label="👀 Opens",
            value=f"{int(total_opens):,}".replace(",", " "),
            delta=None
        )

    with col7:
        # Calculer les logins depuis la base de données
        total_login = data['login'].sum() if 'login' in data.columns else 0

        st.metric(
            label="🔐 Logins",
            value=f"{int(total_login):,}".replace(",", " "),
            delta=None
        )

    with col8:
        total_purchases = data['purchases'].sum() if 'purchases' in data.columns else 0
        st.metric(
            label="🛒 Purchases",
            value=f"{int(total_purchases):,}".replace(",", " "),
            delta=None
        )

    with col9:
        roas = total_revenue / total_spend if total_spend > 0 else 0
        st.metric(
            label="📈 ROAS",
            value=f"{roas:.2f}",
            delta=None
        )

    with col10:
        cpa = total_spend / total_installs if total_installs > 0 else 0
        st.metric(
            label="💸 CPA",
            value=format_currency(cpa),
            delta=None
        )

    st.markdown("</div>", unsafe_allow_html=True)


def display_acquisition_funnel(app_data: pd.DataFrame, web_data: pd.DataFrame):
    """Affichage du funnel d'acquisition App vs Web avec métriques spécialisées"""
    st.markdown("<div class='funnel-section'>", unsafe_allow_html=True)
    st.subheader("🎯 Funnel d'Acquisition App vs Web")

    col1, col2 = st.columns(2)

    # Funnel App: Impressions -> Clics -> Installs -> Opens -> Logins -> Purchases
    with col1:
        st.markdown("#### 📱 Funnel App")
        if not app_data.empty:
            app_totals = {
                'impressions': app_data['impressions'].sum(),
                'clicks': app_data['clicks'].sum(),
                'installs': app_data['installs'].sum(),
                'opens': app_data['opens'].sum(),
                'login': app_data.get('login', pd.Series([0])).sum(),
                'purchases': app_data['purchases'].sum(),
                'cost': app_data['cost'].sum(),
                'revenue': app_data['revenue'].sum()
            }

            # Graphique en entonnoir App
            funnel_data_app = [
                ("Impressions", app_totals['impressions'], "#3498db"),
                ("Clics", app_totals['clicks'], "#2ecc71"),
                ("Installations", app_totals['installs'], "#f39c12"),
                ("Ouvertures", app_totals['opens'], "#9b59b6"),
                ("Connexions", app_totals['login'], "#e67e22"),
                ("Achats", app_totals['purchases'], "#e74c3c")
            ]

            fig_app = create_funnel_chart(funnel_data_app, "App")
            st.plotly_chart(fig_app, use_container_width=True)

            # Métriques App
            col1_1, col1_2, col1_3, col1_4 = st.columns(4)
            with col1_1:
                ctr_app = (app_totals['clicks'] / app_totals['impressions'] * 100) if app_totals[
                                                                                          'impressions'] > 0 else 0
                st.metric("CTR", format_percentage(ctr_app))
            with col1_2:
                install_rate = (app_totals['installs'] / app_totals['clicks'] * 100) if app_totals['clicks'] > 0 else 0
                st.metric("Taux Install", format_percentage(install_rate))
            with col1_3:
                cpa = app_totals['cost'] / app_totals['installs'] if app_totals['installs'] > 0 else 0
                st.metric("CPA", format_currency(cpa))
            with col1_4:
                roas_app = app_totals['revenue'] / app_totals['cost'] if app_totals['cost'] > 0 else 0
                st.metric("ROAS", f"{roas_app:.2f}")

            # Ratios de passage App (corrigés)
            st.markdown("**Ratios de passage:**")
            if app_totals['impressions'] > 0:
                impressions_to_clicks = (app_totals['clicks'] / app_totals['impressions'] * 100)
                st.write(f"• Impressions → Clics: {impressions_to_clicks:.2f}%")
            else:
                st.write(f"• Impressions → Clics: 0.00%")

            if app_totals['clicks'] > 0:
                clicks_to_installs = (app_totals['installs'] / app_totals['clicks'] * 100)
                st.write(f"• Clics → Installs: {clicks_to_installs:.2f}%")
            else:
                st.write(f"• Clics → Installs: 0.00%")

            if app_totals['installs'] > 0:
                installs_to_opens = (app_totals['opens'] / app_totals['installs'] * 100)
                st.write(f"• Installs → Opens: {installs_to_opens:.2f}%")

                if app_totals['login'] > 0:
                    opens_to_logins = (app_totals['login'] / app_totals['opens'] * 100) if app_totals[
                                                                                               'opens'] > 0 else 0
                    st.write(f"• Opens → Logins: {opens_to_logins:.2f}%")

                    logins_to_purchases = (app_totals['purchases'] / app_totals['login'] * 100) if app_totals[
                                                                                                       'login'] > 0 else 0
                    st.write(f"• Logins → Purchases: {logins_to_purchases:.2f}%")
                else:
                    st.write(f"• Opens → Logins: 0.00%")
                    st.write(f"• Logins → Purchases: 0.00%")
            else:
                st.write(f"• Installs → Opens: 0.00%")
                st.write(f"• Opens → Logins: 0.00%")
                st.write(f"• Logins → Purchases: 0.00%")
        else:
            st.info("Aucune donnée App disponible")

    # Funnel Web: Impressions -> Clics -> Add to Cart -> Purchases
    with col2:
        st.markdown("#### 🌐 Funnel Web")
        if not web_data.empty:
            web_totals = {
                'impressions': web_data['impressions'].sum(),
                'clicks': web_data['clicks'].sum(),
                'add_to_cart': web_data.get('add_to_cart', pd.Series([0])).sum(),
                'purchases': web_data['purchases'].sum(),
                'cost': web_data['cost'].sum(),
                'revenue': web_data['revenue'].sum()
            }

            # Graphique en entonnoir Web
            funnel_data_web = [
                ("Impressions", web_totals['impressions'], "#9b59b6"),
                ("Clics", web_totals['clicks'], "#f39c12"),
                ("Ajouts Panier", web_totals['add_to_cart'], "#2ecc71"),
                ("Achats", web_totals['purchases'], "#e74c3c")
            ]

            fig_web = create_funnel_chart(funnel_data_web, "Web")
            st.plotly_chart(fig_web, use_container_width=True)

            # Métriques Web
            col2_1, col2_2, col2_3, col2_4 = st.columns(4)
            with col2_1:
                ctr_web = (web_totals['clicks'] / web_totals['impressions'] * 100) if web_totals[
                                                                                          'impressions'] > 0 else 0
                st.metric("CTR", format_percentage(ctr_web))
            with col2_2:
                cart_rate = (web_totals['add_to_cart'] / web_totals['clicks'] * 100) if web_totals['clicks'] > 0 else 0
                st.metric("Taux Panier", format_percentage(cart_rate))
            with col2_3:
                cpa = web_totals['cost'] / web_totals['purchases'] if web_totals['purchases'] > 0 else 0
                st.metric("CPA", format_currency(cpa))
            with col2_4:
                roas_web = web_totals['revenue'] / web_totals['cost'] if web_totals['cost'] > 0 else 0
                st.metric("ROAS", f"{roas_web:.2f}")

            # Ratios de passage Web (corrigés)
            st.markdown("**Ratios de passage:**")
            if web_totals['impressions'] > 0:
                impressions_to_clicks = (web_totals['clicks'] / web_totals['impressions'] * 100)
                st.write(f"• Impressions → Clics: {impressions_to_clicks:.2f}%")
            else:
                st.write(f"• Impressions → Clics: 0.00%")

            if web_totals['clicks'] > 0:
                clicks_to_cart = (web_totals['add_to_cart'] / web_totals['clicks'] * 100)
                st.write(f"• Clics → Panier: {clicks_to_cart:.2f}%")
            else:
                st.write(f"• Clics → Panier: 0.00%")

            if web_totals['add_to_cart'] > 0:
                cart_to_purchases = (web_totals['purchases'] / web_totals['add_to_cart'] * 100)
                st.write(f"• Panier → Achats: {cart_to_purchases:.2f}%")
            else:
                st.write(f"• Panier → Achats: 0.00%")
        else:
            st.info("Aucune donnée Web disponible")

    st.markdown("</div>", unsafe_allow_html=True)


def create_funnel_chart(data, title):
    """Création d'un graphique en entonnoir avec formatage personnalisé"""
    stages = [item[0] for item in data]
    values = [item[1] for item in data]
    colors = [item[2] for item in data]

    fig = go.Figure(go.Funnel(
        y=stages,
        x=values,
        textinfo="value+percent initial",
        texttemplate="<b>%{value:,.0f}</b><br>%{percentInitial}",
        marker=dict(color=colors),
        connector=dict(line=dict(color="royalblue", dash="dot", width=3))
    ))

    fig.update_layout(
        title=f"Funnel {title}",
        font=dict(size=12),
        height=400
    )

    return fig


def display_temporal_performance(data):
    """Affichage des performances temporelles"""
    st.subheader("📊 Performances Journalières")

    # Grouper par date
    daily_data = data.groupby('date').agg({
        'cost': 'sum',
        'impressions': 'sum',
        'clicks': 'sum',
        'installs': 'sum',
        'purchases': 'sum'
    }).reset_index()

    daily_data['date'] = pd.to_datetime(daily_data['date'])
    daily_data = daily_data.sort_values('date')

    # Graphique des métriques principales
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Coût', 'Impressions', 'Clics', 'Installations'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )

    # Coût
    fig.add_trace(
        go.Scatter(x=daily_data['date'], y=daily_data['cost'],
                   name='Coût', line=dict(color='#e74c3c')),
        row=1, col=1
    )

    # Impressions
    fig.add_trace(
        go.Scatter(x=daily_data['date'], y=daily_data['impressions'],
                   name='Impressions', line=dict(color='#3498db')),
        row=1, col=2
    )

    # Clics
    fig.add_trace(
        go.Scatter(x=daily_data['date'], y=daily_data['clicks'],
                   name='Clics', line=dict(color='#2ecc71')),
        row=2, col=1
    )

    # Installations
    fig.add_trace(
        go.Scatter(x=daily_data['date'], y=daily_data['installs'],
                   name='Installations', line=dict(color='#9b59b6')),
        row=2, col=2
    )

    fig.update_layout(height=600, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)


def display_app_vs_web_comparison(app_data: pd.DataFrame, web_data: pd.DataFrame):
    """Comparaison détaillée App vs Web avec nouvelles métriques"""
    st.subheader("📱 vs 🌐 Comparaison App vs Web")

    col1, col2 = st.columns(2)

    with col1:
        # Performance App
        if not app_data.empty:
            app_totals = {
                'cost': app_data['cost'].sum(),
                'installs': app_data['installs'].sum(),
                'revenue': app_data['revenue'].sum(),
                'purchases': app_data['purchases'].sum()
            }

            st.markdown("#### 📱 Performance App")
            col1_1, col1_2, col1_3 = st.columns(3)
            with col1_1:
                st.metric("Coût Total", format_currency(app_totals['cost']))
                st.metric("Installations", f"{app_totals['installs']:,}")
            with col1_2:
                cpa = app_totals['cost'] / app_totals['installs'] if app_totals['installs'] > 0 else 0
                st.metric("CPA", format_currency(cpa))
                roas = app_totals['revenue'] / app_totals['cost'] if app_totals['cost'] > 0 else 0
                st.metric("ROAS", f"{roas:.2f}")
            with col1_3:
                st.metric("Revenus", format_currency(app_totals['revenue']))
                purchases_formatted = f"{int(app_totals['purchases']):,}".replace(",", " ")
                st.metric("Achats", purchases_formatted)
        else:
            st.info("Aucune donnée App")

    with col2:
        # Performance Web
        if not web_data.empty:
            web_totals = {
                'cost': web_data['cost'].sum(),
                'purchases': web_data['purchases'].sum(),
                'revenue': web_data['revenue'].sum()
            }

            st.markdown("#### 🌐 Performance Web")
            col2_1, col2_2, col2_3 = st.columns(3)
            with col2_1:
                st.metric("Coût Total", format_currency(web_totals['cost']))
                purchases_formatted = f"{int(web_totals['purchases']):,}".replace(",", " ")
                st.metric("Achats", purchases_formatted)
            with col2_2:
                cpa = web_totals['cost'] / web_totals['purchases'] if web_totals['purchases'] > 0 else 0
                st.metric("CPA", format_currency(cpa))
                roas = web_totals['revenue'] / web_totals['cost'] if web_totals['cost'] > 0 else 0
                st.metric("ROAS", f"{roas:.2f}")
            with col2_3:
                st.metric("Revenus", format_currency(web_totals['revenue']))
                clicks_formatted = f"{int(web_totals['clicks']):,}".replace(",", " ")
                st.metric("Clics", clicks_formatted)
        else:
            st.info("Aucune donnée Web")

    # Graphique de comparaison ROAS
    if not app_data.empty and not web_data.empty:
        app_roas = app_data['revenue'].sum() / app_data['cost'].sum() if app_data['cost'].sum() > 0 else 0
        web_roas = web_data['revenue'].sum() / web_data['cost'].sum() if web_data['cost'].sum() > 0 else 0

        fig_comparison = go.Figure(data=[
            go.Bar(name='App', x=['ROAS'], y=[app_roas], marker_color='#3498db'),
            go.Bar(name='Web', x=['ROAS'], y=[web_roas], marker_color='#9b59b6')
        ])
        fig_comparison.update_layout(
            title="Comparaison ROAS App vs Web",
            yaxis_title="ROAS",
            height=300
        )
        st.plotly_chart(fig_comparison, use_container_width=True)


def display_campaign_performance(raw_data: Dict[str, pd.DataFrame]):
    """Performance détaillée des campagnes par source"""
    st.subheader("🎯 Performance par Source")

    # Onglets par source
    tab1, tab2, tab3 = st.tabs(["📊 Google Ads", "🍎 Apple Search Ads", "🌿 Branch.io"])

    with tab1:
        if not raw_data['google_ads'].empty:
            google_summary = raw_data['google_ads'].groupby('campaign_name').agg({
                'cost': 'sum',
                'impressions': 'sum',
                'clicks': 'sum',
                'purchases': 'sum',
                'revenue': 'sum'
            }).reset_index()

            # Calcul des métriques
            google_summary['CTR'] = (google_summary['clicks'] / google_summary['impressions'] * 100).round(2)
            google_summary['CPA'] = (google_summary['cost'] / google_summary['purchases'].replace(0, 1)).round(2)
            google_summary['ROAS'] = (google_summary['revenue'] / google_summary['cost'].replace(0, 1)).round(2)

            st.dataframe(google_summary, use_container_width=True)
        else:
            st.info("Aucune donnée Google Ads")

    with tab2:
        if not raw_data['asa'].empty:
            asa_summary = raw_data['asa'].groupby('date').agg({
                'cost': 'sum',
                'impressions': 'sum',
                'clicks': 'sum',
                'installs': 'sum'
            }).reset_index()

            asa_summary['CTR'] = (asa_summary['clicks'] / asa_summary['impressions'] * 100).round(2)
            asa_summary['CPA'] = (asa_summary['cost'] / asa_summary['installs'].replace(0, 1)).round(2)

            st.dataframe(asa_summary, use_container_width=True)
        else:
            st.info("Aucune donnée Apple Search Ads")

    with tab3:
        if not raw_data['branch'].empty:
            branch_summary = raw_data['branch'].groupby(['campaign_name', 'platform']).agg({
                'installs': 'sum',
                'purchases': 'sum',
                'opens': 'sum',
                'revenue': 'sum'
            }).reset_index()

            branch_summary['Purchase Rate'] = (branch_summary['purchases'] / branch_summary['installs'] * 100).round(2)
            branch_summary['Revenue per Install'] = (
                        branch_summary['revenue'] / branch_summary['installs'].replace(0, 1)).round(2)

            st.dataframe(branch_summary, use_container_width=True)
        else:
            st.info("Aucune donnée Branch.io")


def show_campaign_configuration(data_loader):
    """Interface de configuration des campagnes"""
    st.subheader("🏷️ Configuration des Campagnes")

    # Récupérer la liste des campagnes non configurées
    unconfigured_campaigns = data_loader.get_unconfigured_campaigns()

    if unconfigured_campaigns.empty:
        st.success("✅ Toutes les campagnes sont configurées!")
        if st.button("Fermer"):
            st.session_state.show_campaign_config = False
        return

    # Interface de configuration
    for idx, campaign in unconfigured_campaigns.iterrows():
        with st.expander(f"Configurer: {campaign['campaign_name']}"):
            col1, col2 = st.columns(2)

            with col1:
                campaign_type = st.selectbox(
                    "Type de campagne",
                    options=["branding", "acquisition", "retargeting"],
                    key=f"type_{idx}"
                )

            with col2:
                channel_type = st.selectbox(
                    "Canal",
                    options=["app", "web"],
                    key=f"channel_{idx}"
                )

            if st.button(f"Sauvegarder", key=f"save_{idx}"):
                data_loader.update_campaign_classification(
                    campaign['campaign_name'],
                    campaign_type,
                    channel_type
                )
                st.success("✅ Campagne configurée!")
                st.rerun()

    if st.button("Fermer la configuration"):
        st.session_state.show_campaign_config = False
        st.rerun()


if __name__ == "__main__":
    main()