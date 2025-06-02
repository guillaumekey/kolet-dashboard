import streamlit as st
import pandas as pd


def show_campaign_configuration(data_loader):
    """Interface de configuration des campagnes avec gestion des mises à jour"""
    st.subheader("🏷️ Configuration des Campagnes")

    # Onglets pour séparer les fonctionnalités
    tab1, tab2, tab3 = st.tabs(["➕ Nouvelles Campagnes", "✏️ Modifier Existantes", "📊 Vue d'Ensemble"])

    with tab1:
        _render_new_campaigns_tab(data_loader)

    with tab2:
        _render_update_campaigns_tab(data_loader)

    with tab3:
        _render_overview_tab(data_loader)

    # Bouton pour fermer la configuration
    if st.button("✅ Fermer la configuration", type="primary"):
        st.session_state.show_campaign_config = False
        st.rerun()


def _render_new_campaigns_tab(data_loader):
    """Onglet pour configurer les nouvelles campagnes"""
    st.markdown("### ➕ Campagnes Non Configurées")

    # Récupérer la liste des campagnes non configurées
    unconfigured_campaigns = data_loader.get_unconfigured_campaigns()

    if unconfigured_campaigns.empty:
        st.success("✅ Toutes les campagnes sont configurées!")
        return

    st.info(f"📋 {len(unconfigured_campaigns)} campagne(s) à configurer")

    # Configuration par lot
    if len(unconfigured_campaigns) > 1:
        _render_batch_configuration(unconfigured_campaigns, data_loader)
        st.markdown("---")

    # Configuration individuelle
    st.markdown("#### Configuration Individuelle")

    for idx, campaign in unconfigured_campaigns.iterrows():
        with st.expander(f"🏷️ {campaign['campaign_name']} ({campaign['source']})", expanded=False):
            _render_single_campaign_config(campaign, data_loader, f"new_{idx}")


def _render_update_campaigns_tab(data_loader):
    """Onglet pour modifier les campagnes existantes"""
    st.markdown("### ✏️ Modifier les Campagnes Configurées")

    # Récupérer toutes les campagnes configurées
    configured_campaigns = _get_configured_campaigns(data_loader)

    if configured_campaigns.empty:
        st.info("📭 Aucune campagne configurée à modifier")
        return

    # Filtres pour la recherche
    col1, col2, col3 = st.columns(3)

    with col1:
        search_name = st.text_input("🔍 Rechercher par nom", key="search_campaign")

    with col2:
        filter_type = st.selectbox(
            "Filtrer par type",
            options=["Tous"] + list(configured_campaigns['campaign_type'].dropna().unique()),
            key="filter_type"
        )

    with col3:
        filter_channel = st.selectbox(
            "Filtrer par canal",
            options=["Tous"] + list(configured_campaigns['channel_type'].dropna().unique()),
            key="filter_channel"
        )

    # Appliquer les filtres
    filtered_campaigns = _apply_filters(configured_campaigns, search_name, filter_type, filter_channel)

    if filtered_campaigns.empty:
        st.warning("🔍 Aucune campagne trouvée avec ces critères")
        return

    st.info(f"📋 {len(filtered_campaigns)} campagne(s) trouvée(s)")

    # Option de modification par lot
    if len(filtered_campaigns) > 1:
        _render_batch_update(filtered_campaigns, data_loader)
        st.markdown("---")

    # Modification individuelle
    st.markdown("#### Modification Individuelle")

    for idx, campaign in filtered_campaigns.iterrows():
        with st.expander(
                f"✏️ {campaign['campaign_name']} - {campaign['campaign_type'].title()} ({campaign['channel_type'].title()})",
                expanded=False
        ):
            _render_single_campaign_update(campaign, data_loader, f"update_{idx}")


