'use client';

import { createContext, useCallback, useContext, useEffect, useState, ReactNode } from 'react';
import { authService } from '@/lib/api';
import type { ClientMe, User, WorkerMe } from '@/lib/types';

interface AuthContextValue {
    user: User | null;
    workerProfile: WorkerMe | null;
    clientProfile: ClientMe | null;
    loading: boolean;
    refresh: () => Promise<void>;
    logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [workerProfile, setWorkerProfile] = useState<WorkerMe | null>(null);
    const [clientProfile, setClientProfile] = useState<ClientMe | null>(null);
    const [loading, setLoading] = useState(true);

    const refresh = useCallback(async () => {
        if (!authService.isLoggedIn()) {
            setUser(null);
            setWorkerProfile(null);
            setClientProfile(null);
            setLoading(false);
            return;
        }
        setLoading(true);
        try {
            const me = await authService.getCurrentUser();
            setUser(me);
            if (me.role === 'worker') {
                setWorkerProfile(await authService.getWorkerMe());
            } else if (me.role === 'client') {
                setClientProfile(await authService.getClientMe());
            }
        } catch {
            setUser(null);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        refresh();
    }, [refresh]);

    return (
        <AuthContext.Provider
            value={{ user, workerProfile, clientProfile, loading, refresh, logout: authService.logout }}
        >
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error('useAuth must be used within AuthProvider');
    return ctx;
}
