import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import folium
from streamlit_folium import folium_static
from datetime import datetime, timedelta

# 🖼️ Mise en page large
st.set_page_config(layout="wide")

# 📥 Chargement des données
df_clean = pd.read_csv("data/sncf_clean.csv")
df_clean["Date"] = pd.to_datetime(df_clean["Date"], errors="coerce")
# 🔧 Ajout des colonnes manquantes pour garantir la suppression
if "Heure de départ" not in df_clean.columns:
    df_clean["Heure de départ"] = pd.NaT

if "Heure d'arrivée estimée" not in df_clean.columns:
    df_clean["Heure d'arrivée estimée"] = pd.NaT

if "Type de train" not in df_clean.columns:
    df_clean["Type de train"] = "Inconnu"


# 🧼 Nettoyage des noms de gares
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

# 📍 Coordonnées des gares
gares_coords = {
    "Paris": [48.8566, 2.3522],
    "Lille": [50.6292, 3.0573],
    "Lyon": [45.7640, 4.8357],
    "Marseille": [43.2965, 5.3698],
    "Bordeaux": [44.8378, -0.5792],
    "Strasbourg": [48.5734, 7.7521],
    "Nantes": [47.2184, -1.5536],
    "Toulouse": [43.6047, 1.4442]
}

# 🚉 Sélection dynamique
st.title("🚄 Tableau de bord SNCF")
st.markdown("### Sélectionnez une ligne")

col1, col2 = st.columns(2)
with col1:
    gare_depart = st.selectbox("Gare de départ", df_clean["Gare de départ"].unique())

gares_arrivees_possibles = df_clean[df_clean["Gare de départ"] == gare_depart]["Gare d'arrivée"].unique()
with col2:
    gare_arrivee = st.selectbox("Gare d'arrivée", gares_arrivees_possibles)

ligne_df = df_clean[
    (df_clean["Gare de départ"] == gare_depart) &
    (df_clean["Gare d'arrivée"] == gare_arrivee)
]

st.caption(f"🔗 {ligne_df.shape[0]} trajet(s) disponibles entre {gare_depart} et {gare_arrivee}")

if ligne_df.empty:
    st.warning("Aucune donnée disponible pour cette ligne.")
