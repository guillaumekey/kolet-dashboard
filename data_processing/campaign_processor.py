import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from .base_processor import BaseProcessor


class CampaignProcessor(BaseProcessor):
    """Processeur spécialisé pour l'analyse des campagnes par type"""

    def __init__(self):
        super().__init__()

    def create_campaign_type_analysis(self, df: pd.DataFrame, exclude_unpopulated: bool = True) -> pd.DataFrame:
        """
        Crée l'analyse par type de campagne avec évitement du double comptage

        Args:
            df: DataFrame avec les données consolidées
            exclude_unpopulated: Exclure les données 'Unpopulated' de Branch.io

        Returns:
            DataFrame avec les performances par type de campagne
        """
        print(f"🔍 Analyse par type de campagne:")
        print(f"  • Données totales: {len(df)} lignes")
        print(f"  • Exclude unpopulated: {exclude_unpopulated}")

        if df.empty or 'campaign_type' not in df.columns:
            print("  ⚠️ Aucune classification de campagne trouvée")
            return pd.DataFrame()

        # NOUVEAU : Appliquer le filtre Unpopulated AVANT l'analyse
        data_to_analyze = df.copy()

        if exclude_unpopulated:
            before_filter = len(data_to_analyze)
            data_to_analyze = data_to_analyze[
                ~((data_to_analyze['source'] == 'Branch.io') &
                  (data_to_analyze['campaign_name'] == 'Unpopulated'))
            ]
            after_filter = len(data_to_analyze)
            print(f"  • Filtrage Unpopulated: {before_filter} → {after_filter} lignes")

        # Filtrer les campagnes classifiées
        classified_data = data_to_analyze[data_to_analyze['campaign_type'].notna()].copy()

        if classified_data.empty:
            print("  ⚠️ Aucune campagne classifiée après filtrage")
            return pd.DataFrame()

        print(f"  • Campagnes classifiées: {len(classified_data)} lignes")

        # Séparer les données pour éviter le double comptage
        advertising_data, conversion_data = self._separate_data_sources(classified_data)

        # Agréger séparément
        advertising_agg = self._aggregate_advertising_data(advertising_data)
        conversion_agg = self._aggregate_conversion_data(conversion_data)

        # Combiner les agrégations
        campaign_analysis = self._merge_campaign_data(advertising_agg, conversion_agg)

        # Calculer les métriques
        campaign_analysis = self._calculate_campaign_metrics(campaign_analysis)

        return campaign_analysis

    def _separate_data_sources(self, classified_data: pd.DataFrame) -> tuple:
        """
        CORRIGÉ : Sépare correctement les sources en évitant le double comptage
        """
        advertising_sources = ['Google Ads', 'Google AdWords', 'Apple Search Ads']

        advertising_data = classified_data[classified_data['source'].isin(advertising_sources)].copy()

        # IMPORTANT : Pour les données de conversion, on garde TOUT mais on ne prendra que Branch.io
        # dans _aggregate_conversion_data()
        conversion_data = classified_data.copy()

        print(f"  📊 SÉPARATION DES SOURCES:")
        print(f"    • Données publicitaires: {len(advertising_data)} lignes")
        print(f"    • Sources pub: {advertising_data['source'].unique()}")
        print(f"    • Données pour conversion: {len(conversion_data)} lignes")

        # Debug par source
        for source in conversion_data['source'].unique():
            source_count = len(conversion_data[conversion_data['source'] == source])
            source_installs = conversion_data[conversion_data['source'] == source]['installs'].sum()
            print(f"      - {source}: {source_count} lignes, {source_installs:,} installs")

        return advertising_data, conversion_data

    def _aggregate_advertising_data(self, advertising_data: pd.DataFrame) -> pd.DataFrame:
        """Agrège les données publicitaires par type et canal de campagne"""
        if advertising_data.empty:
            print("    📊 PAS DE DONNÉES PUBLICITAIRES")
            return pd.DataFrame()

        result = advertising_data.groupby(['campaign_type', 'channel_type']).agg({
            'cost': 'sum',
            'impressions': 'sum',
            'clicks': 'sum',
            'purchases': 'sum',  # ← AJOUTÉ pour les campagnes Web
            'revenue': 'sum',  # ← AJOUTÉ pour les campagnes Web
            'campaign_name': 'nunique'
        }).reset_index()

        print(f"    📊 AGRÉGATION PUB: {len(result)} lignes, coût total: {result['cost'].sum():.2f}€")
        return result

    def _aggregate_conversion_data(self, conversion_data: pd.DataFrame) -> pd.DataFrame:
        """
        CORRIGÉ : Agrège SEULEMENT les données de conversion (Branch.io)
        """
        if conversion_data.empty:
            print("    🌿 PAS DE DONNÉES DE CONVERSION")
            return pd.DataFrame()

        # Filtrer pour garder SEULEMENT Branch.io
        branch_only = conversion_data[conversion_data['source'] == 'Branch.io'].copy()

        if branch_only.empty:
            print(f"  ⚠️ Aucune donnée Branch.io trouvée dans les données de conversion")
            return pd.DataFrame()

        print(f"  🌿 DONNÉES CONVERSION (Branch.io seulement):")
        print(f"    • Lignes Branch.io: {len(branch_only)}")
        print(f"    • Installs Branch.io: {branch_only['installs'].sum():,}")

        agg_dict = {
            'installs': 'sum',
            'purchases': 'sum',
            'revenue': 'sum',
            'opens': 'sum',
            'login': 'sum'
        }

        conversion_agg = branch_only.groupby(['campaign_type', 'channel_type']).agg(agg_dict).reset_index()

        # Ajouter add_to_cart pour les campagnes web (estimation)
        conversion_agg = self._add_web_cart_data(conversion_agg, branch_only)

        print(
            f"    🌿 AGRÉGATION CONV: {len(conversion_agg)} lignes, installs total: {conversion_agg['installs'].sum():,}")

        return conversion_agg

    def _add_web_cart_data(self, conversion_agg: pd.DataFrame, conversion_data: pd.DataFrame) -> pd.DataFrame:
        """Ajoute les données add_to_cart pour les campagnes web"""
        if 'add_to_cart' in conversion_data.columns:
            web_conversion_agg = conversion_data[
                conversion_data['channel_type'] == 'web'
                ].groupby(['campaign_type', 'channel_type']).agg({'add_to_cart': 'sum'}).reset_index()

            conversion_agg = conversion_agg.merge(
                web_conversion_agg, on=['campaign_type', 'channel_type'], how='left'
            )
        else:
            # Estimer add_to_cart pour le web (3x les purchases)
            conversion_agg['add_to_cart'] = 0
            web_mask = conversion_agg['channel_type'] == 'web'
            conversion_agg.loc[web_mask, 'add_to_cart'] = conversion_agg.loc[web_mask, 'purchases'] * 3

        return conversion_agg.fillna(0)

    def _merge_campaign_data(self, advertising_agg: pd.DataFrame, conversion_agg: pd.DataFrame) -> pd.DataFrame:
        """
        FIX URGENT : Restaurer les données avec debug complet
        """

        print(f"🔧 FUSION DONNÉES CAMPAGNE (FIX URGENT):")
        print(f"  • Données pub: {len(advertising_agg)} lignes")
        print(f"  • Données conv: {len(conversion_agg)} lignes")

        # DEBUG COMPLET
        if not advertising_agg.empty:
            print(f"  📊 COLONNES PUB: {list(advertising_agg.columns)}")
            print(
                f"  📊 TYPES PUB: {advertising_agg[['campaign_type', 'channel_type']].drop_duplicates().values.tolist()}")
            print(f"  📊 COÛT PUB TOTAL: {advertising_agg['cost'].sum():.2f}€")

        if not conversion_agg.empty:
            print(f"  🌿 COLONNES CONV: {list(conversion_agg.columns)}")
            print(
                f"  🌿 TYPES CONV: {conversion_agg[['campaign_type', 'channel_type']].drop_duplicates().values.tolist()}")
            print(f"  🌿 INSTALLS CONV TOTAL: {conversion_agg['installs'].sum():,}")

        if advertising_agg.empty and conversion_agg.empty:
            print("  ❌ AUCUNE DONNÉE DISPONIBLE")
            return pd.DataFrame()

        # STRATÉGIE : Créer un DataFrame avec TOUTES les combinaisons type/canal
        all_combinations = set()

        if not advertising_agg.empty:
            for _, row in advertising_agg.iterrows():
                all_combinations.add((row['campaign_type'], row['channel_type']))

        if not conversion_agg.empty:
            for _, row in conversion_agg.iterrows():
                all_combinations.add((row['campaign_type'], row['channel_type']))

        print(f"  🔗 COMBINAISONS TROUVÉES: {all_combinations}")

        # Créer le DataFrame final
        campaign_analysis = []

        # FONCTION: _merge_campaign_data()

        for campaign_type, channel_type in all_combinations:
            # Données pub pour cette combinaison
            pub_row = advertising_agg[
                (advertising_agg['campaign_type'] == campaign_type) &
                (advertising_agg['channel_type'] == channel_type)
                ]

            # Données conv pour cette combinaison
            conv_row = conversion_agg[
                (conversion_agg['campaign_type'] == campaign_type) &
                (conversion_agg['channel_type'] == channel_type)
                ]

            # Créer la ligne finale
            final_row = {
                'campaign_type': campaign_type,
                'channel_type': channel_type,
                'cost': pub_row['cost'].sum() if not pub_row.empty else 0,
                'impressions': pub_row['impressions'].sum() if not pub_row.empty else 0,
                'clicks': pub_row['clicks'].sum() if not pub_row.empty else 0,
                'nb_campaigns': pub_row['campaign_name'].sum() if not pub_row.empty else 0,
                'installs': conv_row['installs'].sum() if not conv_row.empty else 0,
                'opens': conv_row['opens'].sum() if not conv_row.empty else 0,
                'login': conv_row['login'].sum() if not conv_row.empty else 0,
            }

            # CORRECTION WEB : Pour les campagnes Web, purchases et revenue viennent de Google Ads !
            if channel_type == 'web':
                # Pour Web : purchases et revenue viennent des données publicitaires (Google Ads)
                final_row['purchases'] = pub_row[
                    'purchases'].sum() if not pub_row.empty and 'purchases' in pub_row.columns else 0
                final_row['revenue'] = pub_row[
                    'revenue'].sum() if not pub_row.empty and 'revenue' in pub_row.columns else 0
                final_row['add_to_cart'] = final_row['purchases'] * 3  # Estimation basée sur purchases
            else:
                # Pour App : purchases et revenue viennent de Branch.io
                final_row['purchases'] = conv_row['purchases'].sum() if not conv_row.empty else 0
                final_row['revenue'] = conv_row['revenue'].sum() if not conv_row.empty else 0
                final_row['add_to_cart'] = 0

            campaign_analysis.append(final_row)

            print(f"    ✅ {campaign_type}/{channel_type}: {final_row['cost']:.2f}€, {final_row['installs']} installs")

        # Convertir en DataFrame
        campaign_analysis = pd.DataFrame(campaign_analysis)

        # DEBUG FINAL
        if not campaign_analysis.empty:
            print(f"  ✅ FUSION TERMINÉE:")
            print(f"    • Lignes créées: {len(campaign_analysis)}")
            print(f"    • Coût total: {campaign_analysis['cost'].sum():.2f}€")
            print(f"    • Installs total: {campaign_analysis['installs'].sum():,}")
            print(f"    • Purchases total: {campaign_analysis['purchases'].sum():,}")
        else:
            print(f"  ❌ DATAFRAME FINAL VIDE!")

        return campaign_analysis

    def _calculate_campaign_metrics(self, campaign_analysis: pd.DataFrame) -> pd.DataFrame:
        """Calcule toutes les métriques pour l'analyse des campagnes"""
        if campaign_analysis.empty:
            print("  ⚠️ Pas de données pour calculer les métriques")
            return campaign_analysis

        # Métriques de base
        campaign_analysis['ctr'] = self._safe_divide(
            campaign_analysis['clicks'], campaign_analysis['impressions']
        ) * 100

        # Taux de conversion selon le canal
        campaign_analysis = self._calculate_conversion_rates(campaign_analysis)

        # Métriques spécifiques par canal
        campaign_analysis = self._calculate_channel_specific_metrics(campaign_analysis)

        # Métriques économiques
        campaign_analysis = self._calculate_economic_metrics(campaign_analysis)

        return campaign_analysis

    def _calculate_conversion_rates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule les taux de conversion selon le canal"""
        df['conversion_rate'] = 0.0

        # Pour les campagnes app : conversion_rate = installs / clicks
        app_mask = df['channel_type'] == 'app'
        df.loc[app_mask, 'conversion_rate'] = self._safe_divide(
            df.loc[app_mask, 'installs'], df.loc[app_mask, 'clicks']
        ) * 100

        # Pour les campagnes web : conversion_rate = purchases / clicks
        web_mask = df['channel_type'] == 'web'
        df.loc[web_mask, 'conversion_rate'] = self._safe_divide(
            df.loc[web_mask, 'purchases'], df.loc[web_mask, 'clicks']
        ) * 100

        return df

    def _calculate_channel_specific_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule les métriques spécifiques à chaque canal"""
        app_mask = df['channel_type'] == 'app'
        web_mask = df['channel_type'] == 'web'

        # Métriques App
        df['purchase_rate_dl'] = 0.0  # Purchases / Installs pour app
        df['open_rate'] = 0.0  # Opens / Installs pour app
        df['login_rate'] = 0.0  # Logins / Installs pour app

        df.loc[app_mask, 'purchase_rate_dl'] = self._safe_divide(
            df.loc[app_mask, 'purchases'], df.loc[app_mask, 'installs']
        ) * 100

        df.loc[app_mask, 'open_rate'] = self._safe_divide(
            df.loc[app_mask, 'opens'], df.loc[app_mask, 'installs']
        ) * 100

        df.loc[app_mask, 'login_rate'] = self._safe_divide(
            df.loc[app_mask, 'login'], df.loc[app_mask, 'installs']
        ) * 100

        # Métriques Web
        df['cart_rate'] = 0.0  # Add_to_cart / Clicks pour web
        df['cart_to_purchase_rate'] = 0.0  # Purchases / Add_to_cart pour web
        df['purchase_rate'] = 0.0  # Purchases / Clicks pour web

        df.loc[web_mask, 'cart_rate'] = self._safe_divide(
            df.loc[web_mask, 'add_to_cart'], df.loc[web_mask, 'clicks']
        ) * 100

        df.loc[web_mask, 'cart_to_purchase_rate'] = self._safe_divide(
            df.loc[web_mask, 'purchases'], df.loc[web_mask, 'add_to_cart']
        ) * 100

        df.loc[web_mask, 'purchase_rate'] = self._safe_divide(
            df.loc[web_mask, 'purchases'], df.loc[web_mask, 'clicks']
        ) * 100

        # Purchase rate pour app = purchases / installs
        df.loc[app_mask, 'purchase_rate'] = df.loc[app_mask, 'purchase_rate_dl']

        return df

    def _calculate_economic_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule les métriques économiques"""
        app_mask = df['channel_type'] == 'app'
        web_mask = df['channel_type'] == 'web'

        # CPC
        df['cpc'] = self._safe_divide(df['cost'], df['clicks'])

        # CPA différent selon le canal
        df['cpa'] = 0.0
        df.loc[app_mask, 'cpa'] = self._safe_divide(
            df.loc[app_mask, 'cost'], df.loc[app_mask, 'installs']
        )
        df.loc[web_mask, 'cpa'] = self._safe_divide(
            df.loc[web_mask, 'cost'], df.loc[web_mask, 'purchases']
        )

        # ROAS et Revenue per Install
        df['roas'] = self._safe_divide(df['revenue'], df['cost'])
        df['revenue_per_install'] = self._safe_divide(df['revenue'], df['installs'])

        return df

    def get_campaign_type_summary(self, campaign_analysis: pd.DataFrame) -> Dict[str, Any]:
        """Génère un résumé des performances par type de campagne"""
        if campaign_analysis.empty:
            return {}

        summary = {}

        for campaign_type in campaign_analysis['campaign_type'].unique():
            type_data = campaign_analysis[campaign_analysis['campaign_type'] == campaign_type]

            # Agrégation totale pour ce type
            total_data = type_data.agg({
                'cost': 'sum',
                'impressions': 'sum',
                'clicks': 'sum',
                'installs': 'sum',
                'purchases': 'sum',
                'revenue': 'sum',
                'nb_campaigns': 'sum'
            })

            # Métriques calculées
            summary[campaign_type] = {
                'total_cost': total_data['cost'],
                'total_impressions': total_data['impressions'],
                'total_clicks': total_data['clicks'],
                'total_installs': total_data['installs'],
                'total_purchases': total_data['purchases'],
                'total_revenue': total_data['revenue'],
                'nb_campaigns': total_data['nb_campaigns'],
                'ctr': self._safe_divide(total_data['clicks'], total_data['impressions']) * 100,
                'conversion_rate': self._safe_divide(total_data['installs'], total_data['clicks']) * 100,
                'purchase_rate': self._safe_divide(total_data['purchases'], total_data['installs']) * 100,
                'cpa': self._safe_divide(total_data['cost'], total_data['installs']),
                'roas': self._safe_divide(total_data['revenue'], total_data['cost']),
                'cost_share': 0  # Sera calculé plus tard
            }

        # Calculer les parts de budget
        total_cost = sum(data['total_cost'] for data in summary.values())
        for campaign_type in summary:
            if total_cost > 0:
                summary[campaign_type]['cost_share'] = (
                                                               summary[campaign_type]['total_cost'] / total_cost
                                                       ) * 100

        return summary

    def get_campaign_type_insights(self, summary: Dict[str, Any]) -> List[Dict[str, str]]:
        """Génère des insights sur les performances par type de campagne"""
        insights = []

        if not summary:
            return insights

        # Trouver le meilleur et le pire en ROAS
        roas_ranking = sorted(summary.items(), key=lambda x: x[1]['roas'], reverse=True)

        if len(roas_ranking) >= 2:
            best_roas = roas_ranking[0]
            worst_roas = roas_ranking[-1]

            insights.append({
                'type': 'success',
                'title': f'Meilleur ROAS: {best_roas[0].title()}',
                'message': f'ROAS de {best_roas[1]["roas"]:.2f} avec {best_roas[1]["nb_campaigns"]:.0f} campagnes'
            })

            if best_roas[1]['roas'] > worst_roas[1]['roas'] * 1.5:
                insights.append({
                    'type': 'warning',
                    'title': 'Écart de performance important',
                    'message': f'{best_roas[0].title()} performe {(best_roas[1]["roas"] / worst_roas[1]["roas"]):.1f}x mieux que {worst_roas[0].title()}'
                })

        # Analyse du budget allocation
        budget_ranking = sorted(summary.items(), key=lambda x: x[1]['cost_share'], reverse=True)

        if budget_ranking:
            biggest_spender = budget_ranking[0]
            insights.append({
                'type': 'info',
                'title': 'Répartition budget',
                'message': f'{biggest_spender[0].title()} représente {biggest_spender[1]["cost_share"]:.0f}% du budget total'
            })

        # Recommandations d'optimisation
        for campaign_type, data in summary.items():
            if data['roas'] < 1.5 and data['cost_share'] > 30:
                insights.append({
                    'type': 'warning',
                    'title': f'Optimisation {campaign_type.title()}',
                    'message': f'ROAS faible ({data["roas"]:.2f}) malgré {data["cost_share"]:.0f}% du budget'
                })

            if data['conversion_rate'] < 5 and data['total_clicks'] > 1000:
                insights.append({
                    'type': 'info',
                    'title': f'Conversion {campaign_type.title()}',
                    'message': f'Taux de conversion à améliorer: {data["conversion_rate"]:.1f}%'
                })

        return insights

    def process(self, df: pd.DataFrame, exclude_unpopulated: bool = True) -> pd.DataFrame:
        """
        Traite les données pour créer l'analyse par type de campagne

        Args:
            df: DataFrame avec les données
            exclude_unpopulated: Exclure les données 'Unpopulated' de Branch.io
        """
        return self.create_campaign_type_analysis(df, exclude_unpopulated)