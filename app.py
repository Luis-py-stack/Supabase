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
#st.markdown("""
#Esta interfaz funciona exclusivamente como un visor. **No almacena ni cachea datos en memoria**.
#Todas las lecturas y escrituras se hacen en tiempo real directamente hacia Supabase.
#""")

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
col_form, col_view = st.columns([1, 5.001], gap="large")

# ==========================================
# 2. Área de Carga / Modificación / Borrado
# ==========================================
with col_form:
    # Detección del estado de la pestaña para desbloquear edición solo en "Actualizar"
    soporta_tabs_dinamicos = True
    try:
        tab_insert, tab_update, tab_delete = st.tabs(
            ["➕ Insertar", "✏️ Actualizar", "🗑️ Eliminar"],
            key="active_tab",
            on_change="rerun"
        )
        modo_edicion = (st.session_state.get("active_tab") == "✏️ Actualizar") or getattr(tab_update, "open", False)
    except TypeError:
        # Fallback para entornos con versiones anteriores de Streamlit
        tab_insert, tab_update, tab_delete = st.tabs(["➕ Insertar", "✏️ Actualizar", "🗑️ Eliminar"])
        soporta_tabs_dinamicos = False
        modo_edicion = False

    # ----------------------------------------
    # PESTAÑA: INSERTAR (INTACTO)
    # ----------------------------------------
    with tab_insert:
        st.subheader("Nuevo Registro")
        with st.form("insert_form", clear_on_submit=True):
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

            st.markdown("<br>", unsafe_allow_html=True) 
            btn_submit = st.form_submit_button("Guardar en Supabase", type="primary", use_container_width=True)

            if btn_submit:
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
                try:
                    response = supabase.table(table_name).insert(data_to_insert).execute()
                    st.success(f"¡Datos insertados! (FOLIO: {input_folio})")
                except Exception as e:
                    st.error("Error al insertar los datos.")
                    st.error(f"Detalle técnico: {e}")

    # ----------------------------------------
    # PESTAÑA: ACTUALIZAR (DESBLOQUEA LA TABLA PRINCIPAL)
    # ----------------------------------------
    with tab_update:
        st.subheader("Modificar Registro")

        # Control adicional solo en caso de que la versión de Streamlit no sea reactiva en tabs
        if not soporta_tabs_dinamicos:
            modo_edicion = st.toggle("🔓 Desbloquear tabla para editar", value=False, key="toggle_unlock_table")

        if "update_success_msg" in st.session_state:
            st.success(st.session_state.pop("update_success_msg"))

        if modo_edicion:
            st.caption("🟢 **Tabla desbloqueada:** Edita o borra las celdas directamente en la tabla de la derecha y luego presiona el botón.")
        else:
            st.caption("🔒 La tabla está protegida. Entra en esta pestaña para habilitar su edición.")

        # Inspección del buffer de cambios de la tabla principal
        editor_version = st.session_state.get("editor_version", 0)
        editor_key = f"main_data_editor_{editor_version}"
        editor_state = st.session_state.get(editor_key, {})
        edited_rows = editor_state.get("edited_rows", {}) if isinstance(editor_state, dict) else getattr(editor_state, "edited_rows", {})

        num_cambios = len(edited_rows)
        if num_cambios > 0 and modo_edicion:
            st.info(f"✏️ Hay cambios listos en **{num_cambios}** fila(s).")
        else:
            st.caption("*(No hay cambios pendientes de guardar)*")

        st.markdown("<br>", unsafe_allow_html=True)
        btn_update = st.button("Actualizar en Supabase", type="primary", use_container_width=True)

        if btn_update:
            if not modo_edicion:
                st.warning("Debes estar en el modo 'Actualizar' para aplicar cambios.")
            elif not edited_rows:
                st.warning("No realizaste ningún cambio en las celdas de la tabla.")
            else:
                cached_data = st.session_state.get("cached_table_data")
                if not cached_data:
                    try:
                        res = supabase.table(table_name).select("*").order("FOLIO", desc=False).execute()
                        cached_data = res.data or []
                    except Exception:
                        cached_data = []

                actualizados = 0
                errores = []

                for r_idx, cambios in edited_rows.items():
                    idx = int(r_idx)
                    if 0 <= idx < len(cached_data):
                        folio_reg = cached_data[idx].get("FOLIO")
                        if folio_reg is not None:
                            update_payload = dict(cambios)
                            update_payload.pop("FOLIO", None)

                            # Conversión de seguridad para campo numérico DIAS
                            if "DIAS" in update_payload:
                                val_dias = update_payload["DIAS"]
                                if val_dias == "" or val_dias is None:
                                    update_payload["DIAS"] = None
                                else:
                                    try:
                                        update_payload["DIAS"] = int(val_dias)
                                    except (ValueError, TypeError):
                                        update_payload["DIAS"] = None

                            if update_payload:
                                try:
                                    supabase.table(table_name).update(update_payload).eq("FOLIO", folio_reg).execute()
                                    actualizados += 1
                                except Exception as e:
                                    errores.append(f"FOLIO {folio_reg}: {e}")

                if actualizados > 0 and not errores:
                    st.session_state["update_success_msg"] = f"¡Se actualizaron {actualizados} registro(s) en Supabase!"
                    st.session_state["editor_version"] = editor_version + 1
                    if hasattr(st, "rerun"):
                        st.rerun()
                    else:
                        st.experimental_rerun()
                elif actualizados > 0 and errores:
                    st.session_state["editor_version"] = editor_version + 1
                    st.warning(f"Se actualizaron {actualizados} registro(s), pero fallaron los siguientes:")
                    for err in errores:
                        st.error(err)
                    if hasattr(st, "rerun"):
                        st.rerun()
                    else:
                        st.experimental_rerun()
                else:
                    for err in errores:
                        st.error(f"Error al actualizar: {err}")

    # ----------------------------------------
    # PESTAÑA: ELIMINAR (INTACTO)
    # ----------------------------------------
    with tab_delete:
        st.subheader("Borrar Registro")
        with st.form("delete_form", clear_on_submit=True):
            delete_folio = st.text_input("🗑️ FOLIO a eliminar (Obligatorio)*")
            
            st.markdown("<br>", unsafe_allow_html=True)
            btn_delete = st.form_submit_button("Eliminar Definitivamente", type="primary", use_container_width=True)

            if btn_delete:
                if not delete_folio:
                    st.error("Debes ingresar el FOLIO que deseas eliminar.")
                else:
                    try:
                        response = supabase.table(table_name).delete().eq("FOLIO", delete_folio).execute()
                        if len(response.data) > 0:
                            st.success(f"¡El registro {delete_folio} ha sido eliminado!")
                        else:
                            st.warning(f"No se encontró el FOLIO: {delete_folio}")
                    except Exception as e:
                        st.error("Error al eliminar los datos.")
                        st.error(f"Detalle técnico: {e}")

