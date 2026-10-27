import pytest
from decimal import Decimal
from app.domain import (Customer, InvalidOrderData, InvalidOrderTransition, Money, Order,
                        OrderItem, OrderItemLimitExceeded, OrderStatus)
from app.specifications import discount_rate
from cargar_csv import load_fixture


def pedido(vip=False, activo=True, promo=False, items=()):
    """Arma un pedido de prueba: items = [(sku, cantidad, precio), ...]"""
    o = Order(Customer("C-T", vip, activo), "T-1", promo)
    for sku, cant, precio in items:
        o.add_item(OrderItem(sku, cant, Money(Decimal(precio))))
    return o


def test_money_negativo():
    with pytest.raises(InvalidOrderData):
        Money(Decimal("-1"))


def test_pedido_o001_inicia_draft():
    orders = load_fixture()
    assert orders["O001"].status.value == "DRAFT"
    assert orders["O001"].units == 4
    assert orders["O001"].total.amount == Decimal("2100.00")


def test_21_unidades_rechazadas():
    o = pedido(items=[("SKU003", 20, "120.00")])
    with pytest.raises(OrderItemLimitExceeded):
        o.add_item(OrderItem("SKU003", 1, Money(Decimal("120.00"))))
    assert o.units == 20


def test_cliente_inactivo_no_confirma():
    o = pedido(activo=False, items=[("SKU001", 1, "600.00")])
    with pytest.raises(InvalidOrderData):
        o.confirm()
    assert o.status == OrderStatus.DRAFT
    assert o.events == []


def test_pedido_vacio_no_confirma():
    with pytest.raises(InvalidOrderData):
        pedido().confirm()


def test_descuento_vip_10():
    o = pedido(vip=True, items=[("SKU001", 4, "600.00")])
    assert discount_rate(o) == Decimal("0.10")


def test_promocion_activa_bloquea_descuento():
    o = pedido(vip=True, promo=True, items=[("SKU001", 4, "600.00")])
    assert discount_rate(o) == Decimal("0")


def test_500_exacto_no_descuenta():
    o = pedido(vip=True, items=[("SKU003", 4, "125.00")])
    assert discount_rate(o) == Decimal("0")


def test_enviar_sin_guia():
    o = pedido(items=[("SKU001", 1, "600.00")])
    o.confirm()
    with pytest.raises(InvalidOrderData):
        o.ship("")
    assert o.status == OrderStatus.CONFIRMED


def test_confirmacion_doble():
    o = pedido(items=[("SKU001", 1, "600.00")])
    o.confirm()
    with pytest.raises(InvalidOrderTransition):
        o.confirm()
    assert len(o.events) == 1


def test_cancelar_desde_shipped():
    o = pedido(items=[("SKU001", 1, "600.00")])
    o.confirm()
    o.ship("GUIA-1")
    with pytest.raises(InvalidOrderTransition):
        o.cancel("tarde")
    assert o.status == OrderStatus.SHIPPED