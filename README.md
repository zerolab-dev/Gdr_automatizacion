# GDR Automatización

Aplicativo Streamlit para generar fichas GDR por CITE.

## Archivos fijos en el repositorio

- `templates/plantilla_gdr.xlsx`: plantilla oficial con las hojas `GDR` y `UP INDICADOR 1`.
- `data/metas_gdr.xlsx`: metas de los tres indicadores por CITE.

## Archivos que carga el usuario

1. Consolidado de indicadores (`.xlsx`).
2. Listado de UP del Indicador 1 (`.xlsx`).

Los nombres de CITE deben coincidir exactamente entre el consolidado, el archivo de metas y el listado UP.

## Reglas principales

- La meta se escribe en la columna G.
- Enero-Diciembre se escriben en H:S.
- El valor alcanzado se escribe en T.
- El avance se calcula para Indicadores 1 y 2 como `alcanzado/meta` y se escribe en U.
- El Indicador 3 no muestra avance; U9:U10 permanece vacío y conserva el formato plomo de la plantilla.
- La hoja `UP INDICADOR 1` se llena desde la fila 4 conservando los estilos alternados de la plantilla.
- Se valida que el número de registros del listado UP coincida con el valor alcanzado del Indicador 1 para el periodo seleccionado.
