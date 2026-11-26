import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

st.set_page_config(page_title="AgGrid vs data_editor", layout="wide")

# ---------------------------------------------------------------------------
# Données fictives
# ---------------------------------------------------------------------------
df = pd.DataFrame(
    {
        "Nom": ["Alice", "Bruno", "Chloé", "David", "Emma", "Farid", "Giulia", "Hugo"],
        "Ville": ["Paris", "Lyon", "Lille", "Nantes", "Nice", "Metz", "Rome", "Brest"],
        "Âge": [34, 28, 41, 25, 37, 52, 30, 45],
        "Score": [82.5, 91.0, 67.3, 74.8, 88.1, 59.9, 95.4, 70.2],
        "Actif": [True, False, True, True, False, True, True, False],
    }
)

# ---------------------------------------------------------------------------
# Couleurs selon le thème
# ---------------------------------------------------------------------------
try:
    dark = st.context.theme.type == "dark"
except Exception:
    dark = st.get_option("theme.base") == "dark"

if dark:
    bg, bg_header, text, text_header = "#0e1117", "#1a1c24", "#fafafa", "rgba(250,250,250,0.6)"
    border, hover, accent = "rgba(250,250,250,0.2)", "rgba(250,250,250,0.06)", "#ff4b4b"
else:
    bg, bg_header, text, text_header = "#ffffff", "#f6f7f9", "#31333f", "rgba(49,51,63,0.6)"
    border, hover, accent = "rgba(49,51,63,0.2)", "rgba(49,51,63,0.04)", "#ff4b4b"

custom_css = {
    ".ag-root-wrapper": {
        "border": f"1px solid {border} !important",
        "border-radius": "0.5rem !important",
        "background-color": f"{bg} !important",
        "font-family": '"Source Sans Pro", "Source Sans", sans-serif !important',
        "font-size": "14px !important",
    },
    ".ag-header": {
        "background-color": f"{bg_header} !important",
        "border-bottom": f"1px solid {border} !important",
    },
    ".ag-header-cell": {
        "background-color": f"{bg_header} !important",
        "border-right": f"1px solid {border} !important",
        "padding": "0 8px !important",
    },
    ".ag-header-cell-text": {
        "color": f"{text_header} !important",
        "font-weight": "400 !important",
    },
    ".ag-header-cell-resize::after": {"display": "none !important"},
    ".ag-row": {
        "background-color": f"{bg} !important",
        "border-bottom": f"1px solid {border} !important",
        "color": f"{text} !important",
    },
    ".ag-row-odd": {"background-color": f"{bg} !important"},
    ".ag-row-hover": {"background-color": f"{hover} !important"},
    ".ag-row-selected": {"background-color": f"{hover} !important"},
    ".ag-cell": {
        "border-right": f"1px solid {border} !important",
        "line-height": "34px !important",
        "padding": "0 8px !important",
    },
    ".ag-cell-focus, .ag-cell-focus:not(.ag-cell-range-selected):focus-within": {
        "border": f"1px solid {accent} !important",
    },
    ".ag-cell-inline-editing": {
        "border": f"1px solid {accent} !important",
        "box-shadow": "none !important",
        "background-color": f"{bg} !important",
    },
    ".ag-checkbox-input-wrapper.ag-checked::after": {"color": f"{accent} !important"},
    ".ag-checkbox-input-wrapper:focus-within": {"box-shadow": "none !important"},
}


def aggrid_data_editor(df, key, selectable=False):
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(editable=True, resizable=True, sortable=True, filter=False)
    if selectable:
        gb.configure_selection(
            "multiple", use_checkbox=True, header_checkbox=True, suppressRowClickSelection=True
        )
    gb.configure_grid_options(rowHeight=35, headerHeight=35, domLayout="normal")

    return AgGrid(
        df,
        gridOptions=gb.build(),
        height=min(35 * (len(df) + 1) + 3, 400),
        theme="streamlit",
        custom_css=custom_css,
        update_mode=GridUpdateMode.MODEL_CHANGED | GridUpdateMode.SELECTION_CHANGED,
        data_return_mode=DataReturnMode.AS_INPUT,
        fit_columns_on_grid_load=True,
        allow_unsafe_jscode=True,
        key=key,
    )


# ---------------------------------------------------------------------------
# Affichage côte à côte
# ---------------------------------------------------------------------------
st.title("AgGrid stylisé vs st.data_editor")

col1, col2 = st.columns(2)

with col1:
    st.subheader("st.data_editor (référence)")
    st.data_editor(df, hide_index=True, key="de")

with col2:
    st.subheader("AgGrid stylisé")
    resp = aggrid_data_editor(df, key="ag")

st.caption("Données après édition dans la grille AgGrid :")
st.dataframe(resp["data"], hide_index=True)