"""
app.py

Main entry point for the Laboratory Information Management System (LIMS).
"""

import streamlit as st

st.set_page_config(
    page_title="LIMS",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🧪 Laboratory Information Management System")

st.markdown(
    """
Bienvenido al nuevo **LIMS**.

Este sistema permitirá gestionar:

- 📦 Almacenamiento de muestras
- 🧬 ADN
- 🧫 Proteínas
- 🧪 Reactivos
- 📋 Pedidos
- 👥 Usuarios

Selecciona un módulo desde el menú lateral para comenzar.
"""
)

st.divider()

st.subheader("Estado del proyecto")

st.success("✔ Base de datos SQLite creada")
st.success("✔ Arquitectura del proyecto creada")
st.success("✔ Storage Engine implementado")

st.info("Siguiente objetivo: Registro y gestión de cajas de almacenamiento.")