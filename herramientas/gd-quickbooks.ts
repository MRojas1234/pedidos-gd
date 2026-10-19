// =====================================================================
//  gd-quickbooks — trae el catalogo directo de QuickBooks, sin archivo
//
//  QUE PUEDE Y QUE NO:
//    - SOLO LEE de QuickBooks. Nunca escribe, nunca borra, nunca toca
//      una factura ni un pago. Si Intuit le diera permiso de escribir,
//      esta funcion no lo usa: no hay una sola llamada que no sea GET.
//    - Manuel puede cortarla cuando quiera, sin pedirmelo a mi:
//      desde el panel ("Desconectar") o desde su propia cuenta de Intuit.
//
//  DONDE VIVE EL SECRETO:
//    QB_CLIENT_ID y QB_CLIENT_SECRET viven en los secretos de Supabase.
//    No estan en este archivo, ni en el repositorio, ni en el panel, ni
//    pasaron por una conversacion. Si alguno paso por chat alguna vez,
//    se ROTA desde developer.intuit.com.
//
//  SI LOS SECRETOS NO ESTAN:
//    la funcion lo DICE, con el contador en cero. No falla callada.
//    (leccion "variable-de-entorno-subida-no-es-variable-activa")
//
//  Desplegar como:  gd-quickbooks   con verify_jwt APAGADO.
//  El verify_jwt va apagado porque Intuit regresa al usuario a esta
//  direccion sin sesion de Supabase. La revision de quien llama la hace
//  esta funcion a mano, abajo, en quienLlama().
// =====================================================================

const SB_URL   = Deno.env.get("SUPABASE_URL")!;
const SB_SERV  = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const CLIENTE  = Deno.env.get("QB_CLIENT_ID") ?? "";
const SECRETO  = Deno.env.get("QB_CLIENT_SECRET") ?? "";
const ENTORNO  = (Deno.env.get("QB_ENTORNO") ?? "produccion").toLowerCase();
const REGRESO  = Deno.env.get("QB_REDIRECT") ?? `${SB_URL}/functions/v1/gd-quickbooks`;

const INTUIT_AUTORIZA = "https://appcenter.intuit.com/connect/oauth2";
const INTUIT_TOKEN    = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer";
const INTUIT_REVOCA   = "https://developer.api.intuit.com/v2/oauth2/tokens/revoke";
const API_BASE = ENTORNO === "sandbox"
  ? "https://sandbox-quickbooks.api.intuit.com"
  : "https://quickbooks.api.intuit.com";

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
};

const TANDA = 250;   // renglones por llamada a gd_qb_cargar

function json(cuerpo: unknown, status = 200) {
  return new Response(JSON.stringify(cuerpo), {
    status,
    headers: { ...CORS, "Content-Type": "application/json" },
  });
}

function pagina(titulo: string, cuerpo: string, bien = true) {
  return new Response(
    `<!doctype html><html lang="es"><head><meta charset="utf-8">
     <meta name="viewport" content="width=device-width,initial-scale=1">
     <title>${titulo}</title><style>
     body{font-family:-apple-system,"Segoe UI",Roboto,sans-serif;background:#f4f5f7;
          margin:0;padding:38px 20px;color:#16191d}
     .c{max-width:420px;margin:0 auto;background:#fff;border-radius:12px;padding:26px;
        box-shadow:0 1px 3px rgba(16,24,40,.1);text-align:center}
     h1{font-size:19px;margin:0 0 10px;color:${bien ? "#065f2b" : "#991b1b"}}
     p{color:#4b5563;line-height:1.5;font-size:15px;margin:0 0 8px}
     </style></head><body><div class="c"><h1>${titulo}</h1>${cuerpo}</div></body></html>`,
    { status: 200, headers: { ...CORS, "Content-Type": "text/html; charset=utf-8" } },
  );
}

// ---------- la base, con la llave de servicio ----------
async function base(ruta: string, opciones: RequestInit = {}) {
  const r = await fetch(`${SB_URL}/rest/v1/${ruta}`, {
    ...opciones,
    headers: {
      apikey: SB_SERV,
      Authorization: `Bearer ${SB_SERV}`,
      "Content-Type": "application/json",
      ...(opciones.headers ?? {}),
    },
  });
  const t = await r.text();
  if (!r.ok) throw new Error(`base ${r.status}: ${t.slice(0, 300)}`);
  return t ? JSON.parse(t) : null;
}

