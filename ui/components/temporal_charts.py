# FICHIER COMPLET: temporal_charts.py avec TOUTES les fonctions existantes + filtres
# Remplacez tout le contenu de votre fichier temporal_charts.py par ce code

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict, Optional, Tuple
import re


# ===== NOUVELLE FONCTION PRINCIPALE AVEC SUPPORT DES FILTRES =====
def render_temporal_performance(data, date_range=None, campaign_types_data=None):
    """
    Fonction principale améliorée qui détecte si les filtres sont disponibles
    et utilise la version appropriée

    Args:
        data: DataFrame consolidé
        date_range: Tuple optionnel (date_debut, date_fin)
        campaign_types_data: DataFrame optionnel avec les classifications
    """
    # Si les paramètres de filtrage sont fournis, utiliser la version avec filtres
    if date_range is not None or campaign_types_data is not None:
        # Assurer que date_range existe
        if date_range is None:
            if 'date' in data.columns:
                date_range = (data['date'].min(), data['date'].max())
            else:
                date_range = (pd.Timestamp.now() - pd.Timedelta(days=30), pd.Timestamp.now())

        # Appeler la version avec filtres
        render_temporal_performance_with_filters(data, date_range, campaign_types_data)
    else:
        # Sinon, utiliser la version originale
        render_temporal_performance_original(data)


# ===== VERSION ORIGINALE (votre code actuel) =====
def render_temporal_performance_original(data):
    """Version originale de la fonction sans filtres"""
    st.subheader("📊 Performances Journalières")

    # Grouper par date - inclure toutes les métriques nécessaires
    daily_data = data.groupby('date').agg({
        'cost': 'sum',
        'impressions': 'sum',
        'clicks': 'sum',
        'installs': 'sum',
        'purchases': 'sum',
        'login': 'sum',
        'revenue': 'sum'
    }).reset_index()

    daily_data['date'] = pd.to_datetime(daily_data['date'])
    daily_data = daily_data.sort_values('date')

    # Calcul des métriques dérivées
    daily_data['cpi'] = daily_data['cost'] / daily_data['installs'].replace(0, 1)
    daily_data['roas'] = daily_data['revenue'] / daily_data['cost'].replace(0, 1)

    # Remplacer les valeurs infinies par 0
    daily_data['cpi'] = daily_data['cpi'].replace([float('inf'), -float('inf')], 0)
    daily_data['roas'] = daily_data['roas'].replace([float('inf'), -float('inf')], 0)

    # ============ GRAPHIQUES PRINCIPAUX (4 existants) ============
    fig_main = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Coût', 'Impressions', 'Clics', 'Installations'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )

    # Coût
    fig_main.add_trace(
        go.Scatter(x=daily_data['date'], y=daily_data['cost'],
                   name='Coût', line=dict(color='#e74c3c')),
        row=1, col=1
    )

    # Impressions
    fig_main.add_trace(
        go.Scatter(x=daily_data['date'], y=daily_data['impressions'],
                   name='Impressions', line=dict(color='#3498db')),
        row=1, col=2
    )

    # Clics
    fig_main.add_trace(
        go.Scatter(x=daily_data['date'], y=daily_data['clicks'],
                   name='Clics', line=dict(color='#2ecc71')),
        row=2, col=1
    )

    # Installations
    fig_main.add_trace(
        go.Scatter(x=daily_data['date'], y=daily_data['installs'],
                   name='Installations', line=dict(color='#9b59b6')),
        row=2, col=2
    )

    fig_main.update_layout(
        height=600,
        showlegend=False
    )

    st.plotly_chart(fig_main, use_container_width=True)

    # ============ NOUVEAUX GRAPHIQUES (5 nouveaux) ============

    # Première ligne : Purchases, Logins, Revenu
    fig_secondary_1 = make_subplots(
        rows=1, cols=3,
        subplot_titles=('Purchases', 'Logins', 'Revenu'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}, {"secondary_y": False}]]
    )

    # Purchases
    fig_secondary_1.add_trace(
        go.Scatter(x=daily_data['date'], y=daily_data['purchases'],
                   name='Purchases', line=dict(color='#f39c12')),
        row=1, col=1
    )

    # Logins
    fig_secondary_1.add_trace(
        go.Scatter(x=daily_data['date'], y=daily_data['login'],
                   name='Logins', line=dict(color='#1abc9c')),
        row=1, col=2
    )

    # Revenu
    fig_secondary_1.add_trace(
        go.Scatter(x=daily_data['date'], y=daily_data['revenue'],
                   name='Revenu', line=dict(color='#27ae60')),
        row=1, col=3
    )

    fig_secondary_1.update_layout(
        height=400,
        showlegend=False
    )

    st.plotly_chart(fig_secondary_1, use_container_width=True)

    # Deuxième ligne : CPI et ROAS
    # REMPLACEZ TOUTE CETTE SECTION :

    # Vérifier quel type de campagnes on affiche
    fig_secondary_2 = make_subplots(
        rows=1, cols=2,
        subplot_titles=('CPI' if has_installs else 'CPA', 'ROAS'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}]]
    )

    # Premier graphique : CPI ou CPA selon le type
    if has_installs and 'cpi' in daily_data.columns:
        fig_secondary_2.add_trace(
            go.Scatter(x=daily_data['date'], y=daily_data['cpi'],
                       name='CPI', line=dict(color='#e67e22')),
            row=1, col=1
        )
    elif 'cpa' in daily_data.columns:
        fig_secondary_2.add_trace(
            go.Scatter(x=daily_data['date'], y=daily_data['cpa'],
                       name='CPA', line=dict(color='#e67e22')),
            row=1, col=1
        )

    # ROAS
    if 'roas' in daily_data.columns:
        fig_secondary_2.add_trace(
            go.Scatter(x=daily_data['date'], y=daily_data['roas'],
                       name='ROAS', line=dict(color='#8e44ad')),
            row=1, col=2
        )

    fig_secondary_2.update_layout(
        height=400,
        showlegend=False
    )

    st.plotly_chart(fig_secondary_2, use_container_width=True)


