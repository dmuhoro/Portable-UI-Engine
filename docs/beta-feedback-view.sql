-- Run this in Supabase Dashboard -> SQL Editor
-- Creates a view for monitoring beta user feedback by category

create view beta_feedback_summary as
select
  category,
  count(*) as count,
  max(created_at) as latest,
  array_agg(message order by created_at desc) filter (where message != '[ACCOUNT_DELETION_REQUEST]') as messages
from daftari_feedback
group by category
order by count desc;

-- Usage: SELECT * FROM beta_feedback_summary;
