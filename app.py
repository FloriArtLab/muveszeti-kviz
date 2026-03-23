import random
from pathlib import Path

import pandas as pd
import streamlit as st

# ---- oldal beállítás ----
st.set_page_config(
    page_title="Művészeti kvíz",
    layout="wide"
)

# ---- kompakt felső margó ----
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

# ---- kisebb felső margó ----
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
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
            st.error("CSV nem létezik")
            return None

        df = pd.read_csv(CSV_FAJL)

       

        # üres helyek levágása
        for col in df.columns:
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
        (df["artist_name"] != "") &
        (df["image_url"] != "")
    ].copy()

    # legalább 4 különböző művész kell
    egyedi_muveszek = df_valid["artist_name"].dropna().unique()
    if len(egyedi_muveszek) < 4 or len(df_valid) == 0:
        return None

    # helyes válasz sora
    helyes_sor = df_valid.sample(1).iloc[0]
    helyes_muvesz = helyes_sor["artist_name"]
    kep_url = helyes_sor["image_url"]
    cim = helyes_sor.get("title", "")

    # rossz válaszok más művészektől
    tobbi_muvesz = [m for m in egyedi_muveszek if m != helyes_muvesz]
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


def uj_kerdes_inditas(df_szurt):
    st.session_state.kerdes = uj_kerdes(df_szurt)
    st.session_state.valasz_ellenorizve = False
    st.session_state.kivalasztott_valasz = None


# ---- adatok beolvasása ----
df = adatbetoltes()

st.markdown("## Magyar művészeti kvíz")

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
    if jatek_mod == "Korszakok":
        st.markdown("**Korszak**")

        korszakok = sorted(df["korszak"].dropna().unique())
        def korszak_kezdete(k):
            try:
                return int(str(k).split("-")[0])
            except:
                return 0  # hibás értékek kiszűrése
        
        korszakok = [k for k in korszakok if korszak_kezdete(k) >= 1801]

        kivalasztott_korszak = st.selectbox(
            "Korszak",
            korszakok,
            label_visibility="collapsed"
        )

        df_szurt = df[df["korszak"] == kivalasztott_korszak].copy()
    else:
        st.markdown("**Korszak**")
        st.caption("Összes korszak")
        df_szurt = df.copy()
        
# ---- ha még nincs kérdés, induljon ----
if st.session_state.kerdes is None:
    uj_kerdes_inditas(df_szurt)

# ---- ha a szűrés megváltozott, lehessen új kérdést kérni ----
if st.button("Új játék / új kérdés"):
    uj_kerdes_inditas(df_szurt)

# ---- ellenőrzés: van-e elég adat ----
if st.session_state.kerdes is None:
    st.warning("Ebben a szűrésben nincs elég adat a játékhoz.")
    st.stop()

kerdes = st.session_state.kerdes

# ---- kép megjelenítés ----

height = 420

st.markdown(
    f"""
    <div style="
        height:{height}px;
        display:flex;
        align-items:center;
        justify-content:center;
        margin-bottom:12px;
    ">
        <img src="{kerdes['kep_url']}"
             style="max-height:100%; max-width:100%; object-fit:contain;" />
    </div>
    """,
    unsafe_allow_html=True
)

# ---- válaszok + akciók egy sorban ----
bal, jobb = st.columns([3, 1.2])

with bal:
    valasztott = st.radio(
        "Ki készítette ezt a művet?",
        kerdes["valaszok"],
        index=None,
        label_visibility="collapsed"
    )

with jobb:
    if st.button("Ellenőrzés", use_container_width=True):
        st.session_state.kivalasztott_valasz = valasztott
        st.session_state.valasz_ellenorizve = True

    if st.button("Következő kérdés", use_container_width=True):
        uj_kerdes_inditas(df_szurt)
        st.rerun()

    if st.session_state.valasz_ellenorizve:
        if st.session_state.kivalasztott_valasz is None:
            st.warning("Előbb válassz egy lehetőséget.")
        elif st.session_state.kivalasztott_valasz == kerdes["helyes_muvesz"]:
            st.success(f"Helyes! {kerdes['helyes_muvesz']}")
        else:
            st.error(f"Helyes válasz: {kerdes['helyes_muvesz']}")

# ---- visszajelzés ----
if st.session_state.valasz_ellenorizve:
    if st.session_state.kivalasztott_valasz is None:
        st.warning("Előbb válassz egy lehetőséget.")
    elif st.session_state.kivalasztott_valasz == kerdes["helyes_muvesz"]:
        st.success(f"Helyes! A művész: {kerdes['helyes_muvesz']}")
    else:
        st.error(
            f"Nem ez a helyes válasz. A helyes válasz: {kerdes['helyes_muvesz']}"
        )

    if kerdes["cim"]:
        st.write(f"**Mű címe:** {kerdes['cim']}")
