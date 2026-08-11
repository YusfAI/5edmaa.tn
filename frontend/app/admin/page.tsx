'use client';

import { useEffect, useState } from 'react';
import { Nav } from '@/components/Nav';
import { Alert, Button, Card, EmptyState, FullPageSpinner, Textarea } from '@/components/ui';
import { useRequireAuth } from '@/lib/hooks';
import { adminService, apiErrorMessage } from '@/lib/api';
import type { PendingProfile } from '@/lib/types';

function PendingList({
    title,
    items,
    onApprove,
    onReject,
    busy,
}: {
    title: string;
    items: PendingProfile[];
    onApprove: (userId: number) => void;
    onReject: (userId: number, reason: string) => void;
    busy: number | null;
}) {
    const [reasons, setReasons] = useState<Record<number, string>>({});

    return (
        <Card>
            <h2 className="text-xl font-black mb-4">
                {title} ({items.length})
            </h2>
            {items.length === 0 ? (
                <EmptyState>Rien en attente.</EmptyState>
            ) : (
                <div className="space-y-4">
                    {items.map((item) => (
                        <div key={item.user_id} className="border-2 border-gray-100 rounded-xl p-4">
                            <p className="font-bold">
                                {item.full_name || item.email} — #{item.user_id}
                            </p>
                            <p className="text-sm text-gray-500 mb-2">
                                {item.email} · {item.phone} · {item.location || '—'}
                            </p>
                            {item.company_name && (
                                <p className="text-sm text-gray-600">🏢 {item.company_name}</p>
                            )}
                            {item.bio && <p className="text-sm text-gray-600 mb-2">{item.bio}</p>}
                            {item.categories && item.categories.length > 0 && (
                                <p className="text-sm text-gray-600 mb-2">
                                    Catégories : {item.categories.join(', ')}
                                </p>
                            )}
                            <div className="flex items-start gap-2 mt-3">
                                <Textarea
                                    placeholder="Motif de rejet (si refus)"
                                    value={reasons[item.user_id] || ''}
                                    onChange={(e) =>
                                        setReasons({ ...reasons, [item.user_id]: e.target.value })
                                    }
                                    className="flex-1 h-16"
                                />
                                <div className="flex flex-col gap-2">
                                    <Button
                                        size="sm"
                                        onClick={() => onApprove(item.user_id)}
                                        disabled={busy === item.user_id}
                                    >
                                        Approuver
                                    </Button>
                                    <Button
                                        size="sm"
                                        variant="outline"
                                        onClick={() =>
                                            onReject(item.user_id, reasons[item.user_id] || 'Non spécifié')
                                        }
                                        disabled={busy === item.user_id}
                                    >
                                        Refuser
                                    </Button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </Card>
    );
}

export default function AdminPage() {
    const { loading } = useRequireAuth(['admin']);
    const [workers, setWorkers] = useState<PendingProfile[]>([]);
    const [clients, setClients] = useState<PendingProfile[]>([]);
    const [fetching, setFetching] = useState(true);
    const [busy, setBusy] = useState<number | null>(null);
    const [error, setError] = useState('');

    const load = () =>
        Promise.all([adminService.pendingWorkers(), adminService.pendingClients()]).then(
            ([w, c]) => {
                setWorkers(w);
                setClients(c);
            }
        );

    useEffect(() => {
        if (!loading) load().finally(() => setFetching(false));
    }, [loading]);

    if (loading || fetching) return <FullPageSpinner />;

    const wrap = (fn: () => Promise<unknown>, userId: number) => async () => {
        setBusy(userId);
        setError('');
        try {
            await fn();
            await load();
        } catch (err) {
            setError(apiErrorMessage(err));
        } finally {
            setBusy(null);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50">
            <Nav />
            <div className="max-w-4xl mx-auto px-6 py-12 space-y-8">
                <h1 className="text-3xl font-black">File de vérification</h1>
                {error && <Alert>{error}</Alert>}

                <PendingList
                    title="Travailleurs en attente"
                    items={workers}
                    busy={busy}
                    onApprove={(id) => wrap(() => adminService.verifyWorker(id), id)()}
                    onReject={(id, reason) => wrap(() => adminService.rejectWorker(id, reason), id)()}
                />
                <PendingList
                    title="Clients en attente"
                    items={clients}
                    busy={busy}
                    onApprove={(id) => wrap(() => adminService.verifyClient(id), id)()}
                    onReject={(id, reason) => wrap(() => adminService.rejectClient(id, reason), id)()}
                />
            </div>
        </div>
    );
}
