import streamlit as st
import pandas as pd
from typing import Dict  # Ajout de l'import manquant
from utils.helpers import format_currency, format_percentage


def render_main_kpis(processed_data):
    """Affichage des KPI principaux avec données séparées"""

    # Récupérer les données consolidées et les données brutes
    data = processed_data['consolidated']
    raw_data = processed_data.get('raw', {})

    # MODIFIÉ : Calcul des clics et impressions uniquement depuis Google Ads et ASA
    google_ads_data = raw_data.get('google_ads', pd.DataFrame())
    asa_data = raw_data.get('asa', pd.DataFrame())

    # Clics et impressions : Google Ads + ASA seulement
    total_clicks = 0
    total_impressions = 0

    if not google_ads_data.empty:
        total_clicks += google_ads_data['clicks'].sum()
        total_impressions += google_ads_data['impressions'].sum()

    if not asa_data.empty:
        total_clicks += asa_data['clicks'].sum()
        total_impressions += asa_data['impressions'].sum()

    # ================== SECTION DONNÉES GLOBALES ==================
    st.markdown("### 📊 Données Globales")
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
        # MODIFIÉ : Utiliser les clics calculés depuis Google Ads + ASA uniquement
        st.metric(
            label="👁️ Impressions",
            value=f"{int(total_impressions):,}".replace(",", " "),
            delta=None,
            help="Sources: Google Ads + Apple Search Ads uniquement"
        )

    with col3:
        # MODIFIÉ : Utiliser les clics calculés depuis Google Ads + ASA uniquement
        st.metric(
            label="🖱️ Clics",
            value=f"{int(total_clicks):,}".replace(",", " "),
            delta=None,
            help="Sources: Google Ads + Apple Search Ads uniquement"
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
        # Espace vide pour équilibrer
        st.write("")

    with col10:
        # Espace vide pour équilibrer
        st.write("")

    st.markdown("</div>", unsafe_allow_html=True)

    # ================== SECTION RATIOS DE PERFORMANCE ==================
    st.markdown("### 📈 Ratios de Performance")
    st.markdown("<div class='kpi-container'>", unsafe_allow_html=True)

    # Utiliser les données des funnels App et Web pour les calculs spécifiques
    app_data = processed_data.get('app', pd.DataFrame())
    web_data = processed_data.get('web', pd.DataFrame())

    # Totaux App (depuis le funnel app)
    if not app_data.empty:
        app_installs = app_data['installs'].sum()
        app_purchases = app_data['purchases'].sum()
        app_logins = app_data['login'].sum() if 'login' in app_data.columns else 0
    else:
        app_installs = app_purchases = app_logins = 0

    # Totaux Web (depuis le funnel web)
    if not web_data.empty:
        web_clicks = web_data['clicks'].sum()
        web_purchases = web_data['purchases'].sum()
    else:
        web_clicks = web_purchases = 0

    # Ratios de performance
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        # CPI (Coût par Install)
        cpi = total_spend / total_installs if total_installs > 0 else 0
        st.metric(
            label="💸 CPI",
            value=format_currency(cpi),
            delta=None,
            help="Coût par Installation"
        )

    with col2:
        # ROAS
        roas = total_revenue / total_spend if total_spend > 0 else 0
        st.metric(
            label="📈 ROAS",
            value=f"{roas:.2f}",
            delta=None,
            help="Return on Ad Spend"
        )

    with col3:
        # CPA (Coût par Achat)
        cpa = total_spend / total_purchases if total_purchases > 0 else 0
        st.metric(
            label="💰 CPA",
            value=format_currency(cpa),
            delta=None,
            help="Coût par Achat"
        )

    with col4:
        # Taux de conversion App (Achats / Installs)
        app_conversion_rate = (app_purchases / app_installs * 100) if app_installs > 0 else 0
        st.metric(
            label="📱 Conv. App",
            value=format_percentage(app_conversion_rate),
            delta=None,
            help="Taux de conversion App (Achats / Installs)"
        )

    with col5:
        # Taux de conversion Web (Achats / Clics)
        web_conversion_rate = (web_purchases / web_clicks * 100) if web_clicks > 0 else 0
        st.metric(
            label="🌐 Conv. Web",
            value=format_percentage(web_conversion_rate),
            delta=None,
            help="Taux de conversion Web (Achats / Clics)"
        )

    with col6:
        # Taux de login App (Logins / Installations)
        app_login_rate = (app_logins / app_installs * 100) if app_installs > 0 else 0
        st.metric(
            label="🔐 Login App",
            value=format_percentage(app_login_rate),
            delta=None,
            help="Taux de login App (Logins / Installations)"
        )

    st.markdown("</div>", unsafe_allow_html=True)


def _calculate_advertising_metrics(raw_data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
    """
    Calcule les métriques publicitaires uniquement depuis Google Ads et ASA

    Args:
        raw_data: Données brutes par source

    Returns:
        Dictionnaire avec les métriques publicitaires
    """

    total_clicks = 0
    total_impressions = 0

    # Google Ads
    google_ads_data = raw_data.get('google_ads', pd.DataFrame())
    if not google_ads_data.empty:
        total_clicks += google_ads_data['clicks'].sum()
        total_impressions += google_ads_data['impressions'].sum()

    # Apple Search Ads
    asa_data = raw_data.get('asa', pd.DataFrame())
    if not asa_data.empty:
        total_clicks += asa_data['clicks'].sum()
        total_impressions += asa_data['impressions'].sum()

    return {
        'total_clicks': total_clicks,
        'total_impressions': total_impressions
    }


def _render_global_metrics_section(data: pd.DataFrame, clicks_impressions: Dict[str, float]):
    """Rendu de la section des métriques globales"""

    st.markdown("### 📊 Données Globales")
    st.markdown("<div class='kpi-container'>", unsafe_allow_html=True)

    # Première ligne de métriques
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        total_spend = data['cost'].sum() if 'cost' in data.columns else 0
        st.metric(
            label="💰 Coût Total",
            value=format_currency(total_spend),
            help="Coût total de toutes les campagnes (Google Ads + ASA)"
        )

    with col2:
        st.metric(
            label="👁️ Impressions",
            value=f"{int(clicks_impressions['total_impressions']):,}".replace(",", " "),
            help="Sources: Google Ads + Apple Search Ads uniquement"
        )

    with col3:
        st.metric(
            label="🖱️ Clics",
            value=f"{int(clicks_impressions['total_clicks']):,}".replace(",", " "),
            help="Sources: Google Ads + Apple Search Ads uniquement"
        )

    with col4:
        total_installs = data['installs'].sum() if 'installs' in data.columns else 0
        st.metric(
            label="📱 Installations",
            value=f"{int(total_installs):,}".replace(",", " "),
            help="Installations tracking via Branch.io"
        )

    with col5:
        total_revenue = data['revenue'].sum() if 'revenue' in data.columns else 0
        st.metric(
            label="💵 Revenus",
            value=format_currency(total_revenue),
            help="Revenus consolidés (Branch.io + Google Ads)"
        )

    # Deuxième ligne de métriques
    col6, col7, col8, col9, col10 = st.columns(5)

    with col6:
        total_opens = data['opens'].sum() if 'opens' in data.columns else 0
        st.metric(
            label="👀 Opens",
            value=f"{int(total_opens):,}".replace(",", " "),
            help="Ouvertures d'application (Branch.io)"
        )

    with col7:
        total_login = data['login'].sum() if 'login' in data.columns else 0
        st.metric(
            label="🔐 Logins",
            value=f"{int(total_login):,}".replace(",", " "),
            help="Connexions utilisateurs (Branch.io)"
        )

    with col8:
        total_purchases = data['purchases'].sum() if 'purchases' in data.columns else 0
        st.metric(
            label="🛒 Purchases",
            value=f"{int(total_purchases):,}".replace(",", " "),
            help="Achats consolidés (Branch.io + Google Ads)"
        )

    with col9:
        # Métrique bonus : CTR global
        total_impressions = clicks_impressions['total_impressions']
        total_clicks = clicks_impressions['total_clicks']
        global_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0

        st.metric(
            label="📈 CTR Global",
            value=format_percentage(global_ctr),
            help="Click-Through Rate global (Clics/Impressions)"
        )

    with col10:
        # Métrique bonus : Taux de conversion global
        total_installs = data['installs'].sum() if 'installs' in data.columns else 0
        global_conversion = (total_installs / total_clicks * 100) if total_clicks > 0 else 0

        st.metric(
            label="🎯 Conv. Globale",
            value=format_percentage(global_conversion),
            help="Taux de conversion global (Installs/Clics)"
        )

    st.markdown("</div>", unsafe_allow_html=True)


def _render_performance_ratios_section(data: pd.DataFrame, processed_data: Dict[str, pd.DataFrame],
                                       clicks_impressions: Dict[str, float]):
    """Rendu de la section des ratios de performance"""

    st.markdown("### 📈 Ratios de Performance")
    st.markdown("<div class='kpi-container'>", unsafe_allow_html=True)

    # Calculer les totaux pour les ratios
    totals = _calculate_performance_totals(data, processed_data, clicks_impressions)

    # Ratios de performance
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        # CPI (Coût par Install)
        st.metric(
            label="💸 CPI",
            value=format_currency(totals['cpi']),
            help="Coût par Installation"
        )

    with col2:
        # ROAS
        st.metric(
            label="📈 ROAS",
            value=f"{totals['roas']:.2f}",
            help="Return on Ad Spend"
        )

    with col3:
        # CPA (Coût par Achat)
        st.metric(
            label="💰 CPA",
            value=format_currency(totals['cpa']),
            help="Coût par Achat"
        )

    with col4:
        # Taux de conversion App
        st.metric(
            label="📱 Conv. App",
            value=format_percentage(totals['app_conversion_rate']),
            help="Taux de conversion App (Achats / Installs)"
        )

    with col5:
        # Taux de conversion Web
        st.metric(
            label="🌐 Conv. Web",
            value=format_percentage(totals['web_conversion_rate']),
            help="Taux de conversion Web (Achats / Clics)"
        )

    with col6:
        # Taux de login App
        st.metric(
            label="🔐 Login App",
            value=format_percentage(totals['app_login_rate']),
            help="Taux de login App (Logins / Installations)"
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # Section d'insights automatiques
    _render_performance_insights(totals)


def _calculate_performance_totals(data: pd.DataFrame, processed_data: Dict[str, pd.DataFrame],
                                  clicks_impressions: Dict[str, float]) -> Dict[str, float]:
    """Calcule tous les totaux nécessaires pour les ratios de performance"""

    # Totaux généraux
    total_spend = data['cost'].sum() if 'cost' in data.columns else 0
    total_installs = data['installs'].sum() if 'installs' in data.columns else 0
    total_revenue = data['revenue'].sum() if 'revenue' in data.columns else 0
    total_purchases = data['purchases'].sum() if 'purchases' in data.columns else 0
    total_clicks = clicks_impressions['total_clicks']

    # Totaux App
    app_data = processed_data.get('app', pd.DataFrame())
    if not app_data.empty:
        app_installs = app_data['installs'].sum()
        app_purchases = app_data['purchases'].sum()
        app_logins = app_data['login'].sum() if 'login' in app_data.columns else 0
    else:
        app_installs = app_purchases = app_logins = 0

    # Totaux Web
    web_data = processed_data.get('web', pd.DataFrame())
    if not web_data.empty:
        web_clicks = web_data['clicks'].sum()
        web_purchases = web_data['purchases'].sum()
    else:
        web_clicks = web_purchases = 0

    # Calcul des ratios
    cpi = total_spend / total_installs if total_installs > 0 else 0
    roas = total_revenue / total_spend if total_spend > 0 else 0
    cpa = total_spend / total_purchases if total_purchases > 0 else 0
    app_conversion_rate = (app_purchases / app_installs * 100) if app_installs > 0 else 0
    web_conversion_rate = (web_purchases / web_clicks * 100) if web_clicks > 0 else 0
    app_login_rate = (app_logins / app_installs * 100) if app_installs > 0 else 0

    return {
        'cpi': cpi,
        'roas': roas,
        'cpa': cpa,
        'app_conversion_rate': app_conversion_rate,
        'web_conversion_rate': web_conversion_rate,
        'app_login_rate': app_login_rate,
        'total_spend': total_spend,
        'total_installs': total_installs,
        'total_revenue': total_revenue,
        'app_installs': app_installs,
        'web_clicks': web_clicks
    }


def _render_performance_insights(totals: Dict[str, float]):
    """Affiche des insights automatiques sur les performances"""

    st.markdown("---")
    st.markdown("### 💡 Insights Performance")

    insights = []

    # Analyse ROAS
    if totals['roas'] > 3:
        insights.append({
            'type': 'success',
            'icon': '🎯',
            'title': 'ROAS Excellent',
            'message': f"Votre ROAS de {totals['roas']:.2f} est excellent ! Chaque euro dépensé génère {totals['roas']:.2f}€ de revenus."
        })
    elif totals['roas'] < 1:
        insights.append({
            'type': 'warning',
            'icon': '⚠️',
            'title': 'ROAS à optimiser',
            'message': f"Votre ROAS de {totals['roas']:.2f} indique que vous dépensez plus que vous ne gagnez. Optimisation nécessaire."
        })

    # Analyse CPI
    if totals['cpi'] < 5:
        insights.append({
            'type': 'success',
            'icon': '💰',
            'title': 'CPI Optimal',
            'message': f"Votre coût par installation de {format_currency(totals['cpi'])} est très compétitif."
        })
    elif totals['cpi'] > 15:
        insights.append({
            'type': 'warning',
            'icon': '💸',
            'title': 'CPI Élevé',
            'message': f"Votre CPI de {format_currency(totals['cpi'])} est élevé. Considérez l'optimisation de vos campagnes."
        })

    # Comparaison App vs Web
    if totals['app_conversion_rate'] > totals['web_conversion_rate'] * 1.5:
        insights.append({
            'type': 'info',
            'icon': '📱',
            'title': 'App plus performant',
            'message': f"L'App convertit mieux ({totals['app_conversion_rate']:.1f}%) que le Web ({totals['web_conversion_rate']:.1f}%)."
        })
    elif totals['web_conversion_rate'] > totals['app_conversion_rate'] * 1.5:
        insights.append({
            'type': 'info',
            'icon': '🌐',
            'title': 'Web plus performant',
            'message': f"Le Web convertit mieux ({totals['web_conversion_rate']:.1f}%) que l'App ({totals['app_conversion_rate']:.1f}%)."
        })

    # Analyse budget
    if totals['total_spend'] > 0 and totals['total_installs'] > 0:
        spend_per_day = totals['total_spend'] / 14  # Période de 14 jours par défaut
        if spend_per_day > 100:
            insights.append({
                'type': 'info',
                'icon': '📊',
                'title': 'Budget conséquent',
                'message': f"Votre budget moyen de {format_currency(spend_per_day)}/jour permet une bonne visibilité."
            })

    # Affichage des insights
    if insights:
        cols = st.columns(min(len(insights), 3))
        for i, insight in enumerate(insights):
            with cols[i % 3]:
                _render_insight_card(insight)
    else:
        st.info("📈 Continuez à optimiser vos campagnes pour améliorer les performances !")


def _render_insight_card(insight: Dict[str, str]):
    """Affiche une carte d'insight"""

    card_class = {
        'success': 'alert-success',
        'warning': 'alert-warning',
        'info': 'alert-info'
    }.get(insight['type'], 'alert-info')

    st.markdown(f"""
    <div class="{card_class}">
        <strong>{insight['icon']} {insight['title']}</strong><br>
        {insight['message']}
    </div>
    """, unsafe_allow_html=True)


def render_kpi_summary_cards():
    """Affiche des cartes résumé KPI pour navigation rapide"""

    st.markdown("### 🎯 Navigation Rapide")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📊 Voir KPI détaillés", use_container_width=True):
            st.experimental_set_query_params(section="kpi")

    with col2:
        if st.button("🎯 Analyser funnels", use_container_width=True):
            st.experimental_set_query_params(section="funnel")

    with col3:
        if st.button("📈 Tendances temporelles", use_container_width=True):
            st.experimental_set_query_params(section="temporal")

    with col4:
        if st.button("🔍 Performance campagnes", use_container_width=True):
            st.experimental_set_query_params(section="campaigns")


def render_mobile_kpi_view(processed_data: Dict[str, pd.DataFrame]):
    """Version mobile/compacte des KPI pour petits écrans"""

    st.markdown("### 📱 Vue Mobile - KPI Essentiels")

    data = processed_data['consolidated']

    # KPI essentiels en version compacte
    col1, col2 = st.columns(2)

    with col1:
        total_spend = data['cost'].sum() if 'cost' in data.columns else 0
        total_installs = data['installs'].sum() if 'installs' in data.columns else 0

        st.metric("💰 Budget", format_currency(total_spend))
        st.metric("📱 Installs", f"{total_installs:,}")

    with col2:
        total_revenue = data['revenue'].sum() if 'revenue' in data.columns else 0
        roas = total_revenue / total_spend if total_spend > 0 else 0

        st.metric("💵 Revenus", format_currency(total_revenue))
        st.metric("📈 ROAS", f"{roas:.2f}")

    # Progress bars pour visualisation rapide
    st.markdown("**🎯 Performance en un coup d'œil**")

    # ROAS progress (objectif 2.0)
    roas_progress = min(roas / 2.0, 1.0)
    st.progress(roas_progress)
    st.caption(f"ROAS: {roas:.2f} / 2.0 (objectif)")

    # Conversion rate progress (objectif 10%)
    app_data = processed_data.get('app', pd.DataFrame())
    if not app_data.empty:
        app_installs = app_data['installs'].sum()
        app_purchases = app_data['purchases'].sum()
        conversion_rate = (app_purchases / app_installs * 100) if app_installs > 0 else 0
        conversion_progress = min(conversion_rate / 10.0, 1.0)

        st.progress(conversion_progress)
        st.caption(f"Taux conversion App: {conversion_rate:.1f}% / 10% (objectif)")