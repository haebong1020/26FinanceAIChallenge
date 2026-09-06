-- Run once in Supabase Dashboard > SQL Editor for an existing project.
-- Keep only the newest review for each user, then enforce one review per user.

delete from public.thesis_reviews as older
using public.thesis_reviews as newer
where older.user_id = newer.user_id
  and (
    older.created_at < newer.created_at
    or (older.created_at = newer.created_at and older.id < newer.id)
  );

alter table public.thesis_reviews
  add constraint thesis_reviews_user_id_unique unique (user_id);
