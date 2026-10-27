import csv
from decimal import Decimal
from cargar_csv import load_fixture, rows
from app.domain import DomainException, OrderItem, Money
from app.specifications import discount_rate

precios = {x["sku"]: Decimal(x["precio_mxn"]) for x in rows("productos.csv")}
escenarios = rows("escenarios.csv")
bitacora = []

def eventos(o):
    return [e.name for e in o.events] or "ninguno"

for esc in escenarios:
    caso, oid, accion = esc["caso_id"], esc["pedido_id"], esc["accion"]
    o = load_fixture()[oid]          # pedido fresco en DRAFT para cada caso
    inicial = o.status.value
    resultado = ""
    try:
        if accion == "evaluar_descuento":
            tasa = discount_rate(o)
            resultado = f"Descuento {int(tasa * 100)}% (total {o.total.amount}, {o.units} uds, VIP={o.customer.is_vip}, promo={o.has_promotion})"
        elif accion == "confirmar":
            o.confirm()
            resultado = "ÉXITO: confirmado"
        elif accion.startswith("agregar"):
            sku = "SKU003"
            o.add_item(OrderItem(sku, 2, Money(precios[sku])))
            resultado = "ÉXITO: artículo agregado"
        elif accion == "confirmar y enviar sin guia":
            o.confirm()
            o.ship("")
            resultado = "ÉXITO"
        elif accion == "confirmar dos veces":
            o.confirm()
            o.confirm()
            resultado = "ÉXITO"
        elif accion == "confirmar, enviar y cancelar":
            o.confirm(); o.ship("GUIA123"); o.cancel("Cliente lo solicitó")
            resultado = "ÉXITO"
        elif accion == "confirmar, enviar y devolver":
            o.confirm(); o.ship("GUIA123"); o.return_order()
            resultado = "ÉXITO: devuelto"
        elif accion == "confirmar, enviar y entregar":
            o.confirm(); o.ship("GUIA123"); o.deliver()
            resultado = "ÉXITO: entregado"
        else:
            resultado = f"ACCIÓN NO RECONOCIDA: {accion}"
    except DomainException as exc:
        resultado = f"RECHAZADO {type(exc).__name__}: {exc}"
    bitacora.append({
        "caso": caso, "pedido": oid, "estado_inicial": inicial,
        "operacion": accion, "esperado": esc["objetivo"],
        "resultado_real": resultado, "estado_final": o.status.value,
        "eventos": str(eventos(o)), "pista": esc["pista"],
    })

for b in bitacora:
    print(f'{b["caso"]} | {b["pedido"]} | {b["estado_inicial"]} -> {b["estado_final"]} | {b["operacion"]}')
    print(f'      esperado: {b["esperado"]} | real: {b["resultado_real"]}')
    print(f'      eventos: {b["eventos"]}')

with open("bitacora.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(bitacora[0].keys()))
    w.writeheader(); w.writerows(bitacora)
print("\nBitácora guardada en bitacora.csv")