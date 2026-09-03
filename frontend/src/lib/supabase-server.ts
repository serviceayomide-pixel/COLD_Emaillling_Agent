import { createClient, SupabaseClient } from '@supabase/supabase-js'

let _supabaseInstance: SupabaseClient | null = null;

function getClient(): SupabaseClient {
  if (!_supabaseInstance) {
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
    if (!supabaseUrl || !supabaseKey) {
      throw new Error("Supabase URL or Key is missing. Please set NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY variables in Railway.");
    }
    _supabaseInstance = createClient(supabaseUrl, supabaseKey);
  }
  return _supabaseInstance;
}

export const supabaseServer = new Proxy({} as SupabaseClient, {
  get(target, prop, receiver) {
    const client = getClient();
    const value = Reflect.get(client, prop, receiver);
    if (typeof value === 'function') {
      return value.bind(client);
    }
    return value;
  }
});
