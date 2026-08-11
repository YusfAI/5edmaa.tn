'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Nav } from '@/components/Nav';
import { Badge, Button, Card, EmptyState, FullPageSpinner } from '@/components/ui';
import { useRequireAuth } from '@/lib/hooks';
import { apiErrorMessage, jobsService } from '@/lib/api';
import type { MyApplication } from '@/lib/types';

const STATUS_VARIANT = {
    pending: 'warning',
    accepted: 'success',
    rejected: 'error',
} as const;

export default function MyApplicationsPage() {
    const { loading } = useRequireAuth(['worker']);
    const [apps, setApps] = useState<MyApplication[]>([]);
    const [fetching, setFetching] = useState(true);
    const [busyId, setBusyId] = useState<number | null>(null);
    const [error, setError] = useState('');

    const load = () => jobsService.myApplications().then(setApps).finally(() => setFetching(false));

    useEffect(() => {
        if (!loading) load();
    }, [loading]);

    if (loading || fetching) return <FullPageSpinner />;

    const handleWithdraw = async (app: MyApplication) => {
        setBusyId(app.id);
        setError('');
        try {
            await jobsService.withdrawApplication(app.job_id, app.id);
            await load();
        } catch (err) {
            setError(apiErrorMessage(err));
        } finally {
            setBusyId(null);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50">
            <Nav />
            <div className="max-w-3xl mx-auto px-6 py-12">
                <h1 className="text-3xl font-black mb-8">Mes candidatures</h1>
                {error && <div className="mb-4"><Badge variant="error">{error}</Badge></div>}

                {apps.length === 0 ? (
                    <EmptyState>
                        Vous n&apos;avez postulé à aucune offre.{' '}
                        <Link href="/jobs" className="text-[#DC143C] font-bold">
                            Parcourir les offres
                        </Link>
                    </EmptyState>
                ) : (
                    <div className="space-y-4">
                        {apps.map((app) => (
                            <Card key={app.id}>
                                <div className="flex items-start justify-between gap-4">
                                    <div>
                                        <div className="flex items-center gap-3 mb-1">
                                            <Link href={`/jobs/${app.job_id}`} className="font-black text-lg hover:underline">
                                                {app.job_title}
                                            </Link>
                                            <Badge variant={STATUS_VARIANT[app.status]}>{app.status}</Badge>
                                        </div>
                                        {app.cover_message && (
                                            <p className="text-sm text-gray-600">{app.cover_message}</p>
                                        )}
                                    </div>
                                    <div className="flex gap-2 shrink-0">
                                        {app.status === 'accepted' && (
                                            <Link href={`/jobs/${app.job_id}`}>
                                                <Button size="sm" variant="secondary">
                                                    💬 Voir
                                                </Button>
                                            </Link>
                                        )}
                                        {app.status === 'pending' && (
                                            <Button
                                                size="sm"
                                                variant="outline"
                                                onClick={() => handleWithdraw(app)}
                                                disabled={busyId === app.id}
                                            >
                                                Retirer
                                            </Button>
                                        )}
                                    </div>
                                </div>
                            </Card>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
