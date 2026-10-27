import pytest
from decimal import Decimal
from app.domain import (Money, OrderItem, InvalidOrderData, InvalidOrderTransition,
                        OrderItemLimitExceeded)
from app.specifications import ten_percent, five_percent
from cargar_csv import load_fixture


def test_money_negativo():
    with pytest.raises(InvalidOrderData):
        Money(Decimal("-1"))


def test_pedido_o001_inicia_draft():
    orders = load_fixture()
    assert orders["O001"].status.value == "DRAFT"
    assert orders["O001"].units == 4
    assert orders["O001"].total.amount == Decimal("2100.00")


def test_21_unidades_rechazadas():
    order = load_fixture()["O009"]            # tiene 19 unidades
    with pytest.raises(OrderItemLimitExceeded):
        order.add_item(OrderItem("SKU003", 2, Money(Decimal("120.00"))))
    assert order.units == 19


def test_cliente_inactivo_no_confirma():
    order = load_fixture()["O003"]
    with pytest.raises(InvalidOrderData):
        order.confirm()
    assert order.status.value == "DRAFT"
    assert order.events == []


def test_pedido_vacio_no_confirma():
    order = load_fixture()["O007"]
    with pytest.raises(InvalidOrderData):
        order.confirm()
    assert order.status.value == "DRAFT"


def test_descuento_vip_10():
    order = load_fixture()["O001"]
    assert ten_percent.is_satisfied_by(order)


def test_descuento_5_alternativo():
    order = load_fixture()["O006"]
    assert five_percent.is_satisfied_by(order)
    assert not ten_percent.is_satisfied_by(order)


def test_promocion_activa_bloquea_descuentos():
    order = load_fixture()["O005"]
    assert not ten_percent.is_satisfied_by(order)
    assert not five_percent.is_satisfied_by(order)


def test_enviar_sin_guia():
    order = load_fixture()["O012"]
    order.confirm()
    with pytest.raises(InvalidOrderData):
        order.ship("")
    assert order.status.value == "CONFIRMED"


def test_confirmacion_doble():
    order = load_fixture()["O013"]
    order.confirm()
    with pytest.raises(InvalidOrderTransition):
        order.confirm()
    assert len(order.events) == 1


def test_cancelar_desde_shipped():
    order = load_fixture()["O014"]
    order.confirm()
    order.ship("GUIA123")
    with pytest.raises(InvalidOrderTransition):
        order.cancel("Cliente lo solicitó")
    assert order.status.value == "SHIPPED"


def test_articulo_con_cantidad_invalida():
    with pytest.raises(InvalidOrderData):
        OrderItem("SKU001", 0, Money(Decimal("100.00")))


def test_flujo_entrega_registra_eventos():
    order = load_fixture()["O016"]
    order.confirm()
    order.ship("GUIA123")
    order.deliver()
    assert order.status.value == "DELIVERED"
    assert [e.name for e in order.events] == ["OrderConfirmed", "OrderShipped", "OrderDelivered"]


def test_flujo_devolucion_registra_eventos():
    order = load_fixture()["O015"]
    order.confirm()
    order.ship("GUIA123")
    order.return_order()
    assert order.status.value == "RETURNED"
    assert [e.name for e in order.events][-1] == "OrderReturned"


def test_cancelar_pedido_confirmado():
    order = load_fixture()["O001"]
    order.confirm()
    order.cancel("Cliente lo solicitó")
    assert order.status.value == "CANCELLED"
    assert [e.name for e in order.events] == ["OrderConfirmed", "OrderCancelled"]


def test_cancelar_sin_motivo():
    order = load_fixture()["O001"]
    order.confirm()
    with pytest.raises(InvalidOrderData):
        order.cancel("")
    assert order.status.value == "CONFIRMED"