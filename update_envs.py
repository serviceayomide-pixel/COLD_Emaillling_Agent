import os

anon = os.getenv('SUPABASE_ANON_KEY', '')
service = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')
db_url = os.getenv('DATABASE_URL', '')
url = os.getenv('SUPABASE_URL', '')

backend_env = 'backend/.env'
if os.path.exists(backend_env):
    with open(backend_env, 'r') as f:
        lines = f.readlines()
    with open(backend_env, 'w') as f:
        for line in lines:
            if line.startswith('DATABASE_URL='):
                f.write(f'DATABASE_URL="{db_url}"\n')
            elif line.startswith('SUPABASE_ANON_KEY='):
                f.write(f'SUPABASE_ANON_KEY="{anon}"\n')
            elif line.startswith('SUPABASE_SERVICE_ROLE_KEY='):
                f.write(f'SUPABASE_SERVICE_ROLE_KEY="{service}"\n')
            elif line.startswith('SUPABASE_URL='):
                f.write(f'SUPABASE_URL="{url}"\n')
            else:
                f.write(line)

frontend_env = 'frontend/.env.local'
if os.path.exists(frontend_env):
    with open(frontend_env, 'r') as f:
        lines = f.readlines()
    with open(frontend_env, 'w') as f:
        for line in lines:
            if line.startswith('NEXT_PUBLIC_SUPABASE_URL='):
                f.write(f'NEXT_PUBLIC_SUPABASE_URL={url}\n')
            elif line.startswith('NEXT_PUBLIC_SUPABASE_ANON_KEY='):
                f.write(f'NEXT_PUBLIC_SUPABASE_ANON_KEY={anon}\n')
            elif line.startswith('SUPABASE_SERVICE_ROLE_KEY='):
                f.write(f'SUPABASE_SERVICE_ROLE_KEY={service}\n')
            else:
                f.write(line)
