import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.helpers import format_currency


def render_app_vs_web_comparison(app_data: pd.DataFrame, web_data: pd.DataFrame):
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
                'revenue': web_data['revenue'].sum(),
                'clicks': web_data['clicks'].sum()
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


def _render_overview_comparison(app_data: pd.DataFrame, web_data: pd.DataFrame):
    """Vue d'ensemble de la comparaison App vs Web"""

    col1, col2 = st.columns(2)

    # Performance App
    with col1:
        _render_app_performance_card(app_data)

    # Performance Web
    with col2:
        _render_web_performance_card(web_data)

    # Graphique de comparaison ROAS
    _render_roas_comparison_chart(app_data, web_data)

    # Recommandations basées sur la comparaison
    _render_comparison_recommendations(app_data, web_data)


def _render_app_performance_card(app_data: pd.DataFrame):
    """Carte de performance App"""

    st.markdown("#### 📱 Performance App")

    if app_data.empty:
        st.info("Aucune donnée App disponible")
        return

    app_totals = {
        'cost': app_data['cost'].sum(),
        'installs': app_data['installs'].sum(),
        'revenue': app_data['revenue'].sum(),
        'purchases': app_data['purchases'].sum(),
        'opens': app_data['opens'].sum(),
        'clicks': app_data['clicks'].sum()
    }

    # Métriques principales
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

    # Métriques spécifiques App
    st.markdown("**🎯 Métriques App spécifiques:**")

    app_metrics_col1, app_metrics_col2 = st.columns(2)

    with app_metrics_col1:
        # Taux d'ouverture
        open_rate = (app_totals['opens'] / app_totals['installs'] * 100) if app_totals['installs'] > 0 else 0
        st.write(f"• **Taux d'ouverture**: {open_rate:.1f}%")

        # Taux de conversion install
        conversion_rate = (app_totals['purchases'] / app_totals['installs'] * 100) if app_totals['installs'] > 0 else 0
        st.write(f"• **Taux de conversion**: {conversion_rate:.1f}%")

    with app_metrics_col2:
        # Revenue per install
        rpi = app_totals['revenue'] / app_totals['installs'] if app_totals['installs'] > 0 else 0
        st.write(f"• **Revenue/Install**: {format_currency(rpi)}")

        # CTR (si disponible)
        if app_totals['clicks'] > 0:
            impressions = app_data['impressions'].sum()
            ctr = (app_totals['clicks'] / impressions * 100) if impressions > 0 else 0
            st.write(f"• **CTR**: {ctr:.2f}%")


def _render_web_performance_card(web_data: pd.DataFrame):
    """Carte de performance Web"""

    st.markdown("#### 🌐 Performance Web")

    if web_data.empty:
        st.info("Aucune donnée Web disponible")
        return

    web_totals = {
        'cost': web_data['cost'].sum(),
        'purchases': web_data['purchases'].sum(),
        'revenue': web_data['revenue'].sum(),
        'clicks': web_data['clicks'].sum(),
        'impressions': web_data['impressions'].sum(),
        'add_to_cart': web_data.get('add_to_cart', pd.Series([0])).sum()
    }

    # Métriques principales
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

    # Métriques spécifiques Web
    st.markdown("**🎯 Métriques Web spécifiques:**")

    web_metrics_col1, web_metrics_col2 = st.columns(2)

    with web_metrics_col1:
        # CTR
        ctr = (web_totals['clicks'] / web_totals['impressions'] * 100) if web_totals['impressions'] > 0 else 0
        st.write(f"• **CTR**: {ctr:.2f}%")

        # Taux de conversion
        conversion_rate = (web_totals['purchases'] / web_totals['clicks'] * 100) if web_totals['clicks'] > 0 else 0
        st.write(f"• **Taux de conversion**: {conversion_rate:.1f}%")

    with web_metrics_col2:
        # Taux d'ajout panier
        cart_rate = (web_totals['add_to_cart'] / web_totals['clicks'] * 100) if web_totals['clicks'] > 0 else 0
        st.write(f"• **Taux ajout panier**: {cart_rate:.1f}%")

        # Revenue per click
        rpc = web_totals['revenue'] / web_totals['clicks'] if web_totals['clicks'] > 0 else 0
        st.write(f"• **Revenue/Clic**: {format_currency(rpc)}")


