import streamlit as st
from supabase import create_client, Client

# ==========================================
# Configuración de la página
# ==========================================
st.set_page_config(
    page_title="Visor y Gestor Supabase",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ Gestor de Base de Datos Supabase (Stateless)")
st.markdown("""
Esta interfaz funciona exclusivamente como un visor. **No almacena ni cachea datos en memoria**.
Todas las lecturas y escrituras se hacen en tiempo real directamente hacia Supabase.
""")

# ==========================================
# 1. Inputs de Configuración (Barra Lateral)
# ==========================================
st.sidebar.header("🔑 Configuración de Conexión")
supabase_url = st.sidebar.text_input("SUPABASE_URL", placeholder="https://xyz.supabase.co")
supabase_key = st.sidebar.text_input("SUPABASE_KEY", type="password", placeholder="sb_secret_...")
table_name = st.sidebar.text_input("TABLE_NAME", value="PRUEBA")

# Verificación de credenciales
if not supabase_url or not supabase_key or not table_name:
    st.info("👈 Por favor, ingresa tus credenciales de Supabase en la barra lateral para comenzar.")
    st.stop() # Detiene la ejecución hasta que haya credenciales

# ==========================================
# Inicialización del Cliente Supabase
# ==========================================
try:
    # Se inicializa el cliente en cada ejecución (stateless) usando los inputs actuales
    supabase: Client = create_client(supabase_url, supabase_key)
except Exception as e:
    st.error(f"Error al inicializar el cliente de Supabase: {e}")
    st.stop()

st.divider()

# Layout en dos columnas para mejor experiencia de usuario
col_form, col_view = st.columns([1, 2], gap="large")

# ==========================================
# 2. Área de Carga / Inserción de Datos
# ==========================================
with col_form:
    st.subheader("➕ Insertar Nuevo Registro")

    # st.form agrupa los inputs y solo recarga la página al hacer submit
    with st.form("insert_form", clear_on_submit=True):
        input_id = st.number_input("ID", min_value=1, step=1)
        input_prueba = st.text_input("Prueba (Ej. Nombre)")
        input_concepto = st.text_input("Concepto (Ej. Matemáticas)")
        input_tipo = st.text_input("Tipo (Ej. Híbrido)")

        btn_submit = st.form_submit_button("Guardar en Supabase", type="primary")

        if btn_submit:
            # Construcción del payload
            data_to_insert = {
                "id": input_id,
                "prueba": input_prueba,
                "concepto": input_concepto,
                "tipo": input_tipo
            }

            # Ejecución de la inserción y manejo de errores
            try:
                # Al ejecutar la inserción en el form, la vista lateral (col_view)
                # se actualizará automáticamente con el nuevo registro al volver a renderizar.
                response = supabase.table(table_name).insert(data_to_insert).execute()
                st.success(f"¡Datos insertados correctamente! (ID: {input_id})")
            except Exception as e:
                st.error("Ocurrió un error al insertar los datos.")
                st.error(f"Detalle técnico: {e}")

# ==========================================
# 3. Vista de los Datos Existentes
# ==========================================
with col_view:
    st.subheader("📊 Vista de Datos (Tiempo Real)")

    try:
        # Petición .select() directa en cada renderizado.
        # Esto garantiza la arquitectura stateless y lectura en tiempo real.
        # Se aplica un .limit(50) para proteger el rendimiento del frontend.
        response = supabase.table(table_name).select("*").order("id", desc=False).limit(100).execute()

        # Extraemos la data del response
        datos_actuales = response.data

        if datos_actuales:
            # Mostramos los datos en una tabla interactiva propia de Streamlit
            st.dataframe(datos_actuales, use_container_width=True)
            st.caption(f"Mostrando los últimos registros (Límite aplicado: 100) de la tabla `{table_name}`.")
        else:
            st.info(f"La tabla `{table_name}` está conectada pero actualmente está vacía.")

    except Exception as e:
        st.error("Ocurrió un error al intentar leer los datos de Supabase.")
        st.error(f"Asegúrate de que la tabla '{table_name}' exista y las políticas RLS permitan lectura. Detalle: {e}")
