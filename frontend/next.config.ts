import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Vercel: backend API'ye CORS proxy (production'da Railway URL'sine yönlendirir)
  async rewrites() {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "";
    // Geçersiz veya placeholder URL varsa rewrite ekleme
    if (!apiUrl.startsWith("http")) return [];
    return [
      {
        source: "/api/backend/:path*",
        destination: `${apiUrl}/:path*`,
      },
    ];
  },
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "*.ticimax.cloud" },
      { protocol: "https", hostname: "*.ticimax.com" },
      { protocol: "http", hostname: "*.ticimax.cloud" },
    ],
  },
};

export default nextConfig;
