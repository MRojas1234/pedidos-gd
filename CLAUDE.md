# General Distribution — app de pedidos

> Léeme completo antes de cambiar nada. Aquí están las decisiones que **ya se tomaron a
> propósito**. Varias se ven como errores y no lo son.

**El negocio:** Manuel Rojas distribuye dulces, abarrotes, bebidas y botanas a tiendas
hispanas, gasolineras y misceláneas en **Utah, Colorado e Idaho**. Vende en ruta: llega a
la tienda, levanta el pedido en el teléfono, cobra el precio de ese cliente.

**Quién construyó esto:** su hermana María, con Claude Code, entre el **28 de septiembre y
el 20 de octubre de 2026**. Está en producción y él lo usa vendiendo.

> **Si vas a levantar el sistema en otra cuenta**, o algo del refresh de QuickBooks no
> cuadra, usa el Skill: `.claude/skills/levantar-general-distribution/`. Trae la ruta en
> seis fases y, en `errores-ya-pagados.md`, los diez errores que ya costaron una vez.

---

## Las tres piezas

| Archivo | Para quién | Qué hace |
|---|---|---|
| `index.html` | Manuel y sus vendedores, en la tienda | Escoge la tienda, levanta el pedido, **cambia el precio ahí mismo** |
| `panel.html` | Manuel, en la oficina | Pedidos, productos, fotos, precios, equipo, refresh de QuickBooks |
| `herramientas/gd-quickbooks.ts` | Nadie: es servidor | Habla con Intuit y refresca el catálogo |

**Son dos páginas a propósito.** El vendedor no necesita ver totales del mes ni usuarios.

HTML plano en GitHub Pages: sin compilar, sin `npm install`. Se edita, se hace commit y en
minutos está en vivo. Lleva `Cache-Control: max-age=600`, así que **un cambio tarda hasta
10 minutos** en verse — eso importa para el orden de los despliegues (más abajo).

---

## Las decisiones que NO hay que "arreglar"

### 1. El JavaScript está escrito a la antigua, y así se queda
Nada de `const`, `let`, funciones flecha, plantillas de texto ni `async/await`.
**Razón:** los vendedores traen teléfonos viejos. Ya pasó con una tableta donde la página
abría pero el JavaScript moderno no corría. Si "modernizas" esto, la app deja de funcionar
en los teléfonos de la gente que la usa y **nadie te va a avisar**: simplemente dejan de
levantar pedidos.

### 2. Al tocar `+` se repinta SOLO ese renglón
La primera versión redibujaba todos los productos en cada toque y **se perdía un toque de
cada tres**. Si tocas esta parte, prueba tocando `+` tres veces seguidas rápido y cuenta.

### 3. El buscador escucha `onkeyup` **y** `oninput` **y** `onchange`
No es redundancia. Con solo `onkeyup` el buscador se cae con **dictado por voz**, pegado y
autocompletado. El vendedor dicta, no teclea: trae las manos ocupadas.

### 4. La llave de Supabase que está en el código es PÚBLICA, y está bien
Comprobado: con ella sola, guardar un pedido devuelve `201` y leer devuelve vacío. Lo peor
que puede hacer quien la saque del código es mandar un pedido falso. **No ve precios, ni
clientes, ni cuánto vende el negocio.**

**Nunca** pongas la llave de servicio (`service_role`) en `index.html` ni en `panel.html`.
Esos archivos son públicos. La llave maestra vive solo dentro de las funciones de servidor.

### 5. El id del pedido lo genera el teléfono, no la base
Para no necesitar permiso de lectura — que es justo lo que le quitamos a la app.
Como efecto, **reintentar subir el mismo pedido es seguro**: la base contesta `409`
(repetido) y el código **trata el 409 como éxito**. No lo cambies a error.

### 6. Hay una cola para cuando no hay señal
El pedido se guarda primero en el teléfono (`localStorage`, llave `gd_cola`) y se sube
después. Si no hay señal se queda en la cola, sale un aviso amarillo, y **se reintenta solo
cada vez que se abre la app**. Probado apuntando la app a un servidor inexistente.