def _render_overview_tab(data_loader):
    """Onglet vue d'ensemble des classifications"""
    st.markdown("### 📊 Vue d'Ensemble des Classifications")

    # Récupérer toutes les campagnes
    all_campaigns = _get_all_campaigns_with_classification(data_loader)

    if all_campaigns.empty:
        st.info("📭 Aucune donnée de campagne disponible")
        return

    # Statistiques générales
    total_campaigns = len(all_campaigns)
    configured_campaigns = len(all_campaigns[all_campaigns['campaign_type'].notna()])
    unconfigured_campaigns = total_campaigns - configured_campaigns

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Campagnes", total_campaigns)

    with col2:
        st.metric("Configurées", configured_campaigns)

    with col3:
        st.metric("Non Configurées", unconfigured_campaigns)

    # Graphique de répartition
    if configured_campaigns > 0:
        _render_classification_charts(all_campaigns)

    # Tableau récapitulatif
    _render_classification_summary_table(all_campaigns)

    # Actions de masse
    st.markdown("---")
    st.markdown("### 🔧 Actions de Masse")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🗑️ Supprimer toutes les classifications", type="secondary"):
            if st.session_state.get('confirm_delete_all', False):
                _delete_all_classifications(data_loader)
                st.session_state.confirm_delete_all = False
                st.success("✅ Toutes les classifications supprimées")
                st.rerun()
            else:
                st.session_state.confirm_delete_all = True
                st.warning("⚠️ Cliquez à nouveau pour confirmer")

    with col2:
        if st.button("📥 Exporter les classifications"):
            _export_classifications(all_campaigns)


def _render_batch_configuration(campaigns_df, data_loader):
    """Configuration par lot pour les nouvelles campagnes"""
    st.markdown("#### ⚡ Configuration par Lot")

    with st.form("batch_config_form"):
        st.write(f"Configurer {len(campaigns_df)} campagne(s) en une fois:")

        col1, col2 = st.columns(2)

        with col1:
            batch_campaign_type = st.selectbox(
                "Type de campagne pour toutes",
                options=["", "branding", "acquisition", "retargeting"],
                key="batch_campaign_type"
            )

        with col2:
            batch_channel_type = st.selectbox(
                "Canal pour toutes",
                options=["", "app", "web"],
                key="batch_channel_type"
            )

        if st.form_submit_button("🚀 Appliquer à toutes"):
            if batch_campaign_type and batch_channel_type:
                success_count = 0
                for _, campaign in campaigns_df.iterrows():
                    if data_loader.update_campaign_classification(
                            campaign['campaign_name'],
                            batch_campaign_type,
                            batch_channel_type
                    ):
                        success_count += 1

                st.success(f"✅ {success_count} campagne(s) configurée(s) en lot!")
                st.rerun()
            else:
                st.error("❌ Veuillez sélectionner un type et un canal")


def _render_batch_update(campaigns_df, data_loader):
    """Mise à jour par lot pour les campagnes existantes"""
    st.markdown("#### ⚡ Modification par Lot")

    with st.form("batch_update_form"):
        st.write(f"Modifier {len(campaigns_df)} campagne(s) sélectionnée(s):")

        col1, col2 = st.columns(2)

        with col1:
            new_campaign_type = st.selectbox(
                "Nouveau type de campagne",
                options=["Conserver"] + ["branding", "acquisition", "retargeting"],
                key="batch_new_campaign_type"
            )

        with col2:
            new_channel_type = st.selectbox(
                "Nouveau canal",
                options=["Conserver"] + ["app", "web"],
                key="batch_new_channel_type"
            )

        if st.form_submit_button("🔄 Mettre à jour toutes"):
            if new_campaign_type != "Conserver" or new_channel_type != "Conserver":
                success_count = 0
                for _, campaign in campaigns_df.iterrows():
                    campaign_type = new_campaign_type if new_campaign_type != "Conserver" else campaign['campaign_type']
                    channel_type = new_channel_type if new_channel_type != "Conserver" else campaign['channel_type']

                    if data_loader.update_campaign_classification(
                            campaign['campaign_name'],
                            campaign_type,
                            channel_type
                    ):
                        success_count += 1

                st.success(f"✅ {success_count} campagne(s) mise(s) à jour en lot!")
                st.rerun()
            else:
                st.warning("⚠️ Aucune modification sélectionnée")


