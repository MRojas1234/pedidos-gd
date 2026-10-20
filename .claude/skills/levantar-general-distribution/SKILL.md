---
name: levantar-general-distribution
description: La ruta probada para levantar, mover o reconstruir el sistema de pedidos de General Distribution (app de pedidos + panel + catálogo que se refresca desde QuickBooks). Úsalo cuando se pida instalar el sistema en una cuenta nueva de Supabase o GitHub, cuando algo del refresh de QuickBooks, los precios por tienda, las fotos del catálogo o el inventario no cuadre, o antes de cambiar index.html o panel.html. Trae las decisiones que parecen errores y no lo son, y los errores que ya se pagaron una vez.
---

# Levantar General Distribution

**El negocio:** Manuel Rojas distribuye dulces, abarrotes, bebidas y botanas a tiendas
hispanas, gasolineras y misceláneas en Utah, Colorado e Idaho. Vende en ruta: llega a la
tienda, levanta el pedido en el teléfono, cobra el precio de ese cliente.

**Quién lo construyó:** su hermana María, con Claude Code, entre el 28 de septiembre y el
20 de octubre de 2026. Está en producción y Manuel lo usa en la ruta.

> **Antes de cambiar una línea, lee `CLAUDE.md` en la raíz del repositorio** y
> [`errores-ya-pagados.md`](errores-ya-pagados.md) de esta misma carpeta. No son
> historia: son las trampas que ya costaron dinero y tiempo una vez.

---

## Las tres piezas

| Pieza | Para quién | Qué hace |
|---|---|---|
| `index.html` | Manuel y sus vendedores, en la tienda | Escoge la tienda, levanta el pedido, **cambia el precio ahí mismo** |
| `panel.html` | Manuel, en la oficina | Pedidos, productos, fotos, precios, equipo, refresh de QuickBooks |
| `herramientas/gd-quickbooks.ts` | Nadie: es servidor | Habla con Intuit y refresca el catálogo |

Son dos páginas a propósito. Están en GitHub Pages: HTML plano, sin compilar, sin
`npm install`. Se abre el archivo, se edita, se hace commit y en minutos está en vivo.

---

## 🔴 Los cuatro frenos

Antes de ejecutar cualquier cosa, estos cuatro se verifican. Si uno falla: **detente y
avisa. No lo rodees en silencio.**

1. **¿Estás en el proyecto de Supabase correcto?** El sistema nació en `jema-app`, el
   proyecto de María, donde **también viven La Piñatería, La Nevería, El Rinconcito y
   Flores Utah**. Si estás trabajando para Manuel, confirma el id del proyecto antes de
   cualquier migración o SQL. Un refresh corrido en la base equivocada apaga el catálogo
   de otro negocio.
2. **La llave de servicio (`service_role`) nunca va en `index.html` ni en `panel.html`.**
   Esos archivos son públicos en GitHub Pages. La llave maestra vive sólo dentro de las
   funciones de servidor, como secreto de Supabase.
3. **Nada se borra.** Los productos se apagan con `activo = false` y `apagado_motivo`.
   La gente se apaga con `activo = false`. Los duplicados se marcan `fusionado_en`.
   No hay política de `DELETE` en ninguna tabla, y es a propósito.
4. **Primero el ensayo, después la aplicación.** Todo lo que toca el catálogo en bloque
   corre en seco primero y reporta números. Se leen los números y **luego** se aplica.

---

## La ruta, en orden

Cada fase termina con una verificación. **Verifica la salida, no la bandera:** cuenta el
resultado real en la base o en la pantalla. Los sistemas dicen "hecho" y mienten.

### Fase 1 — La base de datos

El registro de verdad **no es `esquema.sql`**: son las **migraciones de Supabase**. Son 20
con prefijo `gd_`, más dos sueltas, y el orden importa porque varias arreglan a las
anteriores. `esquema.sql` sólo trae las tres tablas originales de pedidos y se quedó
atrás en septiembre.

Los nombres, en orden de aplicación:

