/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  eslint: { ignoreDuringBuilds: true },
  typescript: { ignoreBuildErrors: true },
  // Keep the default in-tree `.next` build dir. (An out-of-tree distDir breaks
  // @prisma/client module resolution, so we don't use one.)
  outputFileTracingRoot: __dirname,
};

module.exports = nextConfig;
