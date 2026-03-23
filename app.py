import random
from pathlib import Path

import pandas as pd
import streamlit as st

# ---- oldal beállítás ----
st.set_page_config(
    page_title="Művészeti kvíz",
    layout="wide"
)

# ---- kompaktabb felső térköz ----
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 0.6rem;
        padding-bottom: 0.6rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ---- fájl helye ----
CSV_FAJL = Path(__file__).parent / "hungart_korszakokkal.csv"


# ---- adatok betöltése ----
@st.cache_data
def adatbetoltes():
    try:
        if not CSV_FAJL.exists():
            return None

        df = pd.read_csv(CSV_FAJL)

        # oszlopnevek tisztítása
        df.columns = df.columns.str.strip()

        # szöveges oszlopok tisztítása
        for col in df.columns:
            if df[col].dtype == "object":
                df[col] = df[col].astype(str).str.strip()

        df = df.replace("nan", "")
        df = df.replace("None", "")

        return df

    except Exception as e:
        st.error(f"Hiba a betöltésnél: {e}")
        return None


# ---- kérdés generálása ----
def uj_kerdes(df):
    # csak használható sorok
    df_valid = df[
        (df["artist_name"].fillna("") != "") &
        (df["image_url"].fillna("") != "")
    ].copy()

    if len(df_valid) == 0:
        return None

    # legalább 4 különböző művész kell
    egyedi_muveszek = df_valid["artist_name"].dropna().unique()
    if len(egyedi_muveszek) < 4:
        return None

    # helyes sor
    helyes_sor = df_valid.sample(1).iloc[0]
    helyes_muvesz = helyes_sor["artist_name"]
    kep_url = helyes_sor["image_url"]
    cim = helyes_sor["title"] if "title" in df_valid.columns else ""

    # rossz válaszok
    tobbi_muvesz = [m for m in egyedi_muveszek if m != helyes_muvesz]
    if len(tobbi_muvesz) < 3:
        return None

    rosszak = random.sample(list(tobbi_muvesz), 3)

    valaszok = [helyes_muvesz] + rosszak
    random.shuffle(valaszok)

    return {
        "kep_url": kep_url,
        "helyes_muvesz": helyes_muvesz,
        "valaszok": valaszok,
        "cim": cim
    }


# ---- session state ----
if "kerdes" not in st.session_state:
    st.session_state.kerdes = None

if "valasz_ellenorizve" not in st.session_state:
    st.session_state.valasz_ellenorizve = False

if "kivalasztott_valasz" not in st.session_state:
    st.session_state.kivalasztott_valasz = None

if "elozo_mod" not in st.session_state:
    st.session_state.elozo_mod = None

if "elozo_korszak" not in st.session_state:
    st.session_state.elozo_korszak = None


def uj_kerdes_inditas(df_szurt):
    st.session_state.kerdes = uj_kerdes(df_szurt)
    st.session_state.valasz_ellenorizve = False
    st.session_state.kivalasztott_valasz = None


# ---- adatok beolvasása ----
df = adatbetoltes()

st.markdown("### Magyar művészeti kvíz")

if df is None:
    st.error("Nem található vagy nem olvasható a CSV fájl.")
    st.stop()

# ---- kompakt felső beállítások ----
col1, col2 = st.columns([1.2, 2])

with col1:
    st.markdown("**Játék beállítása**")
    jatek_mod = st.radio(
        "Mód",
        ["Összes", "Korszakok"],
        horizontal=True,
        label_visibility="collapsed"
    )

with col2:
    kivalasztott_korszak = None

    if jatek_mod == "Korszakok":
        korszakok = sorted(df["korszak"].dropna().unique())

        def korszak_kezdete(k):
            return int(str(k).split("-")[0])

        korszakok = [k for k in korszakok if korszak_kezdete(k) >= 1801]

        st.markdown("**Válassz korszakot**")
        kivalasztott_korszak = st.selectbox(
            "Korszak",
            korszakok,
            label_visibility="collapsed"
        )

        df_szurt = df[df["korszak"] == kivalasztott_korszak].copy()
    else:
        st.markdown("**Összes korszakból játszol**")
        df_szurt = df.copy()

# ---- ha változott a mód vagy a korszak, induljon új kérdés ----
if (
    st.session_state.elozo_mod != jatek_mod or
    st.session_state.elozo_korszak != kivalasztott_korszak
):
    st.session_state.elozo_mod = jatek_mod
    st.session_state.elozo_korszak = kivalasztott_korszak
    uj_kerdes_inditas(df_szurt)

# ---- gomb új kérdéshez ----
if st.button("Új játék / új kérdés"):
    uj_kerdes_inditas(df_szurt)

# ---- ellenőrzés: van-e kérdés ----
if st.session_state.kerdes is None:
    st.warning("Ebben a szűrésben nincs elég adat a játékhoz.")
    st.stop()

kerdes = st.session_state.kerdes

st.markdown("---")

# ---- kép egységes magassággal ----
height = 420

st.markdown(
    f"""
    <div style="
        height:{height}px;
        display:flex;
        align-items:center;
        justify-content:center;
        margin-bottom:10px;
    ">
        <img src="{kerdes['kep_url']}"
             style="max-height:100%; max-width:100%; object-fit:contain;" />
    </div>
    """,
    unsafe_allow_html=True
)

# ---- válaszlehetőségek ----
valasztott = st.radio(
    "Ki készítette ezt a művet?",
    kerdes["valaszok"],
    index=None
)

col_gomb1, col_gomb2 = st.columns(2)

with col_gomb1:
    if st.button("Ellenőrzés"):
        st.session_state.kivalasztott_valasz = valasztott
        st.session_state.valasz_ellenorizve = True

with col_gomb2:
    if st.button("Következő kérdés"):
        uj_kerdes_inditas(df_szurt)
        st.rerun()

# ---- visszajelzés ----
if st.session_state.valasz_ellenorizve:
    if st.session_state.kivalasztott_valasz is None:
        st.warning("Előbb válassz egy lehetőséget.")
    elif st.session_state.kivalasztott_valasz == kerdes["helyes_muvesz"]:
        st.success(f"Helyes! A művész: {kerdes['helyes_muvesz']}")
    else:
        st.error(f"Nem ez a helyes válasz. A helyes válasz: {kerdes['helyes_muvesz']}")

    if kerdes["cim"]:
        st.write(f"**Mű címe:** {kerdes['cim']}")
