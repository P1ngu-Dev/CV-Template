# CV Workspace

Workspace para mantener el CV maestro, generar versiones especificas por postulacion y guardar contexto/documentacion para futuras actualizaciones.

## Estructura

```text
main/            CV maestro y outputs principales
applications/    CVs adaptados por empresa o rol
contexts/        Contexto personal/profesional fechado
docs/            Documentacion del workflow y catalogos
portfolio/       Casos de estudio para portafolio
linkedin/        Borradores y versiones de perfil LinkedIn
references/      Material de referencias profesionales
scripts/         Automatizacion futura
templates/       Plantillas para nuevas postulaciones
archive/         Diseños alternativos, pruebas y material historico
```

## Convenciones

- Fuente principal del CV: `main/cv.yaml`
- Tema principal actual: `moderncv`
- Idioma principal actual: `spanish`
- Cada postulacion nueva debe vivir en `applications/YYYY-MM-empresa-rol/`
- Los contextos deben guardarse con fecha: `contexts/YYYY-MM-DD.md`

## Flujo Recomendado

1. Mantener `main/cv.yaml` como fuente oficial.
2. Crear carpeta en `applications/` cuando exista una oferta real.
3. Analizar la oferta y adaptar una copia del CV.
4. Renderizar outputs dentro de la carpeta de la postulacion.
5. Registrar seguimiento de la postulacion.

## Automatización inicial

- Flujo operativo: `docs/application_workflow.md`
- Revisión inicial de postulaciones: `docs/job_postings_initial_review_2026-06-22.md`
- Crear postulación: `scripts/create_application.py "Empresa" "Rol" --url "LINK"`
- Renderizar postulación: `scripts/render_application.sh applications/YYYY-MM-empresa-rol`
- Validar CV maestro y postulaciones: `scripts/validate.sh`