# ===== NOUVELLE VERSION AVEC FILTRES =====
def render_temporal_performance_with_filters(data: pd.DataFrame, date_range: Tuple,
                                             campaign_types_data: Optional[pd.DataFrame] = None):
    """
    Version améliorée avec filtres avancés pour les performances journalières
    """
    st.subheader("📊 Performances Journalières")

    # ===== SECTION FILTRES AVANCÉS =====
    with st.expander("🔧 Filtres Avancés", expanded=False):
        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            st.markdown("**🔍 Filtrage par Nom de Campagne**")

            # Mode de filtrage
            filter_mode = st.radio(
                "Mode de filtrage",
                options=["Inclusion", "Exclusion"],
                horizontal=True,
                key="temporal_filter_mode",
                help="Inclusion = garder seulement les campagnes qui matchent | Exclusion = retirer les campagnes qui matchent"
            )

            # Pattern regex
            regex_pattern = st.text_input(
                "Pattern Regex",
                value="",
                placeholder="Ex: SEA.*FR|App.*iOS|Top.*Destinations",
                key="temporal_regex_pattern",
                help="Utilisez | pour 'OU', .* pour 'n'importe quoi', ^ pour début, $ pour fin"
            )

            # Validation regex
            regex_valid = True
            if regex_pattern:
                try:
                    re.compile(regex_pattern)
                    st.success("✅ Regex valide")
                except re.error as e:
                    st.error(f"❌ Regex invalide: {e}")
                    regex_valid = False

        with col2:
            st.markdown("**🏷️ Filtrage par Type et Canal**")

            # Types de campagne disponibles
            available_types = ["branding", "acquisition", "retargeting"]
            if campaign_types_data is not None and not campaign_types_data.empty:
                if 'campaign_type' in campaign_types_data.columns:
                    types_in_data = campaign_types_data['campaign_type'].dropna().unique().tolist()
                    if types_in_data:
                        available_types = types_in_data

            selected_types = st.multiselect(
                "Type de campagne",
                options=available_types,
                default=[],
                key="temporal_campaign_types",
                help="Laissez vide pour inclure tous les types"
            )

            # Canaux disponibles
            available_channels = ["app", "web"]
            if campaign_types_data is not None and not campaign_types_data.empty:
                if 'platform_type' in campaign_types_data.columns:
                    channels_in_data = campaign_types_data['platform_type'].dropna().unique().tolist()
                    if channels_in_data:
                        available_channels = channels_in_data

            selected_channels = st.multiselect(
                "Canal",
                options=available_channels,
                default=[],
                key="temporal_channels",
                help="Laissez vide pour inclure tous les canaux"
            )

        with col3:
            st.markdown("**📅 Période Rapide**")

            period_select = st.selectbox(
                "Sélection rapide",
                options=["Tout", "7 derniers jours", "14 derniers jours", "30 derniers jours", "Mois en cours"],
                key="temporal_period_select"
            )

    # ===== APPLICATION DES FILTRES =====
    filtered_data = apply_temporal_filters(
        data=data,
        campaign_types_data=campaign_types_data,
        regex_pattern=regex_pattern if regex_valid else "",
        filter_mode=filter_mode.lower(),
        selected_types=selected_types,
        selected_channels=selected_channels,
        period_select=period_select,
        date_range=date_range
    )

    # ===== AFFICHAGE DU RÉSUMÉ DES FILTRES =====
    if regex_pattern or selected_types or selected_channels or period_select != "Tout":
        with st.container():
            st.markdown("---")

            col_summary1, col_summary2, col_summary3, col_summary4 = st.columns(4)

            with col_summary1:
                if regex_pattern and regex_valid:
                    st.info(f"🔍 Regex ({filter_mode}): `{regex_pattern}`")

            with col_summary2:
                if selected_types:
                    st.info(f"🏷️ Types: {', '.join(selected_types)}")

            with col_summary3:
                if selected_channels:
                    st.info(f"📱 Canaux: {', '.join(selected_channels)}")

            with col_summary4:
                if period_select != "Tout":
                    st.info(f"📅 Période: {period_select}")

            # Métriques de filtrage
            # Métriques de filtrage
            st.markdown("")
            metric_col1, metric_col2, metric_col3, metric_col4, metric_col5, metric_col6 = st.columns(6)

            with metric_col1:
                nb_campaigns = filtered_data[
                    'campaign_name'].nunique() if 'campaign_name' in filtered_data.columns else 0
                st.metric("Campagnes filtrées", f"{nb_campaigns}")

            with metric_col2:
                nb_days = filtered_data['date'].nunique() if 'date' in filtered_data.columns else 0
                st.metric("Jours affichés", f"{nb_days}")

            with metric_col3:
                total_cost = filtered_data['cost'].sum() if 'cost' in filtered_data.columns else 0
                st.metric("Coût total", f"{total_cost:,.0f}€")

            with metric_col4:
                total_revenue = filtered_data['revenue'].sum() if 'revenue' in filtered_data.columns else 0
                st.metric("Revenu total", f"{total_revenue:,.0f}€")

            with metric_col5:
                total_purchases = filtered_data['purchases'].sum() if 'purchases' in filtered_data.columns else 0
                total_installs = filtered_data['installs'].sum() if 'installs' in filtered_data.columns else 0
                total_login = filtered_data['login'].sum() if 'login' in filtered_data.columns else 0

                # Afficher soit installs (pour App) soit purchases (pour Web) selon ce qui est pertinent
                if total_installs > 0:
                    st.metric("Installs/Logins", f"{total_installs:.0f}/{total_login:.0f}")
                else:
                    st.metric("Purchases", f"{total_purchases:.0f}")

            with metric_col6:
                # Calculer le ROAS
                roas = (total_revenue / total_cost) if total_cost > 0 else 0
                st.metric("ROAS", f"{roas:.2f}")

            st.markdown("---")

    # ===== AFFICHAGE DES GRAPHIQUES (réutilisation du code existant) =====
    if filtered_data.empty:
        st.warning("🔍 Aucune donnée trouvée avec les filtres appliqués")
        return

    # Grouper par date
    daily_data = filtered_data.groupby('date').agg({
        'cost': 'sum',
        'impressions': 'sum',
        'clicks': 'sum',
        'installs': 'sum',
        'purchases': 'sum',
        'login': 'sum',
        'revenue': 'sum'
    }).reset_index()

    daily_data['date'] = pd.to_datetime(daily_data['date'])
    daily_data = daily_data.sort_values('date')

    # PAR :
    has_installs = daily_data['installs'].sum() > 0

    if has_installs:
        # Pour App : calculer CPI
        daily_data['cpi'] = daily_data['cost'] / daily_data['installs'].replace(0, 1)
        daily_data['cpi'] = daily_data['cpi'].replace([float('inf'), -float('inf')], 0)
    else:
        # Pour Web : calculer CPA
        daily_data['cpa'] = daily_data['cost'] / daily_data['purchases'].replace(0, 1)
        daily_data['cpa'] = daily_data['cpa'].replace([float('inf'), -float('inf')], 0)

    # ROAS se calcule toujours
    daily_data['roas'] = daily_data['revenue'] / daily_data['cost'].replace(0, 1)
    daily_data['roas'] = daily_data['roas'].replace([float('inf'), -float('inf')], 0)

    # Graphiques principaux (4 graphiques)
    fig_main = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Coût', 'Impressions', 'Clics', 'Installations'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )

    fig_main.add_trace(
        go.Scatter(x=daily_data['date'], y=daily_data['cost'],
                   name='Coût', line=dict(color='#e74c3c')),
        row=1, col=1
    )

    fig_main.add_trace(
        go.Scatter(x=daily_data['date'], y=daily_data['impressions'],
                   name='Impressions', line=dict(color='#3498db')),
        row=1, col=2
    )

    fig_main.add_trace(
        go.Scatter(x=daily_data['date'], y=daily_data['clicks'],
                   name='Clics', line=dict(color='#2ecc71')),
        row=2, col=1
    )

    fig_main.add_trace(
        go.Scatter(x=daily_data['date'], y=daily_data['installs'],
                   name='Installations', line=dict(color='#9b59b6')),
        row=2, col=2
    )

    fig_main.update_layout(height=600, showlegend=False)
    st.plotly_chart(fig_main, use_container_width=True)

    # Graphiques secondaires (Purchases, Logins, Revenu)
    fig_secondary_1 = make_subplots(
        rows=1, cols=3,
        subplot_titles=('Purchases', 'Logins', 'Revenu'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}, {"secondary_y": False}]]
    )

    fig_secondary_1.add_trace(
        go.Scatter(x=daily_data['date'], y=daily_data['purchases'],
                   name='Purchases', line=dict(color='#f39c12')),
        row=1, col=1
    )

    fig_secondary_1.add_trace(
        go.Scatter(x=daily_data['date'], y=daily_data['login'],
                   name='Logins', line=dict(color='#1abc9c')),
        row=1, col=2
    )

    fig_secondary_1.add_trace(
        go.Scatter(x=daily_data['date'], y=daily_data['revenue'],
                   name='Revenu', line=dict(color='#27ae60')),
        row=1, col=3
    )

    fig_secondary_1.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig_secondary_1, use_container_width=True)

    # Graphiques CPI et ROAS
    fig_secondary_2 = make_subplots(
        rows=1, cols=2,
        subplot_titles=('CPI', 'ROAS'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}]]
    )

    fig_secondary_2.add_trace(
        go.Scatter(x=daily_data['date'], y=daily_data['cpi'],
                   name='CPI', line=dict(color='#e67e22')),
        row=1, col=1
    )

    fig_secondary_2.add_trace(
        go.Scatter(x=daily_data['date'], y=daily_data['roas'],
                   name='ROAS', line=dict(color='#8e44ad')),
        row=1, col=2
    )

    fig_secondary_2.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig_secondary_2, use_container_width=True)