```
gd_pedidos_general_distribution          gd_qb_aplicar_fix_producto_id
gd_perfiles_y_lectura_del_panel          gd_apagado_motivo
gd_dueno_administra_su_equipo            gd_quickbooks_conexion
gd_productos_tiendas_e_inventario        gd_qb_aplicar_arregla_los_nuevos
habilitar_http_para_importar_catalogo    gd_qb_aplicar_codigo_repetido_no_borra_productos
vista_tienda_publica_con_id_v2           gd_fusionado_no_revive
gd_estados_del_pedido                    gd_qb_aplicar_tambien_actualiza_el_codigo
gd_sincronizar_quickbooks                gd_bucket_de_fotos
gd_qb_refresh_rpc                        gd_precios_por_tienda
                                         gd_precio_con_candado
                                         gd_cerrar_la_lista_de_tiendas
```

**El SQL ya viene en el repositorio**, en `CREAR-LA-BASE-DE-DATOS.sql`, en la raiz.
Se pega completo en Supabase -> SQL Editor -> New query -> Run. Son 41,681 caracteres
y **no contiene ni un dato**: ni clientes, ni precios, ni pedidos.

No son las 20 migraciones una por una: las funciones del refresh van en su **version
final**, la que corre hoy. Seis de las migraciones se reemplazan entre si y no aportan
nada a una instalacion nueva. Se comprobo caracter por caracter (md5) contra la base, y
el inventario de lo que crea cuadra exacto con lo que existe: 11 tablas, 2 vistas,
10 funciones, 12 reglas de acceso, 15 indices.

Si algun dia necesitas las 20 migraciones literales (para auditar, no para instalar),
salen del proyecto donde corre el sistema con:

```sql
select version, name, array_to_string(statements, ';')
from supabase_migrations.schema_migrations
where name like 'gd\_%'
   or name in ('habilitar_http_para_importar_catalogo','vista_tienda_publica_con_id_v2')
order by version;
```

**Verifica así:** cuenta las tablas `gd_`. Deben ser **11**:
`gd_productos`, `gd_tiendas`, `gd_pedidos`, `gd_pedido_lineas`, `gd_pedido_historial`,
`gd_inventario_mov`, `gd_precio_tienda`, `gd_perfiles`, `gd_qb_import`,
`gd_qb_conexion` y `gd_qb_oauth_estado`.

Más **2 vistas** (`gd_catalogo`, `gd_tienda_publica`), **10 funciones**, **16 reglas de
acceso**, **3 disparadores** y el bucket de fotos `gd-fotos`.

### Fase 2 — Las dos llaves en los archivos

Cuatro líneas, nada más. En `index.html` (líneas ~185) y en `panel.html` (~308):

```
index.html:  var SB_URL = 'https://PROYECTO.supabase.co/rest/v1';
index.html:  var SB_KEY = 'sb_publishable_...';
panel.html:  var SB     = 'https://PROYECTO.supabase.co';
panel.html:  var KEY    = 'sb_publishable_...';
```

Y el WhatsApp a donde llegan los pedidos, en una sola línea de `index.html`:
`var WHATSAPP = '18018986304';`

> La llave `sb_publishable_` **es pública y está bien que lo sea**. Comprobado: con ella
> sola, guardar un pedido devuelve `201` y leer devuelve vacío. Lo peor que puede hacer
> quien la saque del código es mandar un pedido falso. No ve precios, ni clientes, ni
> cuánto vende el negocio.

### Fase 3 — Las dos funciones de servidor

Las dos están en `herramientas/`. Al desplegar:

- `gd-crear-usuario` — para dar de alta gente sin la llave maestra en el teléfono.
- `gd-quickbooks` — **despliégala con `verify_jwt` APAGADO.** No es descuido: trae su
  propio `quienLlama()` que verifica el gafete contra `gd_perfiles`. Con `verify_jwt`
  prendido, el callback de OAuth de Intuit nunca entra.

Sus secretos (`INTUIT_CLIENT_ID`, `INTUIT_CLIENT_SECRET`) se ponen como secretos de
Supabase. **Nunca los pidas por el chat ni los escribas en un archivo.** Manuel los pega
él mismo en el panel de Supabase.

### Fase 4 — La cuenta de dueño

**El primero que se da de alta con `app='gd'` nace dueño.** Así que la primera cuenta del
proyecto nuevo tiene que ser la de Manuel. De ahí en adelante él da de alta a los demás
desde el panel.

### Fase 5 — El catálogo, desde QuickBooks

