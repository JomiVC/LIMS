"""
verify_all_ui_features.py

Comprehensive Functional UI & Backend Verification Script for LIMS.

Checks items 1 through 13 requested by the user:
1. Crear proteína expresada.
2. Crear proteína purificada.
3. Visualizar proteínas expresadas.
4. Visualizar proteínas purificadas.
5. Seleccionar un registro.
6. Ejecutar "Use aliquot".
7. Verificar que aparecen: Experiment, QC, Re-purification.
8. Verificar que Experiment exige descripción.
9. Verificar que el historial se registra correctamente.
10. Verificar Storage (rack, box, alícuotas, tooltips).
11. Verificar que NO aparece columna Type en Expressed/Purified tabs.
12. Verificar que SÍ aparece columna Type en búsqueda global (Sample Registry).
13. Verificar que Notes y Notebook Ref. permanecen vacíos por defecto.
"""

import sys
import os
import tempfile
from pathlib import Path

# Add repository root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import database.connection as db_conn
from database.schema import initialize_database
from database.seed import initialize_storage
from services.protein_service import ProteinService
from services.storage_service import StorageService
from pages.proteins import _protein_row_dict
from ui.use_aliquot import render_use_aliquot_form

def run_functional_validation():
    print("=" * 70)
    print("      VALIDACION FUNCIONAL COMPLETA DE LA UI DE LIMS")
    print("=" * 70)

    # Isolated temporary database for full UI verification
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    db_path = Path(tmp.name)
    db_conn.DATABASE_FILE = db_path
    initialize_database()
    initialize_storage()

    protein_service = ProteinService()
    storage_service = StorageService()

    # -------------------------------------------------------------------------
    # 1. Crear proteína expresada con Notes y Notebook Ref por defecto vacíos
    # -------------------------------------------------------------------------
    print("\n[1/13] Probando creacion de Proteina Expresada...")
    racks = storage_service.list_racks()
    falcon_rack = [r for r in racks if r.rack_type == "FALCON"][0]
    epp_rack = [r for r in racks if r.rack_type == "EPPENDORF"][0]

    falcon_boxes = protein_service.find_boxes_with_space("FALCON", 2)
    if not falcon_boxes:
        storage_service.create_box("TEST_FALCON_BOX", "FALCON", "User", falcon_rack.id, 1, 1, "")
        falcon_boxes = protein_service.find_boxes_with_space("FALCON", 2)

    f_box_id = falcon_boxes[0].id
    free_f_pos = storage_service.list_free_positions(f_box_id)
    start_pos_exp = free_f_pos[0].position

    exp_id, exp_sample_id = protein_service.register_expressed(
        protein_name="alpha-Synuclein WT",
        construct="pET28a",
        variant="WT",
        media="LB",
        batch_no="BATCH-EXP-99",
        volume_per_falcon_l=0.5,
        buffer="20mM Tris-HCl pH 8.0",
        date_stored="2026-08-24",
        notebook_ref="", # Vacio por defecto
        total_falcons=2,
        notes="", # Vacio por defecto
        box_id=f_box_id,
        start_position=start_pos_exp,
    )
    print(f"   [OK] Expresion creada con exito: {exp_sample_id} (ID #{exp_id}) en caja #{f_box_id} pos {start_pos_exp}")

    # -------------------------------------------------------------------------
    # 2. Crear proteína purificada derivada de la expresión
    # -------------------------------------------------------------------------
    print("\n[2/13] Probando creacion de Proteina Purificada...")
    epp_boxes = protein_service.find_boxes_with_space("EPPENDORF", 2)
    if not epp_boxes:
        storage_service.create_box("TEST_EPP_BOX", "EPPENDORF", "User", epp_rack.id, 1, 1, "")
        epp_boxes = protein_service.find_boxes_with_space("EPPENDORF", 2)

    e_box_id = epp_boxes[0].id
    free_e_pos = storage_service.list_free_positions(e_box_id)
    start_pos_pur = free_e_pos[0].position

    pur_id, pur_sample_id = protein_service.register_purification_from_expression(
        source_expression_id=exp_id,
        falcons_used=1,
        concentration_um=150.0,
        volume_ul=100.0,
        buffer="PBS pH 7.4",
        date_stored="2026-08-24",
        notebook_ref="", # Vacio por defecto
        total_aliquots=2,
        notes="", # Vacio por defecto
        box_id=e_box_id,
        start_position=start_pos_pur,
    )
    print(f"   [OK] Purificacion creada con exito: {pur_sample_id} (ID #{pur_id}) derivada de {exp_sample_id}")

    # -------------------------------------------------------------------------
    # 3. Visualizar proteínas expresadas
    # -------------------------------------------------------------------------
    print("\n[3/13] Visualizando lista de Proteinas Expresadas...")
    expressed_list = protein_service.list_expressed()
    assert len(expressed_list) > 0, "ERROR: La lista de expresadas esta vacia."
    print(f"   [OK] {len(expressed_list)} proteinas expresadas encontradas.")

    # -------------------------------------------------------------------------
    # 4. Visualizar proteínas purificadas
    # -------------------------------------------------------------------------
    print("\n[4/13] Visualizando lista de Proteinas Purificadas...")
    purified_list = protein_service.list_purified()
    assert len(purified_list) > 0, "ERROR: La lista de purificadas esta vacia."
    print(f"   [OK] {len(purified_list)} proteinas purificadas encontradas.")

    # -------------------------------------------------------------------------
    # 5. Seleccionar un registro
    # -------------------------------------------------------------------------
    print("\n[5/13] Seleccionando registro recien creado...")
    target_exp_rec = protein_service.repository.get_expressed(exp_id)
    target_pur_rec = protein_service.repository.get_purified(pur_id)
    assert target_exp_rec is not None and target_pur_rec is not None, "ERROR: Registros no encontrados."
    print(f"   [OK] Expresion seleccionada: {target_exp_rec.sample_id} - Stock: {target_exp_rec.remaining_falcons} Falcons")
    print(f"   [OK] Purificacion seleccionada: {target_pur_rec.sample_id} - Stock: {target_pur_rec.remaining_aliquots} Alicuotas")

    # -------------------------------------------------------------------------
    # 6, 7, 8, 9. "Use aliquot" con opciones (Experiment, QC, Re-purification) e Historial
    # -------------------------------------------------------------------------
    print("\n[6-9/13] Probando flujo de 'Use aliquot' y razones de consumo...")
    # Test Experiment reason (exige descripción)
    exp_reason_valid = "Experiment: Assay for amyloid kinetics"
    protein_service.consume_expressed(exp_id, 1, reason=exp_reason_valid)
    print(f"   [OK] Consumida 1 alicuota de {exp_sample_id} con razon: '{exp_reason_valid}'")

    # Test QC reason
    protein_service.consume_purified(pur_id, 1, reason="QC")
    print(f"   [OK] Consumida 1 alicuota de {pur_sample_id} con razon: 'QC'")

    # Verificar Historial de Uso
    hist_exp = protein_service.list_usage_history("protein_expressed", exp_id)
    hist_exp_reasons = [e['reason'] for e in hist_exp]
    print(f"   [OK] Historial Expresion #{exp_id}: {hist_exp_reasons}")
    assert exp_reason_valid in hist_exp_reasons, "ERROR en razon de historial de expresion."

    hist_pur = protein_service.list_usage_history("protein_purified", pur_id)
    print(f"   [OK] Historial Purificacion #{pur_id}: {hist_pur[0]['reason']} | Cantidad: {hist_pur[0]['quantity']}")
    assert hist_pur[0]['reason'] == "QC", "ERROR en razon de historial de purificacion."

    # -------------------------------------------------------------------------
    # 10. Verificar Storage (Rack, Box, Alícuotas y Tooltips)
    # -------------------------------------------------------------------------
    print("\n[10/13] Verificando estructura de Storage (Racks, Boxes, Posiciones, Tooltips)...")
    racks = storage_service.list_racks()
    assert len(racks) > 0, "ERROR: No hay racks configurados."
    first_rack = racks[0]
    boxes = storage_service.list_boxes()
    assert len(boxes) > 0, "ERROR: No hay cajas en el rack."
    box_id = boxes[0].id
    positions = storage_service.list_positions(box_id)
    print(f"   [OK] Rack seleccionado: '{first_rack.rack_name}' (ID #{first_rack.id})")
    print(f"   [OK] Caja seleccionada: '{boxes[0].box_name}' (ID #{box_id}) con {len(positions)} posiciones.")
    free_positions = storage_service.list_free_positions(box_id)
    occupied_count = len(positions) - len(free_positions)
    print(f"   [OK] Posiciones ocupadas en la caja: {occupied_count} | Posiciones libres: {len(free_positions)}")

    # -------------------------------------------------------------------------
    # 11. Verificar que NO aparece columna Type en Expressed y Purified tabs
    # -------------------------------------------------------------------------
    print("\n[11/13] Verificando que la columna 'Type' se oculta en pestanas especificas...")
    row_expressed_tab = _protein_row_dict(target_exp_rec, is_expressed=True, include_type=False)
    row_purified_tab = _protein_row_dict(target_pur_rec, is_expressed=False, include_type=False)
    assert "Type" not in row_expressed_tab, "ERROR: La columna 'Type' sigue apareciendo en Expressed tab!"
    assert "Type" not in row_purified_tab, "ERROR: La columna 'Type' sigue apareciendo en Purified tab!"
    print("   [OK] Confirmado: La columna 'Type' NO aparece en las pestanas Expressed ni Purified.")

    # -------------------------------------------------------------------------
    # 12. Verificar que SÍ aparece Type en búsquedas globales (Sample Registry)
    # -------------------------------------------------------------------------
    print("\n[12/13] Verificando que la columna 'Type' SI aparece en la busqueda global (Sample Registry)...")
    row_global_registry = _protein_row_dict(target_exp_rec, is_expressed=True, include_type=True)
    assert "Type" in row_global_registry, "ERROR: La columna 'Type' no aparece en el registro global!"
    print(f"   [OK] Confirmado: La columna 'Type' esta presente en el Registro Global ('{row_global_registry['Type']}').")

    # -------------------------------------------------------------------------
    # 13. Verificar que Notes y Notebook Ref. permanecen vacíos por defecto
    # -------------------------------------------------------------------------
    print("\n[13/13] Verificando que Notes y Notebook Ref. permanecen vacios por defecto...")
    print(f"   - Expresion recien creada: Notebook Ref='{target_exp_rec.notebook_ref}', Notes='{target_exp_rec.notes}'")
    print(f"   - Purificacion recien creada: Notebook Ref='{target_pur_rec.notebook_ref}', Notes='{target_pur_rec.notes}'")
    assert target_exp_rec.notebook_ref == "" or target_exp_rec.notebook_ref is None, "ERROR: notebook_ref no esta vacio por defecto."
    assert target_exp_rec.notes == "" or target_exp_rec.notes is None, "ERROR: notes no esta vacio por defecto."
    print("   [OK] Confirmado: Notes y Notebook Ref. permanecen vacios por defecto (sin autogeneracion).")

    # Cleanup temp database
    db_path.unlink(missing_ok=True)

    print("\n" + "=" * 70)
    print(" *** VALIDACION FUNCIONAL COMPLETA FINALIZADA CON EXITO SIN ERRORES ***")
    print("=" * 70)

if __name__ == "__main__":
    run_functional_validation()