# ==========================================
# 3. Vista de los Datos Existentes (BLOQUEADA / DESBLOQUEADA SEGÚN LA PESTAÑA)
# ==========================================
with col_view:
    st.subheader("📊 Vista de Datos (Tiempo Real)")

    try:
        response = supabase.table(table_name).select("*").order("FOLIO", desc=False).execute()
        datos_actuales = response.data

        if datos_actuales:
            st.session_state["cached_table_data"] = datos_actuales

            if modo_edicion:
                # MODO EDITABLE: Solo activo cuando se está en la pestaña "Actualizar"
                editor_version = st.session_state.get("editor_version", 0)
                editor_key = f"main_data_editor_{editor_version}"

                st.data_editor(
                    datos_actuales,
                    key=editor_key,
                    disabled=["FOLIO"],  # El FOLIO se mantiene como llave única inmutable
                    use_container_width=True,
                    height=1000
                )
                st.caption(f"✏️ Modo edición activo. Modifica celdas directamente en la tabla `{table_name}`.")
            else:
                # MODO SOLO LECTURA: Activo por defecto en "Insertar" o "Eliminar"
                st.dataframe(datos_actuales, use_container_width=True, height=1000)
                st.caption(f"Mostrando todos los registros de la tabla `{table_name}`. (Modo solo lectura)")
        else:
            st.info(f"La tabla `{table_name}` está conectada pero actualmente está vacía.")

    except Exception as e:
        st.error("Ocurrió un error al intentar leer los datos de Supabase.")
        st.error(f"Asegúrate de que la tabla '{table_name}' exista y las políticas RLS permitan lectura. Detalle: {e}")
