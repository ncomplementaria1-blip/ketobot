# Spec de lanzamiento — Campaña nueva de Facebook Ads

Complemento operativo de `docs/ads-strategy.md`. Este archivo contiene
todo lo necesario para armar y lanzar la campaña nueva el lunes.

## Estructura general

- **Objetivo:** Mensajes (Messenger / WhatsApp Business)
- **Nombre:** `Mensajes | ABC1-C2 | Mujeres 30-50`
- **Presupuesto diario campaña:** $6.000 CLP
- **Duración inicial:** 7 días, después evaluación y ajuste
- **Ubicación de botón:** WhatsApp Business

## Targeting (conjunto de anuncios)

### Ubicación — Chile, comunas específicas
- Vitacura
- Las Condes
- Lo Barnechea
- Providencia
- Ñuñoa
- La Reina
- Lo Curro
- Colina (sector Chicureo)

### Demografía
- **Edad:** 32 – 50
- **Género:** Mujeres
- **Idioma:** Español

### Intereses detallados
Sumar todos:
- Fitness y bienestar
- Nutrición
- Yoga
- Pilates
- Alimentación saludable
- Pérdida de peso
- Lululemon
- Adidas Women
- Nike Women
- Wellness
- Vida saludable
- Revista Paula
- Revista Ya

### Comportamientos
- Compradores activos en internet
- Tecnología: dispositivos móviles iPhone
- Dispositivos móviles de última generación

### Exclusiones
- Custom audience: leads que ya escribieron al WhatsApp Business en
  los últimos 30 días.
- Excluir intereses de regateo de precio bajo / cupones / descuentos
  agresivos si Meta los ofrece.

## Anuncio A — "Resultados sin rebote"

**Imagen sugerida:** transformación real de cliente con autorización
escrita, o foto profesional de Alejandra midiendo cintura a paciente.

**Copy principal:**
```
¿Cansada de bajar 5 kilos y subir 7?

El efecto rebote no es tu culpa: es porque las dietas restrictivas
reprograman tu metabolismo para guardar grasa.

Método Keto Científico de Ketooficial.cl:
✅ Plan 100% personalizado a tu cuerpo y rutina
✅ Acompañamiento diario por WhatsApp con nutricionista colegiada
✅ Menú chileno fácil — sin pasar hambre
✅ Resultados visibles desde la 1ª semana

Inversión:
📍 1 mes: $30.000
📍 3 meses (transformación completa): $70.000

+8.000 mujeres transformadas desde 2013.
```

- **Título:** Programa Keto Personalizado — Sin Efecto Rebote
- **Descripción:** Acompañamiento diario por WhatsApp con nutricionista
- **CTA:** Enviar mensaje

## Anuncio B — "La nutricionista detrás del método"

**Imagen sugerida:** retrato profesional de Alejandra Varela (delantal,
oficina, fondo neutro).

**Copy principal:**
```
Soy Alejandra Varela, nutricionista colegiada con 12 años de
experiencia en cetosis nutricional.

No vendo recetas genéricas. Cada plan es para TI:
✅ Evaluación clínica inicial
✅ Menú personalizado a tu metabolismo y rutina
✅ Acompañamiento diario por WhatsApp (yo, no un bot)
✅ Ajustes semanales según tus avances
✅ Sin pasar hambre, sin productos caros

Inversión transparente:
📍 1 mes: $30.000
📍 3 meses (lo más pedido): $70.000

Cupos limitados — atiendo personalmente a cada paciente.
```

- **Título:** Nutricionista Keto — Acompañamiento Personal
- **Descripción:** 12 años de experiencia, +8.000 transformaciones
- **CTA:** Enviar mensaje

## Anuncio C — "Comer rico sin culpa"

**Imagen sugerida:** plato keto chileno apetitoso (palta, salmón,
ensalada, huevo de campo).

**Copy principal:**
```
Plato keto chileno: palta, salmón, ensalada de la huerta, huevo de
campo. Saciante. Sabroso. Y baja grasa de verdad.

El método keto no es comer pollo con lechuga 3 veces al día. Es
entender tu metabolismo y comer de manera estratégica para que tu
cuerpo queme grasa por combustible.

Programa Ketooficial.cl:
✅ Recetario chileno completo
✅ Plan personalizado por nutricionista colegiada
✅ Acompañamiento diario por WhatsApp
✅ Sin productos caros, comida del supermercado

Desde $30.000/mes. Plan completo (3 meses): $70.000.
```

- **Título:** Keto Chileno — Comida Real, Resultados Reales
- **Descripción:** Recetas con ingredientes del supermercado
- **CTA:** Enviar mensaje

## Plan de prueba — primeros 7 días

| Día | Acción |
|-----|--------|
| 1-2 | No tocar nada. Meta está en fase de aprendizaje. |
| 3   | Revisar costo por conversación por anuncio. Pausar el peor si la diferencia con el mejor es >40%. |
| 5   | Si el costo total por conversación es >$700, estrechar audiencia o ajustar copy. |
| 7   | Análisis completo. El ganador queda. Los demás se reemplazan con nuevas variantes. |

## Métricas objetivo

| Métrica                              | Meta            |
|--------------------------------------|-----------------|
| Costo por conversación               | <$500 CLP       |
| Conversión a venta (CRM / WhatsApp)  | 15 – 20%        |
| ROI semanal                          | ≥ +200%         |
| % de leads regateadores              | <5% del total   |

## Checklist de lanzamiento (lunes)

- [ ] Confirmar que "Interacción | Chile" ($172k) está pausada.
- [ ] Crear nueva campaña con la estructura de arriba.
- [ ] Subir las 3 creatividades (A / B / C).
- [ ] Configurar audiencia de exclusión (leads de últimos 30 días).
- [ ] Verificar que el botón lleva a WhatsApp Business correcto.
- [ ] Activar campaña en horario de oficina (no de madrugada).
- [ ] Anotar timestamp de inicio para medir 24h, 48h, 7 días.

## Notas para Alejandra

- **No bajes el precio** ni en respuestas privadas ni en anuncios. El
  bot ya está configurado para mantener la dignidad del servicio
  (ver `main.py`).
- Si un anuncio empieza a traer leads de bajo poder adquisitivo,
  revisá las **comunas** y los **intereses** primero — Meta a veces
  expande el targeting solo si lo dejas en "expansión automática".
  **Desactivá esa opción.**
- Después de la primera semana exitosa, considerar duplicar la
  campaña ganadora con presupuesto x2 antes de subirle directo el
  presupuesto a la original (evita reset del aprendizaje).
