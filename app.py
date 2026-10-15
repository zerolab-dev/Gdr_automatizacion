import os
from datetime import datetime

import pandas as pd
import streamlit as st

from config import MESES_UI, TEMPLATE_PATH, METAS_PATH
from validators import (
    validar_datos_entrada,
    validar_metas,
    validar_listado_up,
    validar_cruces,
)
from data_processor import procesar_datos_por_cite, sugerir_mes_final
from excel_generator import (
    generar_excel_bytes,
    generar_zip_todas_las_fichas,
    normalizar_nombre_archivo,
)

st.set_page_config(
    page_title="Generador de Fichas GDR - Red CITE",
    layout="wide",
    page_icon="📊",
)

st.markdown(
    """
    <style>
    .main .block-container { padding-top: 2rem; }
    h1 { color: #B72727; }
    h2, h3 { color: #6F6F6F; }
    .metric-card {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #B72727;
        margin-bottom: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Generador de Fichas GDR")
st.markdown(
    "### Sistema automatizado para la generación de fichas técnicas de indicadores de la Red CITE"
)
st.divider()

for ruta, etiqueta in [
    (TEMPLATE_PATH, "plantilla oficial `templates/plantilla_gdr.xlsx`"),
    (METAS_PATH, "archivo de metas `data/metas_gdr.xlsx`"),
]:
    if not os.path.exists(ruta):
        st.error(f"No se encontró {etiqueta} en el repositorio.")
        st.stop()

try:
    df_metas = pd.read_excel(METAS_PATH)
    df_metas.columns = df_metas.columns.astype(str).str.strip()
    metas_validas, mensaje_metas = validar_metas(df_metas)
    if not metas_validas:
        st.error(mensaje_metas)
        st.stop()
except Exception as exc:
    st.error(f"No se pudo leer el archivo fijo de metas: {exc}")
    st.stop()

st.header("Paso 1: Cargar información")
carga1, carga2 = st.columns(2)
with carga1:
    archivo_consolidado = st.file_uploader(
        "1. Cargar consolidado de indicadores (.xlsx)",
        type=["xlsx"],
        key="consolidado",
    )
with carga2:
    archivo_up = st.file_uploader(
        "2. Cargar listado UP del Indicador 1 (.xlsx)",
        type=["xlsx"],
        key="listado_up",
    )

if archivo_consolidado is None or archivo_up is None:
    st.info("Cargue ambos archivos para continuar.")
    st.stop()

try:
    df = pd.read_excel(archivo_consolidado)
    df.columns = df.columns.astype(str).str.strip()
    es_valido, mensaje, advertencias = validar_datos_entrada(df)
    if not es_valido:
        st.error(mensaje)
        st.stop()

    # dtype=str protege identificadores largos del listado UP durante la lectura.
    df_up = pd.read_excel(archivo_up, dtype={"RUC/DNI/CE/OTROS": str})
    df_up.columns = df_up.columns.astype(str).str.strip()
    up_valido, mensaje_up, advertencias_up = validar_listado_up(df_up)
    if not up_valido:
        st.error(mensaje_up)
        st.stop()

    cruces_validos, errores_cruce = validar_cruces(df, df_metas, df_up)
    if not cruces_validos:
        st.error(
            "Los nombres de CITE deben coincidir exactamente entre consolidado, metas y listado UP."
        )
        for error in errores_cruce:
            st.error(error)
        st.stop()
except Exception as exc:
    st.error(f"No se pudieron validar los archivos de entrada: {exc}")
    st.stop()

st.success("Consolidado, metas y listado UP validados correctamente.")

advertencias_totales = advertencias + advertencias_up
if advertencias_totales:
    with st.expander(f"⚠️ Advertencias de calidad ({len(advertencias_totales)})"):
        for adv in advertencias_totales:
            st.warning(adv)

unidades = [str(x).strip() for x in df["cite_ut"].dropna().unique()]
cites = sorted(unidades)
mes_sugerido = sugerir_mes_final(df)

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(
        f"<div class='metric-card'><b>Consolidado</b><br>{archivo_consolidado.name}</div>",
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        f"<div class='metric-card'><b>CITE detectados</b><br>{len(cites)}</div>",
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        f"<div class='metric-card'><b>Periodo sugerido hasta</b><br>{mes_sugerido}</div>",
        unsafe_allow_html=True,
    )

st.divider()
st.header("Paso 2: Configurar ficha")
f1, f2, f3, f4 = st.columns(4)
with f1:
    anio_sel = st.number_input(
        "Año de reporte",
        min_value=2016,
        max_value=2100,
        value=datetime.now().year,
        step=1,
    )
with f2:
    mes_inicio_sel = st.selectbox("Periodo desde", MESES_UI, index=0)
with f3:
    idx_sugerido = MESES_UI.index(mes_sugerido)
    mes_fin_sel = st.selectbox("Periodo hasta", MESES_UI, index=idx_sugerido)
with f4:
    cite_ui = st.selectbox("CITE/UT", ["Todos los CITE/UT"] + cites)

cite_real = "TODOS" if cite_ui == "Todos los CITE/UT" else cite_ui

if MESES_UI.index(mes_inicio_sel) > MESES_UI.index(mes_fin_sel):
    st.error("El mes inicial no puede ser posterior al mes final.")
    st.stop()

st.divider()
st.header("Paso 3: Vista previa")
cite_preview = cites[0] if cite_real == "TODOS" and cites else cite_real
if not cite_preview:
    st.error("No existen unidades disponibles para mostrar.")
    st.stop()

st.markdown(f"**Vista previa:** {cite_preview.upper()} — {anio_sel}")
try:
    df_preview, alertas = procesar_datos_por_cite(
        df, cite_preview, anio_sel, mes_inicio_sel, mes_fin_sel
    )
    vista = df_preview.copy()
    mask_pct = vista["Indicador"] == "Indicador 3"
    if mask_pct.any():
        idx = vista.index[
            mask_pct & (vista["Variable"] == "Número de encuestas respondidas")
        ]
        if len(idx) == 1 and isinstance(vista.at[idx[0], "Valor Alcanzado"], (int, float)):
            vista.at[idx[0], "Valor Alcanzado"] = f"{vista.at[idx[0], 'Valor Alcanzado']:.2%}"

    meta_preview = df_metas[df_metas["CITE"] == cite_preview].iloc[0]
    st.caption(
        f"Metas: Indicador 1 = {meta_preview['Meta Indicador 1']:g} | "
        f"Indicador 2 = {meta_preview['Meta Indicador 2']:g} | "
        f"Indicador 3 = {meta_preview['Meta Indicador 3']:.2%}"
    )
    st.dataframe(vista, hide_index=True, use_container_width=True)
    for alerta in alertas:
        st.info(alerta)
except Exception as exc:
    st.error(f"No se pudo construir la vista previa: {exc}")
    st.stop()

st.divider()
st.header("Paso 4: Generación")
b1, b2 = st.columns(2)

with b1:
    if cite_real != "TODOS":
        try:
            excel_bytes = generar_excel_bytes(
                df, df_metas, df_up, cite_real, anio_sel, mes_inicio_sel, mes_fin_sel
            )
            nombre_archivo = (
                f"GDR_{normalizar_nombre_archivo(cite_real).upper()}_"
                f"{anio_sel}_{mes_inicio_sel[:3].upper()}_{mes_fin_sel[:3].upper()}.xlsx"
            )
            st.download_button(
                "⬇️ Descargar ficha Excel",
                data=excel_bytes,
                file_name=nombre_archivo,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        except Exception as exc:
            st.error(f"No se pudo generar la ficha: {exc}")
    else:
        st.info("Seleccione una unidad específica para descargar una ficha individual.")

with b2:
    try:
        zip_bytes, cantidad = generar_zip_todas_las_fichas(
            df, df_metas, df_up, anio_sel, mes_inicio_sel, mes_fin_sel
        )
        nombre_zip = (
            f"FICHAS_GDR_{anio_sel}_{mes_inicio_sel[:3].upper()}_"
            f"{mes_fin_sel[:3].upper()}.zip"
        )
        st.download_button(
            f"⬇️ Descargar ZIP ({cantidad} fichas)",
            data=zip_bytes,
            file_name=nombre_zip,
            mime="application/zip",
            use_container_width=True,
        )
    except Exception as exc:
        st.error(f"No se pudo generar el paquete de fichas: {exc}")
