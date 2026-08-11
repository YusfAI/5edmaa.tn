'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Nav } from '@/components/Nav';
import { Alert, Button, Card, FullPageSpinner, Input, Textarea } from '@/components/ui';
import { useRequireAuth } from '@/lib/hooks';
import { apiErrorMessage, servicesService } from '@/lib/api';

export default function NewServicePage() {
    const { loading } = useRequireAuth(['worker']);
    const router = useRouter();

    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [category, setCategory] = useState('');
    const [location, setLocation] = useState('');
    const [basePrice, setBasePrice] = useState('');
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');

    if (loading) return <FullPageSpinner />;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setSaving(true);
        setError('');
        try {
            const service = await servicesService.create({
                title,
                description,
                category,
                location,
                base_price: basePrice ? Number(basePrice) : undefined,
            });
            router.push(`/services/${service.id}`);
        } catch (err) {
            setError(apiErrorMessage(err, 'La publication du service a échoué'));
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50">
            <Nav />
            <div className="max-w-2xl mx-auto px-6 py-12">
                <h1 className="text-3xl font-black mb-8">Publier un service</h1>
                <Card>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <Input
                            label="Titre"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            placeholder="Ex: Nettoyage de climatiseur"
                            required
                        />
                        <div className="grid sm:grid-cols-2 gap-4">
                            <Input
                                label="Catégorie"
                                value={category}
                                onChange={(e) => setCategory(e.target.value)}
                                placeholder="Climatisation"
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
                        <Input
                            label="Prix de base (TND)"
                            type="number"
                            value={basePrice}
                            onChange={(e) => setBasePrice(e.target.value)}
                            placeholder="60"
                        />
                        <Textarea
                            label="Description"
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            className="h-40"
                            placeholder="Décrivez ce que couvre ce service..."
                            required
                        />
                        {error && <Alert>{error}</Alert>}
                        <Button type="submit" size="lg" className="w-full" disabled={saving}>
                            {saving ? 'Publication...' : 'Publier le service'}
                        </Button>
                    </form>
                </Card>
            </div>
        </div>
    );
}
