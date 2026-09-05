import streamlit as st
import pandas as pd
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

# ==========================================
# 1. Conexión y Gestión de Credenciales (Producción)
# ==========================================
# Cargar secretos si existen, o usar inputs como fallback
default_url = st.secrets.get("SUPABASE_URL", "") if "SUPABASE_URL" in st.secrets else ""
default_key = st.secrets.get("SUPABASE_KEY", "") if "SUPABASE_KEY" in st.secrets else ""
default_table = st.secrets.get("TABLE_NAME", "Pantallas_De_Mcdonalds") if "TABLE_NAME" in st.secrets else "Pantallas_De_Mcdonalds"

st.sidebar.header("🔑 Configuración de Conexión")
supabase_url = st.sidebar.text_input("SUPABASE_URL", value=default_url, placeholder="https://xyz.supabase.co")
supabase_key = st.sidebar.text_input("SUPABASE_KEY", value=default_key, type="password", placeholder="sb_secret_...")
table_name = st.sidebar.text_input("TABLE_NAME", value=default_table)

if not supabase_url or not supabase_key or not table_name:
    st.info("👈 Ingresa las credenciales de Supabase en la barra lateral o configúralas en secrets.toml para comenzar.")
    st.stop()

# Inicialización cacheada del cliente para alta concurrencia
@st.cache_resource(show_spinner=False)
def init_supabase_client(url: str, key: str) -> Client:
    return create_client(url, key)

try:
    supabase: Client = init_supabase_client(supabase_url, supabase_key)
except Exception as e:
    st.error(f"Error crítico al inicializar el cliente de Supabase: {e}")
    st.stop()

# Helper para normalizar strings vacíos a NULL en base de datos
def clean_input(val):
    if isinstance(val, str):
        val_s = val.strip()
        return val_s if val_s != "" else None
    return val

st.divider()

col_form, col_view = st.columns([1, 5.001], gap="large")

