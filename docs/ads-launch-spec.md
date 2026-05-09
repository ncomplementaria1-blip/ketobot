# Spec de lanzamiento — Campaña Lookalike Mayo 2026

**Cambio estratégico (2026-05-09):** descartamos limitar a comunas de
Santiago. Aprovechamos los **12.000 pacientes previos** como semilla de
audiencia lookalike. Facebook encuentra mujeres de perfil similar en
todo Chile, y el filtro socioeconómico se hace por comportamiento real
de compra (no por geografía).

> **No modificar "Interacción | Chile".** El algoritmo aprendió el perfil
> equivocado durante $172k de gasto. Cambiar targeting ahora confunde a
> Meta con datos sucios. Pausamos esa campaña y creamos una nueva
> limpia.

## Estructura general

- **Nombre:** `Keto Oficial - Lookalike Premium Mayo 2026`
- **Objetivo:** Mensajes (WhatsApp Business)
- **Presupuesto diario campaña:** $5.000 – $8.000 CLP, divididos entre
  3 conjuntos de anuncios.
- **Duración inicial:** 7 días de test, luego escalar la audiencia
  ganadora.

## Paso 1 — Preparar lista de pacientes

### Formato CSV

Crear un archivo `pacientes.csv` con encabezados en inglés (Meta los
reconoce mejor):

```csv
email,phone,fn,ln
maria.gonzalez@gmail.com,56912345678,maria,gonzalez
carmen.perez@hotmail.com,56987654321,carmen,perez
```

### Reglas para que el match sea alto

- **Email** (obligatorio): minúsculas, sin espacios.
- **phone** (recomendado): formato internacional `56912345678` —
  sin `+`, sin espacios, sin guiones.
- **fn / ln** (opcional pero ayuda): minúsculas, sin tildes
  (`maría` → `maria`).
- Sin duplicados.
- Mínimo 100 contactos para que Meta cree lookalike. Vos tenés 12.000,
  perfecto.

### Privacidad y consentimiento

- Confirmá que los pacientes consintieron uso de sus datos para
  marketing. Si la ficha clínica original lo cubre, ok. Si no,
  agregá ese consentimiento al onboarding actual.
- Meta hashea los datos al recibirlos (no se almacenan en crudo).

## Paso 2 — Subir Custom Audience a Meta

En Ads Manager → menú hamburguesa (arriba izquierda) →
**Audiencias**:

1. Botón `Crear audiencia` → `Audiencia personalizada`.
2. Fuente: `Lista de clientes`.
3. Te pregunta si la lista incluye un valor de cliente (LTV):
   - Si tenés cuánto pagó cada paciente → sí (mejora el lookalike).
   - Si no → "no".
4. Subir el CSV.
5. Mapear las columnas al campo correspondiente (Meta lo detecta solo
   si los encabezados son `email`, `phone`, `fn`, `ln`).
6. Aceptar términos.
7. Nombre de la audiencia: `Pacientes Ketooficial 2013-2026`.
8. Subir y esperar **30 min – 2 hs** hasta que pase de "Procesando" a
   "Lista".

## Paso 3 — Crear Lookalike

Una vez que la custom audience esté lista:

1. Audiencias → `Crear audiencia` → `Audiencia similar (lookalike)`.
2. **Origen:** `Pacientes Ketooficial 2013-2026`.
3. **Ubicación:** Chile.
4. **Tamaño:** **1%** (los más parecidos, ~120.000 personas).
5. Crear. Tarda ~30 min.

> Crear también una segunda lookalike de **3%** como respaldo
> (`~360k personas`), por si la de 1% se agota rápido.

## Paso 4 — Crear la campaña

Estructura: **1 campaña, 3 conjuntos de anuncios** (audiencias
distintas, MISMO copy).

### Conjunto A — "Lookalike Pura"

- **Audiencia:** Lookalike 1% Chile.
- **Edad:** 28 – 47.
- **Género:** Mujeres.
- **Idioma:** Español.
- **Sin intereses adicionales.**
- **Presupuesto:** $2.000/día.

### Conjunto B — "Lookalike + Intereses Premium"

- **Audiencia:** Lookalike 1% Chile.
- **Edad:** 28 – 47, mujeres, español.
- **Restringir por intereses (AND):**
  - Fitness boutique (yoga, pilates, crossfit)
  - Wellness premium
  - Lululemon, Alo Yoga, Sweaty Betty
  - Revistas Paula / Ya / Mujer
  - Spa, tratamientos estéticos
- **Comportamientos:**
  - Compradores activos online
  - Usuarios iPhone
  - Viajeros frecuentes
- **Presupuesto:** $2.000/día.

