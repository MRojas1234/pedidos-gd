# Traspaso a Manuel — para que trabaje con su propio Claude Code

_Escrito el 28 de septiembre de 2026. **Revisado el 20 de octubre.**_

> ### ⚠️ Lee esto primero
>
> Este documento sigue sirviendo para entender **por qué** hay que separar las cuentas, y
> los pasos de GitHub y Supabase siguen siendo buenos. Pero la ruta completa y al día
> vive en el **Skill**: `.claude/skills/levantar-general-distribution/`. Esa es la que hay
> que seguir, porque trae la verificación de cada paso y los errores ya pagados.
>
> Lo que cambió desde septiembre: el catálogo ya **no** sale de Shopify sino de
> **QuickBooks** (775 productos), la base pasó de **3 tablas a 11**, y el instalador ya
> **no** es `esquema.sql` sino `CREAR-LA-BASE-DE-DATOS.sql`.

Hoy la app funciona, pero **vive en las cuentas de María**. Este documento es la lista
exacta para pasarla a las de Manuel, en orden, sin que se rompa nada.

---

## ⚠️ Por qué esto NO es opcional

No es filosofía de propiedad. Es un riesgo concreto:

**Hoy las tablas `gd_` viven en el proyecto de Supabase de María (`jema-app`), junto con
las de La Piñatería, La Nevería, El Rinconcito y Flores Utah.**

Si Manuel conecta su Claude Code a ese proyecto, **su Claude puede leer y modificar las
tablas de los negocios de María.** No por malicia: porque ahí están, y un asistente que
ve una base entera puede tocar lo que no debía.

Por eso el paso de la base de datos es el importante. Lo demás es trámite.

---

## Lo que hace cada quien

| Paso | Quién | Cuánto tarda |
|---|---|---|
| 1. Cuenta de GitHub | Manuel | 5 min |
| 2. Pasarle el repositorio | María | 2 min |
| 3. Cuenta y proyecto de Supabase | Manuel | 10 min |
| 4. Crear las tablas | Manuel o su Claude | 2 min |
| 5. Cambiar dos datos en los archivos | su Claude | 2 min |
| 6. Volver a subir la función de servidor | su Claude | 5 min |
| 7. Crear su cuenta de dueño | su Claude | 5 min |
| 8. Publicar y probar | su Claude | 10 min |

---

## Paso 1 — Manuel abre su cuenta de GitHub

En `github.com`. Que **anote su usuario** y se lo pase a María.
Es gratis. Ahí va a vivir la app.

## Paso 2 — María le pasa el repositorio

En `github.com/MRojas1234/pedidos-gd` →
**Settings → General → hasta abajo, Danger Zone → Transfer ownership**.
Se escribe el usuario de Manuel y se confirma.

Se va **todo**: los archivos y el historial completo. María puede quedarse como
colaboradora si él quiere que le siga ayudando.

> Al transferirlo **cambia la dirección de la página**. Pasa de
> `mrojas1234.github.io/pedidos-gd/` a `<su-usuario>.github.io/pedidos-gd/`.
> **Hay que volver a activar GitHub Pages** en el repositorio nuevo:
> Settings → Pages → Branch: `main` / `(root)` → Save.
> Y hay que **pasarle la dirección nueva a los repartidores**.

## Paso 3 — Manuel abre su propio Supabase

En `supabase.com`, gratis. Crea **un proyecto nuevo** — puede llamarse
`general-distribution`. Que apunte la región más cercana (Estados Unidos, este).

Que **guarde bien** dos datos de **Settings → API**:
- La **URL del proyecto**
- La **llave publicable** (`sb_publishable_...`) ← ésta es la del buzón, va en la app
- La **llave de servicio** (`service_role`) ← **ésta NUNCA va en la app**, es la maestra

> **Aviso del plan gratis:** un proyecto de Supabase **se duerme solo** tras una semana
> sin actividad, y la app deja de guardar hasta que alguien lo despierta. Si el negocio
> va a estar quieto por temporadas, hay que ponerle un "despertador" (una tarea que lo
> toque cada día). Su Claude sabrá hacerlo; está resuelto así en las apps de María.

## Paso 4 — Crear las tablas

En Supabase → **SQL Editor → New query**, pegar completo el archivo
[`CREAR-LA-BASE-DE-DATOS.sql`](CREAR-LA-BASE-DE-DATOS.sql) y darle **Run**.

