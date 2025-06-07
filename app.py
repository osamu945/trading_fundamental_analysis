import streamlit as st
import pandas as pd
from textblob import TextBlob
import plotly.express as px

# --- Dictionnaire des indicateurs avec pondération ---
indicateurs = {
    "Taux d’intérêt": 100,
    "Décision de politique monétaire": 75,
    "Discours banques centrales": 50,
    "Inflation (CPI, Core CPI, PCE)": 50,
    "Création d’emplois": 40,
    "PIB (croissance)": 35,
    "Chômage": 30,
    "Balance commerciale": 20,
    "PMI (ISM, Markit)": 15,
    "Ventes au détail": 15,
    "PPI (indice des prix à la production)": 12.5,
    "Confiance du consommateur": 10,
    "Confiance des entreprises": 10,
    "Production industrielle": 10,
    "Commandes de biens durables": 7.5,
    "Indicateurs immobiliers": 7.5,
    "Stocks de pétrole / énergie": 7.5,
    "Sentiment du marché / volatilité (VIX)": 5,
    "Rumeurs géopolitiques / tensions": 5,
    "Indice de coût de la main-d'œuvre (ECI)": 2.5
}

# --- Paires disponibles ---
paires = {
    "EUR/USD": ("Zone euro", "États-Unis"),
    "GBP/USD": ("Royaume-Uni", "États-Unis"),
    "USD/JPY": ("États-Unis", "Japon"),
    "USD/CAD": ("États-Unis", "Canada"),
    "USD/CHF": ("États-Unis", "Suisse"),
    "AUD/USD": ("Australie", "États-Unis"),
    "NZD/USD": ("Nouvelle-Zélande", "États-Unis"),
    "XAU/USD": ("Or", "États-Unis"),
    "BTC/USD": ("Bitcoin", "États-Unis"),
    "AAPL/USD": ("Apple", "États-Unis"),
    "ETH/USD": ("Ethereum", "États-Unis")
}

# --- Fonction pour analyser un indicateur individuel ---
def analyser_indicateur(row):
    ecart = abs(row['Réel'] - row['Prévu'])
    importance = row['Importance']
    score = ecart * importance
    if row['Effet typique'] == "🔼":
        return score if row['Réel'] > row['Prévu'] else -score
    elif row['Effet typique'] == "🔽":
        return score if row['Réel'] < row['Prévu'] else -score
    else:
        return 0

# --- Estimation durée tendance ---
def estimer_duree_tendance(score_total):
    duree = max(1, min(72, abs(score_total) * 12))
    if duree <= 24:
        terme = "court terme (<24h)"
    elif duree <= 48:
        terme = "moyen terme (24-48h)"
    else:
        terme = "long terme (>48h)"
    return duree, terme

# --- Analyse de discours avec TextBlob ---
def analyser_discours(discours):
    if not discours.strip():
        return 0, "Aucun discours saisi"
    tb = TextBlob(discours)
    polarite = tb.sentiment.polarity
    if polarite > 0.1:
        sentiment = "Positif"
    elif polarite < -0.1:
        sentiment = "Négatif"
    else:
        sentiment = "Neutre"
    score_discours = polarite * 50
    return score_discours, sentiment

# --- Construction du dataframe des indicateurs ---
def construire_dataframe(pond_personnalisee):
    data = []
    for nom, importance in indicateurs.items():
        imp = pond_personnalisee.get(nom, importance)
        data.append({
            "Indicateur": nom,
            "Précédent": 0.0,
            "Prévu": 0.0,
            "Réel": 0.0,
            "Importance": imp,
            "Effet typique": "🔼"
        })
    return pd.DataFrame(data)

# --- Interface Streamlit ---
st.set_page_config(page_title="Analyse Fondamentale IA", layout="wide")

st.title("Analyse Fondamentale IA avec Corrélation Logique")

