'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Nav } from '@/components/Nav';
import { Badge, Button, Card, EmptyState, FullPageSpinner, Input } from '@/components/ui';
import { useAuth } from '@/contexts/AuthContext';
import { jobsService } from '@/lib/api';
import type { JobOffer } from '@/lib/types';

export default function BrowseJobsPage() {
    const { user, loading } = useAuth();
    const [jobs, setJobs] = useState<JobOffer[]>([]);
    const [category, setCategory] = useState('');
    const [location, setLocation] = useState('');
    const [fetching, setFetching] = useState(true);

    const load = async () => {
        setFetching(true);
        try {
            const data = await jobsService.search({
                category: category || undefined,
                location: location || undefined,
            });
            setJobs(data);
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
                    <h1 className="text-3xl font-black">Offres d&apos;emploi</h1>
                    {user?.role === 'client' && (
                        <Link href="/jobs/new">
                            <Button>+ Publier une offre</Button>
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
                ) : jobs.length === 0 ? (
                    <EmptyState>Aucune offre trouvée pour ces critères.</EmptyState>
                ) : (
                    <div className="space-y-4">
                        {jobs.map((job) => (
                            <Link key={job.id} href={`/jobs/${job.id}`} className="block">
                                <Card hoverable>
                                    <div className="flex items-start justify-between gap-4">
                                        <div className="flex-1">
                                            <div className="flex items-center gap-3 mb-2">
                                                <h3 className="text-xl font-black">{job.title}</h3>
                                                {job.boost_until && new Date(job.boost_until) > new Date() && (
                                                    <Badge variant="warning">🚀 Boosté</Badge>
                                                )}
                                            </div>
                                            <p className="text-gray-600 text-sm mb-2 line-clamp-2">
                                                {job.description}
                                            </p>
                                            <div className="flex items-center gap-4 text-sm text-gray-500">
                                                <span>{job.category}</span>
                                                <span>{job.location}</span>
                                                {(job.budget_min || job.budget_max) && (
                                                    <span>
                                                        {job.budget_min ?? '?'}–{job.budget_max ?? '?'} TND
                                                    </span>
                                                )}
                                                <span>{job.application_count} candidat(s)</span>
                                            </div>
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
