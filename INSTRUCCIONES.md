# Guía salarial Selectron

## Archivos necesarios

- `app.py`
- `requirements.txt`
- `data/Base_Selectron_Normalizada.xlsx`

## Despliegue en Streamlit Community Cloud

1. Sube los tres elementos al repositorio privado de GitHub manteniendo la carpeta `data`.
2. En Streamlit, crea una nueva aplicación y selecciona `app.py` como archivo principal.
3. Despliega la aplicación y selecciona acceso público.

La aplicación no muestra registros individuales ni el número de candidatos empleado. Si una consulta no alcanza el umbral interno exigido, devuelve únicamente el mensaje de información insuficiente.