# ==========================================
# 2. Área de Formularios y Acciones
# ==========================================
with col_form:
    soporta_tabs_dinamicos = True
    try:
        tab_insert, tab_update, tab_delete = st.tabs(
            ["➕ Insertar", "✏️ Actualizar", "🗑️ Eliminar"],
            key="active_tab",
            on_change="rerun"
        )
        active_tab_val = st.session_state.get("active_tab")
        modo_edicion = (active_tab_val == "✏️ Actualizar") or getattr(tab_update, "open", False)
        modo_eliminar = (active_tab_val == "🗑️ Eliminar") or getattr(tab_delete, "open", False)
    except TypeError:
        tab_insert, tab_update, tab_delete = st.tabs(["➕ Insertar", "✏️ Actualizar", "🗑️ Eliminar"])
        soporta_tabs_dinamicos = False
        modo_edicion = False
        modo_eliminar = False

    # ----------------------------------------
    # PESTAÑA: INSERTAR
    # ----------------------------------------
    with tab_insert:
        st.subheader("Nuevo Registro")
        with st.form("insert_form", clear_on_submit=True):
            f_col1, f_col2 = st.columns(2)
            
            with f_col1:
                input_folio = st.text_input("FOLIO (Obligatorio)*")
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
                if not clean_input(input_folio):
                    st.error("El campo FOLIO es obligatorio para crear el registro.")
                else:
                    data_to_insert = {
                        "FOLIO": clean_input(input_folio),
                        "AREA": clean_input(input_area),
                        "CLIENTE": clean_input(input_cliente),
                        "CONCEPTO": clean_input(input_concepto),
                        "CLASIFICACION": clean_input(input_clasificacion),
                        "VENDEDOR": clean_input(input_vendedor),
                        "F_VISITA": clean_input(input_f_visita),
                        "F_INICIO": clean_input(input_f_inicio),
                        "F_ENTREGA": clean_input(input_f_entrega),
                        "DIAS": int(input_dias),
                        "AVANCE": clean_input(input_avance)
                    }
                    try:
                        response = supabase.table(table_name).insert(data_to_insert).execute()
                        st.success(f"¡Registro insertado con éxito! (FOLIO: {input_folio})")
                        st.session_state["editor_version"] = st.session_state.get("editor_version", 0) + 1
                    except Exception as e:
                        st.error(f"Error al insertar en la base de datos: {e}")

    # ----------------------------------------
    # PESTAÑA: ACTUALIZAR
    # ----------------------------------------
    with tab_update:
        st.subheader("Modificar Registro")

        if not soporta_tabs_dinamicos:
            modo_edicion = st.toggle("🔓 Desbloquear tabla para editar", value=False, key="toggle_unlock_table")

        if "update_success_msg" in st.session_state:
            st.success(st.session_state.pop("update_success_msg"))

        if modo_edicion:
            st.caption("🟢 **Modo edición activo:** Edita o vacía cualquier celda en la tabla y presiona el botón para sincronizar.")
        else:
            st.caption("🔒 La tabla está protegida. Entra en esta pestaña para habilitar su edición.")

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
                st.warning("Debes encontrarte en la pestaña 'Actualizar' para aplicar los cambios.")
            elif not edited_rows:
                st.warning("No has modificado ninguna celda en la tabla.")
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
                            update_payload = {}
                            for col_name, val in cambios.items():
                                if col_name == "FOLIO":
                                    continue
                                if col_name == "DIAS":
                                    if val == "" or val is None:
                                        update_payload["DIAS"] = None
                                    else:
                                        try:
                                            update_payload["DIAS"] = int(val)
                                        except (ValueError, TypeError):
                                            update_payload["DIAS"] = None
                                else:
                                    update_payload[col_name] = clean_input(val)

                            if update_payload:
                                try:
                                    supabase.table(table_name).update(update_payload).eq("FOLIO", folio_reg).execute()
                                    actualizados += 1
                                except Exception as e:
                                    errores.append(f"FOLIO {folio_reg}: {e}")

                if actualizados > 0 and not errores:
                    st.session_state["update_success_msg"] = f"¡Se sincronizaron {actualizados} registro(s) en Supabase!"
                    st.session_state["editor_version"] = editor_version + 1
                    if hasattr(st, "rerun"):
                        st.rerun()
                    else:
                        st.experimental_rerun()
                elif actualizados > 0 and errores:
                    st.session_state["editor_version"] = editor_version + 1
                    st.warning(f"Se actualizaron {actualizados} registro(s), pero ocurrieron fallos:")
                    for err in errores:
                        st.error(err)
                    if hasattr(st, "rerun"):
                        st.rerun()
                    else:
                        st.experimental_rerun()
                else:
                    for err in errores:
                        st.error(f"Fallo al actualizar: {err}")

    # ----------------------------------------
    # PESTAÑA: ELIMINAR
    # ----------------------------------------
    with tab_delete:
        st.subheader("Borrar Registro")

        if not soporta_tabs_dinamicos:
            modo_eliminar = st.toggle("🔓 Desbloquear modo eliminación", value=False, key="toggle_unlock_delete")

        if "delete_success_msg" in st.session_state:
            st.success(st.session_state.pop("delete_success_msg"))

        if modo_eliminar:
            st.caption("🔴 **Modo eliminación activo:** Marca la casilla a la izquierda de cada fila que deseas borrar y confirma abajo.")
        else:
            st.caption("🔒 La tabla está protegida. Entra en esta pestaña para habilitar el borrado.")

        delete_version = st.session_state.get("delete_version", 0)
        delete_key = f"main_delete_selector_{delete_version}"
        delete_state = st.session_state.get(delete_key, {})

        if isinstance(delete_state, dict):
            selected_indices = delete_state.get("selection", {}).get("rows", [])
        else:
            sel_obj = getattr(delete_state, "selection", {})
            selected_indices = sel_obj.get("rows", []) if isinstance(sel_obj, dict) else getattr(sel_obj, "rows", [])

        cached_data = st.session_state.get("cached_table_data")
        if not cached_data:
            try:
                res = supabase.table(table_name).select("*").order("FOLIO", desc=False).execute()
                cached_data = res.data or []
                st.session_state["cached_table_data"] = cached_data
            except Exception:
                cached_data = []

        folios_a_eliminar = []
        for idx in selected_indices:
            idx_int = int(idx)
            if 0 <= idx_int < len(cached_data):
                f = cached_data[idx_int].get("FOLIO")
                if f is not None:
                    folios_a_eliminar.append(f)

        num_seleccionados = len(folios_a_eliminar)
        if num_seleccionados > 0 and modo_eliminar:
            st.warning(f"⚠️ Filas marcadas para borrado definitivo ({num_seleccionados}):")
            st.write(", ".join([f"`{f}`" for f in folios_a_eliminar]))
        else:
            st.caption("*(No hay filas seleccionadas para eliminar)*")

        st.markdown("<br>", unsafe_allow_html=True)
        btn_delete = st.button("Confirmar Eliminación Definitivamente", type="primary", use_container_width=True)

        if btn_delete:
            if not modo_eliminar:
                st.warning("Debes encontrarte en la pestaña 'Eliminar' para confirmar el borrado.")
            elif not folios_a_eliminar:
                st.warning("No seleccionaste ninguna fila para eliminar.")
            else:
                try:
                    if len(folios_a_eliminar) == 1:
                        supabase.table(table_name).delete().eq("FOLIO", folios_a_eliminar[0]).execute()
                    else:
                        supabase.table(table_name).delete().in_("FOLIO", folios_a_eliminar).execute()

                    st.session_state["delete_success_msg"] = f"¡Se eliminaron {len(folios_a_eliminar)} registro(s) de Supabase!"
                    st.session_state["delete_version"] = delete_version + 1
                    st.session_state["editor_version"] = st.session_state.get("editor_version", 0) + 1
                    st.session_state.pop(delete_key, None)

                    if hasattr(st, "rerun"):
                        st.rerun()
                    else:
                        st.experimental_rerun()
                except Exception as e:
                    st.error(f"Error al eliminar registros: {e}")