def apply_temporal_filters(
        data: pd.DataFrame,
        campaign_types_data: Optional[pd.DataFrame],
        regex_pattern: str,
        filter_mode: str,
        selected_types: list,
        selected_channels: list,
        period_select: str,
        date_range: tuple
) -> pd.DataFrame:
    """
    Applique tous les filtres sur les données pour les performances temporelles
    Version complète avec normalisation des colonnes et debug
    """
    filtered = data.copy()

    # DEBUG : Vérifier les données reçues
    print(f"🔍 DEBUG apply_temporal_filters:")
    print(f"   - Lignes reçues: {len(filtered)}")
    print(f"   - Colonnes disponibles: {filtered.columns.tolist()[:15]}...")

    # ===== NORMALISATION DES COLONNES =====
    # Mapping pour normaliser les noms de colonnes (notamment pour ASA)
    column_mapping = {
        'Campaign Name': 'campaign_name',
        'Campaign': 'campaign_name',
        'campaign': 'campaign_name',
        'Day': 'date',
        'Date': 'date',
        'day': 'date',
        'Spend': 'cost',
        'Cost': 'cost',
        'spend': 'cost',
        'Taps': 'clicks',
        'Clicks': 'clicks',
        'taps': 'clicks',
        'Installs (Tap-Through)': 'installs',
        'Installs': 'installs',
        'installs (tap-through)': 'installs',
        'New Downloads (Tap-Through)': 'new_downloads',
        'Redownloads (Tap-Through)': 'redownloads',
        'Impressions': 'impressions',
        'Impr.': 'impressions',
        'Purchase': 'purchases',
        'Purchases': 'purchases',
        'Revenue': 'revenue',
        'Conv. value': 'revenue',
        'Unified revenue': 'revenue',
        'Unified installs': 'installs',
        'Unified purchases': 'purchases',
        'Unified opens': 'opens',
        'Unified login': 'login'
    }

    # Appliquer le mapping de colonnes
    for old_name, new_name in column_mapping.items():
        if old_name in filtered.columns and new_name not in filtered.columns:
            filtered.rename(columns={old_name: new_name}, inplace=True)
            print(f"   - Renommé: {old_name} → {new_name}")

    # ===== VÉRIFICATION ET CRÉATION DES COLONNES ESSENTIELLES =====

    # Vérifier campaign_name
    if 'campaign_name' not in filtered.columns:
        print("⚠️ Colonne campaign_name manquante après normalisation")
        # Essayer de trouver une alternative
        possible_campaign_cols = [col for col in filtered.columns if 'campaign' in col.lower()]
        if possible_campaign_cols:
            filtered['campaign_name'] = filtered[possible_campaign_cols[0]]
            print(f"   - Utilisé {possible_campaign_cols[0]} comme campaign_name")
        else:
            filtered['campaign_name'] = 'Unknown'
            print("   - Créé campaign_name avec valeur par défaut 'Unknown'")

    # S'assurer que les colonnes numériques sont bien numériques
    numeric_columns = ['cost', 'clicks', 'impressions', 'installs', 'purchases', 'revenue', 'opens', 'login']
    for col in numeric_columns:
        if col in filtered.columns:
            filtered[col] = pd.to_numeric(filtered[col], errors='coerce').fillna(0)

    # Créer les colonnes manquantes avec des valeurs par défaut
    if 'opens' not in filtered.columns:
        filtered['opens'] = 0
    if 'login' not in filtered.columns:
        filtered['login'] = 0
    if 'revenue' not in filtered.columns:
        filtered['revenue'] = 0
    if 'purchases' not in filtered.columns:
        filtered['purchases'] = 0

    # Stats avant filtrage
    print(f"   - Campagnes uniques: {filtered['campaign_name'].nunique()}")
    print(f"   - Exemples campagnes: {filtered['campaign_name'].unique()[:5].tolist()}")
    print(f"   - Coût total avant filtrage: {filtered['cost'].sum():.2f}€" if 'cost' in filtered.columns else "")

    # ===== 1. ENRICHISSEMENT AVEC CLASSIFICATIONS =====
    if campaign_types_data is not None and not campaign_types_data.empty:
        if 'campaign_name' in filtered.columns and 'campaign_name' in campaign_types_data.columns:
            print(f"   - Fusion avec classifications...")

            # Préparer les classifications
            classifications = campaign_types_data[['campaign_name', 'campaign_type', 'platform_type']].drop_duplicates()

            # Merger avec les classifications
            before_merge = len(filtered)
            filtered = filtered.merge(
                classifications,
                on='campaign_name',
                how='left',
                suffixes=('', '_class')
            )
            print(f"   - Lignes après merge: {before_merge} → {len(filtered)}")

            # Gérer les colonnes de classification dupliquées
            if 'campaign_type_class' in filtered.columns:
                if 'campaign_type' not in filtered.columns:
                    filtered['campaign_type'] = filtered['campaign_type_class']
                else:
                    filtered['campaign_type'] = filtered['campaign_type'].fillna(filtered['campaign_type_class'])
                filtered = filtered.drop(columns=['campaign_type_class'])

            if 'platform_type_class' in filtered.columns:
                if 'platform_type' not in filtered.columns:
                    filtered['platform_type'] = filtered['platform_type_class']
                else:
                    filtered['platform_type'] = filtered['platform_type'].fillna(filtered['platform_type_class'])
                filtered = filtered.drop(columns=['platform_type_class'])

    # ===== 2. FILTRE REGEX SUR NOM DE CAMPAGNE =====
    if regex_pattern and 'campaign_name' in filtered.columns:
        try:
            print(f"   - Application regex '{regex_pattern}' en mode {filter_mode}")
            pattern = re.compile(regex_pattern, re.IGNORECASE)

            # Créer le masque
            mask = filtered['campaign_name'].str.contains(pattern, na=False, regex=True)
            matches = mask.sum()

            print(f"   - Campagnes qui matchent le pattern: {matches}/{len(mask)}")

            # Afficher quelques exemples de campagnes qui matchent
            if matches > 0:
                matching_campaigns = filtered[mask]['campaign_name'].unique()[:3]
                print(f"   - Exemples de matches: {matching_campaigns.tolist()}")

            # Appliquer le filtre selon le mode
            if filter_mode == 'inclusion':
                filtered = filtered[mask]
                print(f"   ✅ Après inclusion: {len(filtered)} lignes gardées")
            else:  # exclusion
                filtered = filtered[~mask]
                print(f"   ✅ Après exclusion: {len(filtered)} lignes gardées")

        except re.error as e:
            print(f"   ❌ Erreur regex: {e}")

    # ===== 3. FILTRE SUR TYPE DE CAMPAGNE =====
    if selected_types and 'campaign_type' in filtered.columns:
        print(f"   - Filtre par types: {selected_types}")
        before = len(filtered)
        filtered = filtered[filtered['campaign_type'].isin(selected_types)]
        print(f"   ✅ Après filtre types: {before} → {len(filtered)} lignes")

    # ===== 4. FILTRE SUR CANAL =====
    if selected_channels:
        print(f"   - Filtre par canaux: {selected_channels}")

        # Identifier la colonne canal
        channel_column = None
        if 'platform_type' in filtered.columns:
            channel_column = 'platform_type'
        elif 'channel_type' in filtered.columns:
            channel_column = 'channel_type'
        elif 'platform' in filtered.columns:
            channel_column = 'platform'

        if channel_column:
            before = len(filtered)
            filtered = filtered[filtered[channel_column].isin(selected_channels)]
            print(f"   ✅ Après filtre canaux ({channel_column}): {before} → {len(filtered)} lignes")
        else:
            print(f"   ⚠️ Pas de colonne canal trouvée")

    # ===== 5. FILTRE DE PÉRIODE =====
    if period_select != "Tout" and 'date' in filtered.columns:
        print(f"   - Filtre période: {period_select}")

        # S'assurer que la colonne date est en datetime
        filtered['date'] = pd.to_datetime(filtered['date'], errors='coerce')

        # Retirer les lignes avec dates invalides
        before_date_filter = len(filtered)
        filtered = filtered[filtered['date'].notna()]
        if before_date_filter > len(filtered):
            print(f"   - {before_date_filter - len(filtered)} lignes retirées (dates invalides)")

        # Calculer la période
        end_date = pd.Timestamp(date_range[1])

        if period_select == "7 derniers jours":
            start_date = end_date - pd.Timedelta(days=6)
        elif period_select == "14 derniers jours":
            start_date = end_date - pd.Timedelta(days=13)
        elif period_select == "30 derniers jours":
            start_date = end_date - pd.Timedelta(days=29)
        elif period_select == "Mois en cours":
            start_date = pd.Timestamp(end_date.year, end_date.month, 1)
        else:
            start_date = pd.Timestamp(date_range[0])

        before = len(filtered)
        filtered = filtered[(filtered['date'] >= start_date) & (filtered['date'] <= end_date)]
        print(f"   ✅ Après filtre période ({start_date.date()} à {end_date.date()}): {before} → {len(filtered)} lignes")

    # ===== STATS FINALES =====
    print(f"\n   📊 RÉSULTAT FINAL:")
    print(f"   - Lignes finales: {len(filtered)}")
    if 'campaign_name' in filtered.columns:
        print(f"   - Campagnes uniques: {filtered['campaign_name'].nunique()}")
        print(f"   - Liste campagnes: {filtered['campaign_name'].unique().tolist()[:10]}")
    if 'cost' in filtered.columns:
        print(f"   - Coût total: {filtered['cost'].sum():.2f}€")
    if 'installs' in filtered.columns:
        print(f"   - Installs totales: {filtered['installs'].sum():.0f}")
    if 'revenue' in filtered.columns:
        print(f"   - Revenue total: {filtered['revenue'].sum():.2f}€")

    return filtered


