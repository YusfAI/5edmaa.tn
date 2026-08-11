'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Nav } from '@/components/Nav';
import {
    Alert,
    Badge,
    Button,
    Card,
    EmptyState,
    FullPageSpinner,
    Textarea,
} from '@/components/ui';
import { useAuth } from '@/contexts/AuthContext';
import { apiErrorMessage, jobsService, subscriptionsService } from '@/lib/api';
import type { JobApplication, JobOffer } from '@/lib/types';

export default function JobDetailPage() {
    const { user, loading } = useAuth();
    const params = useParams();
    const jobId = Number(params.id);

    const [job, setJob] = useState<JobOffer | null>(null);
    const [applications, setApplications] = useState<JobApplication[] | null>(null);
    const [coverMessage, setCoverMessage] = useState('');
    const [error, setError] = useState('');
    const [notice, setNotice] = useState('');
    const [busy, setBusy] = useState(false);
    const [fetching, setFetching] = useState(true);

    const isOwner = !!(user && job && user.role === 'client' && job.client_id === user.id);

    const loadJob = async () => {
        try {
            const data = await jobsService.get(jobId);
            setJob(data);
            if (user?.role === 'client' && data.client_id === user.id) {
                setApplications(await jobsService.listApplications(jobId));
            }
        } catch (err) {
            setError(apiErrorMessage(err, 'Offre introuvable'));
        } finally {
            setFetching(false);
        }
    };

    useEffect(() => {
        if (!loading) loadJob();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [loading, user, jobId]);

    if (loading || fetching) return <FullPageSpinner />;
    if (!job) return <div className="p-12 text-center">{error || 'Offre introuvable'}</div>;

    const handleApply = async () => {
        setBusy(true);
        setError('');
        setNotice('');
        try {
            await jobsService.apply(jobId, coverMessage || undefined);
            setNotice('Candidature envoyée !');
        } catch (err) {
            setError(apiErrorMessage(err, "La candidature a échoué"));
        } finally {
            setBusy(false);
        }
    };

    const handleDecision = async (appId: number, action: 'accept' | 'reject') => {
        setBusy(true);
        try {
            if (action === 'accept') await jobsService.acceptApplication(jobId, appId);
            else await jobsService.rejectApplication(jobId, appId);
            setApplications(await jobsService.listApplications(jobId));
        } catch (err) {
            setError(apiErrorMessage(err));
        } finally {
            setBusy(false);
        }
    };

    const handleClose = async () => {
        setBusy(true);
        try {
            setJob(await jobsService.close(jobId));
        } catch (err) {
            setError(apiErrorMessage(err));
        } finally {
            setBusy(false);
        }
    };

    const handleComplete = async () => {
        setBusy(true);
        try {
            setJob(await jobsService.complete(jobId));
        } catch (err) {
            setError(apiErrorMessage(err));
        } finally {
            setBusy(false);
        }
    };

    const handleBoost = async () => {
        setBusy(true);
        try {
            await subscriptionsService.boostJob(jobId, 7);
            setJob(await jobsService.get(jobId));
            setNotice('Offre boostée pour 7 jours !');
        } catch (err) {
            setError(apiErrorMessage(err, 'Le boost a échoué (solde insuffisant ?)'));
        } finally {
            setBusy(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50">
            <Nav />
            <div className="max-w-3xl mx-auto px-6 py-12 space-y-6">
                <Card>
                    <div className="flex items-start justify-between gap-4 mb-4">
                        <div>
                            <div className="flex items-center gap-3 mb-2">
                                <h1 className="text-2xl font-black">{job.title}</h1>
                                <Badge variant={job.status === 'open' ? 'success' : 'default'}>
                                    {job.status === 'open' ? 'Ouverte' : 'Fermée'}
                                </Badge>
                            </div>
                            <p className="text-sm text-gray-500">
                                {job.category} · {job.location}
                                {(job.budget_min || job.budget_max) &&
                                    ` · ${job.budget_min ?? '?'}–${job.budget_max ?? '?'} TND`}
                            </p>
                        </div>
                    </div>
                    <p className="text-gray-700 whitespace-pre-wrap">{job.description}</p>
                </Card>

                {error && <Alert>{error}</Alert>}
                {notice && <Alert variant="success">{notice}</Alert>}

                {isOwner && (
                    <Card>
                        <h2 className="text-xl font-black mb-4">Gérer l&apos;offre</h2>
                        <div className="flex flex-wrap gap-3 mb-6">
                            {job.status === 'open' && (
                                <>
                                    <Button variant="outline" onClick={handleClose} disabled={busy}>
                                        Fermer l&apos;offre
                                    </Button>
                                    <Button variant="secondary" onClick={handleBoost} disabled={busy}>
                                        🚀 Booster (7 jours)
                                    </Button>
                                </>
                            )}
                            {job.status === 'open' && (
                                <Button onClick={handleComplete} disabled={busy}>
                                    Marquer comme terminée
                                </Button>
                            )}
                        </div>

                        <h3 className="font-black mb-3">Candidatures ({applications?.length ?? 0})</h3>
                        {!applications || applications.length === 0 ? (
                            <EmptyState>Aucune candidature pour le moment.</EmptyState>
                        ) : (
                            <div className="space-y-3">
                                {applications.map((app) => (
                                    <div
                                        key={app.id}
                                        className="border-2 border-gray-100 rounded-xl p-4 flex items-start justify-between gap-4"
                                    >
                                        <div>
                                            <p className="font-bold">Travailleur #{app.worker_id}</p>
                                            {app.cover_message && (
                                                <p className="text-sm text-gray-600 mt-1">{app.cover_message}</p>
                                            )}
                                            <Badge
                                                variant={
                                                    app.status === 'accepted'
                                                        ? 'success'
                                                        : app.status === 'rejected'
                                                        ? 'error'
                                                        : 'warning'
                                                }
                                            >
                                                {app.status}
                                            </Badge>
                                        </div>
                                        <div className="flex gap-2 shrink-0">
                                            {app.status === 'pending' && (
                                                <>
                                                    <Button
                                                        size="sm"
                                                        onClick={() => handleDecision(app.id, 'accept')}
                                                        disabled={busy}
                                                    >
                                                        Accepter
                                                    </Button>
                                                    <Button
                                                        size="sm"
                                                        variant="outline"
                                                        onClick={() => handleDecision(app.id, 'reject')}
                                                        disabled={busy}
                                                    >
                                                        Refuser
                                                    </Button>
                                                </>
                                            )}
                                            {app.status === 'accepted' && (
                                                <Link href={`/chat/${job.id}?with=${app.worker_id}`}>
                                                    <Button size="sm" variant="secondary">
                                                        💬 Chat
                                                    </Button>
                                                </Link>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </Card>
                )}

                {!user && (
                    <Card>
                        <h2 className="text-xl font-black mb-2">Intéressé par cette offre ?</h2>
                        <p className="text-gray-600 text-sm mb-4">
                            Connectez-vous ou créez un compte travailleur pour postuler.
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

                {user?.role === 'worker' && !isOwner && (
                    <Card>
                        <h2 className="text-xl font-black mb-4">Postuler à cette offre</h2>
                        <Textarea
                            label="Message de motivation (optionnel)"
                            value={coverMessage}
                            onChange={(e) => setCoverMessage(e.target.value)}
                            className="h-28 mb-4"
                            placeholder="Expliquez pourquoi vous êtes le bon candidat..."
                        />
                        <div className="flex gap-3">
                            <Button onClick={handleApply} disabled={busy || job.status !== 'open'}>
                                {job.status !== 'open' ? 'Offre fermée' : 'Envoyer ma candidature'}
                            </Button>
                            <Link href={`/chat/${job.id}?with=${job.client_id}`}>
                                <Button variant="outline">💬 Contacter le client</Button>
                            </Link>
                        </div>
                    </Card>
                )}
            </div>
        </div>
    );
}
