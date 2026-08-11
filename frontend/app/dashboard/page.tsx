'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button, Input, Card, Badge } from '@/components/ui';
import { authService } from '@/lib/api';
import api from '@/lib/api';
import { User, JobOffer } from '@/lib/types';

export default function DashboardPage() {
    const router = useRouter();
    const [user, setUser] = useState<User | null>(null);
    const [jobs, setJobs] = useState<JobOffer[]>([]);
    const [loading, setLoading] = useState(true);

    // Job form state
    const [jobTitle, setJobTitle] = useState('');
    const [jobDescription, setJobDescription] = useState('');
    const [aiLoading, setAiLoading] = useState(false);

    useEffect(() => {
        loadUser();
    }, []);

    const loadUser = async () => {
        try {
            const userData = await authService.getCurrentUser();
            setUser(userData);

            if (userData.role === 'client' || userData.role === 'admin') {
                loadJobs();
            }
        } catch (error) {
            router.push('/login');
        } finally {
            setLoading(false);
        }
    };

    const loadJobs = async () => {
        try {
            const response = await api.get('/jobs/my');
            setJobs(response.data);
        } catch (error) {
            console.error('Failed to load jobs:', error);
        }
    };

    const handleGenerateDescription = async () => {
        if (!jobTitle) return;
        setAiLoading(true);
        try {
            const response = await api.post('/ai/generate/job_description', {
                title: jobTitle,
                keywords: [],
            });
            setJobDescription(response.data.text);
        } catch (error) {
            console.error('AI generation failed:', error);
        } finally {
            setAiLoading(false);
        }
    };

    const handlePostJob = async () => {
        if (!jobTitle || !jobDescription) return;
        try {
            const response = await api.post('/jobs', {
                title: jobTitle,
                description: jobDescription,
                category: 'Général',
                location: 'Tunis',
                budget_min: 0,
                budget_max: 100,
            });
            setJobs([response.data, ...jobs]);
            setJobTitle('');
            setJobDescription('');
        } catch (error) {
            console.error('Failed to post job:', error);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#DC143C]"></div>
            </div>
        );
    }

    if (!user) return null;

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Nav */}
            <nav className="glass border-b border-gray-200 sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="crimson-gradient p-2 rounded-xl">
                            <span className="text-white text-2xl font-black">5</span>
                        </div>
                        <span className="text-2xl font-black">edma<span className="text-[#DC143C]">.tn</span></span>
                    </div>

                    <div className="flex items-center gap-4">
                        <Badge variant="success">{user.role.toUpperCase()}</Badge>
                        <Button variant="ghost" size="sm" onClick={authService.logout}>
                            Déconnexion
                        </Button>
                    </div>
                </div>
            </nav>

            {/* Content */}
            <div className="max-w-7xl mx-auto px-6 py-12">
                <div className="grid lg:grid-cols-3 gap-8">
                    {/* Sidebar */}
                    <div className="lg:col-span-1">
                        <Card>
                            <div className="text-center mb-6">
                                <div className="w-20 h-20 bg-gradient-to-br from-[#DC143C] to-[#A01028] rounded-full mx-auto mb-4 flex items-center justify-center text-white text-3xl font-black">
                                    {user.email[0].toUpperCase()}
                                </div>
                                <h2 className="text-xl font-black">{user.email}</h2>
                                <p className="text-gray-600 text-sm">{user.phone || 'No phone'}</p>
                            </div>

                            <div className="border-t pt-4 space-y-2">
                                <div className="flex justify-between text-sm">
                                    <span className="text-gray-600">Mes Offres</span>
                                    <span className="font-bold">{jobs.length}</span>
                                </div>
                            </div>
                        </Card>
                    </div>

                    {/* Main Content */}
                    <div className="lg:col-span-2 space-y-8">
                        {/* Post Job */}
                        {(user.role === 'client' || user.role === 'admin') && (
                            <Card>
                                <h3 className="text-2xl font-black mb-6">Poster une Offre</h3>

                                <div className="space-y-4">
                                    <div className="flex gap-3">
                                        <Input
                                            placeholder="Ex: Réparation robinet"
                                            value={jobTitle}
                                            onChange={(e) => setJobTitle(e.target.value)}
                                            className="flex-1"
                                        />
                                        <Button
                                            variant="secondary"
                                            onClick={handleGenerateDescription}
                                            disabled={aiLoading || !jobTitle}
                                        >
                                            {aiLoading ? '⌛' : '🪄'} IA
                                        </Button>
                                    </div>

                                    <textarea
                                        className="w-full px-4 py-3 rounded-xl border-2 border-gray-200 focus:border-[#DC143C] focus:outline-none h-32"
                                        placeholder="Description du travail..."
                                        value={jobDescription}
                                        onChange={(e) => setJobDescription(e.target.value)}
                                    />

                                    <Button
                                        variant="primary"
                                        size="lg"
                                        className="w-full"
                                        onClick={handlePostJob}
                                        disabled={!jobTitle || !jobDescription}
                                    >
                                        Publier
                                    </Button>
                                </div>
                            </Card>
                        )}

                        {/* Jobs List */}
                        <div>
                            <h3 className="text-2xl font-black mb-6">Mes Offres</h3>
                            <div className="space-y-4">
                                {jobs.length === 0 ? (
                                    <Card>
                                        <p className="text-center text-gray-600">Aucune offre pour le moment</p>
                                    </Card>
                                ) : (
                                    jobs.map((job) => (
                                        <Card key={job.id} hoverable>
                                            <div className="flex items-start justify-between">
                                                <div className="flex-1">
                                                    <div className="flex items-center gap-3 mb-2">
                                                        <h4 className="text-xl font-black">{job.title}</h4>
                                                        <Badge variant={job.status === 'open' ? 'success' : 'default'}>
                                                            {job.status === 'open' ? 'Ouvert' : 'Fermé'}
                                                        </Badge>
                                                    </div>
                                                    <p className="text-gray-600 text-sm mb-2">{job.description}</p>
                                                    <div className="flex items-center gap-4 text-sm text-gray-500">
                                                        <span>{job.category}</span>
                                                        <span>{job.location}</span>
                                                        <span>{job.application_count} candidats</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </Card>
                                    ))
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
