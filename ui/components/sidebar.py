import streamlit as st
from datetime import datetime
from typing import Dict, Any, List
import os


def render_sidebar(data_loader) -> Dict[str, Any]:
    """
    Rendu de la sidebar avec tous les contrôles
    CORRIGÉ : Affiche toujours l'upload même sans base de données

    Args:
        data_loader: Instance du DataLoader

    Returns:
        Dictionnaire avec les paramètres sélectionnés
    """

    with st.sidebar:
        st.header("⚙️ Configuration")

        # =================== SECTION UPLOAD (TOUJOURS VISIBLE) ===================
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

        # Traitement des fichiers uploadés
        if uploaded_files:
            if st.button("🔄 Charger les données"):
                with st.spinner("Chargement des données..."):
                    success_count = 0
                    error_count = 0

                    for file in uploaded_files:
                        try:
                            # Lire le contenu du fichier en bytes
                            file_content = file.read()

                            # Afficher info sur le fichier
                            file_size_mb = len(file_content) / (1024 * 1024)
                            st.info(f"🔄 Traitement de {file.name} ({file_size_mb:.1f} MB)")

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
                            error_count += 1
                            st.error(f"❌ Erreur avec {file.name}: {str(e)}")

                            # Affichage des détails d'erreur
                            with st.expander(f"Détails erreur {file.name}"):
                                import traceback
                                st.code(traceback.format_exc())

                    # Résumé final
                    if success_count > 0:
                        st.balloons()
                        st.success(f"🎉 {success_count} fichier(s) traité(s) avec succès!")
                        if error_count > 0:
                            st.warning(f"⚠️ {error_count} fichier(s) en erreur")
                        st.rerun()
                    else:
                        st.error("❌ Aucun fichier n'a pu être traité correctement")

        # =================== SECTION FILTRES ===================
        st.subheader("🔍 Filtres")

        # Sélection de la période
        date_range = st.date_input(
            "Période d'analyse",
            value=(datetime(2025, 5, 16), datetime(2025, 5, 30)),
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
            value=False,
            help="Exclure les campagnes non attribuées dans Branch.io"
        )

        # =================== STATUT BASE DE DONNÉES ===================
        # Affichage des statistiques de données (seulement si la DB existe)
        db_exists = os.path.exists("data/kolet_dashboard.db")

        if db_exists:
            try:
                import sqlite3
                with sqlite3.connect("data/kolet_dashboard.db") as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM campaign_data")
                    record_count = cursor.fetchone()[0]

                    if record_count > 0:
                        st.success(f"📊 {record_count:,} enregistrements en base")

                        # Afficher les sources disponibles
                        cursor.execute("SELECT source, COUNT(*) FROM campaign_data GROUP BY source")
                        sources = cursor.fetchall()
                        st.write("**Sources disponibles:**")
                        for source, count in sources:
                            st.write(f"• {source}: {count:,}")
                    else:
                        st.info("📭 Base de données vide")
            except Exception as e:
                st.warning(f"⚠️ Erreur lecture DB: {e}")
        else:
            st.info("📭 Aucune base de données. Importez des fichiers pour commencer!")

        # =================== CLASSIFICATION DES CAMPAGNES ===================
        st.subheader("🏷️ Classification")

        if db_exists:
            if st.button("⚙️ Configurer les campagnes"):
                st.session_state.show_campaign_config = True
        else:
            st.info("Importez d'abord des données pour configurer les campagnes")

    return {
        'date_range': date_range,
        'platforms': platforms,
        'exclude_unpopulated': exclude_unpopulated
    }


def _render_file_upload_section(data_loader) -> Dict[str, Any]:
    """Section d'upload et gestion des fichiers"""

    st.subheader("📁 Import de données")

    uploaded_files = st.file_uploader(
        "Sélectionner les fichiers CSV",
        type=['csv'],
        accept_multiple_files=True,
        help="Formats acceptés: Google Ads, Apple Search Ads, Branch.io"
    )

    # Bouton pour supprimer la base de données
    if st.button("🗑️ Supprimer toutes les données", type="secondary"):
        _handle_database_deletion()

    # Traitement des fichiers uploadés
    if uploaded_files:
        if st.button("🔄 Charger les données"):
            _process_uploaded_files(uploaded_files, data_loader)

    return {}


def _render_filters_section() -> Dict[str, Any]:
    """Section des filtres"""

    st.subheader("🔍 Filtres")

    # Sélection de la période
    date_range = st.date_input(
        "Période d'analyse",
        value=(datetime(2025, 5, 16), datetime(2025, 5, 30)),
        max_value=datetime.now(),
        help="Sélectionner la période à analyser - Par défaut: période des données Branch.io"
    )

    # Filtre par plateforme
    platforms = st.multiselect(
        "Plateformes",
        options=["App", "Web", "iOS", "Android"],
        default=["App", "Web", "iOS", "Android"],
        help="Sélectionner les plateformes à inclure dans l'analyse"
    )

    # Filtre pour exclure les données "Unpopulated"
    exclude_unpopulated = st.checkbox(
        "Exclure les données 'Unpopulated' de Branch.io",
        value=False,
        help="Exclure les campagnes non attribuées dans Branch.io"
    )

    # Affichage des statistiques de données
    st.info("📊 Chargement des données...")

    return {
        'date_range': date_range,
        'platforms': platforms,
        'exclude_unpopulated': exclude_unpopulated
    }


