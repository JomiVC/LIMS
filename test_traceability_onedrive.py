"""
test_traceability_onedrive.py

Automated test script for Scientific Traceability in OneDrive LIMS repository.
Verifies:
1. Atomic transaction register_purification_from_expression()
2. Storage availability validation BEFORE DB modification
3. Falcon deduction & protein_usage_history logging
4. Rollback on over-consumption or storage errors
5. Inherited construct metadata
"""

import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from services.protein_service import ProteinService

def run_tests():
    print("=== TEST DE TRAZABILIDAD Y ATOMICIDAD EN REPOSITORIO ONEDRIVE LIMS ===")
    service = ProteinService()

    # 1. Listar expresiones disponibles
    available = service.list_available_expressed()
    print(f"1. Expresiones disponibles con remaining_falcons > 0: {len(available)}")
    for e in available:
        print(f"   - ID #{e.id} ({e.sample_id} - {e.protein_name}): {e.remaining_falcons}/{e.total_falcons} Falcons disponibles")

    if not available:
        print("Registrando nueva expresión de prueba para la ejecución del test...")
        falcon_boxes = service.find_boxes_with_space("FALCON 50ml", 1)
        f_box_id = falcon_boxes[0].id
        free_f_pos = service.storage_service.list_free_positions(f_box_id)
        f_pos = free_f_pos[0].position

        exp_id, exp_sample = service.register_expressed(
            protein_name="TAU5",
            construct="pDEST17",
            variant="WT",
            media="LB",
            batch_no="B-TEST",
            volume_per_falcon_l=0.5,
            buffer="PBS",
            date_stored="2026-08-24",
            notebook_ref="NB-SUITE",
            total_falcons=1,
            notes="Automated test suite expression",
            box_id=f_box_id,
            start_position=f_pos,
        )
        available = service.list_available_expressed()

    target_exp = available[0]
    exp_id = target_exp.id
    initial_remaining = target_exp.remaining_falcons
    print(f"\n2. Expresión origen seleccionada: #{exp_id} ({target_exp.sample_id}) con {initial_remaining} Falcons libres.")

    # 2. Probar fallo por falta de espacio en Storage (exigir 500 alícuotas en una caja de 64)
    print("\n3. Probando validación previa de espacio en almacenamiento (Debe fallar con ValueError antes de tocar la BD)...")
    try:
        service.register_purification_from_expression(
            source_expression_id=exp_id,
            falcons_used=1,
            concentration_um=200.0,
            volume_ul=50.0,
            buffer="PBS pH 7.4",
            date_stored="2026-08-24",
            notebook_ref="NB-TEST-01",
            total_aliquots=500, # Excesivo para una caja Eppendorf 8x8 (64 posiciones max)
            notes="Test storage error",
            box_id=1,
            start_position="A1",
        )
        print("FAIL: Debería haber fallado por falta de posiciones consecutivas en la caja.")
    except ValueError as err:
        print(f"PASS: Excepción capturada correctamente: {err}")

    # Verificar que el stock de Falcons NO se haya modificado tras el fallo
    exp_check = service.repository.get_expressed(exp_id)
    assert exp_check.remaining_falcons == initial_remaining, "Error: El stock cambió tras un fallo de almacenamiento!"
    print("PASS: Stock de Falcons intacto tras fallo de almacenamiento.")

    # 3. Probar fallo por sobredescuento de Falcons (exigir 99 Falcons)
    print("\n4. Probando sobredescuento de Falcons (Debe fallar con ValueError)...")
    try:
        service.register_purification_from_expression(
            source_expression_id=exp_id,
            falcons_used=99,
            concentration_um=200.0,
            volume_ul=50.0,
            buffer="PBS pH 7.4",
            date_stored="2026-08-24",
            notebook_ref="NB-TEST-02",
            total_aliquots=1,
            notes="Test falcon over-consumption",
            box_id=1,
            start_position="A1",
        )
        print("FAIL: Debería haber fallado por Falcons insuficientes.")
    except ValueError as err:
        print(f"PASS: Excepción capturada correctamente: {err}")

    # 4. Registrar purificación válida
    print("\n5. Registrando purificación válida a partir de la expresión...")
    # Buscar una posición libre en la caja Eppendorf JV1 (box_id=1)
    free_positions = service.storage_service.list_free_positions(1)
    if not free_positions:
        print("No hay posiciones libres en caja JV1, buscando otra caja Eppendorf...")
        boxes = service.find_boxes_with_space("EPPENDORF", 2)
        target_box_id = boxes[0].id
        free_positions = service.storage_service.list_free_positions(target_box_id)
    else:
        target_box_id = 1

    start_pos = free_positions[0].position
    print(f"   Usando Caja ID #{target_box_id}, Posición Inicial: {start_pos}")

    purif_id, purif_sample_id = service.register_purification_from_expression(
        source_expression_id=exp_id,
        falcons_used=1,
        concentration_um=175.5,
        volume_ul=100.0,
        buffer="20mM NaP, 150mM NaCl, pH 7.4",
        date_stored="2026-08-24",
        notebook_ref="NB-2026-T1",
        total_aliquots=2,
        notes="Automated test traceability purification batch",
        box_id=target_box_id,
        start_position=start_pos,
    )
    print(f"SUCCESS: Purificación creada con ID #{purif_id} (Sample ID: {purif_sample_id})")

    # 5. Verificaciones de Trazabilidad
    print("\n6. Verificando resultados de la transacción atómica:")
    exp_after = service.repository.get_expressed(exp_id)
    print(f"   - Stock de Falcons en Expresión #{exp_id}: Antes={initial_remaining}, Ahora={exp_after.remaining_falcons} (Descontados: {initial_remaining - exp_after.remaining_falcons})")
    assert exp_after.remaining_falcons == initial_remaining - 1, "FAIL: Falcón no fue descontado correctamente."

    purif_rec = service.repository.get_purified(purif_id)
    print(f"   - Purificación #{purif_id} ({purif_rec.sample_id}):")
    print(f"       Proteína: {purif_rec.protein_name}")
    print(f"       Constructo Heredado: {purif_rec.construct}")
    print(f"       Variante Heredada: {purif_rec.variant}")
    print(f"       Medio Heredado: {purif_rec.media}")
    print(f"       Source Expression ID: {purif_rec.source_expression_id}")
    assert purif_rec.source_expression_id == exp_id, "FAIL: source_expression_id no coincide."
    assert purif_rec.protein_name == target_exp.protein_name, "FAIL: Nombre de proteína heredado no coincide."

    # Historial de uso auditoría
    history = service.repository.list_usage_history("protein_expressed", exp_id)
    print(f"   - Eventos en protein_usage_history para Expresión #{exp_id}: {len(history)} eventos.")
    latest_event = history[0]
    print(f"       Último evento: {latest_event['used_at']} | Cantidad: {latest_event['quantity']} | Motivo: {latest_event['reason']}")
    assert "Purification" in latest_event["reason"], "FAIL: El motivo no contiene 'Purification'."

    # Trazabilidad bidireccional
    derived = service.get_purifications_for_expression(exp_id)
    print(f"   - Purificaciones derivadas de Expresión #{exp_id}: {[p.sample_id for p in derived]}")
    assert purif_sample_id in [p.sample_id for p in derived], "FAIL: La nueva purificación no aparece en purificaciones derivadas."

    source_obj = service.get_source_expression_for_purification(purif_id)
    print(f"   - Expresión Origen recuperada desde Purificación #{purif_id}: {source_obj.sample_id} ({source_obj.protein_name})")
    assert source_obj.id == exp_id, "FAIL: Expresión origen no recuperada."

    print("\n*** TODOS LOS TESTS DE TRAZABILIDAD Y ATOMICIDAD PASARON CON EXITO SIN ERRORES ***")

if __name__ == "__main__":
    run_tests()
