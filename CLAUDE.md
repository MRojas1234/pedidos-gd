# General Distribution — app de pedidos

> Léeme completo antes de cambiar nada. Aquí están las decisiones que **ya se tomaron
> a propósito**. Varias se ven como errores y no lo son.

**El negocio:** Manuel distribuye dulces, abarrotes, bebidas y botanas a tiendas hispanas,
gasolineras y misceláneas en Utah. Su tienda en línea es Shopify (`candyshopgd`).

**Quién construyó esto:** su hermana María, con Claude Code, el 28 de septiembre de 2026,
en una tarde. Se hizo para que él la probara al día siguiente en la ruta.

---

## Qué son estos dos archivos

| Archivo | Para quién | Qué hace |
|---|---|---|
| `index.html` | El repartidor, en la tienda | Levanta el pedido y lo guarda |
| `panel.html` | Manuel | Ve los pedidos y administra a su equipo |

**Son dos a propósito.** El repartidor no debe ver precios de negocio, totales del mes ni
usuarios. Y no debe tener que acordarse de una contraseña parado en una tienda.

---

## Las siete decisiones que NO hay que "arreglar"

### 1. El JavaScript está escrito a la antigua, y así se queda
Nada de `const`, `let`, funciones flecha, plantillas de texto ni `async/await`.
**Razón:** los repartidores traen teléfonos viejos. Ya pasó con una tableta donde la página
abría pero el JavaScript moderno no corría. Si "modernizas" esto, la app deja de funcionar
en los teléfonos de la gente que la usa y **nadie te va a avisar**: simplemente dejan de
levantar pedidos.

### 2. Al tocar `+` se repinta SOLO ese renglón
La primera versión redibujaba los 551 productos en cada toque y **se perdía un toque de
cada tres**. Si tocas esta parte, prueba tocando `+` tres veces seguidas rápido y cuenta.

### 3. El buscador escucha `onkeyup` **y** `oninput` **y** `onchange`
No es redundancia. Con solo `onkeyup` el buscador se cae con **dictado por voz**, pegado y
autocompletado. El repartidor dicta, no teclea: trae las manos ocupadas.

### 4. La llave de Supabase que está en el código es PÚBLICA, y está bien
Esa llave **solo puede escribir pedidos, no leerlos**. Está comprobado: guardar devuelve
`201`, leer devuelve `[]`. Si alguien la saca del código, lo peor que puede hacer es mandar
un pedido falso. **No puede ver precios, tiendas ni cuánto vende el negocio.**

**Nunca** pongas la llave de servicio (`service_role`) en `index.html` ni en `panel.html`.
Esa abre todo. Vive solo dentro de la función de servidor.

### 5. El id del pedido lo genera el teléfono, no la base
Para no necesitar permiso de lectura — que es justo lo que le quitamos a la app.
Como efecto, **reintentar subir el mismo pedido es seguro**: la base contesta `409`
(repetido) y el código **trata el 409 como éxito**. No lo cambies a error.

### 6. Hay una cola para cuando no hay señal
El pedido se guarda primero en el teléfono (`localStorage`, llave `gd_cola`) y se sube
después. Si no hay señal se queda en la cola, sale un aviso amarillo, y **se reintenta solo
cada vez que se abre la app**. Probado apuntando la app a un servidor inexistente.

### 7. Los avisos van DENTRO de la app
Nada de `alert()` ni `confirm()`: en la tableta vieja estaban bloqueados y la app se
quedaba muda. Los mensajes salen en recuadros de la propia página.

---

## Cómo está la base de datos

Prefijo `gd_`. Dos tablas de pedidos y una de personas.

| Tabla | Qué guarda |
|---|---|
| `gd_pedidos` | Cabecera: folio, tienda, nota, artículos, total, `es_prueba`, fecha |
| `gd_pedido_lineas` | Renglones: producto, categoría, precio, cantidad, importe |
| `gd_perfiles` | Quién puede entrar al panel: nombre, correo, rol, `activo` |

**El nombre y el precio se congelan en el renglón.** El catálogo vive en Shopify y ahí los
precios cambian; un pedido tiene que poder leerse dentro de un año tal como se hizo.
No lo cambies a una referencia al catálogo.

### Las reglas de acceso (esto es lo que de verdad protege el negocio)

- **Escribir pedidos:** cualquiera con la llave pública. Es un buzón.
- **Leer pedidos:** solo quien tenga fila en `gd_perfiles` con `activo = true`.
- **Dar de alta gente:** solo `rol = 'dueno'`, y **a través de la función de servidor**
  `gd-crear-usuario`, que es la única que tiene la llave maestra.
- **Borrar personas:** no existe. A propósito **no hay política de `DELETE`**.
  Se apaga con `activo = false`, y el historial queda.

Ojo: una política sobre `gd_perfiles` que consulte `gd_perfiles` **entra en recursión
infinita**. Por eso la pregunta "¿es dueño?" vive aparte, en la función `gd_es_dueno()`.

---

## El catálogo

**551 productos**, bajados del catálogo público de Shopify
(`candyshopgd.myshopify.com/products.json`) el 28 de septiembre de 2026.
Están **incrustados dentro de `index.html`**, no se descargan.

- Dulces 303 · Abarrotes 105 · Bebidas 100 · Botanas 30 · Otros 13
- 5 productos sin foto y 5 con precio `$0.00` (la app los marca "Precio por confirmar")
- **Faltan los borradores**: en el admin de Shopify hay 50+ en *Draft* que el catálogo
  público no muestra. Preguntarle a Manuel si esos se venden.

Para actualizarlo hay que volver a bajar el JSON y regenerar el HTML.
**El botón Export de Shopify no sirve** con más de 50 productos: manda el archivo por
correo al dueño de la tienda en vez de descargarlo.

---

## El molde está en `herramientas/`

La app **no se edita a mano**: `index.html` lo escribe un programa a partir del catálogo.
Si editas el HTML directo, el siguiente que regenere lo borra todo.

| Archivo | Qué es |
|---|---|
| `herramientas/generar-app.py` | Arma `index.html` desde el catálogo |
| `herramientas/catalogo-shopify-2026-09-28.json` | Los 551 productos, crudos |
| `herramientas/gd-crear-usuario.ts` | El código de la función de servidor |
| `herramientas/LEEME.md` | Cómo actualizar el catálogo y volver a subir la función |

`panel.html` sí se edita a mano: ése no se genera.

## Las reglas de la casa

1. **Verifica la salida, no la bandera.** Los sistemas dicen "hecho" y mienten. Cuenta el
   resultado real: consulta la base, lee el contador dentro de la página. Las capturas de
   pantalla llegaron retrasadas dos veces en un mismo día y enseñaron lo de antes.
2. **Nada se borra.** Lo de prueba se marca `es_prueba = true`. La gente se apaga con
   `activo = false`.
3. **Nunca inventes datos** — precios, fechas, cifras. Si no lo sabes, dilo.
4. **Nada destructivo sin aprobación** del dueño.

## Cómo se prueba de verdad

No basta con mirar la pantalla. Lo que sirve:

- Servir la carpeta (`python3 -m http.server`) y usarla en tamaño de teléfono (375×812).
- Armar un pedido, recargar la página y **comprobar que sobrevivió**.
- Consultar la base y **cuadrar los números a mano** (cantidad × precio = importe).
- Para la cola: apuntar `SB_URL` a un servidor inexistente, mandar un pedido, y verificar
  que se queda; luego recargar con la dirección buena y ver que sube solo.