// ---------- quien esta llamando ----------
// Devuelve el id del usuario SOLO si trae sesion valida y es dueno activo.
async function quienLlama(req: Request): Promise<string> {
  const auth = req.headers.get("Authorization") ?? "";
  if (!auth.toLowerCase().startsWith("bearer ")) {
    throw new Error("401|Entra al panel primero.");
  }
  const r = await fetch(`${SB_URL}/auth/v1/user`, {
    headers: { apikey: SB_SERV, Authorization: auth },
  });
  if (!r.ok) throw new Error("401|Tu sesion ya vencio. Vuelve a entrar al panel.");
  const u = await r.json();
  if (!u?.id) throw new Error("401|Tu sesion ya vencio. Vuelve a entrar al panel.");

  const perfil = await base(`gd_perfiles?select=rol,activo&id=eq.${u.id}`);
  if (!perfil?.length || !perfil[0].activo || perfil[0].rol !== "dueno") {
    throw new Error("403|Solo el dueno puede conectar o refrescar el catalogo.");
  }
  return u.id as string;
}

function faltanSecretos() {
  return !CLIENTE || !SECRETO;
}

// ---------- tokens de Intuit ----------
function basica() {
  return "Basic " + btoa(`${CLIENTE}:${SECRETO}`);
}

async function pideTokens(cuerpo: string) {
  const r = await fetch(INTUIT_TOKEN, {
    method: "POST",
    headers: {
      Authorization: basica(),
      "Content-Type": "application/x-www-form-urlencoded",
      Accept: "application/json",
    },
    body: cuerpo,
  });
  const t = await r.text();
  if (!r.ok) throw new Error(`Intuit no dio el token (${r.status}): ${t.slice(0, 300)}`);
  return JSON.parse(t);
}

async function conexion() {
  const c = await base("gd_qb_conexion?select=*&id=eq.1");
  return c?.length ? c[0] : null;
}

// Un access_token de Intuit dura una hora. El refresh_token dura 100 dias
// y ROTA cada vez que se usa: hay que guardar el nuevo o se pierde el acceso.
async function accesoFresco() {
  const c = await conexion();
  if (!c) throw new Error("400|QuickBooks no esta conectado todavia.");

  const vence = c.access_vence ? new Date(c.access_vence).getTime() : 0;
  if (c.access_token && vence > Date.now() + 120_000) {
    return { token: c.access_token as string, realm: c.realm_id as string };
  }

  const d = await pideTokens(
    `grant_type=refresh_token&refresh_token=${encodeURIComponent(c.refresh_token)}`,
  );
  await base("gd_qb_conexion?id=eq.1", {
    method: "PATCH",
    body: JSON.stringify({
      refresh_token: d.refresh_token ?? c.refresh_token,
      access_token: d.access_token,
      access_vence: new Date(Date.now() + (d.expires_in ?? 3600) * 1000).toISOString(),
      ultimo_refresh: new Date().toISOString(),
      ultimo_error: null,
    }),
  });
  return { token: d.access_token as string, realm: c.realm_id as string };
}

// ---------- el catalogo, pagina por pagina ----------
async function traeArticulos(token: string, realm: string) {
  const todos: Record<string, unknown>[] = [];
  let desde = 1;
  for (let vueltas = 0; vueltas < 40; vueltas++) {
    const q = `select * from Item where Active = true startposition ${desde} maxresults 1000`;
    const r = await fetch(
      `${API_BASE}/v3/company/${realm}/query?query=${encodeURIComponent(q)}`,
      { headers: { Authorization: `Bearer ${token}`, Accept: "application/json" } },
    );
    const t = await r.text();
    if (!r.ok) throw new Error(`QuickBooks respondio ${r.status}: ${t.slice(0, 300)}`);
    const d = JSON.parse(t);
    const tanda = d?.QueryResponse?.Item ?? [];
    todos.push(...tanda);
    if (tanda.length < 1000) break;
    desde += 1000;
  }
  return todos;
}

// Igual que en el panel: decide si lo que trae el campo SKU es de verdad
// un codigo de barras. Ver la nota "el-sku-de-quickbooks-no-siempre-es-codigo".
function codigoDeBarras(sku: string, nombre: string) {
  if (!sku || sku === nombre) return "";
  if (sku.toUpperCase().includes("E")) return "";
  const d = sku.replace(/[^0-9]/g, "");
  return d.length >= 8 && d.length <= 14 ? d : "";
}

function limpia(s: unknown) {
  return String(s ?? "").replace(/\|/g, " ").replace(/\s+/g, " ").trim();
}

