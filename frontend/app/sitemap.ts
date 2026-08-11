import type { MetadataRoute } from 'next';

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://5edmaa.tn';

export default function sitemap(): MetadataRoute.Sitemap {
    const now = new Date();

    return [
        { url: `${SITE_URL}/`, lastModified: now, changeFrequency: 'weekly', priority: 1 },
        { url: `${SITE_URL}/jobs`, lastModified: now, changeFrequency: 'hourly', priority: 0.9 },
        { url: `${SITE_URL}/services`, lastModified: now, changeFrequency: 'hourly', priority: 0.9 },
        { url: `${SITE_URL}/login`, lastModified: now, changeFrequency: 'yearly', priority: 0.3 },
        { url: `${SITE_URL}/register`, lastModified: now, changeFrequency: 'yearly', priority: 0.5 },
    ];
}