# ===== TOUTES VOS AUTRES FONCTIONS EXISTANTES =====
def _prepare_daily_data(data: pd.DataFrame) -> pd.DataFrame:
    """Prépare les données pour l'analyse temporelle"""
    try:
        if 'date' not in data.columns:
            st.error("Colonne 'date' manquante dans les données")
            return pd.DataFrame()

        if data['date'].dtype == 'object':
            data['date'] = pd.to_datetime(data['date'])

        daily_data = data.groupby('date').agg({
            'cost': 'sum',
            'impressions': 'sum',
            'clicks': 'sum',
            'installs': 'sum',
            'purchases': 'sum',
            'revenue': 'sum',
            'opens': 'sum',
            'login': 'sum'
        }).reset_index()

        daily_data = daily_data.sort_values('date')

        daily_data['ctr'] = (daily_data['clicks'] / daily_data['impressions'] * 100).fillna(0)
        daily_data['conversion_rate'] = (daily_data['installs'] / daily_data['clicks'] * 100).fillna(0)
        daily_data['purchase_rate'] = (daily_data['purchases'] / daily_data['installs'] * 100).fillna(0)
        daily_data['roas'] = (daily_data['revenue'] / daily_data['cost']).fillna(0)

        return daily_data

    except Exception as e:
        st.error(f"Erreur lors de la préparation des données: {e}")
        return pd.DataFrame()


