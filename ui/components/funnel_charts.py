import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.helpers import format_currency, format_percentage


def render_acquisition_funnel(app_data: pd.DataFrame, web_data: pd.DataFrame):
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

            # Ratios de passage App
            st.markdown("**Ratios de passage:**")
            if app_totals['impressions'] > 0:
                impressions_to_clicks = (app_totals['clicks'] / app_totals['impressions'] * 100)
                st.write(f"• Impressions → Clics: {impressions_to_clicks:.2f}%")

            if app_totals['clicks'] > 0:
                clicks_to_installs = (app_totals['installs'] / app_totals['clicks'] * 100)
                st.write(f"• Clics → Installs: {clicks_to_installs:.2f}%")

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

            # Ratios de passage Web
            st.markdown("**Ratios de passage:**")
            if web_totals['impressions'] > 0:
                impressions_to_clicks = (web_totals['clicks'] / web_totals['impressions'] * 100)
                st.write(f"• Impressions → Clics: {impressions_to_clicks:.2f}%")

            if web_totals['clicks'] > 0:
                clicks_to_cart = (web_totals['add_to_cart'] / web_totals['clicks'] * 100)
                st.write(f"• Clics → Panier: {clicks_to_cart:.2f}%")

            if web_totals['add_to_cart'] > 0:
                cart_to_purchases = (web_totals['purchases'] / web_totals['add_to_cart'] * 100)
                st.write(f"• Panier → Achats: {cart_to_purchases:.2f}%")
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


def _render_side_by_side_funnels(app_data: pd.DataFrame, web_data: pd.DataFrame):
    """Affichage côte à côte des funnels"""

    col1, col2 = st.columns(2)

    # Funnel App
    with col1:
        _render_app_funnel(app_data)

    # Funnel Web
    with col2:
        _render_web_funnel(web_data)


def _render_app_funnel(app_data: pd.DataFrame):
    """Rendu du funnel App"""

    st.markdown("#### 📱 Funnel App")

    if app_data.empty:
        st.info("Aucune donnée App disponible")
        return

    # Calcul des totaux
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

    fig_app = _create_funnel_chart(funnel_data_app, "App")
    st.plotly_chart(fig_app, use_container_width=True)

    # Métriques App
    _render_app_metrics(app_totals)

    # Ratios de passage App
    _render_app_conversion_rates(app_totals)


def _render_web_funnel(web_data: pd.DataFrame):
    """Rendu du funnel Web"""

    st.markdown("#### 🌐 Funnel Web")

    if web_data.empty:
        st.info("Aucune donnée Web disponible")
        return

    # Calcul des totaux
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

    fig_web = _create_funnel_chart(funnel_data_web, "Web")
    st.plotly_chart(fig_web, use_container_width=True)

    # Métriques Web
    _render_web_metrics(web_totals)

    # Ratios de passage Web
    _render_web_conversion_rates(web_totals)


def _render_app_metrics(app_totals: dict):
    """Affiche les métriques principales du funnel App"""

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        ctr_app = (app_totals['clicks'] / app_totals['impressions'] * 100) if app_totals['impressions'] > 0 else 0
        st.metric("CTR", format_percentage(ctr_app))

    with col2:
        install_rate = (app_totals['installs'] / app_totals['clicks'] * 100) if app_totals['clicks'] > 0 else 0
        st.metric("Taux Install", format_percentage(install_rate))

    with col3:
        cpa = app_totals['cost'] / app_totals['installs'] if app_totals['installs'] > 0 else 0
        st.metric("CPA", format_currency(cpa))

    with col4:
        roas_app = app_totals['revenue'] / app_totals['cost'] if app_totals['cost'] > 0 else 0
        st.metric("ROAS", f"{roas_app:.2f}")


def _render_web_metrics(web_totals: dict):
    """Affiche les métriques principales du funnel Web"""

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        ctr_web = (web_totals['clicks'] / web_totals['impressions'] * 100) if web_totals['impressions'] > 0 else 0
        st.metric("CTR", format_percentage(ctr_web))

    with col2:
        cart_rate = (web_totals['add_to_cart'] / web_totals['clicks'] * 100) if web_totals['clicks'] > 0 else 0
        st.metric("Taux Panier", format_percentage(cart_rate))

    with col3:
        cpa = web_totals['cost'] / web_totals['purchases'] if web_totals['purchases'] > 0 else 0
        st.metric("CPA", format_currency(cpa))

    with col4:
        roas_web = web_totals['revenue'] / web_totals['cost'] if web_totals['cost'] > 0 else 0
        st.metric("ROAS", f"{roas_web:.2f}")


