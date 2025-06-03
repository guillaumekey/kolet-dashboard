import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from abc import ABC, abstractmethod


class BaseProcessor(ABC):
    """Classe de base abstraite pour tous les processeurs de données"""

    def __init__(self):
        """Initialise le processeur de base"""
        pass

    def _safe_divide(self, numerator, denominator):
        """Division sécurisée qui évite la division par zéro"""
        return np.where(denominator != 0, numerator / denominator, 0)

    def _calculate_percentage(self, part, total, default=0.0):
        """Calcule un pourcentage de manière sécurisée"""
        return self._safe_divide(part, total) * 100 if total != 0 else default

    def _fill_missing_columns(self, df: pd.DataFrame, required_columns: List[str], default_value=0) -> pd.DataFrame:
        """Ajoute les colonnes manquantes avec une valeur par défaut"""
        for col in required_columns:
            if col not in df.columns:
                df[col] = default_value
        return df

    def _group_and_aggregate(self, df: pd.DataFrame, group_by: str, agg_dict: Dict[str, str]) -> pd.DataFrame:
        """Groupe et agrège les données selon le dictionnaire fourni"""
        if df.empty:
            return pd.DataFrame()

        try:
            return df.groupby(group_by).agg(agg_dict).reset_index()
        except Exception as e:
            print(f"Erreur lors de l'agrégation: {e}")
            return pd.DataFrame()

    def _merge_dataframes(self, left: pd.DataFrame, right: pd.DataFrame,
                          on: str, how: str = 'outer', suffixes: Tuple[str, str] = ('', '_right')) -> pd.DataFrame:
        """Merge sécurisé de DataFrames"""
        if left.empty:
            return right
        if right.empty:
            return left

        return left.merge(right, on=on, how=how, suffixes=suffixes)

    def _validate_data(self, df: pd.DataFrame, required_columns: List[str]) -> bool:
        """Valide que le DataFrame contient les colonnes requises"""
        if df.empty:
            return False

        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"Colonnes manquantes: {missing_columns}")
            return False

        return True

    def _clean_numeric_columns(self, df: pd.DataFrame, numeric_columns: List[str]) -> pd.DataFrame:
        """Nettoie et convertit les colonnes numériques"""
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df

    def _convert_dates(self, df: pd.DataFrame, date_columns: List[str] = ['date']) -> pd.DataFrame:
        """Convertit les colonnes de date"""
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        return df

    @abstractmethod
    def process(self, *args, **kwargs):
        """Méthode abstraite pour le traitement principal"""
        pass