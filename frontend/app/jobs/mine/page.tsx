'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Nav } from '@/components/Nav';
import { Badge, Button, Card, EmptyState, FullPageSpinner } from '@/components/ui';
import { useRequireAuth } from '@/lib/hooks';
import { jobsService } from '@/lib/api';
import type { JobOffer } from '@/lib/types';

export default function MyJobsPage() {
    const { loading } = useRequireAuth(['client']);
    const [jobs, setJobs] = useState<JobOffer[]>([]);
    const [fetching, setFetching] = useState(true);

    useEffect(() => {
        if (loading) return;
        jobsService.mine().then(setJobs).finally(() => setFetching(false));
    }, [loading]);

    if (loading || fetching) return <FullPageSpinner />;

    return (
        <div className="min-h-screen bg-gray-50">
            <Nav />
            <div className="max-w-5xl mx-auto px-6 py-12">
                <div className="flex items-center justify-between mb-8">
                    <h1 className="text-3xl font-black">Mes offres</h1>
                    <Link href="/jobs/new">
                        <Button>+ Publier une offre</Button>
                    </Link>
                </div>

                {jobs.length === 0 ? (
                    <EmptyState>Vous n&apos;avez publié aucune offre pour le moment.</EmptyState>
                ) : (
                    <div className="space-y-4">
                        {jobs.map((job) => (
                            <Link key={job.id} href={`/jobs/${job.id}`}>
                                <Card hoverable>
                                    <div className="flex items-center justify-between gap-4">
                                        <div>
                                            <div className="flex items-center gap-3 mb-1">
                                                <h3 className="text-xl font-black">{job.title}</h3>
                                                <Badge variant={job.status === 'open' ? 'success' : 'default'}>
                                                    {job.status === 'open' ? 'Ouverte' : 'Fermée'}
                                                </Badge>
                                            </div>
                                            <p className="text-sm text-gray-500">
                                                {job.category} · {job.location} · {job.application_count}{' '}
                                                candidat(s)
                                            </p>
                                        </div>
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
