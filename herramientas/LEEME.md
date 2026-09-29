# Herramientas — el molde con el que se hizo la app

> Estos archivos **no son la app**. Son con lo que se construye.
> Van aquí para que no se pierdan: antes vivían en una carpeta temporal.

| Archivo | Qué es |
|---|---|
| `generar-app.py` | El programa que arma `index.html` a partir del catálogo |
| `catalogo-shopify-2026-09-28.json` | Los 551 productos, crudos, como los da Shopify |
| `gd-crear-usuario.ts` | El código de la función de servidor |
| `logo_datauri.txt` | El logo GD incrustado, que usa el generador |

---

## Cómo se actualiza el catálogo

`index.html` **no lee el catálogo de internet**: lo trae incrustado. Por eso abre rápido y
funciona aunque el teléfono ande mal de señal. Cuando Manuel agregue o quite productos en
Shopify, hay que volver a generarlo.

**Paso 1 — bajar el catálogo nuevo.** Se pide a la tienda pública, sin cuenta:

```
https://candyshopgd.myshopify.com/products.json?limit=250&page=1
https://candyshopgd.myshopify.com/products.json?limit=250&page=2
https://candyshopgd.myshopify.com/products.json?limit=250&page=3
```

Se juntan los productos de todas las páginas en un solo archivo JSON, con la misma forma
que `catalogo-shopify-2026-09-28.json` (una lista, no un objeto).

> ⚠️ **El botón Export de Shopify no sirve** con más de 50 productos: en vez de descargar
> el archivo, se lo manda **por correo al dueño de la tienda**. Por eso se usa esta vía.
>
> ⚠️ **El catálogo público no trae los borradores.** En el admin hay 50+ productos en
> *Draft* que aquí no aparecen. Si Manuel los vende, hay que publicarlos en Shopify.

**Paso 2 — apuntar el generador al archivo nuevo.** Dentro de `generar-app.py`, la
variable `SRC` de hasta arriba dice cuál archivo leer.

**Paso 3 — correrlo.**

```bash
python3 generar-app.py
```

Escribe `index.html` ya con todo dentro y dice cuántos productos quedaron, cuántos sin
foto y cuántos con precio en cero.

**Paso 4 — probar antes de publicar.** Nunca subir sin abrirlo:

```bash
python3 -m http.server 8777
```

Y revisarlo en tamaño de teléfono. Cuadrar que el número de productos sea el esperado.

---

## Cómo se vuelve a subir la función de servidor

`gd-crear-usuario.ts` se despliega en Supabase → **Edge Functions**, con el nombre
**`gd-crear-usuario`** y **verify_jwt activado**.

Las dos variables que usa (`SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY`) **las pone
Supabase solo**. No hay que escribirlas, ni ponerlas en ningún archivo.

Para comprobar que quedó bien, hay que probar las tres caras:

1. Un **dueño** la llama → crea la cuenta
2. Un **vendedor** la llama → *"Solo el dueño puede dar de alta a alguien"* (403)
3. **Sin sesión** → 401

Si la tercera no da 401, algo quedó mal y **cualquiera podría crear cuentas**.
