import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { AuthProvider } from '@/contexts/AuthContext';
import { PageTransition } from '@/components/PageTransition';

const inter = Inter({ subsets: ['latin'], display: 'swap' });

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://5edmaa.tn';
const SITE_NAME = '5edma.tn';
const DESCRIPTION =
    "5edma.tn est la plateforme tunisienne de mise en relation entre clients et travailleurs vérifiés : offres d'emploi, services à domicile, chat, portefeuille intégré et assistant IA.";

export const metadata: Metadata = {
    metadataBase: new URL(SITE_URL),
    title: {
        default: '5edma.tn — Services et emplois locaux en Tunisie',
        template: '%s | 5edma.tn',
    },
    description: DESCRIPTION,
    keywords: [
        '5edma.tn',
        'emploi Tunisie',
        'services Tunisie',
        'freelance Tunisie',
        'artisan Tunisie',
        'petits travaux',
        'plateforme emploi local',
    ],
    applicationName: SITE_NAME,
    authors: [{ name: '5edma.tn' }],
    generator: 'Next.js',
    referrer: 'strict-origin-when-cross-origin',
    robots: { index: true, follow: true },
    alternates: { canonical: '/' },
    openGraph: {
        type: 'website',
        locale: 'fr_TN',
        url: SITE_URL,
        siteName: SITE_NAME,
        title: '5edma.tn — Services et emplois locaux en Tunisie',
        description: DESCRIPTION,
        images: [{ url: '/og-image.png', width: 1200, height: 630, alt: '5edma.tn' }],
    },
    twitter: {
        card: 'summary_large_image',
        title: '5edma.tn — Services et emplois locaux en Tunisie',
        description: DESCRIPTION,
        images: ['/og-image.png'],
    },
};

const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: '5edma.tn',
    url: SITE_URL,
    logo: `${SITE_URL}/logo-icon.png`,
    description: DESCRIPTION,
    areaServed: {
        '@type': 'Country',
        name: 'Tunisia',
    },
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="fr">
            <head>
                <script
                    type="application/ld+json"
                    dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
                />
            </head>
            <body className={inter.className}>
                <AuthProvider>
                    <PageTransition>{children}</PageTransition>
                </AuthProvider>
            </body>
        </html>
    );
}