def _render_app_conversion_rates(app_totals: dict):
    """Affiche les taux de conversion du funnel App"""

    st.markdown("**📊 Ratios de passage:**")

    rates = []

    if app_totals['impressions'] > 0:
        impressions_to_clicks = (app_totals['clicks'] / app_totals['impressions'] * 100)
        rates.append(f"• Impressions → Clics: {impressions_to_clicks:.2f}%")

    if app_totals['clicks'] > 0:
        clicks_to_installs = (app_totals['installs'] / app_totals['clicks'] * 100)
        rates.append(f"• Clics → Installs: {clicks_to_installs:.2f}%")

    if app_totals['installs'] > 0:
        installs_to_opens = (app_totals['opens'] / app_totals['installs'] * 100)
        rates.append(f"• Installs → Opens: {installs_to_opens:.2f}%")

        if app_totals['login'] > 0:
            opens_to_logins = (app_totals['login'] / app_totals['opens'] * 100) if app_totals['opens'] > 0 else 0
            rates.append(f"• Opens → Logins: {opens_to_logins:.2f}%")

            logins_to_purchases = (app_totals['purchases'] / app_totals['login'] * 100) if app_totals[
                                                                                               'login'] > 0 else 0
            rates.append(f"• Logins → Purchases: {logins_to_purchases:.2f}%")

    for rate in rates:
        st.write(rate)


def _render_web_conversion_rates(web_totals: dict):
    """Affiche les taux de conversion du funnel Web"""

    st.markdown("**📊 Ratios de passage:**")

    rates = []

    if web_totals['impressions'] > 0:
        impressions_to_clicks = (web_totals['clicks'] / web_totals['impressions'] * 100)
        rates.append(f"• Impressions → Clics: {impressions_to_clicks:.2f}%")

    if web_totals['clicks'] > 0:
        clicks_to_cart = (web_totals['add_to_cart'] / web_totals['clicks'] * 100)
        rates.append(f"• Clics → Panier: {clicks_to_cart:.2f}%")

    if web_totals['add_to_cart'] > 0:
        cart_to_purchases = (web_totals['purchases'] / web_totals['add_to_cart'] * 100)
        rates.append(f"• Panier → Achats: {cart_to_purchases:.2f}%")

    for rate in rates:
        st.write(rate)


def _create_funnel_chart(data, title):
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
        height=400,
        showlegend=False
    )

    return fig


def _render_unified_comparison(app_data: pd.DataFrame, web_data: pd.DataFrame):
    """Affichage de comparaison unifiée des funnels"""

    st.markdown("#### 🔄 Comparaison Unifiée App vs Web")

    if app_data.empty and web_data.empty:
        st.warning("Aucune donnée disponible pour la comparaison")
        return

    # Calcul des totaux pour comparaison
    app_totals = _calculate_funnel_totals(app_data) if not app_data.empty else {}
    web_totals = _calculate_funnel_totals(web_data) if not web_data.empty else {}

    # Graphique de comparaison side-by-side
    fig = _create_comparison_chart(app_totals, web_totals)
    st.plotly_chart(fig, use_container_width=True)

    # Tableau de comparaison
    _render_comparison_table(app_totals, web_totals)


def _render_advanced_details(app_data: pd.DataFrame, web_data: pd.DataFrame):
    """Affichage des détails avancés des funnels"""

    st.markdown("#### 📊 Analyse Détaillée des Funnels")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📱 Détails App",
        "🌐 Détails Web",
        "🔄 Comparaison",
        "📈 Optimisations"
    ])

    with tab1:
        _render_app_detailed_analysis(app_data)

    with tab2:
        _render_web_detailed_analysis(web_data)

    with tab3:
        _render_detailed_comparison(app_data, web_data)

    with tab4:
        _render_optimization_suggestions(app_data, web_data)


