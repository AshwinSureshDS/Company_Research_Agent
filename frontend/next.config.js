/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },
  images: {
    domains: ['localhost'],
  },
  experimental: {
    // Only enable optimizeCss if critters is installed
    optimizeCss: false
  }
}

module.exports = nextConfig