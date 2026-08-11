import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // Produces a minimal, self-contained server (.next/standalone) so the
  // Docker image doesn't need to ship node_modules/the full source tree.
  output: 'standalone',
};

export default nextConfig;
