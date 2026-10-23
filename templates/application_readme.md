# {{COMPANY}} — {{ROLE}}

## Estado

draft

## Resumen

- Empresa: {{COMPANY}}
- Rol: {{ROLE}}
- Link: {{URL_OR_PENDING}}
- Creada: {{DATE}}

## Archivos

- `job_description.md`: oferta original o resumen fiel.
- `analysis.md`: match, keywords y estrategia.
- `cv.yaml`: copia derivada de `../../main/cv.yaml`; editar solo esta versión.
- `outputs/`: salidas generadas por RenderCV (no versionadas).
- `cover_letter.md`: carta o mensaje si la postulación lo requiere.
- `application_log.md`: seguimiento del envío.

## Flujo rápido

1. Completar `job_description.md` si falta el texto de la oferta.
2. Completar `analysis.md` con requisitos, keywords y estrategia.
3. Adaptar `cv.yaml` sin inventar experiencia.
4. Renderizar desde la raíz del repo:
   `python3 scripts/cv.py render {{FOLDER_NAME}}`
5. Revisar `outputs/` y registrar el envío en `application_log.md`.
