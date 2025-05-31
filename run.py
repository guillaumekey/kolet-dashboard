#!/usr/bin/env python3
"""
Script de lancement pour le dashboard Kolet
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def check_requirements():
    """Vérifie que les dépendances sont installées"""
    try:
        import streamlit
        import pandas
        import plotly
        print("✅ Toutes les dépendances sont installées")
        return True
    except ImportError as e:
        print(f"❌ Dépendance manquante: {e}")
        print("👉 Installez les dépendances avec: pip install -r requirements.txt")
        return False


def setup_directories():
    """Crée les dossiers nécessaires"""
    directories = ['data', 'uploads', 'backups']

    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"📁 Dossier créé/vérifié: {directory}")


def install_requirements():
    """Installe les dépendances"""
    print("📦 Installation des dépendances...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dépendances installées avec succès")
        return True
    except subprocess.CalledProcessError:
        print("❌ Erreur lors de l'installation des dépendances")
        return False


def run_streamlit(port=8501, host="localhost"):
    """Lance l'application Streamlit"""
    print(f"🚀 Lancement du dashboard sur http://{host}:{port}")

    # Configuration Streamlit
    streamlit_config = [
        "--server.port", str(port),
        "--server.address", host,
        "--server.headless", "true",
        "--server.enableCORS", "false",
        "--server.enableXsrfProtection", "false"
    ]

    cmd = [sys.executable, "-m", "streamlit", "run", "app.py"] + streamlit_config

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n👋 Application arrêtée")
    except Exception as e:
        print(f"❌ Erreur lors du lancement: {e}")


def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(description="Dashboard Marketing Kolet")
    parser.add_argument("--port", type=int, default=8501, help="Port du serveur (défaut: 8501)")
    parser.add_argument("--host", default="localhost", help="Adresse du serveur (défaut: localhost)")
    parser.add_argument("--install", action="store_true", help="Installer les dépendances")
    parser.add_argument("--check", action="store_true", help="Vérifier les dépendances")

    args = parser.parse_args()

    print("🎯 Dashboard Marketing Kolet")
    print("=" * 50)

    # Vérification des dépendances
    if args.check:
        check_requirements()
        return

    # Installation des dépendances
    if args.install:
        if not install_requirements():
            return

    # Vérification des prérequis
    if not check_requirements():
        print("💡 Utilisez --install pour installer les dépendances")
        return

    # Création des dossiers
    setup_directories()

    # Lancement de l'application
    run_streamlit(port=args.port, host=args.host)


if __name__ == "__main__":
    main()