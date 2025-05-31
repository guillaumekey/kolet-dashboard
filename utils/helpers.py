"""
Fonctions utilitaires pour le dashboard Kolet
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
import re
import locale

# Configuration locale pour le formatage
try:
    locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'French_France.1252')
    except:
        pass  # Utiliser les paramètres par défaut


def format_currency(amount: Union[float, int], currency: str = "EUR") -> str:
    """
    Formate un montant en devise

    Args:
        amount: Montant à formater
        currency: Code de la devise

    Returns:
        Montant formaté
    """
    if pd.isna(amount) or amount is None:
        return "0,00 €"

    try:
        if currency == "EUR":
            return f"{amount:,.2f} €".replace(",", " ").replace(".", ",")
        elif currency == "USD":
            return f"${amount:,.2f}"
        else:
            return f"{amount:,.2f} {currency}"
    except:
        return f"{amount} {currency}"


def format_number(number: Union[float, int], decimals: int = 0) -> str:
    """
    Formate un nombre avec séparateurs

    Args:
        number: Nombre à formater
        decimals: Nombre de décimales

    Returns:
        Nombre formaté
    """
    if pd.isna(number) or number is None:
        return "0"

    try:
        if decimals == 0:
            return f"{int(number):,}".replace(",", " ")
        else:
            return f"{number:,.{decimals}f}".replace(",", " ").replace(".", ",")
    except:
        return str(number)


def format_percentage(percentage: Union[float, int], decimals: int = 2) -> str:
    """
    Formate un pourcentage

    Args:
        percentage: Pourcentage à formater
        decimals: Nombre de décimales

    Returns:
        Pourcentage formaté
    """
    if pd.isna(percentage) or percentage is None:
        return "0,00%"

    try:
        formatted = f"{percentage:.{decimals}f}%".replace(".", ",")
        return formatted
    except:
        return f"{percentage}%"


def format_delta(current: float, previous: float, format_type: str = "percentage") -> Dict[str, Any]:
    """
    Calcule et formate la variation entre deux valeurs

    Args:
        current: Valeur actuelle
        previous: Valeur précédente
        format_type: Type de formatage ('percentage', 'absolute', 'currency')

    Returns:
        Dictionnaire avec la variation formatée
    """
    if pd.isna(current) or pd.isna(previous) or previous == 0:
        return {
            'delta': 0,
            'delta_formatted': "0",
            'color': "normal",
            'arrow': ""
        }

    delta = current - previous
    delta_pct = (delta / previous) * 100

    # Déterminer la couleur et la flèche
    if delta > 0:
        color = "normal"  # Streamlit utilise "normal" pour positif
        arrow = "🔺"
    elif delta < 0:
        color = "inverse"  # Streamlit utilise "inverse" pour négatif
        arrow = "🔻"
    else:
        color = "off"
        arrow = "➖"

    # Formater selon le type
    if format_type == "percentage":
        delta_formatted = format_percentage(delta_pct)
    elif format_type == "currency":
        delta_formatted = format_currency(delta)
    else:
        delta_formatted = format_number(delta)

    return {
        'delta': delta,
        'delta_pct': delta_pct,
        'delta_formatted': delta_formatted,
        'color': color,
        'arrow': arrow
    }


def calculate_funnel_metrics(impressions: int, clicks: int, installs: int,
                             purchases: int = 0) -> Dict[str, float]:
    """
    Calcule les métriques du funnel de conversion

    Args:
        impressions: Nombre d'impressions
        clicks: Nombre de clics
        installs: Nombre d'installations
        purchases: Nombre d'achats

    Returns:
        Dictionnaire avec les métriques calculées
    """
    metrics = {
        'impressions': impressions,
        'clicks': clicks,
        'installs': installs,
        'purchases': purchases
    }

    # CTR (Click-Through Rate)
    metrics['ctr'] = (clicks / impressions * 100) if impressions > 0 else 0

    # Taux de conversion Install
    metrics['install_rate'] = (installs / clicks * 100) if clicks > 0 else 0

    # Taux de conversion Purchase
    metrics['purchase_rate'] = (purchases / installs * 100) if installs > 0 else 0

    # Taux de conversion global
    metrics['overall_conversion'] = (installs / impressions * 100) if impressions > 0 else 0

    return metrics


def detect_date_format(date_string: str) -> str:
    """
    Détecte le format d'une date

    Args:
        date_string: Chaîne de date à analyser

    Returns:
        Format de date détecté
    """
    date_formats = [
        '%Y-%m-%d',
        '%d/%m/%Y',
        '%m/%d/%Y',
        '%Y/%m/%d',
        '%d-%m-%Y',
        '%m-%d-%Y',
        '%Y.%m.%d',
        '%d.%m.%Y'
    ]

    for fmt in date_formats:
        try:
            datetime.strptime(date_string, fmt)
            return fmt
        except ValueError:
            continue

    return '%Y-%m-%d'  # Format par défaut


def clean_currency_string(currency_str: Union[str, float, int]) -> float:
    """
    Nettoie une chaîne de devise et la convertit en float

    Args:
        currency_str: Chaîne ou nombre à nettoyer

    Returns:
        Valeur numérique
    """
    if pd.isna(currency_str):
        return 0.0

    if isinstance(currency_str, (int, float)):
        return float(currency_str)

    # Nettoyer la chaîne
    cleaned = re.sub(r'[€$£¥,\s"]', '', str(currency_str))
    cleaned = cleaned.replace(',', '.')

    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def generate_date_range(start_date: str, end_date: str) -> List[str]:
    """
    Génère une liste de dates entre deux dates

    Args:
        start_date: Date de début (YYYY-MM-DD)
        end_date: Date de fin (YYYY-MM-DD)

    Returns:
        Liste des dates
    """
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')

    date_list = []
    current = start

    while current <= end:
        date_list.append(current.strftime('%Y-%m-%d'))
        current += timedelta(days=1)

    return date_list


def get_period_comparison_dates(period: str = "last_30_days") -> Dict[str, str]:
    """
    Génère les dates pour les comparaisons de périodes

    Args:
        period: Période à analyser

    Returns:
        Dictionnaire avec les dates
    """
    today = datetime.now()

    if period == "last_7_days":
        current_end = today
        current_start = today - timedelta(days=6)
        previous_end = current_start - timedelta(days=1)
        previous_start = previous_end - timedelta(days=6)

    elif period == "last_30_days":
        current_end = today
        current_start = today - timedelta(days=29)
        previous_end = current_start - timedelta(days=1)
        previous_start = previous_end - timedelta(days=29)

    elif period == "last_90_days":
        current_end = today
        current_start = today - timedelta(days=89)
        previous_end = current_start - timedelta(days=1)
        previous_start = previous_end - timedelta(days=89)

    else:  # Par défaut last_30_days
        current_end = today
        current_start = today - timedelta(days=29)
        previous_end = current_start - timedelta(days=1)
        previous_start = previous_end - timedelta(days=29)

    return {
        'current_start': current_start.strftime('%Y-%m-%d'),
        'current_end': current_end.strftime('%Y-%m-%d'),
        'previous_start': previous_start.strftime('%Y-%m-%d'),
        'previous_end': previous_end.strftime('%Y-%m-%d')
    }


def calculate_growth_rate(current: float, previous: float) -> float:
    """
    Calcule le taux de croissance

    Args:
        current: Valeur actuelle
        previous: Valeur précédente

    Returns:
        Taux de croissance en pourcentage
    """
    if pd.isna(current) or pd.isna(previous) or previous == 0:
        return 0.0

    return ((current - previous) / previous) * 100


def categorize_performance(value: float, metric: str) -> str:
    """
    Catégorise la performance d'une métrique

    Args:
        value: Valeur de la métrique
        metric: Type de métrique

    Returns:
        Catégorie de performance
    """
    if metric == "cpa":
        if value <= 5:
            return "Excellent"
        elif value <= 15:
            return "Bon"
        elif value <= 30:
            return "Moyen"
        else:
            return "Faible"

    elif metric == "roas":
        if value >= 3:
            return "Excellent"
        elif value >= 2:
            return "Bon"
        elif value >= 1:
            return "Moyen"
        else:
            return "Faible"

    elif metric == "ctr":
        if value >= 3:
            return "Excellent"
        elif value >= 1.5:
            return "Bon"
        elif value >= 0.5:
            return "Moyen"
        else:
            return "Faible"

    elif metric == "conversion_rate":
        if value >= 10:
            return "Excellent"
        elif value >= 5:
            return "Bon"
        elif value >= 2:
            return "Moyen"
        else:
            return "Faible"

    return "Non défini"


def validate_file_upload(file, max_size_mb: int = 50) -> Dict[str, Any]:
    """
    Valide un fichier uploadé

    Args:
        file: Fichier Streamlit uploadé
        max_size_mb: Taille maximale en MB

    Returns:
        Résultat de la validation
    """
    result = {
        'valid': True,
        'errors': [],
        'warnings': []
    }

    if file is None:
        result['valid'] = False
        result['errors'].append("Aucun fichier sélectionné")
        return result

    # Vérifier l'extension
    if not file.name.lower().endswith('.csv'):
        result['valid'] = False
        result['errors'].append("Le fichier doit être au format CSV")

    # Vérifier la taille
    file_size_mb = file.size / (1024 * 1024)
    if file_size_mb > max_size_mb:
        result['valid'] = False
        result['errors'].append(f"Le fichier est trop volumineux ({file_size_mb:.1f}MB > {max_size_mb}MB)")

    return result


def create_summary_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Crée des statistiques résumées pour un DataFrame

    Args:
        df: DataFrame à analyser

    Returns:
        Dictionnaire avec les statistiques
    """
    if df.empty:
        return {}

    numeric_columns = df.select_dtypes(include=[np.number]).columns
    stats = {}

    for col in numeric_columns:
        if col in df.columns:
            stats[col] = {
                'total': df[col].sum(),
                'mean': df[col].mean(),
                'median': df[col].median(),
                'std': df[col].std(),
                'min': df[col].min(),
                'max': df[col].max(),
                'count': df[col].count()
            }

    return stats


