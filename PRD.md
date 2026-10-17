# PRD — Sistema de Administración de Alumnos

**Proyecto:** proyecto_padawans
**Cliente interno:** Bunker4 (jornada formativa)
**Versión:** 0.1.0
**Estado:** Borrador

---

## 1. Resumen

Sistema para administrar alumnos de Bunker4: altas, bajas y modificaciones de
alumnos; gestión de cursos y materias; e interacción según los roles admin,
docente y alumno.

Este documento describe el problema, el alcance y las reglas de negocio. La
arquitectura, el modelo de datos, los endpoints y las decisiones operativas se
documentan en [PLAN.md](./PLAN.md).

## 2. Problema

Bunker4 administra alumnos, cursos e interesados de forma manual, mediante
planillas y documentos dispersos. Esto ocasiona:

- Alumnos duplicados.
- Reportes inconsistentes.
- Falta de control de acceso a la información.
- Dificultad para conocer la ocupación de los cursos.
- Dificultad para relacionar los intereses de aprendizaje de los alumnos con
  las clases disponibles.

## 3. Objetivos

- Centralizar la administración de alumnos y cursos.
- Permitir registrar los temas que interesan a cada alumno y las clases donde
  se trabajan esos temas.
- Permitir agrupar clases y comunicar su temática a los alumnos interesados.
- Registrar quién y cuándo realiza cada operación.
- Restringir las acciones según los roles admin, docente y alumno.
- Evitar inconsistencias, como inscripciones inválidas o cursos sin control de
  cupos.

## 4. Fuera de alcance actual

- Gestión de calificaciones o notas.
- Gestión de asistencia.
- Reportes y dashboard analítico.
- Integraciones externas, como Google Sheets o correo electrónico.
- Multi-tenancy.
- Backup automático.

## 5. Personas y roles

| Rol | Descripción | Acciones permitidas |
|---|---|---|
| **admin** | Coordinador de Bunker4. | Administra alumnos, cursos, materias y docentes; asigna docentes e inscribe alumnos. |
| **docente** | Responsable de uno o varios cursos. | Consulta sus cursos, los alumnos de esos cursos y su perfil. No crea alumnos ni cursos. |
| **alumno** | Persona cursando. | Consulta su perfil y los cursos donde está inscripto. No realiza modificaciones. |

## 6. Reglas de negocio

1. No se pueden crear dos alumnos con el mismo DNI ni el mismo email.
2. Un alumno no puede tener más de una inscripción activa en el mismo curso.
3. Un curso no puede superar su cupo de inscripciones activas.
4. Al dar de baja a un alumno, sus inscripciones activas pasan a baja.
5. Al dar de baja un curso, sus inscripciones activas pasan a baja y se
   desasignan sus docentes.
6. Un usuario alumno debe estar vinculado a un alumno; los usuarios admin y
   docente no deben estar vinculados a un alumno.
7. Toda alta o modificación debe registrar quién la realizó.
8. Las bajas son lógicas: la aplicación no elimina registros de negocio.

## 7. Casos de uso clave

### UC-1: Alta de alumno

**Actor:** admin.

1. El admin inicia sesión.
2. Registra los datos del alumno.
3. El sistema valida la unicidad de DNI y email.
4. El sistema registra el alumno y la auditoría del alta.
5. El sistema informa la creación o los errores de validación.

### UC-2: Inscripción con cupo lleno

**Actor:** admin.

1. El admin intenta inscribir a un alumno en un curso.
2. El sistema verifica que exista cupo disponible.
3. Si el cupo está completo, rechaza la inscripción sin alterar los datos.
4. Si hay cupo, crea una inscripción activa.

### UC-3: Docente consulta sus cursos

**Actor:** docente.

1. El docente inicia sesión.
2. Consulta los cursos que tiene asignados.
3. El sistema muestra los alumnos con inscripción activa en esos cursos.

### UC-4: Alumno consulta sus cursos

**Actor:** alumno.

1. El alumno inicia sesión.
2. Consulta sus cursos.
3. El sistema muestra solo sus inscripciones activas.

## 8. Criterios de aceptación del MVP

1. Un admin puede crear, listar, modificar y dar de baja alumnos.
2. Un admin puede crear cursos y materias dentro de cursos.
3. Un admin puede inscribir alumnos respetando los cupos.
4. Un docente puede iniciar sesión y ver sus cursos y alumnos.
5. Un alumno puede iniciar sesión y ver sus cursos activos.
6. Todas las mutaciones registran la auditoría correspondiente.
7. No se puede inscribir a un alumno en un curso lleno.
8. Las bajas propagan los cambios requeridos a inscripciones y asignaciones.
9. La interfaz y la API informan los errores de forma comprensible.
10. La suite de pruebas cubre los casos de uso clave.

---

**Próximo paso:** [PLAN.md](./PLAN.md) define la arquitectura, el contrato
técnico, las fases de implementación y la operación del sistema.