def _render_classification_section():
    """Section de classification des campagnes"""

    st.subheader("🏷️ Classification")

    if st.button("⚙️ Configurer les campagnes"):
        st.session_state.show_campaign_config = True

    # Raccourcis de classification
    with st.expander("📋 Raccourcis classification"):
        st.markdown("""
        **Types de campagnes:**
        - 🎯 **Acquisition** : Nouvelles installations
        - 🔄 **Retargeting** : Réengagement utilisateurs
        - 🏢 **Branding** : Notoriété de marque

        **Canaux:**
        - 📱 **App** : Campagnes d'installation mobile
        - 🌐 **Web** : Trafic vers le site web
        """)


def _handle_database_deletion():
    """Gère la suppression de la base de données"""

    if st.session_state.get('confirm_delete', False):
        try:
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


def _process_uploaded_files(uploaded_files: List, data_loader):
    """Traite les fichiers uploadés"""

    with st.spinner("Chargement des données..."):
        success_count = 0
        error_count = 0

        # Créer un conteneur pour les messages de progression
        progress_container = st.container()

        for i, file in enumerate(uploaded_files):
            try:
                with progress_container:
                    # Barre de progression
                    progress = (i + 1) / len(uploaded_files)
                    st.progress(progress)

                    # Lire le contenu du fichier
                    file_content = file.read()

                    # Informations sur le fichier
                    file_size_mb = len(file_content) / (1024 * 1024)
                    st.info(f"🔄 Traitement de {file.name} ({file_size_mb:.1f} MB)")

                    # Traiter le fichier
                    processed_data, file_type = data_loader.load_and_process_file(
                        file_content=file_content,
                        filename=file.name
                    )

                    # Validation des données
                    if processed_data.empty:
                        st.warning(f"⚠️ {file.name}: Aucune donnée valide trouvée")
                        continue

                    # Informations sur le traitement
                    st.info(f"📊 Type détecté: {file_type}")
                    st.info(f"📊 Lignes traitées: {len(processed_data):,}")

                    if 'installs' in processed_data.columns:
                        total_installs = processed_data['installs'].sum()
                        st.info(f"📊 Total installs: {total_installs:,}")

                    # Insérer en base
                    inserted_count = data_loader.insert_data(processed_data, file_type, file.name)
                    success_count += 1

                    st.success(f"✅ {file.name}: {inserted_count:,} enregistrements traités ({file_type})")

            except Exception as e:
                error_count += 1
                st.error(f"❌ Erreur avec {file.name}: {str(e)}")

                # Affichage des détails d'erreur en mode debug
                if st.checkbox(f"Voir détails erreur {file.name}", key=f"error_{i}"):
                    import traceback
                    st.code(traceback.format_exc())

        # Résumé final
        if success_count > 0:
            st.balloons()  # Animation de succès
            st.success(f"🎉 {success_count} fichier(s) traité(s) avec succès!")

            if error_count > 0:
                st.warning(f"⚠️ {error_count} fichier(s) en erreur")

            st.rerun()
        else:
            st.error("❌ Aucun fichier n'a pu être traité correctement")


def render_data_summary_sidebar(data):
    """Affiche un résumé des données dans la sidebar"""

    if not data.empty:
        with st.sidebar:
            st.markdown("---")
            st.subheader("📊 Résumé des données")

            # Période couverte
            min_date = data['date'].min()
            max_date = data['date'].max()
            days_span = (max_date - min_date).days + 1

            st.metric("📅 Période", f"{days_span} jours")
            st.caption(f"{min_date.strftime('%d/%m/%Y')} - {max_date.strftime('%d/%m/%Y')}")

            # Sources de données
            sources = data['source'].nunique()
            campaigns = data['campaign_name'].nunique()

            st.metric("🗂️ Sources", sources)
            st.metric("📈 Campagnes", campaigns)

            # Totaux principaux
            total_cost = data['cost'].sum()
            total_installs = data['installs'].sum()

            if total_cost > 0:
                st.metric("💰 Budget total", f"{total_cost:,.0f}€")
            if total_installs > 0:
                st.metric("📱 Installs totaux", f"{total_installs:,.0f}")

            # Indicateur de qualité des données
            data_quality = _calculate_data_quality_score(data)
            quality_color = "green" if data_quality > 80 else "orange" if data_quality > 60 else "red"

            st.markdown(f"""
            <div style="text-align: center; padding: 10px; background-color: {quality_color}20; border-radius: 5px;">
                <strong>Qualité des données: {data_quality:.0f}%</strong>
            </div>
            """, unsafe_allow_html=True)


def _calculate_data_quality_score(data) -> float:
    """Calcule un score de qualité des données"""

    score = 0
    max_score = 0

    # Présence de colonnes importantes
    important_columns = ['date', 'campaign_name', 'source', 'cost', 'installs']
    for col in important_columns:
        max_score += 20
        if col in data.columns and data[col].notna().sum() > 0:
            score += 20

    # Cohérence des dates
    max_score += 10
    if 'date' in data.columns:
        date_consistency = data['date'].notna().sum() / len(data)
        score += date_consistency * 10

    # Données numériques valides
    max_score += 10
    numeric_cols = ['cost', 'installs', 'clicks', 'impressions']
    valid_numeric = sum(1 for col in numeric_cols
                        if col in data.columns and (data[col] >= 0).all())
    score += (valid_numeric / len(numeric_cols)) * 10

    return (score / max_score) * 100 if max_score > 0 else 0