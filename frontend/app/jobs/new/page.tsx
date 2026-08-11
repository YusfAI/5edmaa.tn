'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Nav } from '@/components/Nav';
import { Alert, Button, Card, FullPageSpinner, Input, Textarea } from '@/components/ui';
import { useRequireAuth } from '@/lib/hooks';
import { aiService, apiErrorMessage, jobsService } from '@/lib/api';

export default function NewJobPage() {
    const { loading } = useRequireAuth(['client']);
    const router = useRouter();

    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [category, setCategory] = useState('');
    const [location, setLocation] = useState('');
    const [budgetMin, setBudgetMin] = useState('');
    const [budgetMax, setBudgetMax] = useState('');
    const [aiLoading, setAiLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');

    if (loading) return <FullPageSpinner />;

    const handleGenerate = async () => {
        if (!title || !category) return;
        setAiLoading(true);
        try {
            const generated = await aiService.generateJobDescription(title, category, []);
            setDescription(generated);
        } catch (err) {
            setError(apiErrorMessage(err, 'La génération IA a échoué'));
        } finally {
            setAiLoading(false);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setSaving(true);
        setError('');
        try {
            const job = await jobsService.create({
                title,
                description,
                category,
                location,
                budget_min: budgetMin ? Number(budgetMin) : undefined,
                budget_max: budgetMax ? Number(budgetMax) : undefined,
            });
            router.push(`/jobs/${job.id}`);
        } catch (err) {
            setError(apiErrorMessage(err, "La publication de l'offre a échoué"));
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50">
            <Nav />
            <div className="max-w-2xl mx-auto px-6 py-12">
                <h1 className="text-3xl font-black mb-8">Publier une offre</h1>
                <Card>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <Input
                            label="Titre"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            placeholder="Ex: Réparation robinet"
                            required
                        />
                        <div className="grid sm:grid-cols-2 gap-4">
                            <Input
                                label="Catégorie"
                                value={category}
                                onChange={(e) => setCategory(e.target.value)}
                                placeholder="Plomberie"
                                required
                            />
                            <Input
                                label="Localisation"
                                value={location}
                                onChange={(e) => setLocation(e.target.value)}
                                placeholder="Tunis"
                                required
                            />
                        </div>
                        <div className="grid sm:grid-cols-2 gap-4">
                            <Input
                                label="Budget min (TND)"
                                type="number"
                                value={budgetMin}
                                onChange={(e) => setBudgetMin(e.target.value)}
                            />
                            <Input
                                label="Budget max (TND)"
                                type="number"
                                value={budgetMax}
                                onChange={(e) => setBudgetMax(e.target.value)}
                            />
                        </div>
                        <div>
                            <div className="flex items-center justify-between mb-2">
                                <label className="block text-sm font-bold text-gray-700">Description</label>
                                <Button
                                    type="button"
                                    variant="secondary"
                                    size="sm"
                                    onClick={handleGenerate}
                                    disabled={aiLoading || !title || !category}
                                >
                                    {aiLoading ? '⌛ Génération...' : '🪄 Générer avec IA'}
                                </Button>
                            </div>
                            <Textarea
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                className="h-40"
                                placeholder="Décrivez le travail à effectuer..."
                                required
                            />
                        </div>
                        {error && <Alert>{error}</Alert>}
                        <Button type="submit" size="lg" className="w-full" disabled={saving}>
                            {saving ? 'Publication...' : "Publier l'offre"}
                        </Button>
                    </form>
                </Card>
            </div>
        </div>
    );
}
