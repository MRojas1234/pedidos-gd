-- ============================================================================
--  General Distribution — la base de datos completa, desde cero.
--  Se pega tal cual en: Supabase → SQL Editor → New query → Run.
--  Sirve para levantar el sistema en el proyecto propio de Manuel.
--  Escrito el 28 de septiembre de 2026.
-- ============================================================================

-- ----------------------------------------------------------------------------
--  1. LOS PEDIDOS
-- ----------------------------------------------------------------------------

create table if not exists public.gd_pedidos (
  id          uuid primary key,                      -- lo genera el telefono, no la base
  folio       bigint generated always as identity,
  tienda      text        not null,
  nota        text,
  articulos   integer     not null default 0,
  total       numeric(10,2) not null default 0,
  es_prueba   boolean     not null default false,    -- nada se borra: lo de prueba se marca
  creado      timestamptz not null default now()
);
comment on table public.gd_pedidos is 'Pedidos levantados en tienda con la app.';

create table if not exists public.gd_pedido_lineas (
  id          uuid primary key,
  pedido_id   uuid        not null references public.gd_pedidos(id) on delete cascade,
  producto_id text        not null,                  -- id del producto en Shopify
  producto    text        not null,                  -- nombre congelado al momento del pedido
  categoria   text,
  precio      numeric(10,2) not null default 0,      -- precio congelado: Shopify puede cambiarlo despues
  cantidad    integer     not null check (cantidad > 0),
  importe     numeric(10,2) not null default 0
);
comment on table public.gd_pedido_lineas is 'Renglones del pedido, con nombre y precio del dia.';

create index if not exists gd_pedidos_creado_idx  on public.gd_pedidos (creado desc);
create index if not exists gd_pedidos_tienda_idx  on public.gd_pedidos (tienda);
create index if not exists gd_lineas_pedido_idx   on public.gd_pedido_lineas (pedido_id);
create index if not exists gd_lineas_producto_idx on public.gd_pedido_lineas (producto_id);

-- ----------------------------------------------------------------------------
--  2. QUIEN PUEDE ENTRAR AL PANEL
-- ----------------------------------------------------------------------------

create table if not exists public.gd_perfiles (
  id         uuid primary key references auth.users(id) on delete cascade,
  nombre     text,
  email      text,
  rol        text        not null default 'vendedor',   -- 'dueno' administra; 'vendedor' solo mira
  activo     boolean     not null default true,         -- nunca se borra a nadie: se apaga
  creado_en  timestamptz not null default now()
);
comment on table public.gd_perfiles is 'Quien entra al panel. No se borra a nadie: activo=false.';

-- Al nacer una cuenta con app='gd', se le hace su gafete solo.
-- Sin valor por omision, para no tocar cuentas de otras apps que vivan en el mismo proyecto.
create or replace function public.gd_nuevo_usuario()
returns trigger
language plpgsql
security definer
set search_path to 'public','auth'
as $$
declare v_rol text;
begin
  if coalesce(new.raw_user_meta_data->>'app','') <> 'gd' then
    return new;
  end if;
  if not exists (select 1 from gd_perfiles) then v_rol := 'dueno'; else v_rol := 'vendedor'; end if;
  insert into gd_perfiles (id, nombre, email, rol)
  values (new.id,
          coalesce(nullif(new.raw_user_meta_data->>'nombre',''), split_part(new.email,'@',1)),
          new.email, v_rol)
  on conflict (id) do nothing;
  return new;
end $$;

drop trigger if exists gd_on_auth_user_created on auth.users;
create trigger gd_on_auth_user_created
  after insert on auth.users
  for each row execute function public.gd_nuevo_usuario();

-- "¿Es dueno?" vive en una funcion aparte A PROPOSITO:
-- una politica sobre gd_perfiles que consulte gd_perfiles entra en recursion infinita.
create or replace function public.gd_es_dueno()
returns boolean
language sql
stable
security definer
set search_path to 'public'
as $$
  select exists (
    select 1 from public.gd_perfiles
    where id = auth.uid() and activo and rol = 'dueno'
  );
$$;

-- ----------------------------------------------------------------------------
--  3. LAS REGLAS DE ACCESO. Esto es lo que de verdad protege el negocio.
-- ----------------------------------------------------------------------------

alter table public.gd_pedidos       enable row level security;
alter table public.gd_pedido_lineas enable row level security;
alter table public.gd_perfiles      enable row level security;

-- ESCRIBIR pedidos: cualquiera con la llave publica. Es un buzon: se mete, no se saca.
drop policy if exists gd_pedidos_insert_anon on public.gd_pedidos;
create policy gd_pedidos_insert_anon
  on public.gd_pedidos for insert to anon, authenticated with check (true);

drop policy if exists gd_lineas_insert_anon on public.gd_pedido_lineas;
create policy gd_lineas_insert_anon
  on public.gd_pedido_lineas for insert to anon, authenticated with check (true);

-- LEER pedidos: solo quien tenga gafete activo.
drop policy if exists gd_pedidos_select_equipo on public.gd_pedidos;
create policy gd_pedidos_select_equipo
  on public.gd_pedidos for select to authenticated
  using (exists (select 1 from public.gd_perfiles p where p.id = auth.uid() and p.activo));

drop policy if exists gd_lineas_select_equipo on public.gd_pedido_lineas;
create policy gd_lineas_select_equipo
  on public.gd_pedido_lineas for select to authenticated
  using (exists (select 1 from public.gd_perfiles p where p.id = auth.uid() and p.activo));

-- El dueno ve a todo su equipo; cada quien se ve a si mismo.
drop policy if exists gd_perfiles_lectura on public.gd_perfiles;
create policy gd_perfiles_lectura
  on public.gd_perfiles for select to authenticated
  using (id = auth.uid() or public.gd_es_dueno());

-- El dueno prende y apaga gente. NUNCA borra.
drop policy if exists gd_perfiles_dueno_actualiza on public.gd_perfiles;
create policy gd_perfiles_dueno_actualiza
  on public.gd_perfiles for update to authenticated
  using (public.gd_es_dueno())
  with check (public.gd_es_dueno());

-- A PROPOSITO no hay politica de DELETE en ninguna tabla:
-- desde la app nadie puede borrar nada.
