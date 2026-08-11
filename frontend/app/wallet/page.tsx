'use client';

import { useEffect, useState } from 'react';
import { Nav } from '@/components/Nav';
import { Alert, Badge, Button, Card, EmptyState, FullPageSpinner, Input } from '@/components/ui';
import { useAuth } from '@/contexts/AuthContext';
import { useRequireAuth } from '@/lib/hooks';
import { apiErrorMessage, walletService } from '@/lib/api';
import type { Transaction, TransactionStatus, Wallet } from '@/lib/types';

const STATUS_VARIANT: Record<TransactionStatus, 'success' | 'warning' | 'error' | 'default'> = {
    completed: 'success',
    pending: 'warning',
    failed: 'error',
    cancelled: 'default',
};

export default function WalletPage() {
    const { loading } = useRequireAuth();
    const { user } = useAuth();
    const [wallet, setWallet] = useState<Wallet | null>(null);
    const [transactions, setTransactions] = useState<Transaction[]>([]);
    const [pending, setPending] = useState<Transaction[]>([]);
    const [amount, setAmount] = useState('');
    const [fetching, setFetching] = useState(true);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState('');
    const [notice, setNotice] = useState('');

    const load = async () => {
        const [w, tx] = await Promise.all([walletService.me(), walletService.transactions()]);
        setWallet(w);
        setTransactions(tx);
        if (user?.role === 'admin') {
            setPending(await walletService.pendingTransactions());
        }
    };

    useEffect(() => {
        if (!loading && user) load().finally(() => setFetching(false));
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [loading, user]);

    if (loading || fetching || !user) return <FullPageSpinner />;

    const handleTopUp = async () => {
        const value = Number(amount);
        if (!value || value <= 0) return;
        setBusy(true);
        setError('');
        setNotice('');
        try {
            await walletService.topUp(value);
            setNotice('Demande de recharge envoyée — en attente de validation par un admin.');
            setAmount('');
            await load();
        } catch (err) {
            setError(apiErrorMessage(err, 'La demande a échoué'));
        } finally {
            setBusy(false);
        }
    };

    const handleTxDecision = async (id: number, action: 'approve' | 'reject') => {
        setBusy(true);
        setError('');
        try {
            if (action === 'approve') await walletService.approveTransaction(id);
            else await walletService.rejectTransaction(id);
            await load();
        } catch (err) {
            setError(apiErrorMessage(err));
        } finally {
            setBusy(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50">
            <Nav />
            <div className="max-w-3xl mx-auto px-6 py-12 space-y-8">
                <h1 className="text-3xl font-black">Portefeuille</h1>

                <Card>
                    <p className="text-gray-500 text-sm mb-1">Solde disponible</p>
                    <p className="text-4xl font-black mb-6">
                        {wallet?.balance} {wallet?.currency}
                    </p>

                    <div className="flex gap-3">
                        <Input
                            type="number"
                            placeholder="Montant (TND)"
                            value={amount}
                            onChange={(e) => setAmount(e.target.value)}
                            className="flex-1"
                        />
                        <Button onClick={handleTopUp} disabled={busy || !amount}>
                            Recharger
                        </Button>
                    </div>
                    <p className="text-xs text-gray-500 mt-2">
                        Les recharges sont validées manuellement par un administrateur (D17 / Flouci / virement).
                    </p>
                    {error && <div className="mt-4"><Alert>{error}</Alert></div>}
                    {notice && <div className="mt-4"><Alert variant="success">{notice}</Alert></div>}
                </Card>

                {user.role === 'admin' && (
                    <Card>
                        <h2 className="text-xl font-black mb-4">Recharges en attente ({pending.length})</h2>
                        {pending.length === 0 ? (
                            <EmptyState>Aucune demande en attente.</EmptyState>
                        ) : (
                            <div className="space-y-3">
                                {pending.map((tx) => (
                                    <div
                                        key={tx.id}
                                        className="flex items-center justify-between border-b border-gray-100 pb-3"
                                    >
                                        <div>
                                            <p className="font-bold">
                                                Utilisateur #{tx.user_id} — {tx.amount} TND
                                            </p>
                                            <p className="text-xs text-gray-500">{tx.description}</p>
                                        </div>
                                        <div className="flex gap-2">
                                            <Button size="sm" onClick={() => handleTxDecision(tx.id, 'approve')} disabled={busy}>
                                                Approuver
                                            </Button>
                                            <Button
                                                size="sm"
                                                variant="outline"
                                                onClick={() => handleTxDecision(tx.id, 'reject')}
                                                disabled={busy}
                                            >
                                                Rejeter
                                            </Button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </Card>
                )}

                <Card>
                    <h2 className="text-xl font-black mb-4">Historique des transactions</h2>
                    {transactions.length === 0 ? (
                        <EmptyState>Aucune transaction pour le moment.</EmptyState>
                    ) : (
                        <div className="space-y-2">
                            {transactions.map((tx) => (
                                <div
                                    key={tx.id}
                                    className="flex items-center justify-between border-b border-gray-100 pb-2 last:border-0"
                                >
                                    <div>
                                        <p className="font-bold text-sm">{tx.description || tx.type}</p>
                                        <p className="text-xs text-gray-500">
                                            {new Date(tx.created_at).toLocaleString('fr-TN')}
                                        </p>
                                    </div>
                                    <div className="text-right">
                                        <p className="font-bold">{tx.amount} TND</p>
                                        <Badge variant={STATUS_VARIANT[tx.status]}>{tx.status}</Badge>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </Card>
            </div>
        </div>
    );
}
