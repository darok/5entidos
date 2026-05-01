-- ============================================================
-- 5entidos - schema
-- Ejecutar una sola vez en Supabase > SQL Editor
-- ============================================================

-- TAG TYPES
create table tag_types (
    id   uuid primary key default gen_random_uuid(),
    name text not null unique
);

-- TAGS
create table tags (
    id          uuid primary key default gen_random_uuid(),
    name        text not null unique,
    tag_type_id uuid references tag_types(id) on delete set null
);

-- INGREDIENTS (catalogo maestro)
create table ingredients (
    id   uuid primary key default gen_random_uuid(),
    name text not null unique
);

-- UNITS
create table units (
    id           uuid primary key default gen_random_uuid(),
    name         text not null unique,
    abbreviation text not null
);

-- RECIPES
create table recipes (
    id          uuid primary key default gen_random_uuid(),
    title       text not null,
    description text,
    prep_time   integer,
    cook_time   integer,
    servings    integer,
    created_at  timestamptz default now()
);

-- RECIPE <-> TAGS
create table recipe_tags (
    recipe_id uuid not null references recipes(id) on delete cascade,
    tag_id    uuid not null references tags(id)    on delete cascade,
    primary key (recipe_id, tag_id)
);

-- RECIPE INGREDIENTS
create table recipe_ingredients (
    id            uuid primary key default gen_random_uuid(),
    recipe_id     uuid    not null references recipes(id)     on delete cascade,
    ingredient_id uuid    not null references ingredients(id) on delete restrict,
    quantity      decimal,
    unit_id       uuid references units(id) on delete set null
);

-- RECIPE STEPS
create table recipe_steps (
    id          uuid primary key default gen_random_uuid(),
    recipe_id   uuid    not null references recipes(id) on delete cascade,
    step_number integer not null,
    description text    not null
);

-- Indices para queries frecuentes
create index on recipe_ingredients(recipe_id);
create index on recipe_steps(recipe_id);
create index on tags(tag_type_id);

-- ============================================================
-- SEED: unidades
-- ============================================================
insert into units (name, abbreviation) values
    ('gramos',      'g'),
    ('kilogramos',  'kg'),
    ('mililitros',  'ml'),
    ('litros',      'l'),
    ('taza',        'taza'),
    ('cucharada',   'cda'),
    ('cucharadita', 'cdta'),
    ('unidad',      'u'),
    ('pizca',       'pizca'),
    ('diente',      'diente'),
    ('rebanada',    'reb'),
    ('trozo',       'trozo'),
    ('puñado',      'puñado'),
    ('rama',        'rama'),
    ('hoja',        'hoja'),
    ('sobre',       'sobre');
