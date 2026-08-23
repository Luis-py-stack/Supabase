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

st.title("Visor y Gestor de Datos")
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
table_name = st.sidebar.text_input("TABLE_NAME", value="Pantallas_De_Mcdonalds")

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
col_form, col_view = st.columns([1, 3], gap="large")

# ==========================================
# 2. Área de Carga / Inserción de Datos
# ==========================================
with col_form:
    st.subheader("➕ Insertar Nuevo Registro")

    # st.form agrupa los inputs y solo recarga la página al hacer submit
    with st.form("insert_form", clear_on_submit=True):
        
        # Creamos 2 sub-columnas dentro del formulario para ahorrar espacio vertical
        f_col1, f_col2 = st.columns(2)
        
        with f_col1:
            input_folio = st.text_input("FOLIO")
            input_cliente = st.text_input("CLIENTE")
            input_clasificacion = st.text_input("CLASIFICACION")
            input_f_visita = st.text_input("F_VISITA")
            input_f_entrega = st.text_input("F_ENTREGA")
            input_avance = st.text_input("AVANCE")
            
        with f_col2:
            input_area = st.text_input("AREA")
            input_concepto = st.text_input("CONCEPTO")
            input_vendedor = st.text_input("VENDEDOR")
            input_f_inicio = st.text_input("F_INICIO")
            input_dias = st.number_input("DIAS", step=1, value=0)

        st.markdown("<br>", unsafe_allow_html=True) # Un ligero respiro visual antes del botón
        
        # use_container_width=True hace que el botón abarque todo el ancho del formulario
        btn_submit = st.form_submit_button("Guardar en Supabase", type="primary", use_container_width=True)

        if btn_submit:
            # Construcción del payload (INTACTO)
            data_to_insert = {
                "FOLIO": input_folio,
                "AREA": input_area,
                "CLIENTE": input_cliente,
                "CONCEPTO": input_concepto,
                "CLASIFICACION": input_clasificacion,
                "VENDEDOR": input_vendedor,
                "F_VISITA": input_f_visita,
                "F_INICIO": input_f_inicio,
                "F_ENTREGA": input_f_entrega,
                "DIAS": input_dias,
                "AVANCE": input_avance
            }

            # Ejecución de la inserción y manejo de errores (INTACTO)
            try:
                response = supabase.table(table_name).insert(data_to_insert).execute()
                st.success(f"¡Datos insertados correctamente! (FOLIO: {input_folio})")
            except Exception as e:
                st.error("Ocurrió un error al insertar los datos.")
                st.error(f"Detalle técnico: {e}")
# ==========================================
# 3. Vista de los Datos Existentes
# ==========================================
with col_view:
    st.subheader("📊 Vista de Datos (Tiempo Real)")

    try:
        response = supabase.table(table_name).select("*").order("FOLIO", desc=False).execute()

        # Extraemos la data del response
        datos_actuales = response.data

        if datos_actuales:
            # ¡Aquí está el cambio! Añadimos height=800 (puedes ajustar este número)
            st.dataframe(datos_actuales, use_container_width=True, height=1000)
            st.caption(f"Mostrando todos los registros de la tabla `{table_name}`.")
        else:
            st.info(f"La tabla `{table_name}` está conectada pero actualmente está vacía.")

    except Exception as e:
        st.error("Ocurrió un error al intentar leer los datos de Supabase.")
        st.error(f"Asegúrate de que la tabla '{table_name}' exista y las políticas RLS permitan lectura. Detalle: {e}")