def _calculate_funnel_totals(data: pd.DataFrame) -> dict:
    """Calcule les totaux pour un funnel"""

    if data.empty:
        return {}

    return {
        'impressions': data['impressions'].sum(),
        'clicks': data['clicks'].sum(),
        'installs': data.get('installs', pd.Series([0])).sum(),
        'opens': data.get('opens', pd.Series([0])).sum(),
        'login': data.get('login', pd.Series([0])).sum(),
        'add_to_cart': data.get('add_to_cart', pd.Series([0])).sum(),
        'purchases': data['purchases'].sum(),
        'cost': data['cost'].sum(),
        'revenue': data['revenue'].sum()
    }


def _create_comparison_chart(app_totals: dict, web_totals: dict):
    """Crée un graphique de comparaison des funnels"""

    # Métriques communes pour comparaison
    metrics = ['impressions', 'clicks', 'purchases', 'cost', 'revenue']
    app_values = [app_totals.get(metric, 0) for metric in metrics]
    web_values = [web_totals.get(metric, 0) for metric in metrics]

    fig = go.Figure(data=[
        go.Bar(name='App', x=metrics, y=app_values, marker_color='#3498db'),
        go.Bar(name='Web', x=metrics, y=web_values, marker_color='#9b59b6')
    ])

    fig.update_layout(
        title="Comparaison App vs Web - Métriques Principales",
        barmode='group',
        height=400,
        yaxis_title="Valeurs",
        xaxis_title="Métriques"
    )

    return fig


def _render_comparison_table(app_totals: dict, web_totals: dict):
    """Affiche un tableau de comparaison détaillé"""

    st.markdown("**📋 Tableau de Comparaison**")

    comparison_data = []

    metrics_config = [
        ('Impressions', 'impressions', 'number'),
        ('Clics', 'clicks', 'number'),
        ('Installations', 'installs', 'number'),
        ('Achats', 'purchases', 'number'),
        ('Coût', 'cost', 'currency'),
        ('Revenus', 'revenue', 'currency'),
        ('ROAS', 'roas', 'ratio')
    ]

    for label, key, format_type in metrics_config:
        app_value = app_totals.get(key, 0)
        web_value = web_totals.get(key, 0)

        # Calcul spécial pour ROAS
        if key == 'roas':
            app_value = app_totals.get('revenue', 0) / app_totals.get('cost', 1)
            web_value = web_totals.get('revenue', 0) / web_totals.get('cost', 1)

        # Formatage selon le type
        if format_type == 'currency':
            app_formatted = format_currency(app_value)
            web_formatted = format_currency(web_value)
        elif format_type == 'ratio':
            app_formatted = f"{app_value:.2f}"
            web_formatted = f"{web_value:.2f}"
        else:
            app_formatted = f"{app_value:,.0f}"
            web_formatted = f"{web_value:,.0f}"

        # Calcul de la différence
        if app_value > 0 and web_value > 0:
            if app_value > web_value:
                winner = "📱 App"
                diff = f"+{((app_value - web_value) / web_value * 100):.1f}%"
            elif web_value > app_value:
                winner = "🌐 Web"
                diff = f"+{((web_value - app_value) / app_value * 100):.1f}%"
            else:
                winner = "🟰 Égalité"
                diff = "0%"
        else:
            winner = "📱 App" if app_value > web_value else "🌐 Web"
            diff = "-"

        comparison_data.append({
            'Métrique': label,
            'App': app_formatted,
            'Web': web_formatted,
            'Meilleur': winner,
            'Écart': diff
        })

    comparison_df = pd.DataFrame(comparison_data)
    st.dataframe(comparison_df, use_container_width=True)


def _render_app_detailed_analysis(app_data: pd.DataFrame):
    """Analyse détaillée du funnel App"""

    if app_data.empty:
        st.info("Aucune donnée App pour l'analyse détaillée")
        return

    st.markdown("**📱 Analyse Détaillée - Funnel App**")

    # Analyse temporelle
    if len(app_data) > 1:
        st.markdown("**📈 Évolution temporelle**")

        fig = go.Figure()

        metrics = ['installs', 'opens', 'purchases']
        colors = ['#3498db', '#9b59b6', '#e74c3c']

        for metric, color in zip(metrics, colors):
            if metric in app_data.columns:
                fig.add_trace(go.Scatter(
                    x=app_data['date'],
                    y=app_data[metric],
                    mode='lines+markers',
                    name=metric.capitalize(),
                    line=dict(color=color)
                ))

        fig.update_layout(
            title="Évolution des métriques App par jour",
            xaxis_title="Date",
            yaxis_title="Valeurs",
            height=300
        )

        st.plotly_chart(fig, use_container_width=True)

    # Analyse des goulots d'étranglement
    _analyze_app_bottlenecks(app_data)


