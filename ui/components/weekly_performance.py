"""
Module d'analyse des performances hebdomadaires pour Kolet Dashboard
Utilise EXACTEMENT la même logique de calcul que les KPIs globaux
"""

import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Tuple


def get_week_range_european(date: datetime) -> Tuple[str, str]:
    """
    Retourne le début (lundi) et la fin (dimanche) de la semaine européenne

    Args:
        date: Date quelconque dans la semaine

    Returns:
        Tuple (date_debut, date_fin) au format 'YYYY-MM-DD'
    """
    # Vérifier si la date est valide
    if pd.isna(date) or date is None:
        return None, None

    # Trouver le lundi de cette semaine (0=lundi, 6=dimanche)
    days_since_monday = date.weekday()
    monday = date - timedelta(days=days_since_monday)
    sunday = monday + timedelta(days=6)

    return monday.strftime('%Y-%m-%d'), sunday.strftime('%Y-%m-%d')


def add_week_info(df):
    """Ajoute les informations de semaine à un DataFrame"""
    if df.empty or 'date' not in df.columns:
        return df

    week_info = []
    for date in df['date']:
        week_start, week_end = get_week_range_european(date)
        week_info.append({
            'week_start': week_start,
            'week_end': week_end,
            'week_name': format_week_name(week_start, week_end)
        })
    week_df = pd.DataFrame(week_info)
    return pd.concat([df, week_df], axis=1)


def format_week_name(start_date: str, end_date: str) -> str:
    """Formate le nom de la semaine pour affichage"""
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')

    # Format: "Sem 21 (19/05 → 25/05)"
    week_num = start_dt.isocalendar()[1]
    start_display = start_dt.strftime('%d/%m')
    end_display = end_dt.strftime('%d/%m')

    return f"Sem {week_num} ({start_display} → {end_display})"