### 7. Los avisos van DENTRO de la app
Nada de `alert()`: en la tableta vieja estaban bloqueados y la app se quedaba muda. Los
mensajes salen en recuadros de la propia página.

### 8. El pedido congela el nombre y el precio con el que se vendió
Un pedido tiene que poder leerse dentro de un año tal como se hizo. **No lo cambies a una
referencia al catálogo**, porque QuickBooks mueve los precios.

### 9. `gd_qb_aplicar` inserta los nuevos AL FINAL, después de apagar
Se ve raro y es el arreglo de un bug: cuando el INSERT iba antes, los productos nuevos
caían en la lista de "lo que no vino" y **se apagaban solos en la misma pasada**.

### 10. La llave para emparejar con QuickBooks es `código + nombre`, y el nombre gana
**Un código de barras no es un producto.** QuickBooks tiene 6 códigos puestos en dos
productos distintos cada uno; agrupar solo por código hacía desaparecer uno de cada par.
En QuickBooks el **nombre** sí es único (775 de 775).

---

## Cómo está la base de datos

Prefijo `gd_`. **11 tablas, 2 vistas, 10 funciones.** El archivo
[`CREAR-LA-BASE-DE-DATOS.sql`](CREAR-LA-BASE-DE-DATOS.sql) la levanta completa desde cero.

| Tabla | Qué guarda |
|---|---|
| `gd_productos` | El catálogo. Lo manda QuickBooks |
| `gd_tiendas` | Los clientes, con su código para el link `?t=codigo` |
| `gd_pedidos` | Cabecera: folio, tienda, nota, total, estado, `es_prueba` |
| `gd_pedido_lineas` | Renglones, con nombre y precio **congelados** |
| `gd_pedido_historial` | Cada cambio de estado, con quién y cuándo |
| `gd_inventario_mov` | Aquí vive la verdad del inventario |
| `gd_precio_tienda` | **El precio de cada cliente** |
| `gd_perfiles` | Quién puede entrar al panel |
| `gd_qb_import` | Mesa de trabajo del refresh. Se vacía en cada pasada |
| `gd_qb_conexion` + `gd_qb_oauth_estado` | La conexión con Intuit. Nadie las lee desde la app |

**La existencia la lleva un disparador, no se escribe a mano.** Un error se corrige con
otro movimiento, nunca editando el número.

### Las reglas de acceso (esto es lo que de verdad protege el negocio)

- **Escribir pedidos:** cualquiera con la llave pública. Es un buzón.
- **Leer pedidos:** solo quien tenga fila en `gd_perfiles` con `activo = true`.
- **La lista de clientes:** sin sesión **no se puede listar**. Solo se pregunta por UNA
  tienda sabiendo su código exacto (`gd_tienda_por_codigo`). Esto cerró una fuga real:
  antes cualquiera con un link se bajaba los 108 clientes prendidos.
- **Dar de alta gente:** solo `rol = 'dueno'`, por la función `gd-crear-usuario`.
- **Borrar:** no existe. **No hay política de `DELETE` en ninguna tabla.**

Ojo: una política sobre `gd_perfiles` que consulte `gd_perfiles` **entra en recursión
infinita**. Por eso "¿es dueño?" vive aparte, en `gd_es_dueno()`.

---

## El catálogo: QuickBooks manda

**775 productos activos** (y 1,036 apagados que se conservan, nunca se borran).
Categorías: Abarrotes, Bebidas, Dulces, Helados, Otros, Snacks.

**El catálogo NO está incrustado en el HTML.** Vive en la base y la app lo pide por la
vista `gd_catalogo`, que a propósito no trae existencia ni costos.

**Shopify ya no manda nada.** De ahí solo se jalaron fotos. El archivo
`herramientas/catalogo-shopify-2026-09-28.json` es histórico: no es la fuente de verdad.

El refresh va en el panel: **conectar → ensayo → aplicar**. El ensayo reporta cuántos
entran, se actualizan, se apagan y a cuántos les cambia el código. **Léelos antes de
aplicar.** La función se niega sola si apagaría más del 80% del catálogo.