else:
    # 📊 KPI
    st.markdown("### 📊 Indicateurs de performance")
    col3, col4, col5 = st.columns(3)
    col3.metric("Circulations prévues", int(ligne_df["Nombre de circulations prévues"].sum()))
    col4.metric("Retard moyen (min)", round(ligne_df["Retard moyen de tous les trains à l'arrivée"].mean(), 2))
    taux_retard = ligne_df["Nombre de trains en retard à l'arrivée"].sum() / ligne_df["Nombre de circulations prévues"].sum() * 100
    col5.metric("Taux de retard (%)", f"{round(taux_retard, 2)}%")

    col6, col7, col8 = st.columns(3)
    col6.metric("Trains annulés", int(ligne_df["Nombre de trains annulés"].sum()))
    col7.metric("Période couverte", f"{ligne_df['Date'].min().date()} → {ligne_df['Date'].max().date()}")
    col8.metric("Total de trajets", ligne_df.shape[0])

    # 📈 Graphiques
    st.markdown("### 📈 Évolution mensuelle")
    col9, col10 = st.columns(2)
    with col9:
        fig1, ax1 = plt.subplots()
        ligne_df.groupby("Date")["Retard moyen de tous les trains à l'arrivée"].mean().plot(ax=ax1)
        ax1.set_title("Retard moyen par mois")
        st.pyplot(fig1)
    with col10:
        fig2, ax2 = plt.subplots()
        ligne_df.groupby("Date")["Nombre de circulations prévues"].sum().plot(ax=ax2, color="green")
        ax2.set_title("Circulations prévues par mois")
        st.pyplot(fig2)

    # 🗺️ Carte enrichie
    
    # 🔁 Simulation
    col_map, col_sim = st.columns([2,1])

    with col_map:
        st.markdown("### 🗺️ Carte interactive des lignes depuis la gare de départ")
        if gare_depart in gares_coords:
            lat1, lon1 = gares_coords[gare_depart]
            m = folium.Map(location=[lat1, lon1], zoom_start=6)
            folium.Marker([lat1, lon1], popup=f"Départ: {gare_depart}", icon=folium.Icon(color="green")).add_to(m)

            destinations = df_clean[df_clean["Gare de départ"] == gare_depart]["Gare d'arrivée"].unique()
            for dest in destinations:
                if dest in gares_coords:
                    lat2, lon2 = gares_coords[dest]
                    ligne_dest_df = df_clean[
                        (df_clean["Gare de départ"] == gare_depart) &
                        (df_clean["Gare d'arrivée"] == dest)
                    ]
                    retard_moyen = ligne_dest_df["Retard moyen de tous les trains à l'arrivée"].mean()
                    taux_retard = ligne_dest_df["Nombre de trains en retard à l'arrivée"].sum() / ligne_dest_df["Nombre de circulations prévues"].sum() * 100

                    color = "green" if taux_retard < 10 else "orange" if taux_retard < 20 else "red"
                    popup_text = f"{gare_depart} → {dest}<br>Retard moyen : {round(retard_moyen, 2)} min<br>Taux de retard : {round(taux_retard, 2)}%"
                    folium.Marker([lat2, lon2], popup=popup_text, icon=folium.Icon(color="blue")).add_to(m)
                    folium.PolyLine([[lat1, lon1], [lat2, lon2]], color=color, weight=3).add_to(m)

            folium.LayerControl().add_to(m)
            folium_static(m)

            # 🧭 Légende explicative
            st.markdown("""
            #### 🧭 Légende :
            - 🟢 Ligne verte : taux de retard < 10% (bonne régularité)
            - 🟠 Ligne orange : taux de retard entre 10% et 20%
            - 🔴 Ligne rouge : taux de retard > 20%
            - 🔵 Marqueur bleu : gare d’arrivée
            - 🟢 Marqueur vert : gare de départ
            """)
        else:
            st.warning("🧭 Coordonnées manquantes pour cette gare de départ.")
    with col_sim:
        st.markdown("### 🔁 Simulation d’un train")
        action = st.radio("Action", ["Ajouter un train fictif", "Supprimer un train existant"])

        if action == "Ajouter un train fictif":
            with st.form("form_ajout"):
                date_sim = st.date_input("Date du train simulé")
                heure_depart = st.time_input("Heure de départ")
                duree_moyenne = ligne_df["Durée moyenne du trajet"].mean()
                duree_trajet = st.number_input("Durée prévue du trajet (min)", min_value=10, max_value=600, value=int(duree_moyenne))
                type_train = st.selectbox("Type de train", ["TGV", "TER", "Intercités"])
                retard_sim = st.number_input("Retard estimé (min)", min_value=0, max_value=300, value=10)
                submit_ajout = st.form_submit_button("Ajouter le train")

            if submit_ajout:
                heure_depart_dt = datetime.combine(date_sim, heure_depart)
                heure_arrivee_dt = heure_depart_dt + timedelta(minutes=duree_trajet + retard_sim)
                nouveau_train = pd.DataFrame([{
                    "Date": pd.to_datetime(date_sim),
                    "Gare de départ": gare_depart,
                    "Gare d'arrivée": gare_arrivee,
                    "Durée moyenne du trajet": duree_trajet,
                    "Nombre de circulations prévues": 1,
                    "Nombre de trains annulés": 0,
                    "Nombre de trains en retard à l'arrivée": 1 if retard_sim > 0 else 0,
                    "Retard moyen des trains en retard à l'arrivée": retard_sim if retard_sim > 0 else 0,
                    "Retard moyen de tous les trains à l'arrivée": retard_sim,
                    "Type de train": type_train,
                    "Heure de départ": heure_depart_dt.time(),
                    "Heure d'arrivée estimée": heure_arrivee_dt.time()
                }])
                df_clean = pd.concat([df_clean, nouveau_train], ignore_index=True)
                st.success("✅ Train fictif ajouté.")

        elif action == "Supprimer un train existant":       
            st.markdown("### 🗑️ Sélectionnez un train à supprimer")
            trains_dispo = df_clean[
                (df_clean["Gare de départ"] == gare_depart) &
                (df_clean["Gare d'arrivée"] == gare_arrivee)
            ]

            if trains_dispo.empty:
                st.warning("⚠️ Aucun train disponible à supprimer sur cette ligne.")
            else:
                trains_dispo["ID"] = trains_dispo.index.astype(str)
                trains_dispo["Résumé"] = (
                    trains_dispo["Date"].dt.strftime("%Y-%m-%d") +
                    " à " + trains_dispo["Heure de départ"].astype(str).fillna("–") +
                    " – " + trains_dispo["Type de train"].fillna("Inconnu") +
                    f" ({gare_depart} → {gare_arrivee})"
                )

                train_choisi = st.selectbox("Train existant :", trains_dispo["Résumé"])
                if st.button("Supprimer ce train"):
                    index_choisi = trains_dispo[trains_dispo["Résumé"] == train_choisi]["ID"].values[0]
                    df_clean = df_clean.drop(index=int(index_choisi))
                    st.success("✅ Train supprimé avec succès.")

                    # 🔄 Recalcul des KPI
                    ligne_df = df_clean[
                        (df_clean["Gare de départ"] == gare_depart) &
                        (df_clean["Gare d'arrivée"] == gare_arrivee)
                    ]
                    st.markdown("### 🧠 Analyse d’impact après suppression")
                    col_a, col_b, col_c = st.columns(3)
                    circulations = ligne_df["Nombre de circulations prévues"].sum()
                    retards = ligne_df["Nombre de trains en retard à l'arrivée"].sum()
                    taux_retard = retards / circulations * 100 if circulations > 0 else 0
                    retard_moyen = ligne_df["Retard moyen de tous les trains à l'arrivée"].mean()
                    col_a.metric("🔁 Circulations après suppression", int(circulations))
                    col_b.metric("⏱️ Retard moyen recalculé", round(retard_moyen, 2))
                    col_c.metric("📊 Taux de retard recalculé", f"{round(taux_retard, 2)}%")

            
            
            
            
            

        # 🔄 Recalcul des KPI après action
        ligne_df = df_clean[
            (df_clean["Gare de départ"] == gare_depart) &
            (df_clean["Gare d'arrivée"] == gare_arrivee)
        ]
        st.markdown("### 🧠 Analyse d’impact après action")
        col_a, col_b, col_c = st.columns(3)
        circulations = ligne_df["Nombre de circulations prévues"].sum()
        retards = ligne_df["Nombre de trains en retard à l'arrivée"].sum()
        taux_retard = retards / circulations * 100 if circulations > 0 else 0
        retard_moyen = ligne_df["Retard moyen de tous les trains à l'arrivée"].mean()
        col_a.metric("🔁 Circulations après action", int(circulations))
        col_b.metric("⏱️ Retard moyen recalculé", round(retard_moyen, 2))
        col_c.metric("📊 Taux de retard recalculé", f"{round(taux_retard, 2)}%")