def _render_roas_comparison_chart(app_data: pd.DataFrame, web_data: pd.DataFrame):
    """Graphique de comparaison ROAS et métriques clés"""

    st.markdown("### 📊 Comparaison des Performances")

    # Calcul des métriques pour comparaison
    metrics_comparison = _calculate_comparison_metrics(app_data, web_data)

    if not metrics_comparison:
        st.warning("Données insuffisantes pour la comparaison")
        return

    # Graphique en barres comparatives
    fig = go.Figure()

    metrics_to_plot = ['roas', 'cpa', 'conversion_rate', 'revenue_efficiency']
    metric_labels = ['ROAS', 'CPA (€)', 'Taux Conversion (%)', 'Efficacité Revenus']

    x_labels = ['App', 'Web']

    for i, (metric, label) in enumerate(zip(metrics_to_plot, metric_labels)):
        app_value = metrics_comparison['app'].get(metric, 0)
        web_value = metrics_comparison['web'].get(metric, 0)

        fig.add_trace(go.Bar(
            name=label,
            x=x_labels,
            y=[app_value, web_value],
            text=[f"{app_value:.2f}", f"{web_value:.2f}"],
            textposition='auto',
        ))

    fig.update_layout(
        title="Comparaison App vs Web - Métriques Clés",
        barmode='group',
        height=400,
        yaxis_title="Valeurs",
        xaxis_title="Canal",
        showlegend=True
    )

    st.plotly_chart(fig, use_container_width=True)

    # Tableau de comparaison détaillé
    _render_detailed_comparison_table(metrics_comparison)


def _calculate_comparison_metrics(app_data: pd.DataFrame, web_data: pd.DataFrame) -> dict:
    """Calcule les métriques pour la comparaison"""

    comparison = {'app': {}, 'web': {}}

    # Métriques App
    if not app_data.empty:
        app_cost = app_data['cost'].sum()
        app_installs = app_data['installs'].sum()
        app_revenue = app_data['revenue'].sum()
        app_purchases = app_data['purchases'].sum()

        comparison['app'] = {
            'cost': app_cost,
            'installs': app_installs,
            'revenue': app_revenue,
            'purchases': app_purchases,
            'roas': app_revenue / app_cost if app_cost > 0 else 0,
            'cpa': app_cost / app_installs if app_installs > 0 else 0,
            'conversion_rate': (app_purchases / app_installs * 100) if app_installs > 0 else 0,
            'revenue_efficiency': app_revenue / app_cost if app_cost > 0 else 0
        }

    # Métriques Web
    if not web_data.empty:
        web_cost = web_data['cost'].sum()
        web_clicks = web_data['clicks'].sum()
        web_revenue = web_data['revenue'].sum()
        web_purchases = web_data['purchases'].sum()

        comparison['web'] = {
            'cost': web_cost,
            'clicks': web_clicks,
            'revenue': web_revenue,
            'purchases': web_purchases,
            'roas': web_revenue / web_cost if web_cost > 0 else 0,
            'cpa': web_cost / web_purchases if web_purchases > 0 else 0,
            'conversion_rate': (web_purchases / web_clicks * 100) if web_clicks > 0 else 0,
            'revenue_efficiency': web_revenue / web_cost if web_cost > 0 else 0
        }

    return comparison


