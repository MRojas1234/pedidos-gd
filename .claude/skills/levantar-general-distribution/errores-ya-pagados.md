# Errores ya pagados

Cada uno de éstos se descubrió **después** de creer que el trabajo estaba hecho. El
mensaje decía "listo" y los números estaban mal.

Lee esto como lo que es: la factura de lo que ya costó una vez. No la vuelvas a pagar.

---

## 1. Un código de barras no es un producto

**Lo que pasó:** el refresh agrupaba los productos de QuickBooks por código de barras.
Pero QuickBooks tenía **6 códigos puestos en dos productos distintos cada uno**. Al
agrupar sólo por código, uno de cada par desaparecía y al sobreviviente le cambiaba el
nombre.

**Lo que lo arregló:** la llave es `código + nombre`, y **el nombre gana**. En QuickBooks
el nombre sí es único (775 de 775); el código no.

**La lección de verificación, que es la más importante de todas:**
mi primera comprobación agrupó por código, preguntó "¿hay códigos repetidos?" y respondió
**cero fallas**. Era inútil: estaba usando la misma suposición equivocada que el bug.
La comprobación buena fue **por nombre** → 6 fallas.

> Cuando verifiques, no uses la misma suposición que el código que estás verificando.
> Si lo haces, la prueba pasa siempre y no prueba nada.

---

## 2. Los productos nuevos se insertaban y se apagaban solos

**Lo que pasó:** la lista de "lo que no vino de QuickBooks, hay que apagarlo" se calculaba
**antes** del INSERT de los nuevos. Entraban y se apagaban en la misma pasada.

**Lo que lo arregló:** el orden. Apagar primero, insertar después.

**Cómo se detectó:** preguntando *"¿cuántos renglones de QuickBooks NO quedaron activos?"*
Salieron 7. El reporte del refresh decía que todo había salido bien.

---

## 3. Los duplicados fusionados revivían en cada refresh

**Lo que pasó:** se limpiaban duplicados a mano y el siguiente refresh los traía de vuelta,
porque seguían teniendo el mismo nombre y código que su gemelo. La limpieza se deshacía
sola. Los grupos duplicados pasaron de 6 a 12 después de un refresh.

**Lo que lo arregló:** la columna `fusionado_en`. El refresh los salta.

**Cómo se verificó:** corriendo **dos ensayos seguidos**. El segundo tiene que salir todo
en ceros. Si el segundo ensayo todavía reporta cambios, algo se está deshaciendo solo.

> Correr el ensayo dos veces es la prueba más barata que existe para esta clase de bug.

---

## 4. El refresh nunca actualizaba el código de barras

**Lo que pasó:** el refresh traía nombre, categoría y precio, pero **no el `upc`**. Manuel
corregía un código en QuickBooks y la app se quedaba con el viejo para siempre — y el
código es justo lo que lee el escáner.

**Lo que lo arregló:** el refresh también actualiza `upc`.

**Cómo se aplicó sin romper nada:** fueron 125 cambios. Antes de aplicarlos se
**clasificaron todos**: 105 tenían el nombre metido en el campo del código, 20 no tenían
código en QuickBooks, y **cero códigos reales se sobrescribieron**. Sólo entonces se aplicó.

---

## 5. La tienda escogida no sobrevivía a cerrar la app

**El peor de todos, porque todo se veía bien.**

**Lo que pasó:** al reabrir la app volvía el **nombre** del cliente a la pantalla, pero no
su identidad. Medido: pantalla decía el nombre de la tienda, `TIENDA_ID` estaba vacío, **0 precios
de esa tienda cargados**, y cobraba el precio general. **Sin un solo aviso.**

El pedido tampoco quedaba amarrado a la tienda, así que no aparecía en su historial y no
alimentaba "el precio que siempre le hemos dado".

**Lo que lo arregló:** guardar `gd_tienda_id` y `gd_tienda_cod`, no sólo el nombre, y
volver a pedir sus precios al abrir.

> Es el peor tipo de error: la pantalla se ve correcta y los números están mal.
> Cuando guardes algo en el teléfono, **cierra la app y ábrela** antes de decir que
> funciona. Que el nombre reaparezca no prueba que la identidad se guardó.

---

## 6. El panel contaba los productos apagados

**Lo que pasó:** el panel decía **1,811 productos** cuando el catálogo real eran **775**.
Estaba contando también los apagados.

**Lo que lo arregló:** filtrar por `activo = true` en los contadores.

**Quién lo encontró:** Manuel, no yo. Él sabe cuántos productos tiene.

> El dueño del negocio es el mejor detector de números equivocados. Enséñale cifras
> concretas en vez de decirle "ya quedó".

---

## 7. El permiso quitado antes de publicar la app

**Lo que pasó:** se quitó un permiso de la base **antes** de que la app nueva estuviera en
vivo. La base es instantánea; GitHub Pages tarda minutos. En ese hueco la app vieja pedía
una puerta ya cerrada y **Manuel se quedó sin su app en plena ruta**.

**Lo que lo arregló:** revertir el permiso de inmediato, y después hacerlo en el orden
bueno: publicar → comprobar en vivo → quitar el permiso.

---

## 8. Dos falsos negativos que casi se reportaron como fallas

Los dos iban a hacer que se tirara trabajo bueno.

**Las fotos de Shopify.** `curl` devolvió HTTP 000 en las 64 direcciones. Parecían
imágenes muertas. **No lo estaban**: era un bloqueo de red del entorno. El navegador
cargó las 321 sin problema.

**El SKU borrado en QuickBooks.** Se leyó un export viejo (`ls -t` entregó el archivo
anterior porque la descarga nueva nunca se disparó) y parecía que el cambio no se había
guardado. Se detectó porque **los dos archivos tenían el mismo MD5**.

> Antes de reportar que algo falló, pregunta si lo que falló fue la herramienta de medir.
> Un MD5 idéntico o un error de red uniforme casi siempre es la herramienta, no el dato.

---

## 9. Una medición arruinada por el límite de velocidad

**Lo que pasó:** midiendo cuántas fotos se podían conseguir de Open Food Facts, 255 de 332
consultas fallaron por pedir demasiado rápido. Y la primera tasa de éxito que calculé
**sólo contaba las que no fallaron** — o sea, salía altísima y era mentira.

**Lo que lo arregló:** 1.1 segundos entre consultas → cero errores. Y calcular la tasa
sobre **el total**, no sobre las que respondieron.

**El resultado honesto:** 41% de cobertura. Por eso se recomendó la cámara en el panel.

---

## 10. Dos trampas de la herramienta, no del código

**bash se come los acentos graves de markdown.** Pasó dos veces con `python3 -c` dentro de
comillas dobles, y una tercera con un heredoc largo. La salida: escribe el script a un
archivo y córrelo con `python3 -I`, o usa la herramienta de escritura de archivos.

**Se perdió un renglón transcribiendo un CSV** (`Zumba Forritos Pulpa Fire`). Se detectó
comparando una huella por prefijo entre el archivo y lo cargado. Hazlo siempre que
transcribas una lista: cuenta y compara, no confíes en la vista.

---

## Y una cosa que no es un error, pero se ve como uno

**`localStorage` no se comparte** entre la app agregada a la pantalla de inicio (PWA) y el
navegador, en iOS. Son dos almacenes distintos. Si alguien dice "escogí la tienda y no
aparece", pregunta primero desde dónde abrió la app.
