# Estrategia de Facebook Ads — Ketooficial.cl

Fecha del análisis: 2026-05-09

## 1. Problema detectado

Los anuncios traen leads que no pueden costear el servicio ($30k–$70k/mes).
Síntomas reportados desde WhatsApp:

- Leads de 60+ años con sueldos bajos buscando "una receta de $20k".
- Regateos persistentes (70 → 45 → 20 → 15) y frases como
  "hay que ayudar a algunas personas".
- Reacciones de "imposible de pagar" frente al precio real.
- Conversaciones que terminan en frustración mutua, sin venta.

El precio del servicio **no** es el problema. El targeting sí.

## 2. Estado actual de las campañas

| Vista       | Dato                                                  |
|-------------|-------------------------------------------------------|
| Anuncios    | 14 activos, gasto total $280.347                      |
| Costo/res.  | $653 – $1.099                                         |
| Errores     | 2 anuncios con "Error de entrega"                     |
| Campaña #1  | "Interacción \| Chile" — $172.929 gastado             |
|             | 272 conversaciones, $636 c/u, 1 error activo          |
| Errores     | "3 anuncios de esta campaña tienen 3 errores"         |

ROI estimado: si 10 ventas del plan de 3 meses = $700.000, gastando $173.000
en una sola campaña genérica = 25% del ingreso bruto en ads, sin contar
otras campañas.

## 3. Diagnóstico

1. **Targeting demasiado amplio** — "Interacción | Chile" llega a todo el
   país sin filtros de edad, comuna, intereses ni nivel socioeconómico.
2. **Precio escondido** — Los anuncios no muestran inversión, así que la
   audiencia llega esperando algo gratis o muy barato.
3. **Gasto disperso** — 14 anuncios compitiendo entre sí, varios con errores
   técnicos que consumen presupuesto sin entregar.
4. **Errores de entrega sin resolver** — dinero quemado.

## 4. Plan de acción

### Inmediato (hoy)

- [ ] Pausar campaña "Interacción | Chile" ($172k).
- [ ] Pausar todos los anuncios con "Error de entrega".
- [ ] Pausar anuncios con costo >$1.000 por conversación.
- [ ] Calcular ROI real: gasto vs. ventas confirmadas del último mes.

> Nota técnica: las cuentas de ads donde está el gasto real
> ("María Eliana 2022-12-1" y `783163627199181`) **no tienen Ads MCP
> habilitado** todavía, así que estos pasos hay que hacerlos manualmente
> en Meta Ads Manager.

### Lunes — Crear nueva campaña

**Objetivo:** Mensajes (no Interacción) — leads cualificados a WhatsApp.

**Targeting:**

- Ubicación: comunas ABC1–C2 de Santiago (Vitacura, Las Condes, Lo Barnechea,
  Providencia, Ñuñoa, La Reina). Excluir el resto del país en una primera
  iteración para validar costo/lead.
- Edad: mujeres 30–50 (excluir 55+).
- Intereses: fitness y bienestar, nutrición saludable, yoga, pilates,
  Lululemon, marcas deportivas premium, revistas Paula / Ya / Mujer,
  alimentación consciente, wellness, spa.
- Comportamiento: compradores online, seguidores de influencers de wellness.

**Estructura:** 1 campaña, 2–3 anuncios.

- **A — Resultados:** transformación (con autorización), copy en
  resultados sin efecto rebote.
- **B — Profesional:** foto de Ale como nutricionista, copy en experiencia
  y acompañamiento personalizado.
- **C — Salud:** alimentos keto chilenos, copy en comer rico sin pasar
  hambre, método científico.

**Copy base (precio visible desde el inicio):**

```
Programa Keto Personalizado con Nutricionista — Desde $30.000/mes

¿Cansada de dietas que no funcionan y del efecto rebote?

Método Keto Científico, 12 años de experiencia:
✅ Plan personalizado para TI (no recetas genéricas)
✅ Acompañamiento diario por WhatsApp
✅ Menú chileno fácil de seguir
✅ Sin pasar hambre
✅ Resultados desde la 1ª semana

Inversión según tu meta:
📍 1 mes: $30.000
📍 2 meses: $50.000
📍 3 meses (completo): $70.000

+8.000 personas transformadas desde 2013.
¿Lista para tu transformación?
```

CTA: "Enviar mensaje".

**Presupuesto:**

- $5.000–$8.000 diarios totales (no por anuncio).
- Prueba 5–7 días antes de escalar.
- Métrica clave: costo por conversación <$500, conversión a venta 15–20%.

## 5. Métricas

Sí mide:

- Costo por conversación (meta <$500).
- Calidad del lead (¿coincide con el targeting?).
- Conversión a venta (meta 15–20%).
- ROI semanal: gasto vs. ingresos confirmados.

No te obsesiones con: alcance, impresiones, likes, comentarios.

## 6. Cambio paralelo en el bot

Mientras el targeting se corrige, el bot de WhatsApp ya hace dos cosas
nuevas (ver `main.py`):

1. **Muestra el precio temprano** (segundo o tercer mensaje), filtrando
   antes a quien no puede pagar.
2. **Maneja regateo con dignidad y firmeza**: una respuesta clara, sin
   bajar el precio ni cuestionar el valor del servicio, y cierre amable
   si el lead insiste.

## 7. Resultado esperado

| Métrica           | Antes                          | Después             |
|-------------------|--------------------------------|---------------------|
| Gasto             | $172k en una campaña genérica  | $35–50k/semana      |
| Lead típico       | 62 años, $1.500 sueldo, regateo| Mujer 35–45, ABC1–C2|
| Conversión        | <5%                            | 15–20%              |
| Tono del chat     | "Encuentro todo caro"          | "¿Cuándo partimos?" |