def export_to_excel(dataframes: Dict[str, pd.DataFrame], filename: str = None) -> str:
    """
    Exporte plusieurs DataFrames vers un fichier Excel

    Args:
        dataframes: Dictionnaire {nom_onglet: DataFrame}
        filename: Nom du fichier (optionnel)

    Returns:
        Chemin du fichier créé
    """
    if filename is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"kolet_export_{timestamp}.xlsx"

    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        for sheet_name, df in dataframes.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    return filename


def generate_color_palette(n_colors: int, palette_type: str = "default") -> List[str]:
    """
    Génère une palette de couleurs

    Args:
        n_colors: Nombre de couleurs nécessaires
        palette_type: Type de palette

    Returns:
        Liste des couleurs en hex
    """
    palettes = {
        'default': ['#3498db', '#2ecc71', '#f39c12', '#e74c3c', '#9b59b6', '#1abc9c', '#34495e'],
        'blue': ['#3498db', '#5dade2', '#85c1e9', '#aed6f1', '#d6eaf8'],
        'green': ['#2ecc71', '#58d68d', '#82e0aa', '#abebc6', '#d5f4e6'],
        'warm': ['#e74c3c', '#f39c12', '#f7dc6f', '#f8c471', '#f5b7b1']
    }

    base_colors = palettes.get(palette_type, palettes['default'])

    # Répéter les couleurs si nécessaire
    colors = []
    for i in range(n_colors):
        colors.append(base_colors[i % len(base_colors)])

    return colors


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Division sécurisée qui évite la division par zéro

    Args:
        numerator: Numérateur
        denominator: Dénominateur
        default: Valeur par défaut si division par zéro

    Returns:
        Résultat de la division ou valeur par défaut
    """
    try:
        if denominator == 0 or pd.isna(denominator):
            return default
        return numerator / denominator
    except:
        return default


def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Tronque un texte à une longueur maximale

    Args:
        text: Texte à tronquer
        max_length: Longueur maximale
        suffix: Suffixe à ajouter

    Returns:
        Texte tronqué
    """
    if pd.isna(text) or len(str(text)) <= max_length:
        return str(text)

    return str(text)[:max_length - len(suffix)] + suffix