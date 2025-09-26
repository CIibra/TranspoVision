import pandas as pd
import os

# 📁 Chemins vers les fichiers
FICHIER_BRUT = "data/regularite-mensuelle-tgv-aqst.csv"
FICHIER_CLEAN = "data/sncf_clean.csv"

# 📂 Création du dossier 'data' s'il n'existe pas
os.makedirs("data", exist_ok=True)

# 📥 Chargement du fichier brut
df = pd.read_csv(FICHIER_BRUT, sep=";", encoding="utf-8", on_bad_lines="skip")

# 🧼 Sélection des colonnes utiles
colonnes_utiles = [
    "Date",
    "Gare de départ",
    "Gare d'arrivée",
    "Durée moyenne du trajet",
    "Nombre de circulations prévues",
    "Nombre de trains annulés",
    "Nombre de trains en retard à l'arrivée",
    "Retard moyen des trains en retard à l'arrivée",
    "Retard moyen de tous les trains à l'arrivée"
]
df_clean = df[colonnes_utiles].copy()

def simplifier_nom(gare):
    if "Paris" in gare: return "Paris"
    if "Lille" in gare: return "Lille"
    if "Lyon" in gare: return "Lyon"
    if "Marseille" in gare: return "Marseille"
    if "Bordeaux" in gare: return "Bordeaux"
    if "Strasbourg" in gare: return "Strasbourg"
    if "Nantes" in gare: return "Nantes"
    if "Toulouse" in gare: return "Toulouse"
    return gare

df_clean["Gare de départ"] = df_clean["Gare de départ"].apply(simplifier_nom)
df_clean["Gare d'arrivée"] = df_clean["Gare d'arrivée"].apply(simplifier_nom)


# 🔧 Conversion des types
df_clean["Date"] = pd.to_datetime(df_clean["Date"], errors="coerce")
df_clean["Durée moyenne du trajet"] = pd.to_numeric(df_clean["Durée moyenne du trajet"], errors="coerce")
df_clean["Nombre de circulations prévues"] = pd.to_numeric(df_clean["Nombre de circulations prévues"], errors="coerce")
df_clean["Nombre de trains annulés"] = pd.to_numeric(df_clean["Nombre de trains annulés"], errors="coerce")
df_clean["Nombre de trains en retard à l'arrivée"] = pd.to_numeric(df_clean["Nombre de trains en retard à l'arrivée"], errors="coerce")
df_clean["Retard moyen des trains en retard à l'arrivée"] = pd.to_numeric(df_clean["Retard moyen des trains en retard à l'arrivée"], errors="coerce")
df_clean["Retard moyen de tous les trains à l'arrivée"] = pd.to_numeric(df_clean["Retard moyen de tous les trains à l'arrivée"], errors="coerce")

# 🧹 Nettoyage
df_clean.dropna(subset=[
    "Date",
    "Gare de départ",
    "Gare d'arrivée",
    "Nombre de circulations prévues",
    "Retard moyen de tous les trains à l'arrivée"
], inplace=True)

df_clean["Gare de départ"] = df_clean["Gare de départ"].str.strip().str.title()
df_clean["Gare d'arrivée"] = df_clean["Gare d'arrivée"].str.strip().str.title()
df_clean.drop_duplicates(inplace=True)
df_clean.reset_index(drop=True, inplace=True)

# 💾 Enregistrement du fichier nettoyé
df_clean.to_csv(FICHIER_CLEAN, index=False)

print("✅ Fichier nettoyé enregistré dans :", FICHIER_CLEAN)
print(df_clean.head(10))