Eso crea las **11 tablas**, las 2 vistas, las 10 funciones, las reglas de acceso, los
disparadores y el lugar de las fotos. **No hay que capturar nada a mano.**

> **NO uses `esquema.sql`.** Es de septiembre y sólo trae tres tablas: la base quedaría a
> medias y la app no funcionaría. Se conserva como histórico, con su aviso adentro.

**Comprueba antes de seguir:** cuenta las tablas `gd_`. Deben ser **11**.

> **Los pedidos viejos no se van solos, y se decidió NO moverlos.** Al 20 de octubre hay
> **24 pedidos**, 865 clientes y 1,154 movimientos de inventario en la base de María.
>
> **La salida buena no es mover los datos: es no necesitarlos.** El catálogo y los
> clientes de Manuel salen de **su propio QuickBooks**, así que su proyecto nuevo se llena
> de su propia fuente. Lo único que se quedaría atrás son esos 24 pedidos y unos
> movimientos que de todos modos iba a recontar.
>
> Y hay una razón de peso: sacar esos datos por una puerta temporal en la base **habría
> expuesto los 865 clientes con nombre, teléfono y dirección**. Si algún día de verdad
> hacen falta, los baja **una persona** desde el panel de Supabase, con María presente.

## Paso 5 — Cambiar los dos datos en los archivos

En `index.html` y en `panel.html` hay que cambiar la dirección y la llave publicable por
las nuevas del Paso 3. Están marcadas con comentario y son estas líneas:

```
var SB_URL = 'https://....supabase.co/rest/v1';     ← en index.html
var SB_KEY = 'sb_publishable_...';                   ← en index.html
var SB     = 'https://....supabase.co';              ← en panel.html
var KEY    = 'sb_publishable_...';                   ← en panel.html
```

Y de paso, si cambia el WhatsApp a donde llegan los pedidos, está en **una sola línea**
de `index.html`:

```
var WHATSAPP = '18018986304';
```

## Paso 6 — Volver a subir la función de servidor

La función `gd-crear-usuario` es la que deja que Manuel dé de alta a su gente **sin tener
la llave maestra en el teléfono**. Hay que desplegarla en su proyecto nuevo.

El código completo está en **`herramientas/gd-crear-usuario.ts`**, en este mismo
repositorio, con las instrucciones en `herramientas/LEEME.md`. Su Claude Code puede
desplegarlo si le conecta el MCP de Supabase.

## Paso 7 — Su cuenta de dueño

**El primero que se da de alta con `app='gd'` nace como dueño.** Así que la primera
cuenta que se cree en el proyecto nuevo debe ser la de Manuel. De ahí en adelante él
mismo da de alta a los demás desde el panel.

## Paso 8 — Probar de verdad, no de palabra

Antes de decir "listo", comprobar las cinco:

- [ ] Levantar un pedido desde el teléfono y que **llegue a la base**
- [ ] Cuadrar los números a mano: cantidad × precio = importe
- [ ] Sin señal: que el pedido **se quede en la cola** y suba solo al volver
- [ ] Con la llave publicable sola, **intentar leer** los pedidos → debe dar vacío
- [ ] Apagar a alguien desde el panel y comprobar que **deja de ver todo**

---

## Lo que Manuel le tiene que dar a su Claude Code el primer día

1. **Este repositorio**, ya en su cuenta.
2. **El archivo [`CLAUDE.md`](CLAUDE.md)** que está aquí adentro. Es lo más importante:
   trae las siete decisiones que parecen errores y no lo son. Sin eso, un Claude nuevo va
   a "modernizar" el JavaScript y **la app va a dejar de funcionar en los teléfonos viejos
   de los repartidores, sin que nadie se dé cuenta.**
3. **El MCP de Supabase**, conectado a **su** proyecto, no al de María.

## Lo que le conviene armar aparte

María tiene un **cerebro**: una carpeta de notas donde queda escrito lo que se decide y lo
que se aprende, y que su Claude lee al arrancar cada sesión. Es la razón de que se pueda
retomar el trabajo meses después sin repetir errores.

Si Manuel va a trabajar seguido con Claude Code, **le conviene armar el suyo desde el
primer día**. Es una carpeta con notas y un repositorio, nada más — pero cambia todo.
Que se lo pida a su Claude.
