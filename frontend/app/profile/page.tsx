'use client';

import { useEffect, useState } from 'react';
import { Nav } from '@/components/Nav';
import { Alert, Badge, Button, Card, FullPageSpinner, Input, Textarea } from '@/components/ui';
import { useAuth } from '@/contexts/AuthContext';
import { useRequireAuth } from '@/lib/hooks';
import { aiService, apiErrorMessage, authService } from '@/lib/api';

export default function ProfilePage() {
    const { loading } = useRequireAuth();
    const { user, workerProfile, clientProfile, refresh } = useAuth();

    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    // Worker fields
    const [bio, setBio] = useState('');
    const [categories, setCategories] = useState('');
    const [hourlyRate, setHourlyRate] = useState('');
    const [location, setLocation] = useState('');
    const [aiLoading, setAiLoading] = useState(false);

    // Client fields
    const [fullName, setFullName] = useState('');
    const [companyName, setCompanyName] = useState('');
    const [clientBio, setClientBio] = useState('');
    const [clientLocation, setClientLocation] = useState('');

    useEffect(() => {
        if (workerProfile) {
            setBio(workerProfile.bio || '');
            setCategories((workerProfile.categories || []).join(', '));
            setHourlyRate(workerProfile.hourly_rate?.toString() || '');
            setLocation(workerProfile.location || '');
        }
        if (clientProfile) {
            setFullName(clientProfile.full_name || '');
            setCompanyName(clientProfile.company_name || '');
            setClientBio(clientProfile.bio || '');
            setClientLocation(clientProfile.location || '');
        }
    }, [workerProfile, clientProfile]);

    if (loading || !user) return <FullPageSpinner />;

    const handleGenerateBio = async () => {
        setAiLoading(true);
        try {
            const generated = await aiService.generateBio(
                categories.split(',').map((c) => c.trim()).filter(Boolean),
                categories.split(',')[0]?.trim() || 'services',
                'expérimenté'
            );
            setBio(generated);
        } catch (err) {
            setError(apiErrorMessage(err, "La génération IA a échoué"));
        } finally {
            setAiLoading(false);
        }
    };

    const handleSaveWorker = async () => {
        setSaving(true);
        setError('');
        setSuccess('');
        try {
            await authService.updateWorkerProfile({
                bio,
                categories: categories.split(',').map((c) => c.trim()).filter(Boolean),
                hourly_rate: hourlyRate ? Number(hourlyRate) : undefined,
                location,
            });
            await refresh();
            setSuccess('Profil mis à jour');
        } catch (err) {
            setError(apiErrorMessage(err, 'La mise à jour a échoué'));
        } finally {
            setSaving(false);
        }
    };

    const handleSaveClient = async () => {
        setSaving(true);
        setError('');
        setSuccess('');
        try {
            await authService.updateClientProfile({
                full_name: fullName,
                company_name: companyName,
                bio: clientBio,
                location: clientLocation,
            });
            await refresh();
            setSuccess('Profil mis à jour');
        } catch (err) {
            setError(apiErrorMessage(err, 'La mise à jour a échoué'));
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50">
            <Nav />
            <div className="max-w-3xl mx-auto px-6 py-12">
                <div className="flex items-center gap-4 mb-8">
                    <h1 className="text-3xl font-black">Mon profil</h1>
                    <Badge variant="success">{user.role.toUpperCase()}</Badge>
                </div>

                <Card className="space-y-4">
                    <Input label="Email" value={user.email} disabled />
                    <Input label="Téléphone" value={user.phone} disabled />

                    {user.role === 'worker' && (
                        <>
                            <Input
                                label="Localisation"
                                value={location}
                                onChange={(e) => setLocation(e.target.value)}
                                placeholder="Tunis"
                            />
                            <Input
                                label="Catégories (séparées par des virgules)"
                                value={categories}
                                onChange={(e) => setCategories(e.target.value)}
                                placeholder="Plomberie, Électricité"
                            />
                            <Input
                                label="Tarif horaire (TND)"
                                type="number"
                                value={hourlyRate}
                                onChange={(e) => setHourlyRate(e.target.value)}
                                placeholder="25"
                            />
                            <div>
                                <div className="flex items-center justify-between mb-2">
                                    <label className="block text-sm font-bold text-gray-700">Bio</label>
                                    <Button
                                        type="button"
                                        variant="secondary"
                                        size="sm"
                                        onClick={handleGenerateBio}
                                        disabled={aiLoading || !categories}
                                    >
                                        {aiLoading ? '⌛ Génération...' : '🪄 Générer avec IA'}
                                    </Button>
                                </div>
                                <Textarea
                                    value={bio}
                                    onChange={(e) => setBio(e.target.value)}
                                    className="h-32"
                                    placeholder="Décrivez votre expérience et vos compétences..."
                                />
                            </div>
                            {workerProfile?.rating != null && (
                                <p className="text-sm text-gray-500">
                                    Note moyenne : {workerProfile.rating ?? 'Pas encore de note'}
                                </p>
                            )}
                            {error && <Alert>{error}</Alert>}
                            {success && <Alert variant="success">{success}</Alert>}
                            <Button onClick={handleSaveWorker} disabled={saving} className="w-full">
                                {saving ? 'Enregistrement...' : 'Enregistrer'}
                            </Button>
                        </>
                    )}

                    {user.role === 'client' && (
                        <>
                            <Input
                                label="Nom complet"
                                value={fullName}
                                onChange={(e) => setFullName(e.target.value)}
                            />
                            <Input
                                label="Entreprise (optionnel)"
                                value={companyName}
                                onChange={(e) => setCompanyName(e.target.value)}
                            />
                            <Input
                                label="Localisation"
                                value={clientLocation}
                                onChange={(e) => setClientLocation(e.target.value)}
                                placeholder="Tunis"
                            />
                            <Textarea
                                label="Bio"
                                value={clientBio}
                                onChange={(e) => setClientBio(e.target.value)}
                                className="h-24"
                            />
                            {error && <Alert>{error}</Alert>}
                            {success && <Alert variant="success">{success}</Alert>}
                            <Button onClick={handleSaveClient} disabled={saving} className="w-full">
                                {saving ? 'Enregistrement...' : 'Enregistrer'}
                            </Button>
                        </>
                    )}

                    {user.role === 'admin' && (
                        <p className="text-gray-500">Les comptes administrateurs n&apos;ont pas de profil public.</p>
                    )}
                </Card>
            </div>
        </div>
    );
}