def calculate_weekly_kpis_with_date_filter(processed_data: Dict, date_range: Tuple,
                                           exclude_unpopulated: bool = False) -> pd.DataFrame:
    """
    CORRECTION COMPLÈTE : Reproduire exactement la logique de séparation App/Web de kpi_dashboard.py
    """

    # Récupérer les données EXACTEMENT comme dans kpi_dashboard.py
    consolidated_data = processed_data.get('consolidated', pd.DataFrame())
    raw_data = processed_data.get('raw', {})

    # NOUVEAU : Récupérer les données App et Web séparées (comme kpi_dashboard.py)
    app_data = processed_data.get('app', pd.DataFrame())
    web_data = processed_data.get('web', pd.DataFrame())

    if consolidated_data.empty:
        return pd.DataFrame()

    # Sources de données brutes
    google_ads_data = raw_data.get('google_ads', pd.DataFrame())
    asa_data = raw_data.get('asa', pd.DataFrame())

    # Appliquer le filtre Unpopulated si nécessaire
    if exclude_unpopulated:
        # Filtrer consolidated_data si les colonnes existent
        if 'campaign_name' in consolidated_data.columns and 'source' in consolidated_data.columns:
            mask = ~((consolidated_data['campaign_name'] == 'Unpopulated') & (
                        consolidated_data['source'] == 'branch_io'))
            consolidated_data = consolidated_data[mask]

        # Filtrer les données App et Web aussi
        if not app_data.empty and 'campaign_name' in app_data.columns:
            app_data = app_data[app_data['campaign_name'] != 'Unpopulated']
        if not web_data.empty and 'campaign_name' in web_data.columns:
            web_data = web_data[web_data['campaign_name'] != 'Unpopulated']

    # Filtrer par date
    start_date_str = date_range[0].strftime('%Y-%m-%d') if hasattr(date_range[0], 'strftime') else str(date_range[0])
    end_date_str = date_range[1].strftime('%Y-%m-%d') if hasattr(date_range[1], 'strftime') else str(date_range[1])

    # Filtrer toutes les données par date
    for df_name, df in [('consolidated', consolidated_data), ('app', app_data), ('web', web_data),
                        ('google_ads', google_ads_data), ('asa', asa_data)]:
        if not df.empty and 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df = df[(df['date'] >= start_date_str) & (df['date'] <= end_date_str)]

            # Réassigner les DataFrames filtrés
            if df_name == 'consolidated':
                consolidated_data = df
            elif df_name == 'app':
                app_data = df
            elif df_name == 'web':
                web_data = df
            elif df_name == 'google_ads':
                google_ads_data = df
            elif df_name == 'asa':
                asa_data = df

    if consolidated_data.empty:
        st.warning("Aucune donnée après filtrage par date")
        return pd.DataFrame()

    # Ajouter les informations de semaine à TOUTES les données
    def add_week_info_local(df):
        if df.empty or 'date' not in df.columns:
            return df
        df_clean = df.dropna(subset=['date']).copy()
        if df_clean.empty:
            return df

        # Éviter les colonnes dupliquées
        for col in ['week_start', 'week_end', 'week_name']:
            if col in df_clean.columns:
                df_clean = df_clean.drop(columns=[col])

        week_info = []
        for date in df_clean['date']:
            try:
                week_start, week_end = get_week_range_european(date)
                if week_start is not None and week_end is not None:
                    week_info.append({
                        'week_start': week_start,
                        'week_end': week_end,
                        'week_name': format_week_name(week_start, week_end)
                    })
                else:
                    week_info.append({'week_start': None, 'week_end': None, 'week_name': None})
            except Exception as e:
                week_info.append({'week_start': None, 'week_end': None, 'week_name': None})

        week_df = pd.DataFrame(week_info)
        return pd.concat([df_clean.reset_index(drop=True), week_df.reset_index(drop=True)], axis=1)

    # Ajouter les infos de semaine à toutes les données
    consolidated_data = add_week_info_local(consolidated_data)
    app_data = add_week_info_local(app_data)
    web_data = add_week_info_local(web_data)
    google_ads_data = add_week_info_local(google_ads_data)
    asa_data = add_week_info_local(asa_data)

    # Obtenir toutes les semaines uniques
    all_weeks = set()
    for df_name, df in [('consolidated', consolidated_data), ('app', app_data), ('web', web_data),
                        ('google_ads', google_ads_data), ('asa', asa_data)]:
        if not df.empty and 'week_start' in df.columns:
            valid_weeks_df = df.dropna(subset=['week_start', 'week_end', 'week_name'])
            if not valid_weeks_df.empty:
                df_weeks = set(
                    zip(valid_weeks_df['week_start'], valid_weeks_df['week_end'], valid_weeks_df['week_name']))
                all_weeks.update(df_weeks)

    if not all_weeks:
        return pd.DataFrame()

    valid_weeks = [(start, end, name) for start, end, name in all_weeks
                   if pd.notna(start) and pd.notna(end) and pd.notna(name)]

    if not valid_weeks:
        return pd.DataFrame()

    # Calculer les KPIs pour chaque semaine avec la vraie logique App/Web
    weekly_results = []

    for week_start, week_end, week_name in sorted(valid_weeks):

        # === MÉTRIQUES CONSOLIDÉES (pour cost, installs, revenue, opens, purchases) ===
        week_consolidated = consolidated_data[
            (consolidated_data['week_start'] == week_start) &
            (consolidated_data['week_end'] == week_end)
            ]

        cost = week_consolidated['cost'].sum() if not week_consolidated.empty else 0
        installs = week_consolidated['installs'].sum() if not week_consolidated.empty else 0
        revenue = week_consolidated['revenue'].sum() if not week_consolidated.empty else 0
        opens = week_consolidated['opens'].sum() if not week_consolidated.empty else 0
        login = week_consolidated['login'].sum() if not week_consolidated.empty else 0
        purchases = week_consolidated['purchases'].sum() if not week_consolidated.empty else 0

        # === CLICS ET IMPRESSIONS (Google Ads + ASA pour cette semaine) ===
        clicks = 0
        impressions = 0

        if not google_ads_data.empty and 'week_start' in google_ads_data.columns:
            week_google = google_ads_data[
                (google_ads_data['week_start'] == week_start) &
                (google_ads_data['week_end'] == week_end)
                ]
            if not week_google.empty:
                clicks += week_google['clicks'].sum()
                impressions += week_google['impressions'].sum()

        if not asa_data.empty and 'week_start' in asa_data.columns:
            week_asa = asa_data[
                (asa_data['week_start'] == week_start) &
                (asa_data['week_end'] == week_end)
                ]
            if not week_asa.empty:
                clicks += week_asa['clicks'].sum()
                impressions += week_asa['impressions'].sum()

        # === SÉPARATION APP ET WEB pour les taux de conversion (comme kpi_dashboard.py) ===

        # App data pour cette semaine
        week_app = app_data[
            (app_data['week_start'] == week_start) &
            (app_data['week_end'] == week_end)
            ] if not app_data.empty and 'week_start' in app_data.columns else pd.DataFrame()

        app_installs = week_app['installs'].sum() if not week_app.empty else 0
        app_purchases = week_app['purchases'].sum() if not week_app.empty else 0
        app_logins = week_app['login'].sum() if not week_app.empty and 'login' in week_app.columns else 0

        # Web data pour cette semaine
        week_web = web_data[
            (web_data['week_start'] == week_start) &
            (web_data['week_end'] == week_end)
            ] if not web_data.empty and 'week_start' in web_data.columns else pd.DataFrame()

        web_clicks = week_web['clicks'].sum() if not week_web.empty else 0
        web_purchases = week_web['purchases'].sum() if not week_web.empty else 0

        # Construire la ligne de résultats avec les vraies métriques séparées
        weekly_results.append({
            'week_start': week_start,
            'week_end': week_end,
            'week_name': week_name,
            'cost': cost,
            'impressions': impressions,
            'clicks': clicks,
            'installs': installs,
            'purchases': purchases,
            'revenue': revenue,
            'opens': opens,
            'login': login,
            # Nouvelles colonnes pour les calculs de conversion corrects
            'app_installs': app_installs,
            'app_purchases': app_purchases,
            'app_logins': app_logins,
            'web_clicks': web_clicks,
            'web_purchases': web_purchases
        })

    # Convertir en DataFrame et calculer les KPIs dérivés avec la vraie logique
    weekly_df = pd.DataFrame(weekly_results)

    if weekly_df.empty:
        return pd.DataFrame()

    # Calculer les KPIs dérivés avec la logique corrigée
    weekly_kpis = calculate_derived_kpis_corrected(weekly_df)

    # Trier par semaine (plus récente en premier)
    weekly_kpis = weekly_kpis.sort_values('week_start', ascending=False)

    return weekly_kpis
    """
    Calcule les KPIs hebdomadaires en appliquant d'abord le même filtre de dates que les KPIs globaux

    Args:
        processed_data: Données traitées
        date_range: Tuple (start_date, end_date) pour filtrer
        exclude_unpopulated: Si True, exclut les données Unpopulated

    Returns:
        DataFrame avec une ligne par semaine et tous les KPIs
    """

    # Récupérer les données EXACTEMENT comme dans kpi_dashboard.py
    consolidated_data = processed_data.get('consolidated', pd.DataFrame())
    raw_data = processed_data.get('raw', {})

    if consolidated_data.empty:
        return pd.DataFrame()

    # Sources de données brutes
    google_ads_data = raw_data.get('google_ads', pd.DataFrame())
    asa_data = raw_data.get('asa', pd.DataFrame())

    # Appliquer le filtre Unpopulated si nécessaire
    if exclude_unpopulated:
        # Filtrer consolidated_data si les colonnes existent
        if 'campaign_name' in consolidated_data.columns and 'source' in consolidated_data.columns:
            mask = ~((consolidated_data['campaign_name'] == 'Unpopulated') & (
                        consolidated_data['source'] == 'branch_io'))
            consolidated_data = consolidated_data[mask]

        # Filtrer les données brutes ASA/Google Ads si nécessaire
        for df_name, df in [('google_ads', google_ads_data), ('asa', asa_data)]:
            if not df.empty and 'campaign_name' in df.columns:
                df = df[df['campaign_name'] != 'Unpopulated']

    # Filtrer par date comme les KPIs globaux
    start_date_str = date_range[0].strftime('%Y-%m-%d') if hasattr(date_range[0], 'strftime') else str(date_range[0])
    end_date_str = date_range[1].strftime('%Y-%m-%d') if hasattr(date_range[1], 'strftime') else str(date_range[1])

    # Filtrer consolidated_data par date
    consolidated_data['date'] = pd.to_datetime(consolidated_data['date'])
    consolidated_data = consolidated_data[
        (consolidated_data['date'] >= start_date_str) &
        (consolidated_data['date'] <= end_date_str)
        ]

    # Filtrer Google Ads par date
    if not google_ads_data.empty and 'date' in google_ads_data.columns:
        google_ads_data['date'] = pd.to_datetime(google_ads_data['date'])
        google_ads_data = google_ads_data[
            (google_ads_data['date'] >= start_date_str) &
            (google_ads_data['date'] <= end_date_str)
            ]

    # Filtrer ASA par date
    if not asa_data.empty and 'date' in asa_data.columns:
        asa_data['date'] = pd.to_datetime(asa_data['date'])
        asa_data = asa_data[
            (asa_data['date'] >= start_date_str) &
            (asa_data['date'] <= end_date_str)
            ]

    if consolidated_data.empty:
        st.warning("Aucune donnée après filtrage par date")
        return pd.DataFrame()

    # Maintenant procéder avec les données filtrées
    # Ajouter les informations de semaine manuellement
    # Ajouter les informations de semaine avec debugging
    def add_week_info_local(df):
        if df.empty or 'date' not in df.columns:
            return df

        # Filtrer les dates valides avant traitement
        df_clean = df.dropna(subset=['date']).copy()
        if df_clean.empty:
            st.warning("Toutes les dates sont nulles dans ce DataFrame")
            return df

        # Éviter les colonnes dupliquées - supprimer les colonnes week_* si elles existent déjà
        for col in ['week_start', 'week_end', 'week_name']:
            if col in df_clean.columns:
                df_clean = df_clean.drop(columns=[col])

        week_info = []
        for date in df_clean['date']:
            try:
                week_start, week_end = get_week_range_european(date)
                if week_start is not None and week_end is not None:
                    week_info.append({
                        'week_start': week_start,
                        'week_end': week_end,
                        'week_name': format_week_name(week_start, week_end)
                    })
                else:
                    week_info.append({
                        'week_start': None,
                        'week_end': None,
                        'week_name': None
                    })
            except Exception as e:
                st.warning(f"Erreur calcul semaine pour date {date}: {e}")
                week_info.append({
                    'week_start': None,
                    'week_end': None,
                    'week_name': None
                })

        week_df = pd.DataFrame(week_info)
        return pd.concat([df_clean.reset_index(drop=True), week_df.reset_index(drop=True)], axis=1)

    consolidated_data = add_week_info_local(consolidated_data)
    google_ads_data = add_week_info_local(google_ads_data)
    asa_data = add_week_info_local(asa_data)

    # CORRECTION : Revenir à la vraie logique hebdomadaire mais avec calcul correct
    # Le problème était dans le calcul des semaines européennes

    # Ajouter les informations de semaine
    consolidated_data = add_week_info_local(consolidated_data)
    google_ads_data = add_week_info_local(google_ads_data)
    asa_data = add_week_info_local(asa_data)

    # Obtenir toutes les semaines uniques
    all_weeks = set()

    for df_name, df in [('consolidated', consolidated_data), ('google_ads', google_ads_data), ('asa', asa_data)]:
        if not df.empty and 'week_start' in df.columns:
            valid_weeks_df = df.dropna(subset=['week_start', 'week_end', 'week_name'])
            if not valid_weeks_df.empty:
                df_weeks = set(
                    zip(valid_weeks_df['week_start'], valid_weeks_df['week_end'], valid_weeks_df['week_name']))
                all_weeks.update(df_weeks)

    if not all_weeks:
        return pd.DataFrame()

    valid_weeks = [(start, end, name) for start, end, name in all_weeks
                   if pd.notna(start) and pd.notna(end) and pd.notna(name)]

    if not valid_weeks:
        return pd.DataFrame()

    # Calculer les KPIs pour chaque semaine
    weekly_results = []

    for week_start, week_end, week_name in sorted(valid_weeks):

        # === MÉTRIQUES DEPUIS DONNÉES CONSOLIDÉES ===
        week_consolidated = consolidated_data[
            (consolidated_data['week_start'] == week_start) &
            (consolidated_data['week_end'] == week_end)
            ]

        cost = week_consolidated['cost'].sum() if not week_consolidated.empty else 0
        installs = week_consolidated['installs'].sum() if not week_consolidated.empty else 0
        revenue = week_consolidated['revenue'].sum() if not week_consolidated.empty else 0
        opens = week_consolidated['opens'].sum() if not week_consolidated.empty else 0
        login = week_consolidated['login'].sum() if not week_consolidated.empty else 0
        purchases = week_consolidated['purchases'].sum() if not week_consolidated.empty else 0

        # === CLICS ET IMPRESSIONS POUR CETTE SEMAINE ===
        clicks = 0
        impressions = 0

        # Google Ads pour cette semaine
        if not google_ads_data.empty and 'week_start' in google_ads_data.columns:
            week_google = google_ads_data[
                (google_ads_data['week_start'] == week_start) &
                (google_ads_data['week_end'] == week_end)
                ]
            if not week_google.empty:
                clicks += week_google['clicks'].sum()
                impressions += week_google['impressions'].sum()

        # ASA pour cette semaine
        if not asa_data.empty and 'week_start' in asa_data.columns:
            week_asa = asa_data[
                (asa_data['week_start'] == week_start) &
                (asa_data['week_end'] == week_end)
                ]
            if not week_asa.empty:
                clicks += week_asa['clicks'].sum()
                impressions += week_asa['impressions'].sum()

        # Construire la ligne de résultats pour cette semaine
        weekly_results.append({
            'week_start': week_start,
            'week_end': week_end,
            'week_name': week_name,
            'cost': cost,
            'impressions': impressions,
            'clicks': clicks,
            'installs': installs,
            'purchases': purchases,
            'revenue': revenue,
            'opens': opens,
            'login': login
        })

    # Convertir en DataFrame
    weekly_df = pd.DataFrame(weekly_results)

    if weekly_df.empty:
        return pd.DataFrame()

    # Calculer les KPIs dérivés
    weekly_kpis = calculate_derived_kpis(weekly_df)

    # Trier par semaine (plus récente en premier)
    weekly_kpis = weekly_kpis.sort_values('week_start', ascending=False)

    return weekly_kpis
    """
    Calcule les KPIs hebdomadaires avec EXACTEMENT la même logique que render_main_kpis()

    Args:
        processed_data: Données traitées (même structure que dans app.py)
        exclude_unpopulated: Si True, exclut les données Unpopulated

    Returns:
        DataFrame avec une ligne par semaine et tous les KPIs
    """

    # Récupérer les données EXACTEMENT comme dans kpi_dashboard.py
    consolidated_data = processed_data.get('consolidated', pd.DataFrame())
    raw_data = processed_data.get('raw', {})

    if consolidated_data.empty:
        return pd.DataFrame()

    # Sources de données brutes (même logique que kpi_dashboard.py)
    google_ads_data = raw_data.get('google_ads', pd.DataFrame())
    asa_data = raw_data.get('asa', pd.DataFrame())

    # Calculer d'abord les totaux globaux comme dans kpi_dashboard.py pour vérification
    total_clicks_global = 0
    total_impressions_global = 0

    if not google_ads_data.empty:
        total_clicks_global += google_ads_data['clicks'].sum()
        total_impressions_global += google_ads_data['impressions'].sum()

    if not asa_data.empty:
        total_clicks_global += asa_data['clicks'].sum()
        total_impressions_global += asa_data['impressions'].sum()

    st.write(f"DEBUG - Totaux globaux calculés: {total_clicks_global} clics, {total_impressions_global} impressions")

    # Convertir les dates et ajouter les informations de semaine
    if not consolidated_data.empty:
        consolidated_data['date'] = pd.to_datetime(consolidated_data['date'])

    # CORRECTION : Convertir les dates des données brutes avec gestion des erreurs
    if not google_ads_data.empty and 'date' in google_ads_data.columns:
        try:
            google_ads_data['date'] = pd.to_datetime(google_ads_data['date'])
        except:
            st.warning("Erreur conversion date Google Ads")
            google_ads_data = pd.DataFrame()

    if not asa_data.empty and 'date' in asa_data.columns:
        try:
            asa_data['date'] = pd.to_datetime(asa_data['date'])
        except:
            st.warning("Erreur conversion date ASA")
            asa_data = pd.DataFrame()

    # Debug temporaire - vérifier les totaux AVANT filtrage par semaine
    if not google_ads_data.empty:
        st.write(
            f"DEBUG Google Ads TOTAL: {google_ads_data['clicks'].sum()} clics, {google_ads_data['impressions'].sum()} impressions")
        st.write(f"DEBUG Lignes Google Ads: {len(google_ads_data)}")
    if not asa_data.empty:
        st.write(f"DEBUG ASA TOTAL: {asa_data['clicks'].sum()} clics, {asa_data['impressions'].sum()} impressions")
        st.write(f"DEBUG Lignes ASA: {len(asa_data)}")

    # Debug des semaines trouvées
    if 'valid_weeks' in locals():
        st.write(f"DEBUG Semaines uniques trouvées: {len(valid_weeks)}")
        for week_start, week_end, week_name in valid_weeks[:3]:  # Montrer les 3 premières
            st.write(f"  - {week_name}: {week_start} → {week_end}")
    else:
        st.write("DEBUG: valid_weeks non défini - problème dans le traitement des semaines")

    # Calculer les semaines européennes pour toutes les données
    def add_week_info(df):
        if df.empty:
            return df
        week_info = []
        for date in df['date']:
            week_start, week_end = get_week_range_european(date)
            week_info.append({
                'week_start': week_start,
                'week_end': week_end,
                'week_name': format_week_name(week_start, week_end)
            })
        week_df = pd.DataFrame(week_info)
        return pd.concat([df, week_df], axis=1)

    # Ajouter les infos de semaines
    consolidated_data = add_week_info(consolidated_data)
    google_ads_data = add_week_info(google_ads_data)
    asa_data = add_week_info(asa_data)

    # Obtenir toutes les semaines uniques (en filtrant les valeurs nulles)
    all_weeks = set()
    for df in [consolidated_data, google_ads_data, asa_data]:
        if not df.empty and 'week_start' in df.columns:
            # Filtrer les lignes avec des valeurs non-nulles pour les colonnes de semaine
            valid_weeks = df.dropna(subset=['week_start', 'week_end', 'week_name'])
            if not valid_weeks.empty:
                all_weeks.update(zip(valid_weeks['week_start'], valid_weeks['week_end'], valid_weeks['week_name']))

    if not all_weeks:
        return pd.DataFrame()

    # Filtrer et trier les semaines valides
    valid_weeks = [(start, end, name) for start, end, name in all_weeks
                   if pd.notna(start) and pd.notna(end) and pd.notna(name)]

    if not valid_weeks:
        return pd.DataFrame()

    # Calculer les KPIs pour chaque semaine
    weekly_results = []

    for week_start, week_end, week_name in sorted(valid_weeks):

        # === MÉTRIQUES DEPUIS DONNÉES CONSOLIDÉES ===
        # (Même logique que total_spend, total_installs, etc. dans kpi_dashboard.py)

        week_consolidated = consolidated_data[
            (consolidated_data['week_start'] == week_start) &
            (consolidated_data['week_end'] == week_end)
            ]

        # Agrégations depuis consolidated (même logique que kpi_dashboard.py)
        cost = week_consolidated['cost'].sum() if not week_consolidated.empty else 0
        installs = week_consolidated['installs'].sum() if not week_consolidated.empty else 0
        revenue = week_consolidated['revenue'].sum() if not week_consolidated.empty else 0
        opens = week_consolidated['opens'].sum() if not week_consolidated.empty else 0
        login = week_consolidated['login'].sum() if not week_consolidated.empty else 0
        purchases = week_consolidated['purchases'].sum() if not week_consolidated.empty else 0

        # === CLICS ET IMPRESSIONS : UNIQUEMENT Google Ads + ASA ===
        # (EXACTEMENT la même logique que kpi_dashboard.py)

        clicks = 0
        impressions = 0

        # Google Ads pour cette semaine
        if not google_ads_data.empty:
            week_google = google_ads_data[
                (google_ads_data['week_start'] == week_start) &
                (google_ads_data['week_end'] == week_end)
                ]
            if not week_google.empty:
                clicks += week_google['clicks'].sum()
                impressions += week_google['impressions'].sum()

        # ASA pour cette semaine
        if not asa_data.empty:
            week_asa = asa_data[
                (asa_data['week_start'] == week_start) &
                (asa_data['week_end'] == week_end)
                ]
            if not week_asa.empty:
                clicks += week_asa['clicks'].sum()
                impressions += week_asa['impressions'].sum()

        # Construire la ligne de résultats
        weekly_results.append({
            'week_start': week_start,
            'week_end': week_end,
            'week_name': week_name,
            'cost': cost,
            'impressions': impressions,
            'clicks': clicks,
            'installs': installs,
            'purchases': purchases,
            'revenue': revenue,
            'opens': opens,
            'login': login
        })

    # Convertir en DataFrame
    weekly_df = pd.DataFrame(weekly_results)

    if weekly_df.empty:
        return pd.DataFrame()

    # Calculer les KPIs dérivés (même formules que kpi_dashboard.py)
    weekly_kpis = calculate_derived_kpis(weekly_df)

    # Trier par semaine (plus récente en premier)
    weekly_kpis = weekly_kpis.sort_values('week_start', ascending=False)

    return weekly_kpis