def _render_detailed_comparison_table(metrics_comparison: dict):
    """Tableau de comparaison détaillé"""

    st.markdown("### 📋 Tableau Comparatif Détaillé")

    if not metrics_comparison['app'] and not metrics_comparison['web']:
        st.warning("Aucune donnée pour le tableau comparatif")
        return

    # Préparation des données pour le tableau
    comparison_data = []

    metrics_config = [
        ('Coût Total', 'cost', 'currency'),
        ('Revenus', 'revenue', 'currency'),
        ('ROAS', 'roas', 'ratio'),
        ('CPA', 'cpa', 'currency'),
        ('Taux Conversion', 'conversion_rate', 'percentage'),
        ('Installs/Achats', ['installs', 'purchases'], 'number')
    ]

    for label, key, format_type in metrics_config:
        app_value = 0
        web_value = 0

        if isinstance(key, list):
            # Cas spécial pour installs/purchases
            app_value = metrics_comparison['app'].get('installs', 0)
            web_value = metrics_comparison['web'].get('purchases', 0)
        else:
            app_value = metrics_comparison['app'].get(key, 0)
            web_value = metrics_comparison['web'].get(key, 0)

        # Formatage
        if format_type == 'currency':
            app_formatted = format_currency(app_value)
            web_formatted = format_currency(web_value)
        elif format_type == 'percentage':
            app_formatted = f"{app_value:.1f}%"
            web_formatted = f"{web_value:.1f}%"
        elif format_type == 'ratio':
            app_formatted = f"{app_value:.2f}"
            web_formatted = f"{web_value:.2f}"
        else:
            app_formatted = f"{app_value:,.0f}"
            web_formatted = f"{web_value:,.0f}"

        # Déterminer le gagnant
        if app_value > web_value and app_value > 0:
            winner = "📱 App"
            advantage = f"+{((app_value - web_value) / web_value * 100):.1f}%" if web_value > 0 else "Seul canal"
        elif web_value > app_value and web_value > 0:
            winner = "🌐 Web"
            advantage = f"+{((web_value - app_value) / app_value * 100):.1f}%" if app_value > 0 else "Seul canal"
        else:
            winner = "🟰 Égalité"
            advantage = "0%"

        comparison_data.append({
            'Métrique': label,
            'App': app_formatted,
            'Web': web_formatted,
            'Meilleur Canal': winner,
            'Avantage': advantage
        })

    # Affichage du tableau
    comparison_df = pd.DataFrame(comparison_data)
    st.dataframe(comparison_df, use_container_width=True)


def _render_detailed_performance_comparison(app_data: pd.DataFrame, web_data: pd.DataFrame):
    """Comparaison détaillée des performances"""

    st.markdown("### 🔍 Analyse Performance Détaillée")

    tab1, tab2, tab3 = st.tabs(["Efficacité Budget", "Qualité Trafic", "Rentabilité"])

    with tab1:
        _render_budget_efficiency_analysis(app_data, web_data)

    with tab2:
        _render_traffic_quality_analysis(app_data, web_data)

    with tab3:
        _render_profitability_analysis(app_data, web_data)


def _render_budget_efficiency_analysis(app_data: pd.DataFrame, web_data: pd.DataFrame):
    """Analyse de l'efficacité du budget"""

    st.markdown("#### 💰 Efficacité du Budget")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**📱 App - Efficacité par Euro**")
        if not app_data.empty:
            app_cost = app_data['cost'].sum()
            app_installs = app_data['installs'].sum()
            app_revenue = app_data['revenue'].sum()

            if app_cost > 0:
                st.metric("Installs par €", f"{app_installs / app_cost:.2f}")
                st.metric("Revenus par €", f"{app_revenue / app_cost:.2f}")
                st.metric("ROI", f"{(app_revenue - app_cost) / app_cost * 100:+.1f}%")

    with col2:
        st.markdown("**🌐 Web - Efficacité par Euro**")
        if not web_data.empty:
            web_cost = web_data['cost'].sum()
            web_purchases = web_data['purchases'].sum()
            web_revenue = web_data['revenue'].sum()

            if web_cost > 0:
                st.metric("Achats par €", f"{web_purchases / web_cost:.2f}")
                st.metric("Revenus par €", f"{web_revenue / web_cost:.2f}")
                st.metric("ROI", f"{(web_revenue - web_cost) / web_cost * 100:+.1f}%")

    # Recommandation d'allocation budget
    _render_budget_allocation_recommendation(app_data, web_data)


