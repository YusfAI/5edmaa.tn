'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import type { UserRole } from './types';

/** Redirects to /login if not authenticated, or /dashboard if role doesn't match. */
export function useRequireAuth(allowedRoles?: UserRole[]) {
    const { user, loading } = useAuth();
    const router = useRouter();

    useEffect(() => {
        if (loading) return;
        if (!user) {
            router.replace('/login');
        } else if (allowedRoles && !allowedRoles.includes(user.role)) {
            router.replace('/dashboard');
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [user, loading]);

    return { user, loading };
}
