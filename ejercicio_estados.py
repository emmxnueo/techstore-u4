from cargar_csv import load_fixture
from app.domain import DomainException

orders = load_fixture()
order = orders["O013"]
print("Inicio:", order.status.value, order.units, order.total.amount)

order.confirm()
print("1er confirm:", order.status.value, [e.name for e in order.events])

try:
    order.confirm()
except DomainException as exc:
    print("2do confirm RECHAZADO:", type(exc).__name__, "-", exc)
print("Después:", order.status.value, [e.name for e in order.events])