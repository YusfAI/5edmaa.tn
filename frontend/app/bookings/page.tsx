'use client';

import { useEffect, useState } from 'react';
import { Nav } from '@/components/Nav';
import { Alert, Badge, Button, Card, EmptyState, FullPageSpinner } from '@/components/ui';
import { useAuth } from '@/contexts/AuthContext';
import { useRequireAuth } from '@/lib/hooks';
import { apiErrorMessage, bookingsService } from '@/lib/api';
import type { Booking, BookingStatus } from '@/lib/types';

const STATUS_VARIANT: Record<BookingStatus, 'success' | 'warning' | 'error' | 'default'> = {
    pending: 'warning',
    confirmed: 'success',
    completed: 'default',
    cancelled: 'error',
};

export default function BookingsPage() {
    const { loading } = useRequireAuth(['worker', 'client']);
    const { user } = useAuth();
    const [bookings, setBookings] = useState<Booking[]>([]);
    const [fetching, setFetching] = useState(true);
    const [error, setError] = useState('');
    const [busyId, setBusyId] = useState<number | null>(null);

    const isWorker = user?.role === 'worker';

    const load = () => {
        const fetcher = isWorker ? bookingsService.asWorker : bookingsService.asClient;
        return fetcher().then(setBookings).finally(() => setFetching(false));
    };

    useEffect(() => {
        if (!loading && user) load();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [loading, user]);

    if (loading || fetching || !user) return <FullPageSpinner />;

    const act = async (fn: () => Promise<Booking>, id: number) => {
        setBusyId(id);
        setError('');
        try {
            await fn();
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
                <h1 className="text-3xl font-black mb-8">
                    {isWorker ? 'Demandes de réservation' : 'Mes réservations'}
                </h1>
                {error && <div className="mb-4"><Alert>{error}</Alert></div>}

                {bookings.length === 0 ? (
                    <EmptyState>Aucune réservation pour le moment.</EmptyState>
                ) : (
                    <div className="space-y-4">
                        {bookings.map((booking) => (
                            <Card key={booking.id}>
                                <div className="flex items-start justify-between gap-4">
                                    <div>
                                        <div className="flex items-center gap-3 mb-1">
                                            <span className="font-black">Réservation #{booking.id}</span>
                                            <Badge variant={STATUS_VARIANT[booking.status]}>
                                                {booking.status}
                                            </Badge>
                                        </div>
                                        <p className="text-sm text-gray-500">
                                            {new Date(booking.scheduled_for).toLocaleString('fr-TN')}
                                        </p>
                                        {booking.note && (
                                            <p className="text-sm text-gray-600 mt-1">{booking.note}</p>
                                        )}
                                    </div>
                                    <div className="flex gap-2 shrink-0">
                                        {isWorker && booking.status === 'pending' && (
                                            <Button
                                                size="sm"
                                                onClick={() => act(() => bookingsService.confirm(booking.id), booking.id)}
                                                disabled={busyId === booking.id}
                                            >
                                                Confirmer
                                            </Button>
                                        )}
                                        {isWorker && booking.status === 'confirmed' && (
                                            <Button
                                                size="sm"
                                                onClick={() => act(() => bookingsService.complete(booking.id), booking.id)}
                                                disabled={busyId === booking.id}
                                            >
                                                Terminer
                                            </Button>
                                        )}
                                        {['pending', 'confirmed'].includes(booking.status) && (
                                            <Button
                                                size="sm"
                                                variant="outline"
                                                onClick={() => act(() => bookingsService.cancel(booking.id), booking.id)}
                                                disabled={busyId === booking.id}
                                            >
                                                Annuler
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