**Al 20 de octubre de 2026:** 322 con foto, **453 sin foto**, 179 sin código de barras.

---

## Los tres precios, que no son lo mismo

Confundirlos es cobrarle mal a un cliente. Están separados a propósito:

| Precio | Dónde vive | Quién lo manda |
|---|---|---|
| **De catálogo** | `gd_productos.precio` | QuickBooks, en cada refresh |
| **General con 🔒 candado** | `gd_productos.precio_fijo` | Manuel, desde el panel. El refresh ya no lo toca |
| **De esa tienda** | `gd_precio_tienda` | Manuel, vendiendo. **Es el que gana** |

El candado salió gratis de tener las tablas separadas: si el precio de una tienda vive en
su propia tabla, el refresh no tiene cómo pisarlo.

---

## 🔴 El orden de los despliegues, cuando el cambio toca la base y la app

**La base es instantánea. GitHub Pages tarda minutos.** Si quitas un permiso antes de que
la app nueva esté en vivo, dejas al vendedor con la app vieja pidiendo una puerta ya
cerrada. El orden es siempre:

1. Publicar la app
2. **Comprobar que está en vivo** (no suponerlo: abrirla y verla)
3. Hasta entonces, quitar el permiso en la base

Esto ya se hizo al revés una vez y tumbó la app de Manuel mientras vendía.

---

## Las reglas de la casa

1. **Verifica la salida, no la bandera.** Los sistemas dicen "hecho" y mienten. Cuenta el
   resultado real en la base. Y **no verifiques con la misma suposición que el código que
   estás verificando**: la primera comprobación de los códigos repetidos agrupaba por
   código igual que el bug, respondió "cero fallas" y no probaba nada.
2. **Nada se borra.** Lo de prueba se marca `es_prueba = true`. Los productos se apagan con
   `activo = false` y `apagado_motivo`. La gente con `activo = false`.
3. **Nunca inventes datos** — precios, códigos de barras, fechas, cifras. Si no lo sabes,
   dilo. Un código de barras inventado manda mercancía equivocada.
4. **Nada destructivo sin aprobación** del dueño.
5. **Los secretos no pasan por el chat.** Las llaves de Intuit las pega Manuel en el panel
   de Supabase.

---

## Cómo se prueba de verdad

No basta con mirar la pantalla:

- Servirlo y usarlo en tamaño de teléfono (375×812).
- Armar un pedido, **recargar** y comprobar que sobrevivió.
- **Escoger una tienda, cerrar la app y abrirla**: tienen que seguir sus precios. Que
  reaparezca el nombre no prueba nada — ya pasó que volvía el nombre sin la identidad, y
  cobraba el precio general sin avisar.
- Cuadrar a mano: cantidad × precio = importe.
- Para la cola: apuntar `SB_URL` a un servidor inexistente, mandar un pedido, y verificar
  que se queda; luego recargar con la dirección buena y ver que sube solo.
- Para el refresh: correr el ensayo **dos veces**. La segunda tiene que salir en ceros.

---

## Qué cambió desde el 28 de septiembre

Este documento decía cosas que ya no son ciertas. Queda anotado para que nadie se guíe por
la versión vieja si se la encuentra en el historial:

- **Ya no son 551 productos de Shopify incrustados en `index.html`.** Son 775 de
  QuickBooks, y viven en la base.
- **`herramientas/generar-app.py` no existe.** Se mencionaba un generador que armaba el
  HTML desde el catálogo; ese camino se abandonó cuando el catálogo pasó a la base.
  **`index.html` ahora sí se edita a mano**, igual que `panel.html`.
- **`esquema.sql` ya no es el instalador.** Se quedó con las tres tablas de pedidos. Se
  conserva como histórico, con su aviso adentro. El bueno es
  `CREAR-LA-BASE-DE-DATOS.sql`.
- **La base pasó de 3 tablas a 11**, con tiendas, inventario, estados del pedido, precios
  por tienda y la conexión con QuickBooks.
