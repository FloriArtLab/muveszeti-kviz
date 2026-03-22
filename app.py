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
CSV_FAJL = Path("data/hungart_osszes_muvesz_adatok.csv")
KEP_MAPPA = Path("images")


# ---- adatok betöltése ----
@st.cache_data
def adatbetoltes():
    if not CSV_FAJL.exists():
        return None

    df = pd.read_csv(CSV_FAJL)

    # szöveges oszlopok tisztítása
    for col in df.columns:
        df[col] = df[col].fillna("").astype(str).str.strip()

    # ha nincs filename oszlop, készítsük el az image_url-ből
    if "filename" not in df.columns:
        if "image_url" in df.columns:
            df["filename"] = df["image_url"].str.split("/").str[-1]
        else:
            df["filename"] = ""

    # helyi képelérési út
    df["local_image_path"] = df["filename"].apply(lambda x: str(KEP_MAPPA / x) if x else "")

    # csak olyan sorok maradjanak, ahol van művész + kép
    if "artist_name" not in df.columns:
        st.error("A CSV-ben nincs 'artist_name' oszlop.")
        st.stop()

    df = df[(df["artist_name"] != "") & (df["local_image_path"] != "")].copy()

    # csak a ténylegesen létező képeket használjuk
    df = df[df["local_image_path"].apply(lambda p: Path(p).exists())].copy()

    return df


# ---- kérdés generálása ----
def uj_kerdes(df):
    kulonbozo_alkotok = df["artist_name"].dropna().unique().tolist()

    if len(kulonbozo_alkotok) < 4:
        return None

    sor = df.sample(1).iloc[0]
    helyes_alkoto = sor["artist_name"]

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
    st.error("Nem találom a CSV fájlt itt: data/hungart_osszes_muvesz_adatok.csv")
    st.stop()

if len(df) == 0:
    st.error("Nincs használható adat vagy kép az adatbázisban.")
    st.stop()

# ---- szűrés alkotóra ----
alkoto_lista = sorted(df["artist_name"].dropna().unique().tolist())
alkoto_valasztas = st.sidebar.selectbox(
    "Szűrés alkotóra",
    ["Összes"] + alkoto_lista
)

if alkoto_valasztas == "Összes":
    szurt_df = df.copy()
else:
    szurt_df = df[df["artist_name"] == alkoto_valasztas].copy()

st.sidebar.write(f"Képek száma: {len(szurt_df)}")

if len(szurt_df) == 0:
    st.error("Ehhez a szűréshez nincs elérhető kép.")
    st.stop()

# ---- új kérdés ----
if st.session_state.aktualis_kerdes is None:
    st.session_state.aktualis_kerdes = uj_kerdes(szurt_df if alkoto_valasztas == "Összes" else df)

kerdes = st.session_state.aktualis_kerdes

if kerdes is None:
    st.error("Nem sikerült kérdést készíteni. Legalább 4 különböző művész kell.")
    st.stop()

sor = kerdes["sor"]

# ---- kép elérési út ellenőrzése ----
kep_ut = sor["local_image_path"]

if not Path(kep_ut).exists():
    st.error(f"Nem találom ezt a képet: {kep_ut}")
    st.stop()

# ---- adatok biztonságos kiolvasása ----
cim = sor["title"] if "title" in sor else ""
ev = sor["year"] if "year" in sor else ""
technika = sor["technique"] if "technique" in sor else ""
meret = sor["size"] if "size" in sor else ""
hely = sor["location"] if "location" in sor else ""
kategori = sor["category"] if "category" in sor else ""

# ---- felület ----
bal, jobb = st.columns([1.3, 1])

with bal:
    st.image(kep_ut, use_container_width=True)

with jobb:
    st.subheader(cim if cim else "Cím nélkül")
    if ev:
        st.write(f"**Év:** {ev}")
    if kategori:
        st.write(f"**Kategória:** {kategori}")
    if technika:
        st.write(f"**Technika:** {technika}")
    if meret:
        st.write(f"**Méret:** {meret}")
    if hely:
        st.write(f"**Gyűjtemény / hely:** {hely}")

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
        uj_df = szurt_df if alkoto_valasztas == "Összes" else df
        st.session_state.aktualis_kerdes = uj_kerdes(uj_df)
        st.session_state.ellenorizve = False
        st.session_state.utolso_valasz = None
        st.rerun()

st.divider()
st.write(f"**Pontszám:** {st.session_state.pont} / {st.session_state.osszkerdes}")

with st.expander("Adatok megjelenítése"):
    st.dataframe(df, use_container_width=True)
