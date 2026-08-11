'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Button, Input, Card } from '@/components/ui';
import { authService } from '@/lib/api';

export default function LoginPage() {
    const router = useRouter();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            await authService.login(email, password);
            router.push('/dashboard');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Login failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-50 to-blue-50 px-4">
            <Card className="max-w-md w-full animate-fade-in">
                <div className="text-center mb-8">
                    <div className="inline-block crimson-gradient p-3 rounded-2xl mb-4">
                        <span className="text-white text-4xl font-black">5</span>
                    </div>
                    <h1 className="text-3xl font-black text-gray-900 mb-2">Bon retour !</h1>
                    <p className="text-gray-600">Connectez-vous à votre compte</p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <Input
                        label="Email"
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="votre@email.com"
                        required
                    />

                    <Input
                        label="Mot de passe"
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="••••••••"
                        required
                    />

                    {error && (
                        <div className="bg-red-50 border border-red-200 rounded-xl p-3 text-red-700 text-sm">
                            {error}
                        </div>
                    )}

                    <Button
                        type="submit"
                        variant="primary"
                        size="lg"
                        className="w-full"
                        disabled={loading}
                    >
                        {loading ? 'Connexion...' : 'Se connecter'}
                    </Button>

                    <div className="text-center pt-4">
                        <p className="text-gray-600 text-sm">
                            Pas encore de compte ?{' '}
                            <Link href="/register" className="text-[#DC143C] font-bold hover:underline">
                                S'inscrire
                            </Link>
                        </p>
                    </div>
                </form>
            </Card>
        </div>
    );
}
