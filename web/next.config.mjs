/** @type {import('next').NextConfig} */
const backendOrigin = process.env.BACKEND_ORIGIN || "http://127.0.0.1:8080";

const nextConfig = {
  // Emit a self-contained server build for a small Docker image.
  output: "standalone",
  // Same-origin proxy: the browser only ever calls /api/*, which Next forwards
  // to the FastAPI backend. No CORS needed in dev or in Docker — only
  // BACKEND_ORIGIN changes between environments.
  async rewrites() {
    return [
      { source: "/api/:path*", destination: `${backendOrigin}/:path*` },
    ];
  },
};

export default nextConfig;
