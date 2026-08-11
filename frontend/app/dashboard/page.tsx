'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Nav } from '@/components/Nav';
import { Badge, Card, EmptyState, FullPageSpinner } from '@/components/ui';
import { useAuth } from '@/contexts/AuthContext';
import { useRequireAuth } from '@/lib/hooks';
import { adminService, jobsService, servicesService, walletService } from '@/lib/api';
import type { Wallet } from '@/lib/types';

function StatusBadge({ status }: { status: 'pending' | 'approved' | 'rejected' }) {
    const variant = status === 'approved' ? 'success' : status === 'rejected' ? 'error' : 'warning';
    const label = status === 'approved' ? 'Vérifié' : status === 'rejected' ? 'Rejeté' : 'En attente';
    return <Badge variant={variant}>{label}</Badge>;
}

export default function DashboardPage() {
    const { loading } = useRequireAuth();
    const { user, workerProfile, clientProfile } = useAuth();
    const [wallet, setWallet] = useState<Wallet | null>(null);
    const [jobCount, setJobCount] = useState<number | null>(null);
    const [serviceCount, setServiceCount] = useState<number | null>(null);
    const [pendingCounts, setPendingCounts] = useState<{ workers: number; clients: number } | null>(null);

    useEffect(() => {
        if (!user) return;
        walletService.me().then(setWallet).catch(() => {});

        if (user.role === 'worker') {
            servicesService.mine().then((s) => setServiceCount(s.length)).catch(() => {});
        } else if (user.role === 'client') {
            jobsService.mine().then((j) => setJobCount(j.length)).catch(() => {});
        } else if (user.role === 'admin') {
            Promise.all([adminService.pendingWorkers(), adminService.pendingClients()]).then(
                ([workers, clients]) => setPendingCounts({ workers: workers.length, clients: clients.length })
            ).catch(() => {});
        }
    }, [user]);

    if (loading || !user) return <FullPageSpinner />;

    return (
        <div className="min-h-screen bg-gray-50">
            <Nav />
            <div className="max-w-7xl mx-auto px-6 py-12">
                <h1 className="text-3xl font-black mb-8">
                    Bonjour, {user.email.split('@')[0]} 👋
                </h1>

                <div className="grid md:grid-cols-3 gap-6 mb-10">
                    <Card>
                        <p className="text-gray-500 text-sm mb-1">Solde du portefeuille</p>
                        <p className="text-3xl font-black">
                            {wallet ? `${wallet.balance} ${wallet.currency}` : '—'}
                        </p>
                        <Link href="/wallet" className="text-[#DC143C] text-sm font-bold">
                            Voir le portefeuille →
                        </Link>
                    </Card>

                    {user.role === 'worker' && workerProfile && (
                        <>
                            <Card>
                                <p className="text-gray-500 text-sm mb-1">Statut du compte</p>
                                <StatusBadge status={workerProfile.status} />
                                {workerProfile.status === 'rejected' && workerProfile.rejection_reason && (
                                    <p className="text-xs text-red-600 mt-2">{workerProfile.rejection_reason}</p>
                                )}
                                {workerProfile.status === 'pending' && (
                                    <p className="text-xs text-gray-500 mt-2">
                                        Complétez votre profil pour être vérifié par un admin.
                                    </p>
                                )}
                            </Card>
                            <Card>
                                <p className="text-gray-500 text-sm mb-1">Mes services</p>
                                <p className="text-3xl font-black">{serviceCount ?? '—'}</p>
                                <Link href="/services/mine" className="text-[#DC143C] text-sm font-bold">
                                    Gérer →
                                </Link>
                            </Card>
                        </>
                    )}

                    {user.role === 'client' && clientProfile && (
                        <>
                            <Card>
                                <p className="text-gray-500 text-sm mb-1">Statut du compte</p>
                                <StatusBadge status={clientProfile.status} />
                                {clientProfile.status === 'rejected' && clientProfile.rejection_reason && (
                                    <p className="text-xs text-red-600 mt-2">{clientProfile.rejection_reason}</p>
                                )}
                            </Card>
                            <Card>
                                <p className="text-gray-500 text-sm mb-1">Mes offres publiées</p>
                                <p className="text-3xl font-black">{jobCount ?? '—'}</p>
                                <Link href="/jobs/mine" className="text-[#DC143C] text-sm font-bold">
                                    Gérer →
                                </Link>
                            </Card>
                        </>
                    )}

                    {user.role === 'admin' && (
                        <>
                            <Card>
                                <p className="text-gray-500 text-sm mb-1">Travailleurs en attente</p>
                                <p className="text-3xl font-black">{pendingCounts?.workers ?? '—'}</p>
                                <Link href="/admin" className="text-[#DC143C] text-sm font-bold">
                                    Vérifier →
                                </Link>
                            </Card>
                            <Card>
                                <p className="text-gray-500 text-sm mb-1">Clients en attente</p>
                                <p className="text-3xl font-black">{pendingCounts?.clients ?? '—'}</p>
                                <Link href="/admin" className="text-[#DC143C] text-sm font-bold">
                                    Vérifier →
                                </Link>
                            </Card>
                        </>
                    )}
                </div>

                {user.role === 'worker' && !workerProfile?.verified && (
                    <EmptyState>
                        Votre compte n&apos;est pas encore vérifié — vous pourrez postuler aux offres et
                        publier des services une fois approuvé par un administrateur.{' '}
                        <Link href="/profile" className="text-[#DC143C] font-bold">
                            Compléter mon profil
                        </Link>
                    </EmptyState>
                )}
                {user.role === 'client' && !clientProfile?.verified && (
                    <EmptyState>
                        Votre compte n&apos;est pas encore vérifié — vous pourrez publier des offres une
                        fois approuvé par un administrateur.{' '}
                        <Link href="/profile" className="text-[#DC143C] font-bold">
                            Compléter mon profil
                        </Link>
                    </EmptyState>
                )}
            </div>
        </div>
    );
}
