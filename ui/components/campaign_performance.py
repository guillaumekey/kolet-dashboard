import streamlit as st
import pandas as pd
from typing import Dict


def render_campaign_performance(raw_data: Dict[str, pd.DataFrame]):
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