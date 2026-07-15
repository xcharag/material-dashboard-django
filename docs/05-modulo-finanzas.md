# 05 · Módulo de Finanzas

La app `apps.finance` gestiona el dinero asociado a cada consulta. Se apoya en dos
modelos: **`PaymentRequest`** (lo que se debe cobrar) y **`Payment`** (cada pago
concreto).

## Concepto: solicitud de cobro vs. pago

- Una **solicitud de cobro** (`PaymentRequest`) representa el monto **esperado** por
  una consulta. Hay exactamente **una por consulta** (relación 1:1).
- Un **pago** (`Payment`) es una transacción concreta contra esa solicitud. Una
  solicitud puede recibir **varios pagos** (pagos parciales hasta completar el
  total).

Esta separación permite modelar el caso real: el paciente debe 200 BOB, paga 100 en
efectivo hoy y 100 con tarjeta la próxima semana.

## `PaymentRequest`

| Campo | Propósito |
|---|---|
| `consultation` | Consulta asociada (1:1). |
| `expected_amount` | Monto esperado (Decimal, puede ser nulo). |
| `currency` | Moneda (por defecto `BOB`). |
| `notes` | Observaciones. |

### Propiedades calculadas

Estas propiedades no se almacenan; se calculan al vuelo a partir de los pagos:

```python
@property
def amount_paid(self):   # suma de todos los Payment asociados
    return self.payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

@property
def balance(self):       # saldo pendiente
    return (self.expected_amount or 0) - self.amount_paid

@property
def status(self):        # estado derivado
    if not expected_amount:      -> 'pending'
    if amount_paid <= 0:         -> 'pending'
    if amount_paid >= expected:  -> 'paid'
    else:                        -> 'partial'
```

El **estado** (`pending`, `partial`, `paid`) siempre refleja la realidad de los
pagos registrados, sin necesidad de actualizarlo manualmente.

## `Payment`

| Campo | Propósito |
|---|---|
| `request` | Solicitud de cobro a la que abona (FK). |
| `amount` | Monto del pago (Decimal). |
| `currency` | Moneda (por defecto `BOB`). |
| `method` | `cash` (efectivo), `card` (tarjeta) o `qr`. |
| `reference` | Referencia opcional (nº de comprobante). |
| `paid_at` | Fecha/hora del pago. |
| `created_by` | Usuario que registró el pago. |

## Índices de base de datos

Ambos modelos declaran índices para acelerar reportes financieros:

- `PaymentRequest`: por `currency` y `created_at`.
- `Payment`: por `paid_at` y `method`.

Esto agiliza consultas como "pagos por método en un rango de fechas" o "ingresos por
moneda".

## Señales (signals)

El archivo `apps/finance/signals.py` contiene lógica automática (por ejemplo,
rellenar el `expected_amount` a partir del `charge` de la consulta). La migración
`0002_backfill_expected_amount.py` completó este dato para registros históricos.

## Interfaz

- `/finance/` — panel financiero con ApexCharts.
- Historial de pagos con filtros por método y fecha.

Continúa en → [06 · IA de Análisis de Pacientes](06-ia-analisis-pacientes.md).