def _render_web_detailed_analysis(web_data: pd.DataFrame):
    """Analyse détaillée du funnel Web"""

    if web_data.empty:
        st.info("Aucune donnée Web pour l'analyse détaillée")
        return

    st.markdown("**🌐 Analyse Détaillée - Funnel Web**")

    # Analyse temporelle similaire à App
    if len(web_data) > 1:
        st.markdown("**📈 Évolution temporelle**")

        fig = go.Figure()

        metrics = ['clicks', 'add_to_cart', 'purchases']
        colors = ['#f39c12', '#2ecc71', '#e74c3c']

        for metric, color in zip(metrics, colors):
            if metric in web_data.columns:
                fig.add_trace(go.Scatter(
                    x=web_data['date'],
                    y=web_data[metric],
                    mode='lines+markers',
                    name=metric.replace('_', ' ').title(),
                    line=dict(color=color)
                ))

        fig.update_layout(
            title="Évolution des métriques Web par jour",
            xaxis_title="Date",
            yaxis_title="Valeurs",
            height=300
        )

        st.plotly_chart(fig, use_container_width=True)

    # Analyse des goulots d'étranglement
    _analyze_web_bottlenecks(web_data)


def _analyze_app_bottlenecks(app_data: pd.DataFrame):
    """Analyse les goulots d'étranglement du funnel App"""

    st.markdown("**🔍 Analyse des Goulots d'Étranglement**")

    totals = _calculate_funnel_totals(app_data)

    # Calcul des taux de conversion entre chaque étape
    conversion_rates = []

    if totals['impressions'] > 0:
        ctr = (totals['clicks'] / totals['impressions']) * 100
        conversion_rates.append(('Impressions → Clics', ctr, 'CTR'))

    if totals['clicks'] > 0:
        install_rate = (totals['installs'] / totals['clicks']) * 100
        conversion_rates.append(('Clics → Installs', install_rate, 'Taux d\'installation'))

    if totals['installs'] > 0:
        open_rate = (totals['opens'] / totals['installs']) * 100
        conversion_rates.append(('Installs → Opens', open_rate, 'Taux d\'ouverture'))

    if totals['opens'] > 0 and totals['login'] > 0:
        login_rate = (totals['login'] / totals['opens']) * 100
        conversion_rates.append(('Opens → Logins', login_rate, 'Taux de connexion'))

    if totals['login'] > 0:
        purchase_rate = (totals['purchases'] / totals['login']) * 100
        conversion_rates.append(('Logins → Purchases', purchase_rate, 'Taux d\'achat'))

    # Identification du plus gros goulot
    if conversion_rates:
        min_rate = min(conversion_rates, key=lambda x: x[1])
        max_rate = max(conversion_rates, key=lambda x: x[1])

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"**🔴 Plus gros goulot**")
            st.write(f"{min_rate[0]}: {min_rate[1]:.2f}%")
            st.caption(f"Étape à optimiser en priorité")

        with col2:
            st.markdown(f"**🟢 Meilleure étape**")
            st.write(f"{max_rate[0]}: {max_rate[1]:.2f}%")
            st.caption(f"Performance à maintenir")


