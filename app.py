import os
from datetime import datetime

import pandas as pd
import streamlit as st

from config import MESES_UI, TEMPLATE_PATH
from validators import validar_datos_entrada
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

if not os.path.exists(TEMPLATE_PATH):
    st.error(
        "No se encontró la plantilla oficial. Coloque el archivo "
        "`plantilla_gdr.xlsx` dentro de la carpeta `templates`."
    )
    st.stop()

if "df_cargado" not in st.session_state:
    st.session_state.df_cargado = None
if "mes_sugerido" not in st.session_state:
    st.session_state.mes_sugerido = "Enero"
if "archivo_actual" not in st.session_state:
    st.session_state.archivo_actual = None

st.header("Paso 1: Cargar información")
archivo_subido = st.file_uploader(
    "Cargar archivo de resultados maestros (.xlsx)",
    type=["xlsx"],
)

if archivo_subido is not None:
    if st.session_state.archivo_actual != archivo_subido.name:
        try:
            df = pd.read_excel(archivo_subido)
            df.columns = df.columns.astype(str).str.strip()
            es_valido, mensaje, advertencias = validar_datos_entrada(df)

            if es_valido:
                st.session_state.df_cargado = df
                st.session_state.mes_sugerido = sugerir_mes_final(df)
                st.session_state.archivo_actual = archivo_subido.name
                st.session_state.advertencias = advertencias
            else:
                st.session_state.df_cargado = None
                st.error(mensaje)
        except Exception as exc:
            st.session_state.df_cargado = None
            st.error(f"No se pudo leer el Excel: {exc}")

if st.session_state.df_cargado is not None:
    df = st.session_state.df_cargado
    st.success("Archivo validado correctamente.")

    advertencias = st.session_state.get("advertencias", [])
    if advertencias:
        with st.expander(f"⚠️ Advertencias de calidad ({len(advertencias)})"):
            for adv in advertencias:
                st.warning(adv)

    unidades = [str(x).strip() for x in df["cite_ut"].dropna().unique()]
    cites = sorted([x for x in unidades if x != "0NACIONAL"])
    tiene_nacional = "0NACIONAL" in unidades

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f"<div class='metric-card'><b>Archivo</b><br>{st.session_state.archivo_actual}</div>",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"<div class='metric-card'><b>Unidades detectadas</b><br>"
            f"{len(unidades)} ({len(cites)} CITE/UT)</div>",
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"<div class='metric-card'><b>Periodo sugerido hasta</b><br>"
            f"{st.session_state.mes_sugerido}</div>",
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
        idx_sugerido = MESES_UI.index(st.session_state.mes_sugerido)
        mes_fin_sel = st.selectbox("Periodo hasta", MESES_UI, index=idx_sugerido)

    opciones = ["Todos los CITE/UT"]
    if tiene_nacional:
        opciones.append("NACIONAL")
    opciones.extend(cites)

    with f4:
        cite_ui = st.selectbox("CITE/UT", opciones)

    cite_real = (
        "TODOS" if cite_ui == "Todos los CITE/UT"
        else "0NACIONAL" if cite_ui == "NACIONAL"
        else cite_ui
    )

    if MESES_UI.index(mes_inicio_sel) > MESES_UI.index(mes_fin_sel):
        st.error("El mes inicial no puede ser posterior al mes final.")
        st.stop()

    st.divider()
    st.header("Paso 3: Vista previa")

    cite_preview = cites[0] if cite_real == "TODOS" and cites else (
        "0NACIONAL" if cite_real == "TODOS" else cite_real
    )
    if not cite_preview:
        st.error("No existen unidades disponibles para mostrar.")
        st.stop()

    nombre_mostrar = "NACIONAL" if cite_preview == "0NACIONAL" else cite_preview
    st.markdown(f"**Vista previa:** {nombre_mostrar} — {anio_sel}")

    try:
        df_preview, alertas = procesar_datos_por_cite(
            df, cite_preview, anio_sel, mes_inicio_sel, mes_fin_sel
        )
        vista = df_preview.copy()
        # Solo para visualización: mostrar porcentajes de forma amigable.
        mask_pct = vista["Indicador"] == "Indicador 3"
        if mask_pct.any():
            idx = vista.index[
                mask_pct & (vista["Variable"] == "Número de encuestas respondidas")
            ]
            if len(idx) == 1 and isinstance(vista.at[idx[0], "Valor Alcanzado"], (int, float)):
                vista.at[idx[0], "Valor Alcanzado"] = f"{vista.at[idx[0], 'Valor Alcanzado']:.2%}"
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
                    df, cite_real, anio_sel, mes_inicio_sel, mes_fin_sel
                )
                nombre_archivo = (
                    f"GDR_{normalizar_nombre_archivo(nombre_mostrar).upper()}_"
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
        incluir_nacional = st.checkbox(
            "Incluir ficha Nacional",
            value=True,
            disabled=not tiene_nacional,
        )
        try:
            zip_bytes, cantidad = generar_zip_todas_las_fichas(
                df, anio_sel, mes_inicio_sel, mes_fin_sel, incluir_nacional
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