def calculate_derived_kpis_corrected(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule les KPIs dérivés avec la VRAIE logique de séparation App/Web (comme kpi_dashboard.py)
    """

    kpis = df.copy()

    # === RATIOS DE PERFORMANCE (logique corrigée) ===

    # CPI (Cost Per Install)
    kpis['cpi'] = (kpis['cost'] / kpis['installs']).fillna(0)

    # ROAS (Return On Advertising Spend)
    kpis['roas'] = (kpis['revenue'] / kpis['cost']).fillna(0)

    # CPA (Cost Per Acquisition)
    kpis['cpa'] = (kpis['cost'] / kpis['purchases']).fillna(0)

    # === TAUX DE CONVERSION CORRIGÉS (exactement comme kpi_dashboard.py) ===

    # Conv. App = app_purchases / app_installs * 100
    kpis['conv_app'] = (kpis['app_purchases'] / kpis['app_installs'] * 100).fillna(0)

    # Conv. Web = web_purchases / web_clicks * 100
    kpis['conv_web'] = (kpis['web_purchases'] / kpis['web_clicks'] * 100).fillna(0)

    # Login App = app_logins / app_installs * 100 (comme kpi_dashboard.py)
    kpis['login_app'] = (kpis['app_logins'] / kpis['app_installs'] * 100).fillna(0)

    # === FORMATAGE POUR AFFICHAGE ===

    # Formater les montants
    kpis['cout_total_display'] = kpis['cost'].apply(lambda x: f"{x:,.2f} €")
    kpis['revenue_display'] = kpis['revenue'].apply(lambda x: f"{x:,.2f} €")
    kpis['cpi_display'] = kpis['cpi'].apply(lambda x: f"{x:.2f} €")
    kpis['cpa_display'] = kpis['cpa'].apply(lambda x: f"{x:.2f} €")

    # Formater les ratios
    kpis['roas_display'] = kpis['roas'].apply(lambda x: f"{x:.2f}")
    kpis['conv_app_display'] = kpis['conv_app'].apply(lambda x: f"{x:.2f}%")
    kpis['conv_web_display'] = kpis['conv_web'].apply(lambda x: f"{x:.2f}%")
    kpis['login_app_display'] = kpis['login_app'].apply(lambda x: f"{x:.2f}%")

    # Formater les nombres (même format que kpi_dashboard.py)
    kpis['impressions_display'] = kpis['impressions'].apply(lambda x: f"{int(x):,}".replace(",", " "))
    kpis['clicks_display'] = kpis['clicks'].apply(lambda x: f"{int(x):,}".replace(",", " "))
    kpis['installs_display'] = kpis['installs'].apply(lambda x: f"{int(x):,}".replace(",", " "))
    kpis['purchases_display'] = kpis['purchases'].apply(lambda x: f"{int(x):,}".replace(",", " "))
    kpis['opens_display'] = kpis['opens'].apply(lambda x: f"{int(x):,}".replace(",", " "))
    kpis['login_display'] = kpis['login'].apply(lambda x: f"{int(x):,}".replace(",", " "))

    return kpis


def render_weekly_performance_table(processed_data: Dict, date_range: Tuple, exclude_unpopulated: bool = False):
    """
    Affiche le tableau des performances hebdomadaires dans Streamlit

    Args:
        processed_data: Données traitées (même structure que dans render_main_kpis)
        date_range: Tuple (start_date, end_date) - MÊME FILTRE que les KPIs globaux
        exclude_unpopulated: Si True, exclut les données Unpopulated
    """

    st.subheader("📊 Performances Hebdomadaires")

    # Calculer les KPIs hebdomadaires avec le même filtrage de dates que les KPIs globaux
    weekly_data = calculate_weekly_kpis_with_date_filter(processed_data, date_range, exclude_unpopulated)

    if weekly_data.empty:
        st.warning("Aucune donnée disponible pour la période sélectionnée")
        return

    # Afficher les filtres appliqués
    filter_info = []
    if exclude_unpopulated:
        filter_info.append("Données 'Unpopulated' exclues")

    if filter_info:
        st.info(f"🔍 Filtres actifs: {' • '.join(filter_info)}")

    st.write(f"📈 **{len(weekly_data)} semaines** analysées du {date_range[0]} au {date_range[1]}")

    # === TABLEAU PRINCIPAL ===

    # Colonnes à afficher dans l'ordre souhaité
    display_columns = {
        'week_name': 'Semaine',
        'cout_total_display': '💰 Coût Total',
        'impressions_display': '👁️ Impressions',
        'clicks_display': '🖱️ Clics',
        'installs_display': '📱 Installations',
        'opens_display': '📖 Opens',
        'login_display': '🔐 Logins',
        'purchases_display': '🛒 Purchases',
        'revenue_display': '💚 Revenus',
        'cpi_display': '📊 CPI',
        'roas_display': '🎯 ROAS',
        'cpa_display': '💡 CPA',
        'conv_app_display': '📱 Conv. App',
        'conv_web_display': '🌐 Conv. Web',
        'login_app_display': '🔐 Login App'
    }

    # Créer le DataFrame d'affichage
    display_df = weekly_data[list(display_columns.keys())].copy()
    display_df.columns = list(display_columns.values())

    # Afficher le tableau avec styling
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

    # === RÉSUMÉ GLOBAL ===

    st.subheader("📈 Résumé de la période")

    # Calculer les totaux/moyennes
    totals = {
        'cost': weekly_data['cost'].sum(),
        'impressions': weekly_data['impressions'].sum(),
        'clicks': weekly_data['clicks'].sum(),
        'installs': weekly_data['installs'].sum(),
        'purchases': weekly_data['purchases'].sum(),
        'revenue': weekly_data['revenue'].sum(),
        'opens': weekly_data['opens'].sum(),
        'login': weekly_data['login'].sum()
    }

    # Recalculer les ratios globaux (même logique que kpi_dashboard.py)
    global_cpi = totals['cost'] / totals['installs'] if totals['installs'] > 0 else 0
    global_roas = totals['revenue'] / totals['cost'] if totals['cost'] > 0 else 0
    global_cpa = totals['cost'] / totals['purchases'] if totals['purchases'] > 0 else 0
    global_conv_app = (totals['purchases'] / totals['installs'] * 100) if totals['installs'] > 0 else 0
    global_conv_web = (totals['purchases'] / totals['clicks'] * 100) if totals['clicks'] > 0 else 0
    global_login_app = (totals['login'] / totals['opens'] * 100) if totals['opens'] > 0 else 0

    # Afficher en colonnes (même format que kpi_dashboard.py)
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("💰 Coût Total", f"{totals['cost']:,.2f} €")
        st.metric("👁️ Impressions", f"{int(totals['impressions']):,}".replace(",", " "))

    with col2:
        st.metric("🖱️ Clics", f"{int(totals['clicks']):,}".replace(",", " "))
        st.metric("📱 Installations", f"{int(totals['installs']):,}".replace(",", " "))

    with col3:
        st.metric("💚 Revenus", f"{totals['revenue']:,.2f} €")
        st.metric("📖 Opens", f"{int(totals['opens']):,}".replace(",", " "))

    with col4:
        st.metric("🔐 Logins", f"{int(totals['login']):,}".replace(",", " "))
        st.metric("🛒 Purchases", f"{int(totals['purchases']):,}".replace(",", " "))

    with col5:
        st.metric("📊 CPI", f"{global_cpi:.2f} €")
        st.metric("🎯 ROAS", f"{global_roas:.2f}")

    # Deuxième ligne de ratios
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("💡 CPA", f"{global_cpa:.2f} €")

    with col2:
        st.metric("📱 Conv. App", f"{global_conv_app:.2f}%")

    with col3:
        st.metric("🔐 Login App", f"{global_login_app:.2f}%")

    # === EXPORT DES DONNÉES ===

    with st.expander("📥 Exporter les données"):

        # Bouton de téléchargement CSV
        csv_data = weekly_data.to_csv(index=False)
        st.download_button(
            label="💾 Télécharger CSV complet",
            data=csv_data,
            file_name=f"kolet_performances_hebdomadaires_{date_range[0]}_{date_range[1]}.csv",
            mime="text/csv"
        )

        # Afficher les données brutes pour debug
        if st.checkbox("🔍 Voir données brutes"):
            st.dataframe(weekly_data, use_container_width=True)