function arma(articulos: Record<string, any>[]) {
  // Las "categorias" de QuickBooks son articulos de tipo Category; los
  // productos las apuntan con ParentRef. Pero ParentRef tambien se usa
  // para sub-articulos de un producto normal: por eso el mapa se arma
  // SOLO con los de tipo Category, y lo demas cae en "Otros".
  const cats = new Map<string, string>();
  for (const a of articulos) {
    if (a.Type === "Category") cats.set(String(a.Id), limpia(a.Name));
  }

  const lineas: string[] = [];
  const cuenta = { total: 0, codigo: 0, nombre: 0, vacio: 0, raro: 0, categorias: cats.size };
  const porTipo: Record<string, number> = {};

  for (const a of articulos) {
    if (a.Type === "Category") continue;
    const nom = limpia(a.Name);
    if (!nom) continue;
    const sku = limpia(a.Sku);
    const cod = codigoDeBarras(sku, nom);

    cuenta.total++;
    if (cod) cuenta.codigo++;
    else if (!sku) cuenta.vacio++;
    else if (sku === nom) cuenta.nombre++;
    else cuenta.raro++;
    porTipo[a.Type ?? "?"] = (porTipo[a.Type ?? "?"] ?? 0) + 1;

    const cat = cats.get(String(a.ParentRef?.value ?? "")) ?? "Otros";
    lineas.push([
      nom,
      cod,
      sku,
      cat || "Otros",
      Number(a.UnitPrice ?? 0).toFixed(2),
      Number(a.PurchaseCost ?? 0).toFixed(2),
      String(Math.round(Number(a.QtyOnHand ?? 0))),
    ].join("|"));
  }
  return { lineas, cuenta, porTipo };
}

// ---------- las funciones de la base, con la sesion de quien llamo ----------
// A proposito se usa SU sesion y no la llave de servicio: asi la revision
// de "solo el dueno" vive en un solo lugar, dentro de gd_qb_aplicar.
async function rpc(auth: string, fn: string, cuerpo: unknown) {
  const r = await fetch(`${SB_URL}/rest/v1/rpc/${fn}`, {
    method: "POST",
    headers: { apikey: SB_SERV, Authorization: auth, "Content-Type": "application/json" },
    body: JSON.stringify(cuerpo),
  });
  const t = await r.text();
  if (!r.ok) throw new Error(`${fn} respondio ${r.status}: ${t.slice(0, 300)}`);
  return t ? JSON.parse(t) : null;
}

