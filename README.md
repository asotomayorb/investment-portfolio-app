# Investment Portfolio App

Aplicación privada y local para monitorear una cartera de inversión. Esta primera entrega implementa **Stage 0** de la especificación V1.

## Alcance actual

- Dashboard de cartera en USD.
- Cartera inicial de 13 instrumentos: VT, SMH, BTCUSD, INDA, MSFT, NVDA, AVGO, GLD, URA, XLE, VHT, PLTR y QQQ.
- Pesos objetivo iniciales: activos 95% y efectivo 5%. El objetivo de efectivo es fijo en esta etapa.
- Edición de cantidades, costo promedio, tipo de activo, nombre y pesos objetivo.
- Cálculo de valor conocido, valor invertido y pesos actuales.
- Persistencia local en SQLite.
- Respaldo CSV con importación y exportación.
- Pruebas automatizadas y workflow CI.

## Advertencia sobre los datos demo

Los precios mostrados son **sintéticos e ilustrativos**. No son cotizaciones actuales ni datos históricos. La app no consulta proveedores externos, no se conecta a IBKR y no envía órdenes. Los instrumentos agregados manualmente sin precio demo se muestran como no valorados; la app indica que la valoración está incompleta en vez de inventar un precio.

## Requisitos

- Python 3.11 o superior.
- pip.

## Instalación y ejecución

Desde la raíz del repositorio:

```bash
python -m venv .venv
```

Activar el entorno:

**macOS / Linux**
```bash
source .venv/bin/activate
```

**Windows PowerShell**
```powershell
.venv\\Scripts\\Activate.ps1
```

Instalar dependencias y ejecutar:

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

La aplicación se abrirá en el navegador local. La base de datos `portfolio.db` se crea automáticamente junto al código y queda excluida de Git.

## Uso básico

1. Edita las cantidades y los demás campos en la tabla.
2. Ingresa el efectivo disponible en USD.
3. Pulsa **Guardar cartera**. Los cambios quedan almacenados en SQLite.
4. Usa **Exportar cartera CSV** para crear un respaldo.
5. Para recuperar un respaldo, carga el CSV y pulsa **Validar e importar CSV**.

Los pesos objetivo de los instrumentos deben sumar 95%, porque el efectivo mantiene un objetivo fijo de 5%. Las cantidades iniciales son cero: los pesos objetivo no representan posiciones reales.

## Pruebas

```bash
python -m pytest -q
```

GitHub Actions ejecuta las pruebas al hacer push a `main` y en pull requests dirigidos a `main`.

## Estructura

- `app.py`: interfaz Streamlit.
- `portfolio.py`: cartera inicial, validación, cálculos y CSV.
- `storage.py`: persistencia SQLite.
- `tests/`: pruebas de cálculos, validación, CSV y persistencia.
- `.github/workflows/tests.yml`: integración continua.

## Próximas etapas (no incluidas todavía)

- **Stage 1:** un proveedor de precios de referencia con fuente y timestamp.
- **Stage 2:** HH52 y ATR20W con validaciones de integridad histórica.
- **Stage 3:** conexión IBKR exclusivamente de lectura y conciliación.
- **Stage 4:** propuestas basadas en reglas solo tras aprobación y congelamiento explícito de reglas operativas.

No hay funciones de trading, apalancamiento, CFDs, margen ni envío de órdenes en esta versión.
