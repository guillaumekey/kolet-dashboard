import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict  # Ajout des imports typing manquants

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict

def render_temporal_performance(data):
    """Affichage des performances temporelles avec tous les graphiques"""
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
    fig_secondary_2 = make_subplots(
        rows=1, cols=2,
        subplot_titles=('CPI', 'ROAS'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}]]
    )

    # CPI
    fig_secondary_2.add_trace(
        go.Scatter(x=daily_data['date'], y=daily_data['cpi'],
                   name='CPI', line=dict(color='#e67e22')),
        row=1, col=1
    )

    # ROAS
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

def _prepare_daily_data(data: pd.DataFrame) -> pd.DataFrame:
    """Prépare les données pour l'analyse temporelle"""

    try:
        # Conversion de la date si nécessaire
        if 'date' not in data.columns:
            st.error("Colonne 'date' manquante dans les données")
            return pd.DataFrame()

        # Conversion en datetime si ce n'est pas déjà fait
        if data['date'].dtype == 'object':
            data['date'] = pd.to_datetime(data['date'])

        # Groupement par date
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

        # Tri par date
        daily_data = daily_data.sort_values('date')

        # Calcul des métriques dérivées
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

    # Couleurs pour les métriques
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