// =====================================================================
Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });

  const url = new URL(req.url);

  // ---------- 1. el regreso de Intuit (es el navegador, sin sesion) ----------
  if (req.method === "GET" && (url.searchParams.has("code") || url.searchParams.has("error"))) {
    const err = url.searchParams.get("error");
    if (err) {
      return pagina("No se conecto", `<p>Intuit contesto: <b>${err}</b></p>
        <p>Puedes cerrar esta pestaña e intentar de nuevo desde el panel.</p>`, false);
    }
    try {
      const estado = url.searchParams.get("state") ?? "";
      const code   = url.searchParams.get("code") ?? "";
      const realm  = url.searchParams.get("realmId") ?? "";
      if (!realm) throw new Error("Intuit no dijo de que empresa se trata.");

      const fila = await base(
        `gd_qb_oauth_estado?select=*&estado=eq.${encodeURIComponent(estado)}&usado=eq.false`,
      );
      if (!fila?.length) throw new Error("Esta liga ya se uso o ya vencio. Pide una nueva desde el panel.");
      const edad = Date.now() - new Date(fila[0].creado).getTime();
      if (edad > 20 * 60 * 1000) throw new Error("La liga vencio (dura 20 minutos). Pide una nueva desde el panel.");

      const d = await pideTokens(
        `grant_type=authorization_code&code=${encodeURIComponent(code)}` +
        `&redirect_uri=${encodeURIComponent(REGRESO)}`,
      );

      await base("gd_qb_conexion", {
        method: "POST",
        headers: { Prefer: "resolution=merge-duplicates" },
        body: JSON.stringify({
          id: 1,
          realm_id: realm,
          refresh_token: d.refresh_token,
          access_token: d.access_token,
          access_vence: new Date(Date.now() + (d.expires_in ?? 3600) * 1000).toISOString(),
          entorno: ENTORNO,
          conectado_por: fila[0].usuario,
          conectado_el: new Date().toISOString(),
          ultimo_refresh: new Date().toISOString(),
          ultimo_error: null,
        }),
      });
      await base(`gd_qb_oauth_estado?estado=eq.${encodeURIComponent(estado)}`, {
        method: "PATCH",
        body: JSON.stringify({ usado: true }),
      });

      return pagina("Ya quedo conectado", `
        <p>QuickBooks y la aplicacion ya se hablan.</p>
        <p><b>Cierra esta pestaña y vuelve al panel.</b> Ahi aprieta
        <i>Revisar sin cambiar nada</i> y te dira que va a pasar.</p>
        <p style="font-size:13px;color:#6b7280;margin-top:14px">Esta conexion
        <b>solo lee</b> de QuickBooks. Puedes cortarla cuando quieras desde el panel.</p>`);
    } catch (e) {
      return pagina("No se conecto", `<p>${String(e.message ?? e)}</p>`, false);
    }
  }

  if (req.method !== "POST") {
    return pagina("Funcion de QuickBooks",
      `<p>Esta direccion la usa el panel. No hay nada que ver aqui.</p>`);
  }

  // ---------- 2. todo lo demas: lo pide el panel, con sesion de dueno ----------
  let usuario: string;
  try {
    usuario = await quienLlama(req);
  } catch (e) {
    const [cod, msg] = String(e.message ?? e).split("|");
    return json({ ok: false, error: msg ?? cod }, Number(cod) || 400);
  }

  let cuerpo: Record<string, unknown> = {};
  try { cuerpo = await req.json(); } catch { /* sin cuerpo */ }
  const accion = String(cuerpo.accion ?? "estado");

  try {
    // --- esta todo puesto? Lo contesta el proceso, no el panel de Supabase ---
    if (accion === "estado") {
      const c = await conexion();
      return json({
        ok: true,
        secretos_puestos: !faltanSecretos(),
        entorno: ENTORNO,
        regreso: REGRESO,
        conectado: !!c,
        empresa: c?.realm_id ?? null,
        conectado_el: c?.conectado_el ?? null,
        ultimo_refresh: c?.ultimo_refresh ?? null,
        ultimo_error: c?.ultimo_error ?? null,
        aviso: faltanSecretos()
          ? "Faltan los secretos QB_CLIENT_ID y QB_CLIENT_SECRET en Supabase. Sin ellos no se puede conectar."
          : null,
      });
    }

    if (accion === "autorizar") {
      if (faltanSecretos()) {
        return json({
          ok: false,
          productos: 0,
          error: "Faltan los secretos QB_CLIENT_ID y QB_CLIENT_SECRET en Supabase.",
        }, 400);
      }
      const estado = crypto.randomUUID();
      await base("gd_qb_oauth_estado", {
        method: "POST",
        body: JSON.stringify({ estado, usuario }),
      });
      const u = new URL(INTUIT_AUTORIZA);
      u.searchParams.set("client_id", CLIENTE);
      u.searchParams.set("response_type", "code");
      u.searchParams.set("scope", "com.intuit.quickbooks.accounting");
      u.searchParams.set("redirect_uri", REGRESO);
      u.searchParams.set("state", estado);
      return json({ ok: true, url: u.toString() });
    }

    if (accion === "desconectar") {
      const c = await conexion();
      if (c && !faltanSecretos()) {
        // Se le avisa a Intuit, no nada mas se borra de aqui.
        try {
          await fetch(INTUIT_REVOCA, {
            method: "POST",
            headers: { Authorization: basica(), "Content-Type": "application/json" },
            body: JSON.stringify({ token: c.refresh_token }),
          });
        } catch { /* si Intuit no contesta, igual se corta de este lado */ }
      }
      await base("gd_qb_conexion?id=eq.1", { method: "DELETE" });
      return json({ ok: true, conectado: false });
    }

    if (accion === "refrescar") {
      if (faltanSecretos()) {
        return json({
          ok: false,
          productos: 0,
          error: "Faltan los secretos QB_CLIENT_ID y QB_CLIENT_SECRET en Supabase.",
        }, 400);
      }
      const deVerdad = cuerpo.de_verdad === true;
      const auth = req.headers.get("Authorization")!;

      let acceso;
      try {
        acceso = await accesoFresco();
      } catch (e) {
        await base("gd_qb_conexion?id=eq.1", {
          method: "PATCH",
          body: JSON.stringify({ ultimo_error: String(e.message ?? e).slice(0, 400) }),
        }).catch(() => {});
        throw e;
      }

      const articulos = await traeArticulos(acceso.token, acceso.realm);
      const { lineas, cuenta, porTipo } = arma(articulos);

      if (!lineas.length) {
        return json({
          ok: false,
          productos: 0,
          error: "QuickBooks contesto bien pero no mando ningun producto. No se toco nada.",
        }, 400);
      }

      for (let i = 0; i < lineas.length; i += TANDA) {
        await rpc(auth, "gd_qb_cargar", {
          p_lineas: lineas.slice(i, i + TANDA).join("\n"),
          p_primera: i === 0,
        });
      }
      const resumen = await rpc(auth, "gd_qb_aplicar", { p_de_verdad: deVerdad });

      return json({
        ok: true,
        de_verdad: deVerdad,
        articulos_de_intuit: articulos.length,
        productos: lineas.length,
        cuenta,
        por_tipo: porTipo,
        resumen,
      });
    }

    return json({ ok: false, error: `No conozco la accion "${accion}".` }, 400);
  } catch (e) {
    return json({ ok: false, productos: 0, error: String(e.message ?? e) }, 400);
  }
});
