-- Optional seed data for local testing (without embeddings)
insert into public.notes (url, title, description, tags)
values
  ('https://flutter.dev', 'Flutter', 'UI toolkit for building beautiful apps for mobile, web, and desktop from a single codebase.', '{dev,flutter}'),
  ('https://fastapi.tiangolo.com', 'FastAPI', 'FastAPI framework, high performance, easy to learn, fast to code, ready for production', '{dev,python,api}'),
  ('https://supabase.com', 'Supabase', 'Open source Firebase alternative. Start your project with a Postgres database, Authentication, instant APIs, Realtime, Functions, and Storage.', '{dev,postgres,supabase}');