def _render_traffic_quality_analysis(app_data: pd.DataFrame, web_data: pd.DataFrame):
    """Analyse de la qualité du trafic"""

    st.markdown("#### 👥 Qualité du Trafic")

    # Métriques de qualité
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**📱 App - Qualité Utilisateurs**")
        if not app_data.empty:
            app_installs = app_data['installs'].sum()
            app_opens = app_data['opens'].sum()
            app_purchases = app_data['purchases'].sum()

            open_rate = (app_opens / app_installs * 100) if app_installs > 0 else 0
            purchase_rate = (app_purchases / app_installs * 100) if app_installs > 0 else 0

            st.metric("Taux ouverture D1", f"{open_rate:.1f}%")
            st.metric("Taux achat", f"{purchase_rate:.1f}%")

            # Score de qualité
            quality_score = (open_rate * 0.6 + purchase_rate * 4) / 5  # Pondération
            st.metric("Score Qualité", f"{quality_score:.0f}/100")

    with col2:
        st.markdown("**🌐 Web - Qualité Visiteurs**")
        if not web_data.empty:
            web_clicks = web_data['clicks'].sum()
            web_purchases = web_data['purchases'].sum()
            web_add_to_cart = web_data.get('add_to_cart', pd.Series([0])).sum()

            purchase_rate = (web_purchases / web_clicks * 100) if web_clicks > 0 else 0
            cart_rate = (web_add_to_cart / web_clicks * 100) if web_clicks > 0 else 0

            st.metric("Taux ajout panier", f"{cart_rate:.1f}%")
            st.metric("Taux achat", f"{purchase_rate:.1f}%")

            # Score de qualité
            quality_score = (cart_rate * 0.3 + purchase_rate * 7) / 10  # Pondération
            st.metric("Score Qualité", f"{quality_score:.0f}/100")


def _render_profitability_analysis(app_data: pd.DataFrame, web_data: pd.DataFrame):
    """Analyse de rentabilité"""

    st.markdown("#### 📈 Analyse de Rentabilité")

    # Calcul des marges et profits
    profitability_data = []

    if not app_data.empty:
        app_cost = app_data['cost'].sum()
        app_revenue = app_data['revenue'].sum()
        app_profit = app_revenue - app_cost
        app_margin = (app_profit / app_revenue * 100) if app_revenue > 0 else 0

        profitability_data.append({
            'Canal': 'App',
            'Revenus': app_revenue,
            'Coûts': app_cost,
            'Profit': app_profit,
            'Marge (%)': app_margin,
            'ROAS': app_revenue / app_cost if app_cost > 0 else 0
        })

    if not web_data.empty:
        web_cost = web_data['cost'].sum()
        web_revenue = web_data['revenue'].sum()
        web_profit = web_revenue - web_cost
        web_margin = (web_profit / web_revenue * 100) if web_revenue > 0 else 0

        profitability_data.append({
            'Canal': 'Web',
            'Revenus': web_revenue,
            'Coûts': web_cost,
            'Profit': web_profit,
            'Marge (%)': web_margin,
            'ROAS': web_revenue / web_cost if web_cost > 0 else 0
        })

    if profitability_data:
        profitability_df = pd.DataFrame(profitability_data)

        # Format du tableau
        st.dataframe(
            profitability_df,
            column_config={
                "Revenus": st.column_config.NumberColumn("Revenus", format="%.2f €"),
                "Coûts": st.column_config.NumberColumn("Coûts", format="%.2f €"),
                "Profit": st.column_config.NumberColumn("Profit", format="%.2f €"),
                "Marge (%)": st.column_config.NumberColumn("Marge (%)", format="%.1f%%"),
                "ROAS": st.column_config.NumberColumn("ROAS", format="%.2f")
            },
            use_container_width=True
        )


def _render_roi_analysis(app_data: pd.DataFrame, web_data: pd.DataFrame):
    """Analyse ROI avancée"""

    st.markdown("### 💹 Analyse ROI Avancée")

    # Graphique en waterfall du ROI
    _render_roi_waterfall_chart(app_data, web_data)

    # Projections ROI
    _render_roi_projections(app_data, web_data)