def _create_line_chart(daily_data: pd.DataFrame, metrics: List[str], show_trend: bool) -> go.Figure:
    """Crée un graphique en lignes"""

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Coût et Revenus', 'Trafic (Impressions/Clics)', 'Conversions', 'Métriques de Performance'),
        specs=[[{"secondary_y": True}, {"secondary_y": True}],
               [{"secondary_y": True}, {"secondary_y": True}]]
    )

    colors = {
        'cost': '#e74c3c',
        'revenue': '#27ae60',
        'impressions': '#3498db',
        'clicks': '#2ecc71',
        'installs': '#9b59b6',
        'purchases': '#f39c12',
        'opens': '#1abc9c',
        'login': '#e67e22'
    }

    # Graphique 1: Coût et Revenus
    if 'cost' in metrics and 'cost' in daily_data.columns:
        fig.add_trace(
            go.Scatter(x=daily_data['date'], y=daily_data['cost'],
                       name='Coût', line=dict(color=colors['cost'])),
            row=1, col=1
        )

    if 'revenue' in metrics and 'revenue' in daily_data.columns:
        fig.add_trace(
            go.Scatter(x=daily_data['date'], y=daily_data['revenue'],
                       name='Revenus', line=dict(color=colors['revenue'])),
            row=1, col=1, secondary_y=True
        )

    # Graphique 2: Trafic
    if 'impressions' in metrics and 'impressions' in daily_data.columns:
        fig.add_trace(
            go.Scatter(x=daily_data['date'], y=daily_data['impressions'],
                       name='Impressions', line=dict(color=colors['impressions'])),
            row=1, col=2
        )

    if 'clicks' in metrics and 'clicks' in daily_data.columns:
        fig.add_trace(
            go.Scatter(x=daily_data['date'], y=daily_data['clicks'],
                       name='Clics', line=dict(color=colors['clicks'])),
            row=1, col=2, secondary_y=True
        )

    # Graphique 3: Conversions
    if 'installs' in metrics and 'installs' in daily_data.columns:
        fig.add_trace(
            go.Scatter(x=daily_data['date'], y=daily_data['installs'],
                       name='Installations', line=dict(color=colors['installs'])),
            row=2, col=1
        )

    if 'purchases' in metrics and 'purchases' in daily_data.columns:
        fig.add_trace(
            go.Scatter(x=daily_data['date'], y=daily_data['purchases'],
                       name='Achats', line=dict(color=colors['purchases'])),
            row=2, col=1, secondary_y=True
        )

    # Graphique 4: Métriques de performance
    fig.add_trace(
        go.Scatter(x=daily_data['date'], y=daily_data['ctr'],
                   name='CTR (%)', line=dict(color='#34495e')),
        row=2, col=2
    )

    fig.add_trace(
        go.Scatter(x=daily_data['date'], y=daily_data['conversion_rate'],
                   name='Taux Conv. (%)', line=dict(color='#95a5a6')),
        row=2, col=2, secondary_y=True
    )

    # Ajout des lignes de tendance si demandé
    if show_trend:
        _add_trend_lines(fig, daily_data, metrics)

    fig.update_layout(
        height=800,
        showlegend=True,
        title="Évolution des Performances par Jour"
    )

    return fig