def _analyze_web_bottlenecks(web_data: pd.DataFrame):
    """Analyse les goulots d'étranglement du funnel Web"""

    st.markdown("**🔍 Analyse des Goulots d'Étranglement**")

    totals = _calculate_funnel_totals(web_data)

    # Calcul des taux de conversion entre chaque étape
    conversion_rates = []

    if totals['impressions'] > 0:
        ctr = (totals['clicks'] / totals['impressions']) * 100
        conversion_rates.append(('Impressions → Clics', ctr, 'CTR'))

    if totals['clicks'] > 0:
        cart_rate = (totals['add_to_cart'] / totals['clicks']) * 100
        conversion_rates.append(('Clics → Panier', cart_rate, 'Taux d\'ajout panier'))

    if totals['add_to_cart'] > 0:
        purchase_rate = (totals['purchases'] / totals['add_to_cart']) * 100
        conversion_rates.append(('Panier → Achats', purchase_rate, 'Taux de finalisation'))

    # Identification du plus gros goulot
    if conversion_rates:
        min_rate = min(conversion_rates, key=lambda x: x[1])
        max_rate = max(conversion_rates, key=lambda x: x[1])

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"**🔴 Plus gros goulot**")
            st.write(f"{min_rate[0]}: {min_rate[1]:.2f}%")
            st.caption(f"Étape à optimiser en priorité")

        with col2:
            st.markdown(f"**🟢 Meilleure étape**")
            st.write(f"{max_rate[0]}: {max_rate[1]:.2f}%")
            st.caption(f"Performance à maintenir")


def _render_detailed_comparison(app_data: pd.DataFrame, web_data: pd.DataFrame):
    """Comparaison détaillée entre App et Web"""

    st.markdown("**🔄 Comparaison Détaillée App vs Web**")

    if app_data.empty or web_data.empty:
        st.warning("Données insuffisantes pour une comparaison détaillée")
        return

    # Comparaison des efficacités par étape
    app_totals = _calculate_funnel_totals(app_data)
    web_totals = _calculate_funnel_totals(web_data)

    # Efficacité par euro dépensé
    st.markdown("**💰 Efficacité par Euro Dépensé**")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**📱 App**")
        if app_totals['cost'] > 0:
            installs_per_euro = app_totals['installs'] / app_totals['cost']
            purchases_per_euro = app_totals['purchases'] / app_totals['cost']
            revenue_per_euro = app_totals['revenue'] / app_totals['cost']

            st.metric("Installs / €", f"{installs_per_euro:.2f}")
            st.metric("Achats / €", f"{purchases_per_euro:.2f}")
            st.metric("Revenus / €", f"{revenue_per_euro:.2f}")

    with col2:
        st.markdown("**🌐 Web**")
        if web_totals['cost'] > 0:
            clicks_per_euro = web_totals['clicks'] / web_totals['cost']
            purchases_per_euro = web_totals['purchases'] / web_totals['cost']
            revenue_per_euro = web_totals['revenue'] / web_totals['cost']

            st.metric("Clics / €", f"{clicks_per_euro:.2f}")
            st.metric("Achats / €", f"{purchases_per_euro:.2f}")
            st.metric("Revenus / €", f"{revenue_per_euro:.2f}")


def _render_optimization_suggestions(app_data: pd.DataFrame, web_data: pd.DataFrame):
    """Suggestions d'optimisation basées sur l'analyse des funnels"""

    st.markdown("**🎯 Suggestions d'Optimisation**")

    suggestions = []

    # Analyse App
    if not app_data.empty:
        app_totals = _calculate_funnel_totals(app_data)
        app_suggestions = _generate_app_suggestions(app_totals)
        suggestions.extend(app_suggestions)

    # Analyse Web
    if not web_data.empty:
        web_totals = _calculate_funnel_totals(web_data)
        web_suggestions = _generate_web_suggestions(web_totals)
        suggestions.extend(web_suggestions)

    # Comparaison App vs Web
    if not app_data.empty and not web_data.empty:
        comparison_suggestions = _generate_comparison_suggestions(app_data, web_data)
        suggestions.extend(comparison_suggestions)

    # Affichage des suggestions
    if suggestions:
        for i, suggestion in enumerate(suggestions, 1):
            with st.expander(f"{suggestion['priority']} {suggestion['title']}", expanded=False):
                st.write(suggestion['description'])
                if 'action' in suggestion:
                    st.markdown(f"**Action recommandée:** {suggestion['action']}")
                if 'impact' in suggestion:
                    st.markdown(f"**Impact estimé:** {suggestion['impact']}")
    else:
        st.info("🎉 Vos funnels semblent bien optimisés ! Continuez le bon travail.")


