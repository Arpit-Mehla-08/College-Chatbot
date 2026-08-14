/** @type {import('next').NextConfig} */
const nextConfig = {
  // 'standalone' output is only for the self-hosted Docker build (Dockerfile.frontend sets
  // DOCKER_BUILD=true). Vercel builds/hosts Next.js itself and doesn't need or want this.
  output: process.env.DOCKER_BUILD === 'true' ? 'standalone' : undefined,
  async rewrites() {
    const rawUrl = process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_BACKEND_URL;
    if (!rawUrl) {
      return [];
    }
    let clean = rawUrl.trim().replace(/\/+$/, '');
    if (clean.endsWith('/api')) {
      clean = clean.slice(0, -4);
    }

    return [
      {
        source: '/api/:path*',
        destination: `${clean}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