# Sélection de la paire de devises
pair = st.selectbox("Choisissez une paire Forex/Actif", list(paires.keys()))
region1, region2 = paires[pair]
st.markdown(f"**Région 1 :** {region1}  |  **Région 2 :** {region2}")

pond_on = st.checkbox("Activer personnalisation pondérations", value=False)
pond_personnalisee = {}
if pond_on:
    st.markdown("### Personnalisez l'importance (%) des indicateurs :")
    for nom, imp in indicateurs.items():
        val = st.slider(f"{nom}", min_value=0, max_value=100, value=int(imp), step=1)
        pond_personnalisee[nom] = val

# Données régionales
st.markdown(f"### Saisissez les données économiques pour {region1} :")
df1 = construire_dataframe(pond_personnalisee)
df1_edit = st.data_editor(df1[["Indicateur", "Précédent", "Prévu", "Réel"]], num_rows="dynamic", key="region1_editor")

st.markdown(f"### Saisissez les données économiques pour {region2} :")
df2 = construire_dataframe(pond_personnalisee)
df2_edit = st.data_editor(df2[["Indicateur", "Précédent", "Prévu", "Réel"]], num_rows="dynamic", key="region2_editor")

for idx, val in enumerate(df1_edit["Indicateur"]):
    df1.loc[df1["Indicateur"] == val, ["Précédent", "Prévu", "Réel"]] = df1_edit.loc[idx, ["Précédent", "Prévu", "Réel"]].values

for idx, val in enumerate(df2_edit["Indicateur"]):
    df2.loc[df2["Indicateur"] == val, ["Précédent", "Prévu", "Réel"]] = df2_edit.loc[idx, ["Précédent", "Prévu", "Réel"]].values

st.markdown("### Entrez un discours à analyser (facultatif) :")
discours = st.text_area("Discours de banque centrale, président, etc.")

if st.button("Démarrer l'analyse"):
    df1["Score"] = df1.apply(analyser_indicateur, axis=1)
    df2["Score"] = df2.apply(analyser_indicateur, axis=1)

    score1 = df1["Score"].sum()
    score2 = df2["Score"].sum()

    # Corrélation logique inversée de la devise 2
    score_total = score1 - score2

    score_discours, sentiment_discours = analyser_discours(discours)
    score_total += score_discours

    duree_h, terme = estimer_duree_tendance(score_total)

    seuil_achat = 20
    seuil_vente = -20
    if score_total > seuil_achat:
        decision = "ACHAT"
    elif score_total < seuil_vente:
        decision = "VENTE"
    else:
        decision = "NEUTRE"

    st.markdown("## Résultat de l'analyse IA")
    st.markdown(f"**Paire analysée :** {pair}")
    st.markdown(f"**Score total corrigé IA :** {score_total:.2f}")
    st.markdown(f"**Sentiment discours :** {sentiment_discours}")
    st.markdown(f"**Décision recommandée :** {decision}")
    st.markdown(f"**Durée estimée de la tendance :** {duree_h:.1f} heures ({terme})")

    def color_score(val):
        if val > 0:
            return "background-color: #d4f7d4"
        elif val < 0:
            return "background-color: #f7d4d4"
        else:
            return ""

    st.markdown("### Détails Région 1")
    st.dataframe(df1.style.applymap(color_score, subset=["Score"]))

    st.markdown("### Détails Région 2")
    st.dataframe(df2.style.applymap(color_score, subset=["Score"]))

    df_combined = pd.concat([
        df1[["Indicateur", "Score"]].assign(Région=region1),
        df2[["Indicateur", "Score"]].assign(Région=region2)
    ])
    fig = px.bar(
        df_combined.sort_values("Score"),
        x="Score", y="Indicateur", color="Région", orientation="h",
        title="Impact des indicateurs économiques (IA corrigée)",
    )
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Remplissez les données économiques et cliquez sur 'Démarrer l'analyse'.")
