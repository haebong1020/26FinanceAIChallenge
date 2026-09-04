-- Run once in Supabase Dashboard > SQL Editor.
-- This migration preserves all existing thesis_reviews records.

alter table public.thesis_reviews
  add column if not exists factor_detail text not null default '',
  add column if not exists evidence_url text,
  add column if not exists workflow_version text not null default 'design-v1';

comment on column public.thesis_reviews.factor_detail is
  'Optional detail supporting the selected investment criteria in the design-v1 workflow.';

comment on column public.thesis_reviews.evidence_url is
  'Optional user-supplied reference URL in the design-v1 workflow.';

comment on column public.thesis_reviews.workflow_version is
  'Version of the question workflow used to create this review.';
