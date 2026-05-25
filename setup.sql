-- ============================================================
-- Sage database setup
-- ============================================================
-- Run this in your Supabase project's SQL Editor.
-- Project → SQL Editor → New query → paste this → Run.
-- ============================================================

-- 1. Captures table — stores every "what shifted" entry
create table sage_captures (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  bucket text not null,
  sub text not null,
  source text,
  shift text not null,
  created_at timestamptz default now()
);

-- 2. Routing table — stores your custom routing data (one row per user)
create table sage_routing (
  user_id uuid primary key references auth.users(id) on delete cascade,
  data jsonb not null,
  updated_at timestamptz default now()
);

-- 3. Files table — stores your Sage.md, Processes, Appendices
create table sage_files (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  filename text not null,
  content text not null,
  updated_at timestamptz default now(),
  unique(user_id, filename)
);

-- ============================================================
-- Row-level security: each user only sees their own data
-- ============================================================

alter table sage_captures enable row level security;
alter table sage_routing enable row level security;
alter table sage_files enable row level security;

create policy "Users see their own captures"
  on sage_captures for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

create policy "Users see their own routing"
  on sage_routing for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

create policy "Users see their own files"
  on sage_files for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

-- ============================================================
-- Done. Three tables, row-level security on. Ready for Sage.
-- ============================================================
