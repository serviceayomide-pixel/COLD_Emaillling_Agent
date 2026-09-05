import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  env: {
    NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL || "https://xnwyphxigwpidknyjfge.supabase.co",
    NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhud3lwaHhpZ3dwaWRrbnlqZmdlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODg0MjYwMzcsImV4cCI6MjEwNDAwMjAzN30.uOYX_OCE7mhaerSDfzxd4loO4GG_0ZZEQSwUnRAjHNc",
  },
};

export default nextConfig;
