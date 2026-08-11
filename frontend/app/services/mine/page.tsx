'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Nav } from '@/components/Nav';
import { Alert, Badge, Button, Card, EmptyState, FullPageSpinner } from '@/components/ui';
import { useRequireAuth } from '@/lib/hooks';
import { apiErrorMessage, servicesService } from '@/lib/api';
import type { Service } from '@/lib/types';

export default function MyServicesPage() {
    const { loading } = useRequireAuth(['worker']);
    const [services, setServices] = useState<Service[]>([]);
    const [fetching, setFetching] = useState(true);
    const [error, setError] = useState('');
    const [busyId, setBusyId] = useState<number | null>(null);

    const load = () => servicesService.mine().then(setServices).finally(() => setFetching(false));

    useEffect(() => {
        if (!loading) load();
    }, [loading]);

    if (loading || fetching) return <FullPageSpinner />;

    const handleDelete = async (id: number) => {
        setBusyId(id);
        setError('');
        try {
            await servicesService.remove(id);
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
            <div className="max-w-4xl mx-auto px-6 py-12">
                <div className="flex items-center justify-between mb-8">
                    <h1 className="text-3xl font-black">Mes services</h1>
                    <Link href="/services/new">
                        <Button>+ Nouveau service</Button>
                    </Link>
                </div>
                {error && <div className="mb-4"><Alert>{error}</Alert></div>}

                {services.length === 0 ? (
                    <EmptyState>Vous n&apos;avez publié aucun service pour le moment.</EmptyState>
                ) : (
                    <div className="space-y-4">
                        {services.map((service) => (
                            <Card key={service.id}>
                                <div className="flex items-start justify-between gap-4">
                                    <div>
                                        <div className="flex items-center gap-3 mb-1">
                                            <h3 className="text-lg font-black">{service.title}</h3>
                                            {service.is_premium && <Badge variant="warning">⭐ Premium</Badge>}
                                        </div>
                                        <p className="text-sm text-gray-500">
                                            {service.category} · {service.location}
                                            {service.base_price != null && ` · ${service.base_price} TND`}
                                        </p>
                                    </div>
                                    <Button
                                        size="sm"
                                        variant="outline"
                                        onClick={() => handleDelete(service.id)}
                                        disabled={busyId === service.id}
                                    >
                                        Supprimer
                                    </Button>
                                </div>
                            </Card>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