# ==========================================
# 3. Vista de Datos Principal (Reactiva)
# ==========================================
with col_view:
    st.subheader("📊 Vista de Datos (Tiempo Real)")

    try:
        # Límite amplio explícito para evitar truncado silencioso de 1000 registros por defecto
        response = supabase.table(table_name).select("*").order("FOLIO", desc=False).limit(5000).execute()
        datos_actuales = response.data

        if datos_actuales:
            st.session_state["cached_table_data"] = datos_actuales

            if modo_edicion:
                editor_version = st.session_state.get("editor_version", 0)
                editor_key = f"main_data_editor_{editor_version}"

                st.data_editor(
                    datos_actuales,
                    key=editor_key,
                    disabled=["FOLIO"],
                    use_container_width=True,
                    height=1000
                )
                st.caption(f"✏️ Modo edición activo. Modifica celdas directamente en la tabla `{table_name}`.")

            elif modo_eliminar:
                delete_version = st.session_state.get("delete_version", 0)
                delete_key = f"main_delete_selector_{delete_version}"

                st.dataframe(
                    datos_actuales,
                    key=delete_key,
                    on_select="rerun",
                    selection_mode="multi-row",
                    use_container_width=True,
                    height=1000
                )
                st.caption(f"🗑️ Modo eliminación activo. Marca las casillas de las filas que deseas borrar en `{table_name}`.")

            else:
                st.dataframe(datos_actuales, use_container_width=True, height=1000)
                st.caption(f"Mostrando todos los registros de `{table_name}`. (Modo solo lectura)")
        else:
            st.info(f"La tabla `{table_name}` está conectada pero actualmente está vacía.")

    except Exception as e:
        st.error("Ocurrió un error al leer los datos de Supabase.")
        st.error(f"Verifica que la tabla exista y las políticas RLS permitan lectura/escritura. Detalle: {e}")
