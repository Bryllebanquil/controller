create or replace function start_totp_setup(secret_cipher text)
returns void
language sql stable
security definer
set search_path = public
as $$
insert into public.totp_secrets (user_id, secret_encrypted, enabled, setup_completed)
values (auth.uid(), decode(secret_cipher, 'base64'), false, false)
on conflict (user_id) do update set secret_encrypted = excluded.secret_encrypted, enabled = false, setup_completed = false;
$$;

create or replace function get_totp_setup_ciphertext()
returns text
language sql stable
security definer
set search_path = public
as $$
select encode(secret_encrypted, 'base64')
from public.totp_secrets
where user_id = auth.uid() and setup_completed = false
limit 1;
$$;

create or replace function confirm_totp_setup()
returns void
language sql stable
security definer
set search_path = public
as $$
update public.totp_secrets
set enabled = true, setup_completed = true
where user_id = auth.uid();
$$;

create or replace function get_totp_ciphertext_for_login()
returns text
language sql stable
security definer
set search_path = public
as $$
select encode(secret_encrypted, 'base64')
from public.totp_secrets
where user_id = auth.uid() and enabled = true
limit 1;
$$;

-- Admin parameterized variants (service-role calls)
create or replace function start_totp_setup_admin(user_uuid uuid, secret_cipher text)
returns void
language sql stable
security definer
set search_path = public
as $$
insert into public.totp_secrets (user_id, secret_encrypted, enabled, setup_completed)
values (user_uuid, decode(secret_cipher, 'base64'), false, false)
on conflict (user_id) do update
  set secret_encrypted = excluded.secret_encrypted,
      enabled = false,
      setup_completed = false;
$$;

create or replace function get_totp_setup_ciphertext_admin(user_uuid uuid)
returns text
language sql stable
security definer
set search_path = public
as $$
select encode(secret_encrypted, 'base64')
from public.totp_secrets
where user_id = user_uuid and setup_completed = false
limit 1;
$$;

create or replace function confirm_totp_setup_admin(user_uuid uuid)
returns void
language sql stable
security definer
set search_path = public
as $$
update public.totp_secrets
set enabled = true, setup_completed = true
where user_id = user_uuid;
$$;

create or replace function get_totp_ciphertext_for_login_admin(user_uuid uuid)
returns text
language sql stable
security definer
set search_path = public
as $$
select encode(secret_encrypted, 'base64')
from public.totp_secrets
where user_id = user_uuid and enabled = true
limit 1;
$$;
