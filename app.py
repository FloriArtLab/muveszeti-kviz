import random
from pathlib import Path

import pandas as pd
import streamlit as st

# ---- oldal beállítás ----
st.set_page_config(
    page_title="Művészeti kvíz",
    layout="wide"
)

# ---- fájl helye ----
CSV_FAJL = Path(r"D:\Flori_Art_Lab\muveszeti_jatek\muveszet_adatbank.csv")


# ---- adatok betöltése ----
@st.cache_data
def adatbetoltes():
    if not CSV_FAJL.exists():
        return None

    df = pd.read_csv(CSV_FAJL)

    # üres helyek levágása
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()

    return df


# ---- kérdés generálása ----
def uj_kerdes(df):
    # csak olyan sorok maradjanak, ahol van alkotó és képútvonal
    df = df[(df["alkoto"] != "") & (df["kep_url"] != "")]
    df = df.copy()

    # legalább 4 különböző alkotó kell
    kulonbozo_alkotok = df["alkoto"].dropna().unique().tolist()
    if len(kulonbozo_alkotok) < 4:
        return None

    # kiválasztunk 1 képet
    sor = df.sample(1).iloc[0]
    helyes_alkoto = sor["alkoto"]

    # 3 másik alkotó
    mas_alkotok = [a for a in kulonbozo_alkotok if a != helyes_alkoto]
    valaszok = random.sample(mas_alkotok, 3)
    valaszok.append(helyes_alkoto)
    random.shuffle(valaszok)

    return {
        "sor": sor,
        "helyes_alkoto": helyes_alkoto,
        "valaszok": valaszok
    }


# ---- session state indulás ----
if "pont" not in st.session_state:
    st.session_state.pont = 0

if "osszkerdes" not in st.session_state:
    st.session_state.osszkerdes = 0

if "ellenorizve" not in st.session_state:
    st.session_state.ellenorizve = False

if "utolso_valasz" not in st.session_state:
    st.session_state.utolso_valasz = None

if "aktualis_kerdes" not in st.session_state:
    st.session_state.aktualis_kerdes = None


# ---- adatok beolvasása ----
df = adatbetoltes()

st.title("Magyar művészeti kvíz")
st.write("Válaszd ki, ki festette a képet.")

if df is None:
    st.error("Nem találom a CSV fájlt itt: D:\\Flori_Art_Lab\\muveszeti_jatek\\muveszet_adatbank.csv")
    st.stop()

# ---- szűrés alkotóra ----
alkoto_lista = sorted(df["alkoto"].dropna().unique().tolist())
alkoto_valasztas = st.sidebar.selectbox(
    "Szűrés alkotóra",
    ["Összes"] + alkoto_lista
)

if alkoto_valasztas == "Összes":
    szurt_df = df.copy()
else:
    szurt_df = df[df["alkoto"] == alkoto_valasztas].copy()

st.sidebar.write(f"Képek száma: {len(szurt_df)}")

# ---- ha nincs elég adat ----
if len(szurt_df) < 4 and alkoto_valasztas == "Összes":
    st.error("Legalább 4 különböző alkotó kell a játékhoz.")
    st.stop()

if alkoto_valasztas != "Összes":
    st.warning("Ha csak egy alkotóra szűrsz, a 4 válaszlehetőség nem fog jól működni. Kezdésnek hagyd 'Összes'-en.")

# ---- új kérdés ----
if st.session_state.aktualis_kerdes is None:
    st.session_state.aktualis_kerdes = uj_kerdes(df)

kerdes = st.session_state.aktualis_kerdes

if kerdes is None:
    st.error("Nem sikerült kérdést készíteni. Ellenőrizd a CSV adatokat.")
    st.stop()

sor = kerdes["sor"]

# ---- kép elérési út ellenőrzése ----
kep_ut = sor["kep_url"]

# ha a pandas 'nan'-t olvasott be szövegként
if kep_ut.lower() == "nan":
    st.error("A kép útvonala hiányzik a CSV-ben.")
    st.stop()

if not Path(kep_ut).exists():
    st.error(f"Nem találom ezt a képet: {kep_ut}")
    st.info("Valószínűleg a CSV-ben a kép neve vagy a kiterjesztése (.jpg / .png) nem pontos.")
    st.stop()

# ---- felület ----
bal, jobb = st.columns([1.3, 1])

with bal:
    st.image(kep_ut, use_container_width=True)

with jobb:
    st.subheader(sor["kepcim"])
    st.write(f"**Év:** {sor['ev']}")
    st.write(f"**Téma:** {sor['tema']}")
    st.write(f"**Gyűjtemény:** {sor['gyujtemeny']}")
    st.write(f"**Technika:** {sor['technika']}")
    st.write(f"**Hordozó:** {sor['hordozo']}")
    st.write(f"**Méret:** {sor['meret']}")

    valasztott = st.radio(
        "Ki az alkotó?",
        kerdes["valaszok"],
        index=None,
        disabled=st.session_state.ellenorizve
    )

    if st.button("Válasz ellenőrzése", disabled=st.session_state.ellenorizve or valasztott is None):
        st.session_state.ellenorizve = True
        st.session_state.utolso_valasz = valasztott
        st.session_state.osszkerdes += 1

        if valasztott == kerdes["helyes_alkoto"]:
            st.session_state.pont += 1

# ---- visszajelzés ----
if st.session_state.ellenorizve:
    if st.session_state.utolso_valasz == kerdes["helyes_alkoto"]:
        st.success(f"Helyes válasz! Az alkotó: {kerdes['helyes_alkoto']}")
    else:
        st.error(f"Nem jó. A helyes válasz: {kerdes['helyes_alkoto']}")

    if st.button("Következő kép"):
        st.session_state.aktualis_kerdes = uj_kerdes(df)
        st.session_state.ellenorizve = False
        st.session_state.utolso_valasz = None
        st.rerun()

st.divider()
st.write(f"**Pontszám:** {st.session_state.pont} / {st.session_state.osszkerdes}")

with st.expander("Adatok megjelenítése"):
    st.dataframe(df, use_container_width=True)