def _create_bar_chart(daily_data: pd.DataFrame, metrics: List[str]) -> go.Figure:
    """Crée un graphique en barres"""

    fig = go.Figure()

    colors = {
        'cost': '#e74c3c',
        'revenue': '#27ae60',
        'impressions': '#3498db',
        'clicks': '#2ecc71',
        'installs': '#9b59b6',
        'purchases': '#f39c12'
    }

    for metric in metrics:
        if metric in daily_data.columns:
            fig.add_trace(go.Bar(
                x=daily_data['date'],
                y=daily_data[metric],
                name=metric.capitalize(),
                marker_color=colors.get(metric, '#7f8c8d')
            ))

    fig.update_layout(
        title="Performances Journalières - Vue en Barres",
        xaxis_title="Date",
        yaxis_title="Valeurs",
        height=500,
        barmode='group'
    )

    return fig


def _create_area_chart(daily_data: pd.DataFrame, metrics: List[str]) -> go.Figure:
    """Crée un graphique en aires empilées"""

    fig = go.Figure()

    colors = ['#3498db', '#2ecc71', '#f39c12', '#e74c3c', '#9b59b6', '#1abc9c']

    for i, metric in enumerate(metrics):
        if metric in daily_data.columns:
            fig.add_trace(go.Scatter(
                x=daily_data['date'],
                y=daily_data[metric],
                mode='lines',
                stackgroup='one',
                name=metric.capitalize(),
                fill='tonexty' if i > 0 else 'tozeroy',
                line=dict(color=colors[i % len(colors)])
            ))

    fig.update_layout(
        title="Performances Journalières - Aires Empilées",
        xaxis_title="Date",
        yaxis_title="Valeurs",
        height=500
    )

    return fig


