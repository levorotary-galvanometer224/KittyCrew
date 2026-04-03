# KittyCrew - un hogar cálido para tus mascotas y compañeros de IA

[English](../../README.md) | [简体中文](./README.zh-CN.md) | [繁體中文](./README.zh-TW.md) | [日本語](./README.ja.md) | [한국어](./README.ko.md) | Español | [Русский](./README.ru.md)

KittyCrew es un hogar adorable y local-first para tus mascotas y compañeros de IA. Puedes reunir a Claude Code, Codex y GitHub Copilot como personalidades distintas, dar a cada miembro su propio espacio y conjunto de habilidades, y convivir con ellos en un entorno cálido con temática felina.

![KittyCrew homepage](../../assets/homepage.png)

---

## Navegación Rápida

[Por qué KittyCrew](#por-qué-kittycrew) · [Funciones](#funciones) · [Inicio Rápido](#inicio-rápido) · [Cómo Funciona](#cómo-funciona) · [Hoja de Ruta](#hoja-de-ruta)

---

## Por qué KittyCrew

La mayoría de las herramientas de IA se sienten como paneles fríos y utilitarios. KittyCrew las convierte en un hogar compartido y acogedor:

- Reúne a Claude Code, Codex y GitHub Copilot como compañeros con personalidades distintas.
- Organiza a tus mascotas y compañeros en crews pequeñas de hasta cinco miembros.
- Configura para cada miembro su modelo, directorio de trabajo y lista aprobada de habilidades.
- Mantén historial de chat, memoria de contexto y respuestas en streaming para cada miembro en la misma interfaz.
- Funciona con enfoque local-first y detecta los providers disponibles en tu propia máquina.

KittyCrew está pensado para quienes quieren sentir a la IA como compañía cercana, sin renunciar al control local ni a una interfaz amable.

## Funciones

### Un hogar acogedor para varias mascotas

- Crea y administra múltiples crews en una sola aplicación web.
- Convierte cada crew en una pequeña familia de mascotas y compañeros de IA.
- Observa por separado las respuestas y el estado de cada miembro.

### Personalidades de IA distintas

- Soporta miembros de Claude Code, Codex y GitHub Copilot.
- Detecta los CLI locales de provider en tiempo de ejecución.
- Conserva la selección de modelo por miembro para mantener su estilo en conversaciones futuras.

### Privado y local

- Cada miembro tiene su propio estado de sesión persistente.
- Cada miembro puede usar un directorio de trabajo diferente.
- El acceso a skills puede limitarse por miembro en vez de exponerlo todo.

### Una UI pensada para el apego

- Tarjetas de crew con temática felina y selección de avatar.
- Flujos inline para renombrar, eliminar, poner en cola y cancelar.
- Vista ampliada del miembro para conversaciones más largas y personales.

## Inicio Rápido

### 1. Instalar

```bash
python -m pip install -e .
```

### 2. Lanzar

```bash
kittycrew
```

La interfaz web se ejecuta por defecto en [http://127.0.0.1:8731](http://127.0.0.1:8731).

Si prefieres ejecutarlo directamente desde la raíz del repositorio:

```bash
PYTHONPATH=src python -m kittycrew
```

## Cómo Funciona

KittyCrew combina una aplicación web FastAPI con adaptadores de provider expuestos mediante `a2a-sdk`.

- La UI web administra crews, members, estado del chat y persistencia local.
- Los adaptadores conectan con los CLI de Claude Code, Codex y GitHub Copilot.
- Cada miembro se asigna a un registro de sesión aislado con su propia configuración de ejecución.
- La salida en streaming vuelve a la interfaz para que cada compañero se sienta presente en el mismo lugar.

## Casos de Uso

- Cuidar una pequeña familia de mascotas y compañeros de IA con personalidades distintas.
- Crear crews para compañía diaria, rituales compartidos o proyectos personales.
- Dar a cada miembro su propia habitación, modelo y lista blanca de skills.
- Mantener abierto un hogar local de IA que se sienta más como un espacio vivo que como un panel de herramientas.

## Estructura del Proyecto

```text
src/kittycrew/        App FastAPI, capa de servicios, adaptadores de provider, UI estática
tests/                Cobertura de regresión para servicios y app
assets/               Recursos del proyecto y del README
data/                 Almacenamiento local de sesiones y estado
docs/readme/          README en varios idiomas
```

## Hoja de Ruta

- Más tipos de compañeros bajo el mismo modelo de crew.
- Mejores interacciones, rutinas y experiencias compartidas entre miembros.
- Formas más ricas de entender la historia y el estado de cada miembro.
- Mejor experiencia de instalación y onboarding.

## Notas

- KittyCrew conserva el historial por miembro y reutiliza el contexto reciente en turnos futuros.
- La aplicación espera que los CLI de provider correspondientes y `a2a-sdk` estén disponibles en el entorno activo.
- La disponibilidad de provider se detecta en tiempo de ejecución, por lo que los entornos incompletos degradan de forma razonable.

## License

MIT.
