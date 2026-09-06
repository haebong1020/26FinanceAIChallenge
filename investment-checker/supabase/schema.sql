-- Run this script once in Supabase Dashboard > SQL Editor.
-- Each record belongs to a Supabase Auth user.
-- Never use a service_role key in the Streamlit app.

create table if not exists public.thesis_reviews (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null unique references auth.users(id) on delete cascade,
  original_thesis text not null,
  holdings jsonb not null,
  questionnaire jsonb not null,
  cross_examination_answers jsonb not null,
  ai_analysis jsonb,
  ai_error text,
  evidence_metadata jsonb,
  factor_detail text not null default '',
  evidence_url text,
  workflow_version text not null default 'design-v1',
  completed_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);

alter table public.thesis_reviews enable row level security;

drop policy if exists "Allow users to insert their own reviews" on public.thesis_reviews;
create policy "Allow users to insert their own reviews"
on public.thesis_reviews
for insert
to authenticated
with check ((select auth.uid()) = user_id);

drop policy if exists "Allow users to read their own reviews" on public.thesis_reviews;
create policy "Allow users to read their own reviews"
on public.thesis_reviews
for select
to authenticated
using ((select auth.uid()) = user_id);

drop policy if exists "Allow users to update their own reviews" on public.thesis_reviews;
create policy "Allow users to update their own reviews"
on public.thesis_reviews
for update
to authenticated
using ((select auth.uid()) = user_id)
with check ((select auth.uid()) = user_id);