def _add_trend_lines(fig: go.Figure, daily_data: pd.DataFrame, metrics: List[str]):
    """Ajoute des lignes de tendance aux graphiques"""

    import numpy as np
    try:
        from scipy import stats

        x_numeric = list(range(len(daily_data)))

        for metric in ['cost', 'installs']:
            if metric in metrics and metric in daily_data.columns:
                y = daily_data[metric].values
                slope, intercept, r_value, p_value, std_err = stats.linregress(x_numeric, y)
                trend_line = [slope * x + intercept for x in x_numeric]

                # Ajouter la ligne de tendance (exemple pour le premier graphique)
                fig.add_trace(
                    go.Scatter(
                        x=daily_data['date'],
                        y=trend_line,
                        mode='lines',
                        name=f'Tendance {metric}',
                        line=dict(dash='dash', width=2),
                        showlegend=False
                    ),
                    row=1, col=1
                )
    except ImportError:
        # Si scipy n'est pas disponible, passer
        pass
    except Exception:
        # En cas d'erreur, continuer sans tendance
        pass


def _render_temporal_metrics(daily_data: pd.DataFrame):
    """Affiche les métriques de performance temporelle"""

    st.markdown("### 📈 Métriques Temporelles")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # Moyenne mobile 7 jours
        if len(daily_data) >= 7:
            recent_avg_cost = daily_data['cost'].tail(7).mean()
            st.metric(
                "Coût moyen (7j)",
                f"{recent_avg_cost:.2f}€",
                help="Moyenne mobile sur 7 jours"
            )

    with col2:
        # Croissance jour-à-jour
        if len(daily_data) >= 2:
            last_installs = daily_data['installs'].iloc[-1]
            prev_installs = daily_data['installs'].iloc[-2]
            growth = ((last_installs - prev_installs) / prev_installs * 100) if prev_installs > 0 else 0

            st.metric(
                "Croissance installs",
                f"{growth:+.1f}%",
                help="Croissance jour-à-jour"
            )

    with col3:
        # Meilleur jour
        if 'installs' in daily_data.columns:
            best_day_idx = daily_data['installs'].idxmax()
            best_day = daily_data.loc[best_day_idx, 'date']
            best_installs = daily_data.loc[best_day_idx, 'installs']

            st.metric(
                "Meilleur jour",
                f"{best_installs:.0f} installs",
                help=f"Le {best_day.strftime('%d/%m/%Y')}"
            )

    with col4:
        # Volatilité
        if len(daily_data) > 1:
            cost_volatility = daily_data['cost'].std() / daily_data['cost'].mean() * 100
            st.metric(
                "Volatilité coût",
                f"{cost_volatility:.1f}%",
                help="Coefficient de variation du coût"
            )