### Conjunto C — "Solo Intereses Premium" (control)

- **Audiencia:** sin lookalike.
- **Edad:** 28 – 47, mujeres, español, todo Chile.
- **Intereses + comportamientos** del Conjunto B.
- **Presupuesto:** $2.000/día.
- Sirve como **referencia**: si A o B no le ganan a C, la lookalike no
  está aportando y el problema es otro (copy, oferta).

### IMPORTANTE — Configuraciones de la campaña

- **Desactivar "Expansión automática de detalles del público".**
  Si está prendido Meta amplía el targeting solo y volvés al problema
  inicial.
- **Optimización de entrega:** conversaciones (mensajes), no
  impresiones.
- **Píxel:** usar uno limpio o evento separado, no el de la campaña
  vieja.

## Paso 5 — Creatividad (1 sola, igual en los 3 conjuntos)

Para que la comparación entre conjuntos sea limpia, usar el mismo
anuncio. Después del día 7, cuando elijas la audiencia ganadora, ahí
sí variamos creatividades.

**Imagen:** plato keto chileno apetitoso o foto profesional de
Alejandra (probar ambas como variantes posteriores).

**Título:**
```
Programa Keto Personalizado con Nutricionista — Desde $30.000/mes
```

**Texto principal:**
```
¿Cansada de dietas que no funcionan y el efecto rebote?

Método Keto Científico con 12 años de experiencia:
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

**Descripción:** Acompañamiento diario por WhatsApp con nutricionista
colegiada
**CTA:** Enviar mensaje (a WhatsApp Business)

## Paso 6 — Plan de los 7 días

| Día | Acción |
|-----|--------|
| 1-2 | No tocar nada. Meta está aprendiendo. |
| 3   | Revisar costo por conversación por conjunto. Pausar el peor si la diferencia con el mejor es >40%. |
| 5   | Si el costo total por conversación es >$700, revisar copy o estrechar a Lookalike 1%. |
| 7   | Análisis final. Mantener al ganador, pausar los otros. Duplicar al ganador con presupuesto x2 (campaña hermana, no subir presupuesto directo a la original — evita reset del aprendizaje). |

## Métricas objetivo

| Métrica                              | Meta            |
|--------------------------------------|-----------------|
| Costo por conversación               | <$500 CLP       |
| Conversión a venta (CRM / WhatsApp)  | 15 – 20%        |
| ROI semanal                          | ≥ +200%         |
| % de leads regateadores              | <5% del total   |

## Checklist pre-lanzamiento

- [ ] Pausar "Interacción | Chile" ($172k gastados).
- [ ] Verificar que "Interaccion | Chile | VIDEO TEST 01" sigue activa
      (si querés mantener algo corriendo mientras construyes la nueva).
- [ ] Exportar lista de 12.000 pacientes a CSV con formato indicado.
- [ ] Confirmar consentimiento de marketing en los registros.
- [ ] Subir Custom Audience.
- [ ] Esperar a que esté "Lista".
- [ ] Crear Lookalike 1% Chile.
- [ ] Esperar a que esté "Lista".
- [ ] Crear campaña con 3 conjuntos (A, B, C).
- [ ] Subir creatividad única en los 3.
- [ ] Desactivar "Expansión automática de detalles del público".
- [ ] Activar campaña en horario de oficina.
- [ ] Anotar timestamp de inicio.

## Por qué crear nueva en vez de modificar

1. **Algoritmo aprendido mal.** $172k enseñándole a Meta que tu
   cliente es mujer 55-65 nivel D-E. Reentrenar es más barato que
   resetear.
2. **Datos sucios en el píxel.** Las conversaciones previas están
   marcadas como "leads exitosos" para Meta aunque para vos eran
   basura. Píxel limpio = aprendizaje correcto.
3. **Cambios grandes resetean igual.** Modificar edad, geografía e
   intereses de raíz manda la campaña a fase de aprendizaje de todas
   formas, pero con peso histórico negativo.
4. **Comparación A/B.** Dejar la vieja pausada (no eliminada) sirve
   para comparar performance y aprender qué cambió.

## Notas adicionales

- **Si tenés CRM/Excel con valor pagado por paciente** (LTV), incluí
  esa columna `value` en el CSV — Meta arma una lookalike ponderada
  por valor (los que más pagaron cuentan más). Brutal mejora.
- **Después del primer mes ganador**, crear una lookalike adicional
  basada solo en pacientes del último año (más reciente = más
  relevante para Meta).
- **Excluir audiencia** de quienes ya escribieron al WhatsApp en los
  últimos 30 días (custom audience desde tu cuenta de WhatsApp
  Business si está integrada al pixel).