def _render_roi_waterfall_chart(app_data: pd.DataFrame, web_data: pd.DataFrame):
    """Graphique en waterfall du ROI"""

    st.markdown("#### 🌊 Décomposition ROI par Canal")

    # Calcul des composants ROI
    app_cost = app_data['cost'].sum() if not app_data.empty else 0
    app_revenue = app_data['revenue'].sum() if not app_data.empty else 0
    web_cost = web_data['cost'].sum() if not web_data.empty else 0
    web_revenue = web_data['revenue'].sum() if not web_data.empty else 0

    total_cost = app_cost + web_cost
    total_revenue = app_revenue + web_revenue
    total_profit = total_revenue - total_cost

    # Données pour le waterfall
    categories = ['Revenus App', 'Revenus Web', 'Coûts App', 'Coûts Web', 'Profit Total']
    values = [app_revenue, web_revenue, -app_cost, -web_cost, total_profit]

    fig = go.Figure(go.Waterfall(
        name="ROI Analysis",
        orientation="v",
        measure=["relative", "relative", "relative", "relative", "total"],
        x=categories,
        text=[f"{v:,.0f}€" for v in values],
        y=values,
        connector={"line": {"color": "rgb(63, 63, 63)"}},
    ))

    fig.update_layout(
        title="Décomposition du ROI par Canal",
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)


def _render_roi_projections(app_data: pd.DataFrame, web_data: pd.DataFrame):
    """Projections ROI basées sur les tendances actuelles"""

    st.markdown("#### 🔮 Projections ROI")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Scénario d'optimisation App**")
        if not app_data.empty:
            current_app_roas = app_data['revenue'].sum() / app_data['cost'].sum() if app_data['cost'].sum() > 0 else 0
            optimized_roas = current_app_roas * 1.2  # Amélioration 20%

            st.write(f"• ROAS actuel: {current_app_roas:.2f}")
            st.write(f"• ROAS optimisé: {optimized_roas:.2f}")
            st.write(f"• Gain potentiel: +{((optimized_roas - current_app_roas) / current_app_roas * 100):.0f}%")

    with col2:
        st.markdown("**Scénario d'optimisation Web**")
        if not web_data.empty:
            current_web_roas = web_data['revenue'].sum() / web_data['cost'].sum() if web_data['cost'].sum() > 0 else 0
            optimized_roas = current_web_roas * 1.15  # Amélioration 15%

            st.write(f"• ROAS actuel: {current_web_roas:.2f}")
            st.write(f"• ROAS optimisé: {optimized_roas:.2f}")
            st.write(f"• Gain potentiel: +{((optimized_roas - current_web_roas) / current_web_roas * 100):.0f}%")


def _render_temporal_evolution_comparison(app_data: pd.DataFrame, web_data: pd.DataFrame):
    """Comparaison de l'évolution temporelle"""

    st.markdown("### ⏱️ Évolution Temporelle Comparative")

    if len(app_data) < 2 and len(web_data) < 2:
        st.info("Données temporelles insuffisantes pour l'analyse")
        return

    # Graphique d'évolution comparative
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('ROAS par jour', 'Coût par jour', 'Conversions par jour', 'Revenus par jour'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )

    # ROAS évolution
    if not app_data.empty and len(app_data) > 1:
        app_daily_roas = app_data['revenue'] / app_data['cost']
        fig.add_trace(
            go.Scatter(x=app_data['date'], y=app_daily_roas, name='ROAS App', line=dict(color='#3498db')),
            row=1, col=1
        )

    if not web_data.empty and len(web_data) > 1:
        web_daily_roas = web_data['revenue'] / web_data['cost']
        fig.add_trace(
            go.Scatter(x=web_data['date'], y=web_daily_roas, name='ROAS Web', line=dict(color='#9b59b6')),
            row=1, col=1
        )

    # Autres métriques...
    fig.update_layout(height=600, showlegend=True)
    st.plotly_chart(fig, use_container_width=True)