def _generate_app_suggestions(app_totals: dict) -> list:
    """Génère des suggestions d'optimisation pour l'App"""

    suggestions = []

    # CTR faible
    if app_totals['impressions'] > 0:
        ctr = (app_totals['clicks'] / app_totals['impressions']) * 100
        if ctr < 2:
            suggestions.append({
                'priority': '🔴',
                'title': 'CTR App faible',
                'description': f'Votre CTR App de {ctr:.2f}% est en dessous des standards (>2%).',
                'action': 'Optimiser les créatifs publicitaires et le ciblage',
                'impact': 'Augmentation du trafic qualifié'
            })

    # Taux d'installation faible
    if app_totals['clicks'] > 0:
        install_rate = (app_totals['installs'] / app_totals['clicks']) * 100
        if install_rate < 15:
            suggestions.append({
                'priority': '🟡',
                'title': 'Taux d\'installation à améliorer',
                'description': f'Votre taux d\'installation de {install_rate:.2f}% peut être optimisé.',
                'action': 'Améliorer la page de l\'App Store et les descriptions',
                'impact': 'Plus d\'installations pour le même trafic'
            })

    # Faible rétention (opens/installs)
    if app_totals['installs'] > 0:
        open_rate = (app_totals['opens'] / app_totals['installs']) * 100
        if open_rate < 50:
            suggestions.append({
                'priority': '🟡',
                'title': 'Rétention Day 1 faible',
                'description': f'Seulement {open_rate:.1f}% des utilisateurs ouvrent l\'app après installation.',
                'action': 'Améliorer l\'onboarding et envoyer des notifications push pertinentes',
                'impact': 'Meilleure activation des utilisateurs'
            })

    return suggestions


def _generate_web_suggestions(web_totals: dict) -> list:
    """Génère des suggestions d'optimisation pour le Web"""

    suggestions = []

    # CTR faible
    if web_totals['impressions'] > 0:
        ctr = (web_totals['clicks'] / web_totals['impressions']) * 100
        if ctr < 1.5:
            suggestions.append({
                'priority': '🔴',
                'title': 'CTR Web faible',
                'description': f'Votre CTR Web de {ctr:.2f}% est en dessous des standards (>1.5%).',
                'action': 'Optimiser les annonces et les mots-clés',
                'impact': 'Plus de trafic qualifié sur le site'
            })

    # Taux d'abandon panier élevé
    if web_totals['add_to_cart'] > 0:
        cart_to_purchase = (web_totals['purchases'] / web_totals['add_to_cart']) * 100
        if cart_to_purchase < 20:
            suggestions.append({
                'priority': '🟡',
                'title': 'Abandon panier élevé',
                'description': f'Seulement {cart_to_purchase:.1f}% des paniers se transforment en achats.',
                'action': 'Simplifier le checkout et réduire les frictions',
                'impact': 'Augmentation significative des conversions'
            })

    return suggestions


def _generate_comparison_suggestions(app_data: pd.DataFrame, web_data: pd.DataFrame) -> list:
    """Génère des suggestions basées sur la comparaison App vs Web"""

    suggestions = []

    app_totals = _calculate_funnel_totals(app_data)
    web_totals = _calculate_funnel_totals(web_data)

    # Comparer les ROAS
    app_roas = app_totals['revenue'] / app_totals['cost'] if app_totals['cost'] > 0 else 0
    web_roas = web_totals['revenue'] / web_totals['cost'] if web_totals['cost'] > 0 else 0

    if app_roas > web_roas * 1.5:
        suggestions.append({
            'priority': '🟢',
            'title': 'Réallouer budget vers App',
            'description': f'L\'App génère un ROAS de {app_roas:.2f} vs {web_roas:.2f} pour le Web.',
            'action': 'Augmenter le budget des campagnes App et réduire celui du Web',
            'impact': 'Amélioration du ROAS global'
        })
    elif web_roas > app_roas * 1.5:
        suggestions.append({
            'priority': '🟢',
            'title': 'Réallouer budget vers Web',
            'description': f'Le Web génère un ROAS de {web_roas:.2f} vs {app_roas:.2f} pour l\'App.',
            'action': 'Augmenter le budget des campagnes Web et optimiser l\'App',
            'impact': 'Amélioration du ROAS global'
        })

    return suggestions