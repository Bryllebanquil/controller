create table if not exists public.totp_base32_secrets (
  user_id uuid primary key,
  secret_base32 text not null,
  issuer text default 'Neural Control Hub',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.totp_base32_secrets enable row level security;

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists trg_totp_base32_updated on public.totp_base32_secrets;
create trigger trg_totp_base32_updated
before update on public.totp_base32_secrets
for each row execute function public.set_updated_at();