def _render_single_campaign_config(campaign, data_loader, key_prefix):
    """Configuration d'une campagne individuelle"""
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.write(f"**Source:** {campaign['source']}")

    with col2:
        campaign_type = st.selectbox(
            "Type de campagne",
            options=["branding", "acquisition", "retargeting"],
            key=f"{key_prefix}_type"
        )

    with col3:
        channel_type = st.selectbox(
            "Canal",
            options=["app", "web"],
            key=f"{key_prefix}_channel"
        )

    if st.button(f"💾 Sauvegarder", key=f"{key_prefix}_save"):
        if data_loader.update_campaign_classification(
                campaign['campaign_name'],
                campaign_type,
                channel_type
        ):
            st.success("✅ Campagne configurée!")
            st.rerun()
        else:
            st.error("❌ Erreur lors de la sauvegarde")


def _render_single_campaign_update(campaign, data_loader, key_prefix):
    """Mise à jour d'une campagne individuelle"""
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.write(f"**Source:** {campaign['source']}")
        st.write(
            f"**Configuration actuelle:** {campaign['campaign_type'].title()} - {campaign['channel_type'].title()}")

    with col2:
        current_type_index = ["branding", "acquisition", "retargeting"].index(campaign['campaign_type'])
        new_campaign_type = st.selectbox(
            "Nouveau type",
            options=["branding", "acquisition", "retargeting"],
            index=current_type_index,
            key=f"{key_prefix}_type"
        )

    with col3:
        current_channel_index = ["app", "web"].index(campaign['channel_type'])
        new_channel_type = st.selectbox(
            "Nouveau canal",
            options=["app", "web"],
            index=current_channel_index,
            key=f"{key_prefix}_channel"
        )

    # Afficher les changements
    changes = []
    if new_campaign_type != campaign['campaign_type']:
        changes.append(f"Type: {campaign['campaign_type']} → {new_campaign_type}")
    if new_channel_type != campaign['channel_type']:
        changes.append(f"Canal: {campaign['channel_type']} → {new_channel_type}")

    if changes:
        st.info(f"📝 Changements: {', '.join(changes)}")

    col_save, col_delete = st.columns(2)

    with col_save:
        if st.button(f"🔄 Mettre à jour", key=f"{key_prefix}_update"):
            if data_loader.update_campaign_classification(
                    campaign['campaign_name'],
                    new_campaign_type,
                    new_channel_type
            ):
                st.success("✅ Campagne mise à jour!")
                st.rerun()
            else:
                st.error("❌ Erreur lors de la mise à jour")

    with col_delete:
        if st.button(f"🗑️ Supprimer", key=f"{key_prefix}_delete"):
            if _delete_campaign_classification(data_loader, campaign['campaign_name']):
                st.success("✅ Classification supprimée!")
                st.rerun()
            else:
                st.error("❌ Erreur lors de la suppression")


def _get_configured_campaigns(data_loader):
    """Récupère toutes les campagnes configurées"""
    try:
        # Récupérer toutes les campagnes avec classification
        query = """
            SELECT DISTINCT cd.campaign_name, cd.source, cc.campaign_type, cc.channel_type
            FROM campaign_data cd
            INNER JOIN campaign_classification cc ON cd.campaign_name = cc.campaign_name
            ORDER BY cd.campaign_name
        """

        import sqlite3
        with sqlite3.connect(data_loader.db_manager.db_path) as conn:
            return pd.read_sql_query(query, conn)
    except Exception as e:
        st.error(f"Erreur lors de la récupération des campagnes: {e}")
        return pd.DataFrame()


