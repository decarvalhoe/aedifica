/** @type {import('next').NextConfig} */
const API = process.env.AEDIFICA_API || "http://127.0.0.1:8090";

const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    // Proxy the product API (FastAPI) so the app calls same-origin /api/*.
    return [{ source: "/api/:path*", destination: `${API}/api/:path*` }];
  },
};

export default nextConfig;
