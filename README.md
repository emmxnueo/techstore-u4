# TechStore U4: núcleo de negocio de pedidos

Práctica guiada de la Unidad 4 (Componentes de Lógica de Negocio, FIME-UANL).
Implementa en Python el dominio de pedidos de una tienda ficticia: Value Objects,
entidad Order con máquina de estados, reglas de descuento con Specification Pattern,
Domain Events y una API REST con FastAPI. No usa base de datos: los pedidos se cargan
desde CSV y se mantienen en memoria.

**Integrantes:** (escribe aquí los nombres del equipo)

## Instalación

Requiere Python 3.11 o superior.

```
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install fastapi uvicorn pytest httpx
```

## Ejecución

Cargar los 16 pedidos de ejemplo:

```
python cargar_csv.py
```

Ejecutar los 15 escenarios (genera `bitacora.csv`):

```
python ejecutar_escenarios.py
```

Levantar la API y abrir la documentación:

```
uvicorn app.api:app --reload
# Swagger:  http://127.0.0.1:8000/docs
# OpenAPI:  http://127.0.0.1:8000/openapi.json
```

Correr las pruebas:

```
python -m pytest -v
Deben pasar las 29 pruebas (16 de dominio, 6 de Specifications y 7 de la API).
```

## Estructura

```
app/domain.py                  Money, Customer, OrderItem, Order, DomainEvent, excepciones
app/specifications.py          Specification Pattern, descuentos y regla de pedido confirmable
app/api.py                     API REST (FastAPI)
tests/test_domain.py           Pruebas del dominio (16)
tests/test_specifications.py   Pruebas de las Specifications (6)
tests/test_api.py              Pruebas de la API REST (7)
datos/                         CSV de clientes, productos, pedidos y escenarios
cargar_csv.py                  Cargador de datos del paquete
ejecutar_escenarios.py         Ejecuta los 15 escenarios y genera bitacora.csv
ejercicio_estados.py           Ejercicio de la máquina de estados (pedido O013)
openapi.json                   Contrato OpenAPI de la API
```

## Reglas de negocio

- Money es inmutable, usa Decimal y no admite montos negativos ni monedas distintas al sumar.
- Customer, OrderItem y Order validan sus datos en el constructor (id vacío, cantidad cero o negativa).
- Un pedido es confirmable si tiene al menos un artículo y el cliente está activo (regla `confirmable`).
- Un pedido admite como máximo 20 unidades (se cuentan unidades, no renglones) y solo
  se pueden agregar artículos mientras está en DRAFT.
- Confirmar exige estado DRAFT, al menos un artículo y cliente activo.
- Enviar exige estado CONFIRMED y número de guía no vacío.
- Cancelar exige estado CONFIRMED y motivo no vacío. Un pedido enviado no se puede cancelar.
- Entregar y devolver exigen estado SHIPPED.
- Una operación rechazada no cambia el estado ni registra eventos.

**Descuentos**

- 10 %: total mayor a 500, cliente VIP, al menos 4 unidades y sin promoción activa.
- 5 %: total mayor a 5000 y sin promoción activa.
- Si se cumplen ambas, se aplica primero el 10 %.

## Máquina de estados y eventos

```
DRAFT --confirm--> CONFIRMED --ship--> SHIPPED --deliver--> DELIVERED
                       |                  |
                     cancel            return
                       |                  |
                  CANCELLED           RETURNED
```

Cada transición válida registra un evento: OrderConfirmed, OrderShipped,
OrderCancelled, OrderDelivered u OrderReturned.

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/orders/{order_id}` | Consulta un pedido |
| POST | `/orders/{order_id}/confirm` | Confirma un pedido |
| POST | `/orders/{order_id}/ship` | Envía un pedido (cuerpo: `tracking_number`) |
| POST | `/orders/{order_id}/cancel` | Cancela un pedido (cuerpo: `reason`) |

| Código | Cuándo |
|---|---|
| 200 | Operación exitosa |
| 404 | El pedido no existe |
| 409 | Transición no permitida (por ejemplo confirmar dos veces) |
| 422 | Datos inválidos (pedido vacío, cliente inactivo, guía o motivo vacíos) |

Los pedidos viven en memoria: al reiniciar el servidor vuelven a su estado inicial.