QuickBooks es la fuente de verdad del catálogo: **775 productos activos**. Shopify ya no lo
es — de ahí sólo se jalaron fotos, nunca productos ni precios.

En el panel, la tarjeta de QuickBooks hace **conectar → ensayo → aplicar**. El ensayo
reporta cuántos entran, cuántos se actualizan, cuántos se apagan y a cuántos les cambia el
código de barras. **Léelos antes de aplicar.** La función se niega sola si el refresh
apagaría más del 80% del catálogo.

**La llave para emparejar productos es `código + nombre`, y el nombre gana.** Esto no es un
detalle: ver *"Un código de barras no es un producto"* en
[`errores-ya-pagados.md`](errores-ya-pagados.md).

**Verifica así, no con el mensaje de "listo":** cuenta los productos activos y compáralos
con los de QuickBooks. Luego corre el ensayo **otra vez**: si no sale todo en ceros, algo
se está deshaciendo solo en cada pasada.

### Fase 6 — Publicar y probar

GitHub Pages: Settings → Pages → Branch `main` / `(root)`.
Lleva `Cache-Control: max-age=600`, así que **un cambio tarda hasta 10 minutos** en verse.
Eso importa para el orden de los despliegues: ver el freno de abajo.

Las seis pruebas que de verdad valen:

- [ ] Levantar un pedido desde el teléfono y que **llegue a la base**
- [ ] Cuadrar a mano: cantidad × precio = importe
- [ ] Escoger una tienda, **cerrar la app, abrirla** y comprobar que siguen sus precios
- [ ] Sin señal: que el pedido **se quede en la cola** y suba solo al volver la señal
- [ ] Con la llave pública sola, **intentar leer** los pedidos → tiene que dar vacío
- [ ] Apagar a alguien desde el panel y comprobar que **deja de ver todo**

---

## 🔴 El orden de los despliegues, cuando el cambio toca la base y la app

**La base es instantánea. GitHub Pages tarda minutos.** Si quitas un permiso antes de que
la app nueva esté en vivo, dejas al vendedor con la app vieja pidiendo una puerta ya
cerrada — y se rompe en plena ruta.

El orden es siempre:

1. Publicar la app
2. **Comprobar que está en vivo** (no suponerlo: abrirla y verla)
3. Hasta entonces, quitar el permiso en la base

Esto ya se hizo al revés una vez y tumbó la app de Manuel mientras vendía.

---

## Los tres precios, que no son lo mismo

Confundirlos es cobrarle mal a un cliente. Están separados a propósito, en tres lugares:

| Precio | Dónde vive | Quién lo manda |
|---|---|---|
| **De catálogo** | `gd_productos.precio` | QuickBooks, en cada refresh |
| **General con 🔒 candado** | `gd_productos.precio_fijo = true` | Manuel, desde el panel. El refresh ya no lo toca |
| **De esa tienda** | `gd_precio_tienda` | Manuel, vendiendo. Es el que gana |

El candado salió gratis de tener las tablas separadas: si el precio de una tienda vive en
su propia tabla, el refresh de QuickBooks no tiene cómo pisarlo.

**El pedido guarda el precio con el que se vendió**, congelado en el renglón. Un pedido
tiene que poder leerse dentro de un año tal como se hizo. No lo cambies a una referencia
al catálogo.

---

## Lo que está pendiente (al 20 de octubre de 2026)

- **Los clientes todavía no se sincronizan desde QuickBooks.** Manuel mantiene teléfonos y
  direcciones directo en QuickBooks y quiere que bajen solos. Es el siguiente trabajo.
- **454 productos sin foto.** Se midió: de las fuentes automáticas se alcanzó 41%. Lo que
  falta se resuelve con fotos de bodega — por eso existe la cámara en el panel.
- **179 productos sin código de barras** en QuickBooks. No se inventan: los corrige Manuel.
- **`LM Paleta Cookies and Cream`** tiene código de 9 dígitos (`677800007`) donde sus ocho
  hermanos tienen 10 que empiezan con `6777800`. Sospechoso, sin confirmar. Pendiente de él.
- **Faltan los escáneres de código de barras.** No se han pedido.
- **`esquema.sql` quedó atrás** en septiembre. Si lo vas a usar, actualízalo primero contra
  las migraciones reales.