def _render_trend_analysis(daily_data: pd.DataFrame, metrics: List[str]):
    """Analyse des tendances"""

    st.markdown("### 🔍 Analyse des Tendances")

    if len(daily_data) < 3:
        st.info("Données insuffisantes pour l'analyse des tendances")
        return

    # Calcul des tendances simples
    trends = {}

    for metric in metrics:
        if metric in daily_data.columns and len(daily_data) >= 3:
            values = daily_data[metric].values

            # Tendance simple (comparaison première moitié vs deuxième moitié)
            mid_point = len(values) // 2
            first_half = values[:mid_point].mean()
            second_half = values[mid_point:].mean()

            if first_half > 0:
                trend_pct = ((second_half - first_half) / first_half) * 100
                trends[metric] = {
                    'value': trend_pct,
                    'direction': '📈' if trend_pct > 5 else '📉' if trend_pct < -5 else '➡️'
                }

    # Affichage des tendances
    if trends:
        cols = st.columns(len(trends))
        for i, (metric, trend_data) in enumerate(trends.items()):
            with cols[i]:
                st.metric(
                    f"{trend_data['direction']} {metric.capitalize()}",
                    f"{trend_data['value']:+.1f}%",
                    help=f"Tendance sur la période"
                )

    # Insights automatiques
    _render_temporal_insights(daily_data, trends)


def _render_temporal_insights(daily_data: pd.DataFrame, trends: Dict):
    """Génère des insights temporels automatiques"""

    st.markdown("### 💡 Insights Temporels")

    insights = []

    # Analyse des weekends vs semaine
    if len(daily_data) >= 7:
        daily_data['day_of_week'] = daily_data['date'].dt.dayofweek
        daily_data['is_weekend'] = daily_data['day_of_week'] >= 5

        weekend_avg = daily_data[daily_data['is_weekend']]['installs'].mean()
        weekday_avg = daily_data[~daily_data['is_weekend']]['installs'].mean()

        if weekend_avg > weekday_avg * 1.2:
            insights.append({
                'type': 'info',
                'title': 'Performance weekend',
                'message': f"Les weekends performent {((weekend_avg / weekday_avg - 1) * 100):.0f}% mieux que la semaine"
            })
        elif weekday_avg > weekend_avg * 1.2:
            insights.append({
                'type': 'info',
                'title': 'Performance semaine',
                'message': f"La semaine performe {((weekday_avg / weekend_avg - 1) * 100):.0f}% mieux que les weekends"
            })

    # Analyse des tendances
    for metric, trend_data in trends.items():
        if abs(trend_data['value']) > 20:
            trend_type = 'positive' if trend_data['value'] > 0 else 'warning'
            insights.append({
                'type': trend_type,
                'title': f'Tendance {metric}',
                'message': f"Évolution de {trend_data['value']:+.1f}% sur la période"
            })

    # Détection de pics/creux
    if 'cost' in daily_data.columns:
        cost_max_day = daily_data.loc[daily_data['cost'].idxmax()]
        cost_max = cost_max_day['cost']
        cost_avg = daily_data['cost'].mean()

        if cost_max > cost_avg * 2:
            insights.append({
                'type': 'warning',
                'title': 'Pic de coût détecté',
                'message': f"Le {cost_max_day['date'].strftime('%d/%m')} : {cost_max:.0f}€ (vs {cost_avg:.0f}€ en moyenne)"
            })

    # Affichage des insights
    if insights:
        for insight in insights:
            if insight['type'] == 'positive':
                st.success(f"✅ **{insight['title']}**: {insight['message']}")
            elif insight['type'] == 'warning':
                st.warning(f"⚠️ **{insight['title']}**: {insight['message']}")
            else:
                st.info(f"ℹ️ **{insight['title']}**: {insight['message']}")
    else:
        st.info("📊 Performances stables sur la période analysée")


def render_weekly_summary(data: pd.DataFrame):
    """Affiche un résumé hebdomadaire"""

    st.markdown("### 📅 Résumé Hebdomadaire")

    if data.empty:
        st.info("Aucune donnée pour le résumé hebdomadaire")
        return

    # Conversion en semaines
    data_copy = data.copy()
    data_copy['date'] = pd.to_datetime(data_copy['date'])
    data_copy['week'] = data_copy['date'].dt.isocalendar().week
    data_copy['year'] = data_copy['date'].dt.year
    data_copy['week_label'] = data_copy['year'].astype(str) + '-S' + data_copy['week'].astype(str)

    # Agrégation par semaine
    weekly_data = data_copy.groupby('week_label').agg({
        'cost': 'sum',
        'installs': 'sum',
        'purchases': 'sum',
        'revenue': 'sum'
    }).reset_index()

    # Calcul des métriques hebdomadaires
    weekly_data['cpa'] = weekly_data['cost'] / weekly_data['installs']
    weekly_data['roas'] = weekly_data['revenue'] / weekly_data['cost']
    weekly_data['cpa'] = weekly_data['cpa'].fillna(0)
    weekly_data['roas'] = weekly_data['roas'].fillna(0)

    # Affichage du tableau
    st.dataframe(
        weekly_data,
        column_config={
            "week_label": "Semaine",
            "cost": st.column_config.NumberColumn("Coût", format="%.2f €"),
            "installs": st.column_config.NumberColumn("Installs", format="%d"),
            "purchases": st.column_config.NumberColumn("Achats", format="%d"),
            "revenue": st.column_config.NumberColumn("Revenus", format="%.2f €"),
            "cpa": st.column_config.NumberColumn("CPA", format="%.2f €"),
            "roas": st.column_config.NumberColumn("ROAS", format="%.2f")
        },
        use_container_width=True
    )