def _get_all_campaigns_with_classification(data_loader):
    """Récupère toutes les campagnes avec leur classification"""
    try:
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
            GROUP BY cd.campaign_name, cd.source, cc.campaign_type, cc.channel_type
            ORDER BY cd.campaign_name
        """

        import sqlite3
        with sqlite3.connect(data_loader.db_manager.db_path) as conn:
            return pd.read_sql_query(query, conn)
    except Exception as e:
        st.error(f"Erreur lors de la récupération: {e}")
        return pd.DataFrame()


def _apply_filters(campaigns_df, search_name, filter_type, filter_channel):
    """Applique les filtres de recherche"""
    filtered_df = campaigns_df.copy()

    # Filtre par nom
    if search_name:
        filtered_df = filtered_df[
            filtered_df['campaign_name'].str.contains(search_name, case=False, na=False)
        ]

    # Filtre par type
    if filter_type != "Tous":
        filtered_df = filtered_df[filtered_df['campaign_type'] == filter_type]

    # Filtre par canal
    if filter_channel != "Tous":
        filtered_df = filtered_df[filtered_df['channel_type'] == filter_channel]

    return filtered_df


def _render_classification_charts(campaigns_df):
    """Affiche les graphiques de répartition des classifications"""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    configured_campaigns = campaigns_df[campaigns_df['campaign_type'].notna()]

    if configured_campaigns.empty:
        return

    # Graphiques de répartition
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Répartition par Type', 'Répartition par Canal'),
        specs=[[{"type": "pie"}, {"type": "pie"}]]
    )

    # Répartition par type de campagne
    type_counts = configured_campaigns['campaign_type'].value_counts()
    fig.add_trace(
        go.Pie(
            labels=type_counts.index,
            values=type_counts.values,
            name="Type",
            textinfo='label+percent'
        ),
        row=1, col=1
    )

    # Répartition par canal
    channel_counts = configured_campaigns['channel_type'].value_counts()
    fig.add_trace(
        go.Pie(
            labels=channel_counts.index,
            values=channel_counts.values,
            name="Canal",
            textinfo='label+percent'
        ),
        row=1, col=2
    )

    fig.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)


def _render_classification_summary_table(campaigns_df):
    """Affiche le tableau récapitulatif des classifications"""
    st.markdown("#### 📋 Tableau Récapitulatif")

    # Préparer les données pour l'affichage
    display_df = campaigns_df.copy()

    # Ajouter une colonne de statut
    display_df['status'] = display_df['campaign_type'].apply(
        lambda x: "✅ Configurée" if pd.notna(x) else "❌ Non configurée"
    )

    # Remplacer les valeurs NaN
    display_df['campaign_type'] = display_df['campaign_type'].fillna('Non défini')
    display_df['channel_type'] = display_df['channel_type'].fillna('Non défini')

    # Sélectionner les colonnes à afficher
    columns_to_show = ['campaign_name', 'source', 'campaign_type', 'channel_type', 'status']
    if 'total_cost' in display_df.columns:
        columns_to_show.extend(['records_count', 'total_cost', 'total_installs'])

    display_df = display_df[columns_to_show]

    # Configuration des colonnes
    column_config = {
        "campaign_name": st.column_config.TextColumn("Nom de Campagne", width="large"),
        "source": st.column_config.TextColumn("Source", width="medium"),
        "campaign_type": st.column_config.TextColumn("Type", width="medium"),
        "channel_type": st.column_config.TextColumn("Canal", width="small"),
        "status": st.column_config.TextColumn("Statut", width="medium"),
    }

    if 'total_cost' in display_df.columns:
        column_config.update({
            "records_count": st.column_config.NumberColumn("Enregistrements", format="%d"),
            "total_cost": st.column_config.NumberColumn("Coût Total", format="%.2f €"),
            "total_installs": st.column_config.NumberColumn("Installs", format="%d")
        })

    st.dataframe(
        display_df,
        column_config=column_config,
        use_container_width=True,
        hide_index=True
    )


def _delete_campaign_classification(data_loader, campaign_name):
    """Supprime la classification d'une campagne"""
    try:
        import sqlite3
        with sqlite3.connect(data_loader.db_manager.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM campaign_classification WHERE campaign_name = ?",
                (campaign_name,)
            )
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        st.error(f"Erreur lors de la suppression: {e}")
        return False


def _delete_all_classifications(data_loader):
    """Supprime toutes les classifications"""
    try:
        import sqlite3
        with sqlite3.connect(data_loader.db_manager.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM campaign_classification")
            conn.commit()
            return True
    except Exception as e:
        st.error(f"Erreur lors de la suppression: {e}")
        return False


def _export_classifications(campaigns_df):
    """Exporte les classifications en CSV"""
    try:
        csv = campaigns_df.to_csv(index=False)
        st.download_button(
            label="📥 Télécharger CSV",
            data=csv,
            file_name=f"classifications_campagnes_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    except Exception as e:
        st.error(f"Erreur lors de l'export: {e}")


# Fonction helper pour l'interface simplifiée (compatibilité)
def show_campaign_configuration_simple(data_loader):
    """Interface simplifiée pour compatibilité avec l'ancien code"""
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