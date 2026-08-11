'use client';

import Image from 'next/image';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { Badge, Button } from './ui';

const WORKER_LINKS = [
    { href: '/dashboard', label: 'Tableau de bord' },
    { href: '/jobs', label: 'Offres' },
    { href: '/applications', label: 'Mes candidatures' },
    { href: '/services/mine', label: 'Mes services' },
    { href: '/bookings', label: 'Réservations' },
    { href: '/wallet', label: 'Portefeuille' },
];

const CLIENT_LINKS = [
    { href: '/dashboard', label: 'Tableau de bord' },
    { href: '/jobs/mine', label: 'Mes offres' },
    { href: '/services', label: 'Trouver un pro' },
    { href: '/bookings', label: 'Réservations' },
    { href: '/wallet', label: 'Portefeuille' },
];

const ADMIN_LINKS = [
    { href: '/admin', label: 'Vérifications' },
    { href: '/wallet', label: 'Transactions' },
];

export function Nav() {
    const { user, logout } = useAuth();
    const pathname = usePathname();

    const links = user?.role === 'worker' ? WORKER_LINKS : user?.role === 'client' ? CLIENT_LINKS : ADMIN_LINKS;

    return (
        <nav className="glass border-b border-gray-200 sticky top-0 z-50">
            <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between gap-6">
                <Link href={user ? '/dashboard' : '/'} className="flex items-center gap-2.5 shrink-0">
                    <Image src="/logo-icon.png" alt="5edmaa.tn" width={40} height={36} className="h-9 w-auto" priority />
                    <span className="text-2xl font-black hidden sm:inline">
                        edma<span className="text-[#D8202B]">.tn</span>
                    </span>
                </Link>

                {user && (
                    <div className="hidden md:flex items-center gap-1 flex-1 overflow-x-auto">
                        {links.map((link) => (
                            <Link
                                key={link.href}
                                href={link.href}
                                className={`px-3 py-2 rounded-lg text-sm font-bold whitespace-nowrap transition-colors ${
                                    pathname === link.href
                                        ? 'bg-red-50 text-[#D8202B]'
                                        : 'text-gray-600 hover:bg-gray-100'
                                }`}
                            >
                                {link.label}
                            </Link>
                        ))}
                    </div>
                )}

                {user ? (
                    <div className="flex items-center gap-3 shrink-0">
                        <Link href="/profile">
                            <Badge variant="success">{user.role.toUpperCase()}</Badge>
                        </Link>
                        <Button variant="ghost" size="sm" onClick={logout}>
                            Déconnexion
                        </Button>
                    </div>
                ) : (
                    <div className="flex items-center gap-3 shrink-0">
                        <Link href="/login">
                            <Button variant="ghost" size="sm">
                                Se connecter
                            </Button>
                        </Link>
                        <Link href="/register">
                            <Button variant="primary" size="sm">
                                S&apos;inscrire
                            </Button>
                        </Link>
                    </div>
                )}
            </div>
        </nav>
    );
}
