# Reglas y Restricciones para SEO Skills

> **Instrucciones:** Este archivo define las reglas que la IA debe seguir al generar contenido y realizar auditorías.
> Puedes personalizar las reglas según las necesidades de tu proyecto.
> NUNCA elimines las reglas de seguridad (API keys, datos confidenciales).

---

## Formato de Archivos

- Reportes: `outputs/YYYYMMDD_reporte_[nombre].md`
- Artículos: `outputs/YYYYMMDD_articulo_[keyword-slug].md`
- Publicaciones: `outputs/YYYYMMDD_publicacion_[keyword-slug].md`
- Usar siempre formato Markdown con UTF-8
- Los archivos MDX pueden incluir frontmatter YAML y sintaxis JSX

---

## Reglas de Contenido

- **NUNCA** inventar datos, estadísticas o citas sin fuente verificable
- **NUNCA** hacer keyword stuffing (densidad máxima recomendada: 1-2%)
- **SIEMPRE** escribir para el humano primero, Google después
- **SIEMPRE** respetar la intención de búsqueda de la keyword
- **SIEMPRE** incluir enlaces internos a otras páginas del sitio
- **SIEMPRE** usar lenguaje claro y evitar jerga innecesaria

---

## Reglas de Meta Tags

- Meta título: máximo 60 caracteres, mínimo 40
- Meta descripción: máximo 155 caracteres, mínimo 120
- El H1 debe ser único en el sitio y contener la keyword principal
- Los H2 deben cubrir subtemas relevantes (nunca repetir el H1)
- La URL (slug) debe ser descriptiva, corta y con guiones

---

## Reglas de Publicación

- **NUNCA** publicar contenido sin aprobación previa (a menos que sea automático)
- **SIEMPRE** verificar que el slug no exista ya en el sitio
- **NUNCA** crear canibalización de keywords (dos páginas para la misma keyword)
- Comprimir imágenes antes de publicar (máx 150kb)
- Revisar enlaces rotos antes de publicar

---

## Reglas de Datos

- **NUNCA** exponer API keys o credenciales en outputs o commits
- Los datos de GA4 y GSC son confidenciales del cliente
- No compartir métricas sin contexto de comparación (período anterior, benchmark)
- Distinguir claramente datos reales de estimaciones o suposiciones
- No incluir información personal identificable (PII) en reportes

---

## Reglas de Git

- Los commits automáticos deben empezar con `auto:`
- No hacer push si no hay cambios
- No incluir archivos `.env`, `*.json` de credenciales, o `__pycache__/` en commits
- Escribir mensajes de commit descriptivos
- Hacer pull antes de push para evitar conflictos

---

## Reglas de Calidad

- Mínimo 800 palabras para artículos de blog informacionales
- Mínimo 400 palabras para páginas de servicio
- Párrafos máximos de 4-5 líneas para facilitar la lectura
- Usar listas, tablas y negritas para mejorar la escaneabilidad
- Incluir un CTA (llamada a la acción) relevante en cada pieza de contenido
- Revisar ortografía y gramática antes de entregar

---

## Reglas Específicas por Framework (Next.js / React)

- No romper la sintaxis JSX/TSX
- Preservar imports y componentes existentes
- No eliminar funcionalidad interactiva
- Los archivos MDX pueden contener componentes React importados
- Respetar la estructura de carpetas del App Router

---

## Reglas de Frecuencia

- Monitoreo automático: 1 vez al día (08:00)
- Auditoría por página: 2 veces al día (10:00 y 22:00)
- Reporte semanal: cada lunes (09:00)
- No ejecutar fuera del horario laboral a menos que sea crítico
