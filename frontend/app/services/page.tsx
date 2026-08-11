'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Nav } from '@/components/Nav';
import { Badge, Button, Card, EmptyState, FullPageSpinner, Input } from '@/components/ui';
import { useAuth } from '@/contexts/AuthContext';
import { servicesService } from '@/lib/api';
import type { Service } from '@/lib/types';

export default function BrowseServicesPage() {
    const { user, loading } = useAuth();
    const [services, setServices] = useState<Service[]>([]);
    const [category, setCategory] = useState('');
    const [location, setLocation] = useState('');
    const [fetching, setFetching] = useState(true);

    const load = async () => {
        setFetching(true);
        try {
            const data = await servicesService.browse({
                category: category || undefined,
                location: location || undefined,
            });
            setServices(data);
        } finally {
            setFetching(false);
        }
    };

    useEffect(() => {
        load();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    if (loading) return <FullPageSpinner />;

    return (
        <div className="min-h-screen bg-gray-50">
            <Nav />
            <div className="max-w-5xl mx-auto px-6 py-12">
                <div className="flex items-center justify-between mb-8">
                    <h1 className="text-3xl font-black">Trouver un professionnel</h1>
                    {user?.role === 'worker' && (
                        <Link href="/services/new">
                            <Button>+ Publier un service</Button>
                        </Link>
                    )}
                </div>

                <Card className="mb-8">
                    <div className="grid sm:grid-cols-3 gap-4">
                        <Input
                            placeholder="Catégorie"
                            value={category}
                            onChange={(e) => setCategory(e.target.value)}
                        />
                        <Input
                            placeholder="Localisation"
                            value={location}
                            onChange={(e) => setLocation(e.target.value)}
                        />
                        <Button onClick={load}>Rechercher</Button>
                    </div>
                </Card>

                {fetching ? (
                    <FullPageSpinner />
                ) : services.length === 0 ? (
                    <EmptyState>Aucun service trouvé pour ces critères.</EmptyState>
                ) : (
                    <div className="grid sm:grid-cols-2 gap-4">
                        {services.map((service) => (
                            <Link key={service.id} href={`/services/${service.id}`}>
                                <Card hoverable className="h-full">
                                    <div className="flex items-center gap-2 mb-2">
                                        <h3 className="text-lg font-black">{service.title}</h3>
                                        {service.is_premium && <Badge variant="warning">⭐ Premium</Badge>}
                                    </div>
                                    <p className="text-gray-600 text-sm mb-3 line-clamp-2">
                                        {service.description}
                                    </p>
                                    <div className="flex items-center justify-between text-sm text-gray-500">
                                        <span>
                                            {service.category} · {service.location}
                                        </span>
                                        {service.base_price != null && (
                                            <span className="font-bold text-gray-900">
                                                {service.base_price} TND
                                            </span>
                                        )}
                                    </div>
                                </Card>
                            </Link>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
