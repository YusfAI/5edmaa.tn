'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Nav } from '@/components/Nav';
import Link from 'next/link';
import { Alert, Badge, Button, Card, EmptyState, FullPageSpinner, Input, Stars, Textarea } from '@/components/ui';
import { useAuth } from '@/contexts/AuthContext';
import { apiErrorMessage, bookingsService, reviewsService, servicesService } from '@/lib/api';
import type { Review, Service } from '@/lib/types';

export default function ServiceDetailPage() {
    const { user, loading } = useAuth();
    const params = useParams();
    const serviceId = Number(params.id);

    const [service, setService] = useState<Service | null>(null);
    const [reviews, setReviews] = useState<Review[]>([]);
    const [fetching, setFetching] = useState(true);
    const [scheduledFor, setScheduledFor] = useState('');
    const [note, setNote] = useState('');
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState('');
    const [notice, setNotice] = useState('');

    useEffect(() => {
        if (loading) return;
        servicesService
            .get(serviceId)
            .then(async (svc) => {
                setService(svc);
                setReviews(await reviewsService.workerReviews(svc.provider_id).catch(() => []));
            })
            .finally(() => setFetching(false));
    }, [loading, serviceId]);

    if (loading || fetching) return <FullPageSpinner />;
    if (!service) return <div className="p-12 text-center">Service introuvable</div>;

    const avgRating = reviews.length
        ? reviews.reduce((sum, r) => sum + r.rating, 0) / reviews.length
        : null;

    const handleBook = async () => {
        if (!scheduledFor) return;
        setBusy(true);
        setError('');
        try {
            await bookingsService.create({
                service_id: service.id,
                scheduled_for: new Date(scheduledFor).toISOString(),
                note: note || undefined,
            });
            setNotice('Réservation envoyée !');
        } catch (err) {
            setError(apiErrorMessage(err, 'La réservation a échoué'));
        } finally {
            setBusy(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50">
            <Nav />
            <div className="max-w-3xl mx-auto px-6 py-12 space-y-6">
                <Card>
                    <div className="flex items-center gap-3 mb-2">
                        <h1 className="text-2xl font-black">{service.title}</h1>
                        {service.is_premium && <Badge variant="warning">⭐ Premium</Badge>}
                    </div>
                    <p className="text-sm text-gray-500 mb-4">
                        {service.category} · {service.location}
                        {service.base_price != null && ` · À partir de ${service.base_price} TND`}
                    </p>
                    {avgRating != null && <Stars rating={avgRating} />}
                    <p className="text-gray-700 whitespace-pre-wrap mt-4">{service.description}</p>
                </Card>

                {!user && (
                    <Card>
                        <h2 className="text-xl font-black mb-2">Intéressé par ce service ?</h2>
                        <p className="text-gray-600 text-sm mb-4">
                            Connectez-vous ou créez un compte client pour réserver.
                        </p>
                        <div className="flex gap-3">
                            <Link href="/login">
                                <Button>Se connecter</Button>
                            </Link>
                            <Link href="/register">
                                <Button variant="outline">Créer un compte</Button>
                            </Link>
                        </div>
                    </Card>
                )}

                {user?.role === 'client' && (
                    <Card>
                        <h2 className="text-xl font-black mb-4">Réserver ce service</h2>
                        <div className="space-y-4">
                            <Input
                                label="Date et heure souhaitées"
                                type="datetime-local"
                                value={scheduledFor}
                                onChange={(e) => setScheduledFor(e.target.value)}
                                required
                            />
                            <Textarea
                                label="Note (optionnel)"
                                value={note}
                                onChange={(e) => setNote(e.target.value)}
                                className="h-24"
                                placeholder="Adresse, détails particuliers..."
                            />
                            {error && <Alert>{error}</Alert>}
                            {notice && <Alert variant="success">{notice}</Alert>}
                            <Button onClick={handleBook} disabled={busy || !scheduledFor} className="w-full">
                                {busy ? 'Envoi...' : 'Demander une réservation'}
                            </Button>
                        </div>
                    </Card>
                )}

                <Card>
                    <h2 className="text-xl font-black mb-4">Avis ({reviews.length})</h2>
                    {reviews.length === 0 ? (
                        <EmptyState>Pas encore d&apos;avis pour ce professionnel.</EmptyState>
                    ) : (
                        <div className="space-y-3">
                            {reviews.map((review) => (
                                <div key={review.id} className="border-b border-gray-100 pb-3 last:border-0">
                                    <Stars rating={review.rating} />
                                    {review.comment && (
                                        <p className="text-sm text-gray-600 mt-1">{review.comment}</p>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                </Card>
            </div>
        </div>
    );
}
