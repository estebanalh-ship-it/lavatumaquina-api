<div align="center">

<pre>
+================================================================+
|                                .                               |
|                 L A V A   T U   M A Q U I N A                  |
|             Sistema Integral de Gestión Automotriz             |
|                                                                |
|            Agendas  /  Clientes  /  Administración             |
|                                                                |
|                  Rengo, Chile  -  2025 - 2026                  |
|                                .                               |
+================================================================+
</pre>
<br/>

[![Estado](https://img.shields.io/badge/STATUS-IN_DEVELOPMENT-4a5568?style=flat-square)](#)
[![Versión](https://img.shields.io/badge/VERSION-1.0.0--beta-1a365d?style=flat-square)](#)
[![Licencia](https://img.shields.io/badge/LICENSE-MIT-0f0f0f?style=flat-square)](LICENSE)
[![Build](https://img.shields.io/badge/BUILD-PASSING-2d3748?style=flat-square)](#)

<br/>

[![Python](https://img.shields.io/badge/PYTHON-3.10+-1a365d?style=flat-square&logo=python&logoColor=white)](#)
[![Flask](https://img.shields.io/badge/FLASK-3.x-0f0f0f?style=flat-square&logo=flask&logoColor=white)](#)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-1e3a5f?style=flat-square&logo=mysql&logoColor=white)](#)
[![Bootstrap](https://img.shields.io/badge/BOOTSTRAP-5.3-2d3748?style=flat-square&logo=bootstrap&logoColor=white)](#)
[![PythonAnywhere](https://img.shields.io/badge/HOST-PythonAnywhere-1a365d?style=flat-square&logo=pythonanywhere&logoColor=white)](#)

---

</div>

## ▌ TABLA DE CONTENIDOS

```
[01] Descripción General          [05] Arquitectura del Sistema
[02] Objetivos Estratégicos       [06] Módulos Funcionales
[03] Stack Tecnológico            [07] Roadmap & Deployment
[04] Características Core         [08] Desarrollador & Contacto
```

---

## ▌ [01] DESCRIPCIÓN GENERAL

**Lava Tu Máquina** es una plataforma web de gestión integral diseñada para centros de servicio automotriz. Desarrollada como solución B2C/B2B, el sistema centraliza la operación de un lavadero ubicado en Rengo, Chile (Región de O'Higgins), integrando reservas online, gestión administrativa y en un futuro la integración de un modulo para servicios mecánicos en una única interfaz unificada.

El producto resuelve los siguientes problemas operativos reales:

- **Agendamiento manual** proceso poco eficiente y un bajo control de gestión.
- **Falta de trazabilidad** no existe control y tampoco historial de los clientes.
- **Gestión de precios descentralizada** no existe una matriz de precios acorde al mercado.
- **Ausencia de reportes** para la toma de decisiones administrativas.

---

## ▌ [02] OBJETIVOS ESTRATÉGICOS

```yaml
Automatización:     Eliminar procesos manuales en reservas y cotizaciones.
Experiencia:        Proveer una UX intuitiva multiplataforma (PWA-like).
Gestión:            Dashboard administrativo con KPIs en tiempo real.
Escalabilidad:      Arquitectura modular preparada para multi-sucursal.
Confiabilidad:      Reducir errores operativos en un >80%.
```

---

## ▌ [03] STACK TECNOLÓGICO

### `Frontend`

| Tecnología | Rol | Versión |
|---|---|---|
| `HTML5` | Estructura semántica | Living Standard |
| `CSS3` | Estilos responsive / Flexbox / Grid | ES2023 |
| `JavaScript (ES6+)` | Lógica cliente / fetch API | ES2023 |
| `Bootstrap 5` | Sistema de diseño / componentes | 5.3.x |
| `Font Awesome` | Iconografía vectorial | 6.x |

### `Backend`

| Tecnología | Rol | Versión |
|---|---|---|
| `Python` | Lenguaje servidor | 3.10+ |
| `Flask` | Microframework | 3.x |
| `MySQL` | Base de datos relacional | 8.0 |
| `Jinja2` | Motor de templates | 2.x |
| `REST API` | Comunicación cliente-servidor | JSON |

### `DevOps & Tooling`

| Tecnología | Rol |
|---|---|
| `Git` | Control de versiones |
| `GitHub` | Repositorio remoto / CI |
| `PythonAnywhere` | Hosting / Deployment |
| `Debian` | OS de desarrollo (100% Linux) |
| `AI-Assisted Dev` | Copilot / Code review |

---

## ▌ [04] CARACTERÍSTICAS CORE

### ► Motor de Reservas

```
[ Cliente ] --> [ Catálogo Servicios ] --> [ Selección Horario ]
      |                  |                         |
      v                  v                         v
[ Disponibilidad ]  [ Validación DB ]      [ Confirmación ]
```

- Reservas 24/7 con validación de slots disponibles.
- Tipos de servicio: `Lavado General` / `Lavado Premium` / `Servicios Mecánicos`.
- Gestión de horarios con bloqueo de franjas ocupadas.

### ► Panel Administrativo

- **Dashboard**: KPIs diarios, semanales, mensuales.
- **CRM**: gestión centralizada de clientes y vehículos.
- **Citas**: CRUD completo con estados (`pendiente`, `en proceso`, `finalizada`, `cancelada`).
- **Cotizaciones**: generación, envío y seguimiento.
- **Precios**: módulo con versionado e historial de cambios.
- **Reportes**: exportación a CSV/Excel.

### ► Interfaz

- Diseño **responsive mobile-first** (breakpoints: `sm / md / lg / xl / xxl`).
- Compatibilidad cross-browser: Chrome, Brave, Edge, Safari iOS, Android WebView.
- Navegación simplificada con jerarquía visual clara.

---

## ▌ [05] ARQUITECTURA DEL SISTEMA

```
┌─────────────────────────────────────────────────────────────┐
│                      CLIENTE (Browser)                      │
│         HTML5 + CSS3 + JS (Bootstrap 5 + Font Awesome)      │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS / REST
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                 PYTHONANYWHERE (WSGI)                       │
│  ┌───────────────┐   ┌──────────────┐   ┌───────────────┐   │
│  │  Flask App    │──▶│  Jinja2      │──▶│  Templates    │   │
│  │  (Rutas/API)  │   │  Templates   │   │  HTML         │   │
│  └───────┬───────┘   └──────────────┘   └───────────────┘   │
│          │                                                   │
│          ▼                                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              MySQL 8.0 (RDBMS)                        │  │
│  │  [clientes] [vehiculos] [citas] [servicios] [precios] │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Flujo de Deployment

```
Local (Debian) --[git push]--> GitHub --[git pull]--> PythonAnywhere --[reload]--> PROD
```

---

## ▌ [06] MÓDULOS FUNCIONALES

### `Módulo Cliente`

- Registro / Login / Recuperar contraseña.
- Historial de servicios por vehículo.
- Notificaciones por email.
- Dashboard personal con próximas citas.

### `Módulo Servicios`

- Catálogo dinámico (editable desde admin).
- Sistema de precios con versionado.
- Gestión de inventario de insumos.
- Cotizaciones formalizadas.

### `Módulo Administración`

- CRUD completo de usuarios y roles.
- Reportes financieros y operativos.
- Auditoría de cambios (precios, estados).
- Exportación de datos.

---

## ▌ [07] ROADMAP

```yaml
v1.0.0-beta:  [x] Core funcional (reservas + admin básico)
v1.1.0:       [x] Módulo cotizaciones
v1.2.0:       [x] Módulo precios con versionado
v1.3.0:       [ ] Módulo reportes avanzados (Chart.js)
v1.4.0:       [ ] Notificaciones SMS / WhatsApp API
v2.0.0:       [ ] Multi-sucursal / SaaS
```

```yaml
RELEASE PÚBLICO: ABRIL 2026
  [ ] Repositorio abierto en GitHub
  [ ] Documentación técnica completa
  [ ] Guías de instalación / deployment
  [ ] Comunidad de contribuidores
```

---

## ▌ [08] FILOSOFÍA DEL PROYECTO

```
"El conocimiento que se comparte, se multiplica."
```

Este proyecto se construye sobre cuatro principios:

1. **Accesibilidad**: el desarrollo web debe estar al alcance de todos.
2. **Aprendizaje real**: los proyectos en producción son la mejor escuela.
3. **Código abierto**: compartir enriquece a toda la comunidad.
4. **Calidad para principiantes**: recursos bien estructurados desde el día uno.

El código fuente completo se liberará en **abril de 2026** bajo licencia MIT, disponible para:

```
study   -- aprender de un proyecto real en producción
fork    -- implementar tu propia versión
extend  -- contribuir con nuevas funcionalidades
adapt   -- personalizarlo para tu negocio
```

---

## ▌ [09] SOBRE EL DESARROLLADOR

**Esteban A.**
`Full-Stack Developer` — autodidacta enfocado en proyectos reales con impacto tangible.

```yaml
Ubicación:      Santiago (Ñuñoa) / Rengo — Chile
Stack:          Python, Flask, MySQL, JavaScript, Bootstrap
OS:             Debian Linux (100% del flujo de trabajo)
Enfoque:        Aprendizaje mediante productos en producción
Objetivo:       Desarrollador profesional — disponible para ofertas laborales
```

### Contacto profesional

```
email   ::  esteban.alh@gmail.com
phone   ::  +56 9 6682 2259
github  ::  estebanalh-ship-it
```

### Key Learnings

```
[✓] Desarrollo full-stack end-to-end
[✓] Integración frontend ↔ backend con API REST
[✓] Diseño y normalización de esquemas MySQL
[✓] Deployment en PythonAnywhere (WSGI)
[✓] UX/UI responsive mobile-first
[✓] Metodologías ágiles aplicadas
[✓] Workflow profesional con Git + GitHub
[✓] Desarrollo 100% en entorno Linux (Debian)
```

---

<div align="center">

```
─────────────────────────────────────────────
        MADE WITH CODE + COFFEE
           Rengo, Chile — 2025/2026
─────────────────────────────────────────────
```

[![GitHub](https://img.shields.io/badge/GITHUB-PROFILE-0f0f0f?style=for-the-badge&logo=github&logoColor=white)](#)
[![Email](https://img.shields.io/badge/EMAIL-CONTACT-1a365d?style=for-the-badge&logo=gmail&logoColor=white)](mailto:esteban.alh@gmail.com)
[![LinkedIn](https://img.shields.io/badge/LINKEDIN-PROFILE-2d3748?style=for-the-badge&logo=linkedin&logoColor=white)](#)

</div>
