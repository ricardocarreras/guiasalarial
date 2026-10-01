from pathlib import Path
import math

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Guía salarial Selecta",
    page_icon="💼",
    layout="centered",
)


MIN_OBSERVACIONES = 5
REDONDEO_EUROS = 500
TODAS_LAS_CIUDADES = "Toda España"


def localizar_base() -> Path:
    candidatos = [
        Path("data/Base_Selectron_Normalizada.xlsx"),
        Path("data/Base_Selectron_Normalizada(1).xlsx"),
        Path("Base_Selectron_Normalizada.xlsx"),
        Path("Base_Selectron_Normalizada(1).xlsx"),
    ]
    for ruta in candidatos:
        if ruta.exists():
            return ruta
    raise FileNotFoundError(
        "No se encuentra la base normalizada. Sube el archivo como "
        "data/Base_Selectron_Normalizada.xlsx."
    )


@st.cache_data(show_spinner=False)
def cargar_datos(ruta: str) -> pd.DataFrame:
    columnas = [
        "Ciudad normalizada",
        "Puesto normalizado",
        "Experiencia normalizada (años)",
        "Salario normalizado EUR/año",
        "Calidad salario",
    ]
    datos = pd.read_excel(
        ruta,
        sheet_name="Candidatos normalizados",
        usecols=columnas,
    )

    datos["Experiencia normalizada (años)"] = pd.to_numeric(
        datos["Experiencia normalizada (años)"], errors="coerce"
    )
    datos["Salario normalizado EUR/año"] = pd.to_numeric(
        datos["Salario normalizado EUR/año"], errors="coerce"
    )

    # Solo se admiten salarios ya considerados utilizables en la normalización.
    calidades_validas = {
        "EUR/año plausible",
        "Convertido desde miles de EUR",
        "Convertido desde EUR/mes",
    }
    datos = datos[
        datos["Calidad salario"].isin(calidades_validas)
        & datos["Salario normalizado EUR/año"].notna()
        & datos["Experiencia normalizada (años)"].notna()
        & datos["Puesto normalizado"].notna()
        & datos["Ciudad normalizada"].notna()
    ].copy()

    return datos


def redondear_salario(valor: float) -> int:
    return int(math.floor(valor / REDONDEO_EUROS + 0.5) * REDONDEO_EUROS)


def euros(valor: float) -> str:
    return f"{redondear_salario(valor):,.0f} €".replace(",", ".")


def calcular_resultado(
    datos: pd.DataFrame,
    puesto: str,
    ciudad: str,
    experiencia_minima: int,
    experiencia_maxima: int,
) -> dict | None:
    filtro = datos["Puesto normalizado"].eq(puesto)

    if ciudad != TODAS_LAS_CIUDADES:
        filtro &= datos["Ciudad normalizada"].eq(ciudad)

    # Límites estrictos: más de la mínima y menos de la máxima.
    filtro &= datos["Experiencia normalizada (años)"].gt(experiencia_minima)
    filtro &= datos["Experiencia normalizada (años)"].lt(experiencia_maxima)

    salarios = datos.loc[filtro, "Salario normalizado EUR/año"]
    if len(salarios) < MIN_OBSERVACIONES:
        return None

    return {
        "media": salarios.mean(),
        "mediana": salarios.median(),
        "p25": salarios.quantile(0.25),
        "p75": salarios.quantile(0.75),
    }


logo = Path("SELECTA-Logo.png")
if logo.exists():
    st.image(str(logo), width=300)

st.title("Guía salarial")
st.caption(
    "Estimación basada en expectativas salariales registradas en Selectron. "
    "Importes brutos anuales en euros."
)

try:
    ruta_base = localizar_base()
    df = cargar_datos(str(ruta_base))
except Exception:
    st.error(
        "No ha sido posible cargar la base salarial. Comprueba que el archivo "
        "data/Base_Selectron_Normalizada.xlsx está en el repositorio."
    )
    st.stop()


puestos = sorted(df["Puesto normalizado"].dropna().unique().tolist())
ciudades = [TODAS_LAS_CIUDADES] + sorted(
    ciudad
    for ciudad in df["Ciudad normalizada"].dropna().unique().tolist()
    if ciudad not in {"Sin especificar", "España"}
)

with st.form("consulta_salarial"):
    puesto = st.selectbox("Perfil profesional", puestos)
    ciudad = st.selectbox("Ciudad", ciudades)

    col_min, col_max = st.columns(2)
    with col_min:
        experiencia_minima = st.number_input(
            "Más de estos años",
            min_value=0,
            max_value=49,
            value=2,
            step=1,
        )
    with col_max:
        experiencia_maxima = st.number_input(
            "Menos de estos años",
            min_value=1,
            max_value=50,
            value=20,
            step=1,
        )

    consultar = st.form_submit_button(
        "Consultar salario",
        type="primary",
        use_container_width=True,
    )


if consultar:
    if experiencia_minima >= experiencia_maxima:
        st.warning("La experiencia máxima debe ser superior a la mínima.")
    else:
        resultado = calcular_resultado(
            df,
            puesto,
            ciudad,
            int(experiencia_minima),
            int(experiencia_maxima),
        )

        st.subheader(f"{puesto} · {ciudad}")
        st.caption(
            f"Más de {int(experiencia_minima)} y menos de "
            f"{int(experiencia_maxima)} años de experiencia"
        )

        if resultado is None:
            st.info(
                "No tengo información que pueda considerarse estadísticamente "
                "sólida con esos requisitos."
            )
        else:
            st.metric("Expectativa salarial media", euros(resultado["media"]))

            col_mediana, col_rango = st.columns(2)
            with col_mediana:
                st.metric("Mediana", euros(resultado["mediana"]))
            with col_rango:
                st.metric(
                    "Rango salarial central",
                    f"{euros(resultado['p25'])} – {euros(resultado['p75'])}",
                )

            st.caption(
                "Resultados agregados y redondeados a los 500 € más próximos."
            )
