'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Button, Input, Card, Alert } from '@/components/ui';
import { apiErrorMessage, authService } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';

export default function RegisterPage() {
    const router = useRouter();
    const { refresh } = useAuth();
    const [formData, setFormData] = useState({
        email: '',
        password: '',
        confirmPassword: '',
        phone: '',
        address: '',
        role: 'client' as 'client' | 'worker',
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        if (formData.password !== formData.confirmPassword) {
            setError('Les mots de passe ne correspondent pas');
            setLoading(false);
            return;
        }

        try {
            await authService.register({
                email: formData.email,
                password: formData.password,
                phone: formData.phone,
                role: formData.role,
                address: formData.address || 'Tunis',
            });

            // Auto-login after registration
            await authService.login(formData.email, formData.password);
            await refresh();
            router.push('/dashboard');
        } catch (err) {
            setError(apiErrorMessage(err, "L'inscription a échoué"));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-50 to-blue-50 px-4 py-12">
            <Card className="max-w-md w-full animate-fade-in">
                <div className="text-center mb-8">
                    <div className="inline-block tunisian-gradient p-3 rounded-2xl mb-4">
                        <span className="text-white text-4xl font-black">5</span>
                    </div>
                    <h1 className="text-3xl font-black text-gray-900 mb-2">Rejoignez-nous !</h1>
                    <p className="text-gray-600">Créez votre compte 5edma.tn</p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <Input
                        label="Email"
                        type="email"
                        value={formData.email}
                        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                        placeholder="votre@email.com"
                        required
                    />

                    <Input
                        label="Téléphone"
                        type="tel"
                        value={formData.phone}
                        onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                        placeholder="55 123 456"
                        required
                    />

                    <div>
                        <label className="block text-sm font-bold text-gray-700 mb-2">
                            Vous êtes...
                        </label>
                        <div className="grid grid-cols-2 gap-3">
                            {(['client', 'worker'] as const).map((role) => (
                                <button
                                    key={role}
                                    type="button"
                                    onClick={() => setFormData({ ...formData, role })}
                                    className={`p-3 rounded-xl border-2 font-bold transition-all ${formData.role === role
                                            ? 'border-[#DC143C] bg-red-50 text-[#DC143C]'
                                            : 'border-gray-200 text-gray-600 hover:border-gray-300'
                                        }`}
                                >
                                    {role === 'client' ? '👤 Client' : '🔧 Travailleur'}
                                </button>
                            ))}
                        </div>
                    </div>

                    <Input
                        label="Ville"
                        value={formData.address}
                        onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                        placeholder="Tunis"
                    />

                    <Input
                        label="Mot de passe"
                        type="password"
                        value={formData.password}
                        onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                        placeholder="••••••••"
                        required
                    />

                    <Input
                        label="Confirmer le mot de passe"
                        type="password"
                        value={formData.confirmPassword}
                        onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                        placeholder="••••••••"
                        required
                    />

                    {error && <Alert>{error}</Alert>}

                    <Button
                        type="submit"
                        variant="primary"
                        size="lg"
                        className="w-full"
                        disabled={loading}
                    >
                        {loading ? 'Inscription...' : "S'inscrire"}
                    </Button>

                    <div className="text-center pt-4">
                        <p className="text-gray-600 text-sm">
                            Déjà inscrit ?{' '}
                            <Link href="/login" className="text-[#DC143C] font-bold hover:underline">
                                Se connecter
                            </Link>
                        </p>
                    </div>
                </form>
            </Card>
        </div>
    );
}
