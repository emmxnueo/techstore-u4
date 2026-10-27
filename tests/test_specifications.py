from app.specifications import (ten_percent, five_percent, any_discount, confirmable,
                                ActivePromotionSpec)
from cargar_csv import load_fixture


def test_and_exige_todas_las_condiciones():
    order = load_fixture()["O011"]            # VIP y total > 500, pero solo 3 unidades
    assert not ten_percent.is_satisfied_by(order)


def test_or_cumple_si_basta_una():
    orders = load_fixture()
    assert any_discount.is_satisfied_by(orders["O001"])   # solo cumple la de 10 %
    assert any_discount.is_satisfied_by(orders["O006"])   # solo cumple la de 5 %


def test_or_falla_si_no_cumple_ninguna():
    assert not any_discount.is_satisfied_by(load_fixture()["O002"])


def test_not_invierte_el_resultado():
    order = load_fixture()["O005"]            # tiene promoción activa
    assert ActivePromotionSpec().is_satisfied_by(order)
    assert not (~ActivePromotionSpec()).is_satisfied_by(order)


def test_pedido_confirmable():
    orders = load_fixture()
    assert confirmable.is_satisfied_by(orders["O001"])
    assert not confirmable.is_satisfied_by(orders["O007"])   # sin artículos
    assert not confirmable.is_satisfied_by(orders["O003"])   # cliente inactivo


def test_specification_no_modifica_el_pedido():
    order = load_fixture()["O001"]
    ten_percent.is_satisfied_by(order)
    assert order.status.value == "DRAFT"
    assert order.events == []
    assert order.units == 4