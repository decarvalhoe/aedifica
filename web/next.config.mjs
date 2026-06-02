/** @type {import('next').NextConfig} */
// The product API is proxied at runtime by app/api/[...path]/route.ts (it reads
// AEDIFICA_API per request), so the image is not tied to a build-time API URL.
const nextConfig = {
  reactStrictMode: true,
};

export default nextConfig;
