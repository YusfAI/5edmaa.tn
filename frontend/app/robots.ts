import type { MetadataRoute } from 'next';

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://5edmaa.tn';

export default function robots(): MetadataRoute.Robots {
    return {
        rules: [
            {
                userAgent: '*',
                allow: ['/', '/jobs', '/services', '/login', '/register'],
                // Authenticated-only sections have nothing to offer a crawler
                // (they redirect to /login or show private per-user data).
                disallow: [
                    '/dashboard',
                    '/profile',
                    '/admin',
                    '/wallet',
                    '/applications',
                    '/bookings',
                    '/chat',
                    '/jobs/new',
                    '/jobs/mine',
                    '/services/new',
                    '/services/mine',
                ],
            },
        ],
        sitemap: `${SITE_URL}/sitemap.xml`,
    };
}