def _render_budget_allocation_recommendation(app_data: pd.DataFrame, web_data: pd.DataFrame):
    """Recommandation d'allocation de budget"""

    st.markdown("#### 🎯 Recommandation d'Allocation Budget")

    if app_data.empty or web_data.empty:
        st.info("Données insuffisantes pour les recommandations d'allocation")
        return

    # Calcul des performances relatives
    app_roas = app_data['revenue'].sum() / app_data['cost'].sum() if app_data['cost'].sum() > 0 else 0
    web_roas = web_data['revenue'].sum() / web_data['cost'].sum() if web_data['cost'].sum() > 0 else 0

    total_budget = app_data['cost'].sum() + web_data['cost'].sum()
    current_app_share = (app_data['cost'].sum() / total_budget * 100) if total_budget > 0 else 0

    # Recommandation basée sur ROAS
    if app_roas > web_roas * 1.2:
        recommended_app_share = min(current_app_share + 15, 80)
        recommendation = f"📱 **Augmenter budget App** de {current_app_share:.0f}% à {recommended_app_share:.0f}%"
        reason = f"ROAS App ({app_roas:.2f}) supérieur à Web ({web_roas:.2f})"
    elif web_roas > app_roas * 1.2:
        recommended_app_share = max(current_app_share - 15, 20)
        recommendation = f"🌐 **Augmenter budget Web** - Réduire App de {current_app_share:.0f}% à {recommended_app_share:.0f}%"
        reason = f"ROAS Web ({web_roas:.2f}) supérieur à App ({app_roas:.2f})"
    else:
        recommendation = f"⚖️ **Maintenir équilibre actuel** ({current_app_share:.0f}% App / {100 - current_app_share:.0f}% Web)"
        reason = "Performances similaires entre les canaux"

    st.success(recommendation)
    st.caption(f"Justification: {reason}")


def _render_comparison_recommendations(app_data: pd.DataFrame, web_data: pd.DataFrame):
    """Recommandations basées sur la comparaison"""

    st.markdown("### 💡 Recommandations Stratégiques")

    recommendations = []

    if not app_data.empty and not web_data.empty:
        # Comparaison ROAS
        app_roas = app_data['revenue'].sum() / app_data['cost'].sum() if app_data['cost'].sum() > 0 else 0
        web_roas = web_data['revenue'].sum() / web_data['cost'].sum() if web_data['cost'].sum() > 0 else 0

        if app_roas > web_roas * 1.3:
            recommendations.append({
                'priority': '🔴 Haute',
                'title': 'Réallouer budget vers App',
                'description': f'L\'App génère un ROAS de {app_roas:.2f} vs {web_roas:.2f} pour le Web.',
                'action': 'Augmenter le budget App de 20-30% et optimiser les campagnes Web'
            })
        elif web_roas > app_roas * 1.3:
            recommendations.append({
                'priority': '🔴 Haute',
                'title': 'Réalloquer budget vers Web',
                'description': f'Le Web génère un ROAS de {web_roas:.2f} vs {app_roas:.2f} pour l\'App.',
                'action': 'Augmenter le budget Web de 20-30% et optimiser les campagnes App'
            })

        # Autres recommandations basées sur les métriques spécifiques
        app_conversion = (app_data['purchases'].sum() / app_data['installs'].sum() * 100) if app_data[
                                                                                                 'installs'].sum() > 0 else 0
        if app_conversion < 5:
            recommendations.append({
                'priority': '🟡 Moyenne',
                'title': 'Améliorer conversion App',
                'description': f'Taux de conversion App de {app_conversion:.1f}% en dessous des standards.',
                'action': 'Optimiser l\'onboarding et les notifications push'
            })

    # Affichage des recommandations
    if recommendations:
        for rec in recommendations:
            with st.expander(f"{rec['priority']} - {rec['title']}"):
                st.write(rec['description'])
                st.markdown(f"**Action recommandée:** {rec['action']}")
    else:
        st.info("🎉 Vos canaux sont bien équilibrés ! Continuez l'optimisation continue.")