import axios from 'axios';
import type {
    Booking,
    ChatMessage,
    ClientMe,
    JobApplication,
    JobOffer,
    MyApplication,
    PendingProfile,
    Review,
    Service,
    SubscriptionPlan,
    Transaction,
    User,
    Wallet,
    WorkerMe,
} from './types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

const api = axios.create({
    baseURL: API_URL,
    headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
    if (typeof window !== 'undefined') {
        const token = localStorage.getItem('token');
        if (token) config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401 && typeof window !== 'undefined') {
            localStorage.removeItem('token');
            if (!window.location.pathname.startsWith('/login')) {
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);

export function apiErrorMessage(err: unknown, fallback = 'Une erreur est survenue'): string {
    const detail = axios.isAxiosError(err) ? err.response?.data?.detail : undefined;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg;
    return fallback;
}

export function wsUrl(path: string): string {
    return API_URL.replace(/^http/, 'ws') + path;
}

// === Auth ===

export const authService = {
    login: async (email: string, password: string) => {
        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);
        const response = await api.post('/auth/login', formData, {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        });
        const { access_token } = response.data;
        localStorage.setItem('token', access_token);
        return access_token as string;
    },

    register: async (data: {
        email: string;
        password: string;
        phone: string;
        role: 'worker' | 'client';
        address?: string;
    }) => {
        const response = await api.post('/auth/register/simple', data);
        return response.data;
    },

    getCurrentUser: async (): Promise<User> => (await api.get('/auth/me')).data,
    getWorkerMe: async (): Promise<WorkerMe> => (await api.get('/auth/worker/me')).data,
    getClientMe: async (): Promise<ClientMe> => (await api.get('/auth/client/me')).data,

    updateWorkerProfile: async (data: Partial<WorkerMe>) =>
        (await api.put('/auth/worker/profile', data)).data,
    updateClientProfile: async (data: Partial<ClientMe>) =>
        (await api.put('/auth/client/profile', data)).data,

    logout: () => {
        localStorage.removeItem('token');
        window.location.href = '/';
    },

    isLoggedIn: () => typeof window !== 'undefined' && !!localStorage.getItem('token'),
};

// === Jobs & Applications ===

export const jobsService = {
    search: async (params?: { category?: string; location?: string }): Promise<JobOffer[]> =>
        (await api.get('/jobs', { params })).data,
    mine: async (): Promise<JobOffer[]> => (await api.get('/jobs/my')).data,
    get: async (id: number): Promise<JobOffer> => (await api.get(`/jobs/${id}`)).data,
    myApplications: async (): Promise<MyApplication[]> => (await api.get('/jobs/applications/mine')).data,
    create: async (data: {
        title: string;
        description: string;
        category: string;
        location: string;
        budget_min?: number;
        budget_max?: number;
    }): Promise<JobOffer> => (await api.post('/jobs', data)).data,
    update: async (id: number, data: Partial<JobOffer>): Promise<JobOffer> =>
        (await api.patch(`/jobs/${id}`, data)).data,
    close: async (id: number): Promise<JobOffer> => (await api.post(`/jobs/${id}/close`)).data,
    complete: async (id: number): Promise<JobOffer> => (await api.post(`/jobs/${id}/complete`)).data,
    remove: async (id: number) => (await api.delete(`/jobs/${id}`)).data,

    apply: async (jobId: number, coverMessage?: string): Promise<JobApplication> =>
        (await api.post(`/jobs/${jobId}/apply`, { cover_message: coverMessage })).data,
    listApplications: async (jobId: number): Promise<JobApplication[]> =>
        (await api.get(`/jobs/${jobId}/applications`)).data,
    acceptApplication: async (jobId: number, appId: number) =>
        (await api.post(`/jobs/${jobId}/applications/${appId}/accept`)).data,
    rejectApplication: async (jobId: number, appId: number) =>
        (await api.post(`/jobs/${jobId}/applications/${appId}/reject`)).data,
    withdrawApplication: async (jobId: number, appId: number) =>
        (await api.post(`/jobs/${jobId}/applications/${appId}/withdraw`)).data,
};

// === Services & Bookings ===

export const servicesService = {
    browse: async (params?: {
        category?: string;
        location?: string;
        provider_id?: number;
    }): Promise<Service[]> => (await api.get('/services', { params })).data,
    mine: async (): Promise<Service[]> => (await api.get('/services/my')).data,
    get: async (id: number): Promise<Service> => (await api.get(`/services/${id}`)).data,
    create: async (data: {
        title: string;
        description: string;
        category: string;
        location: string;
        base_price?: number;
    }): Promise<Service> => (await api.post('/services', data)).data,
    update: async (id: number, data: Partial<Service> & { is_active?: boolean }): Promise<Service> =>
        (await api.patch(`/services/${id}`, data)).data,
    remove: async (id: number) => (await api.delete(`/services/${id}`)).data,
};

export const bookingsService = {
    asClient: async (): Promise<Booking[]> => (await api.get('/bookings/my')).data,
    asWorker: async (): Promise<Booking[]> => (await api.get('/bookings/my-requests')).data,
    create: async (data: { service_id: number; scheduled_for: string; note?: string }): Promise<Booking> =>
        (await api.post('/bookings', data)).data,
    confirm: async (id: number): Promise<Booking> => (await api.post(`/bookings/${id}/confirm`)).data,
    cancel: async (id: number): Promise<Booking> => (await api.post(`/bookings/${id}/cancel`)).data,
    complete: async (id: number): Promise<Booking> => (await api.post(`/bookings/${id}/complete`)).data,
};

// === Reviews ===

export const reviewsService = {
    workerReviews: async (workerId: number): Promise<Review[]> =>
        (await api.get(`/reviews/workers/${workerId}`)).data,
    myReceived: async (): Promise<Review[]> => (await api.get('/reviews/me/received')).data,
    myGiven: async (): Promise<Review[]> => (await api.get('/reviews/me/given')).data,
    reviewJobAsClient: async (jobId: number, appId: number, rating: number, comment?: string) =>
        (await api.post(`/reviews/jobs/${jobId}/applications/${appId}/review-as-client`, { rating, comment })).data,
    reviewJobAsWorker: async (jobId: number, appId: number, rating: number, comment?: string) =>
        (await api.post(`/reviews/jobs/${jobId}/applications/${appId}/review-as-worker`, { rating, comment })).data,
    reviewBookingAsClient: async (bookingId: number, rating: number, comment?: string) =>
        (await api.post(`/reviews/bookings/${bookingId}/review-as-client`, { rating, comment })).data,
    reviewBookingAsWorker: async (bookingId: number, rating: number, comment?: string) =>
        (await api.post(`/reviews/bookings/${bookingId}/review-as-worker`, { rating, comment })).data,
};

// === Wallet ===

export const walletService = {
    me: async (): Promise<Wallet> => (await api.get('/wallet/me')).data,
    transactions: async (): Promise<Transaction[]> => (await api.get('/wallet/transactions')).data,
    topUp: async (amount: number, method = 'manual'): Promise<Transaction> =>
        (await api.post('/wallet/top-up', { amount, method })).data,

    // admin
    pendingTransactions: async (): Promise<Transaction[]> =>
        (await api.get('/wallet/admin/transactions/pending')).data,
    approveTransaction: async (id: number) =>
        (await api.post(`/wallet/admin/transactions/${id}/approve`)).data,
    rejectTransaction: async (id: number) =>
        (await api.post(`/wallet/admin/transactions/${id}/reject`)).data,
};

// === Chat ===

export const chatService = {
    history: async (jobId: number): Promise<ChatMessage[]> =>
        (await api.get(`/chat/history/${jobId}`)).data,
    send: async (data: { job_id: number; receiver_id: number; content: string }): Promise<ChatMessage> =>
        (await api.post('/chat', data)).data,
};

// === AI ===

export const aiService = {
    generateBio: async (keywords: string[], category: string, experienceLevel: string): Promise<string> =>
        (await api.post('/ai/generate-bio', { keywords, category, experience_level: experienceLevel })).data.bio,
    generateJobDescription: async (title: string, category: string, keywords: string[]): Promise<string> =>
        (await api.post('/ai/generate-job-description', { title, category, keywords })).data.description,
};

// === Subscriptions ===

export const subscriptionsService = {
    listPlans: async (): Promise<SubscriptionPlan[]> => (await api.get('/subscriptions/plans')).data,
    purchase: async (planId: number) => (await api.post(`/subscriptions/purchase/${planId}`)).data,
    boostJob: async (jobId: number, durationDays = 7) =>
        (await api.post('/subscriptions/boost-job', { job_id: jobId, duration_days: durationDays })).data,
};

// === Admin ===

export const adminService = {
    pendingWorkers: async (): Promise<PendingProfile[]> => (await api.get('/admin/workers/pending')).data,
    pendingClients: async (): Promise<PendingProfile[]> => (await api.get('/admin/clients/pending')).data,
    verifyWorker: async (userId: number) => (await api.post(`/admin/workers/${userId}/verify`)).data,
    rejectWorker: async (userId: number, reason: string) =>
        (await api.post(`/admin/workers/${userId}/reject`, { rejection_reason: reason })).data,
    verifyClient: async (userId: number) => (await api.post(`/admin/clients/${userId}/verify`)).data,
    rejectClient: async (userId: number, reason: string) =>
        (await api.post(`/admin/clients/${userId}/reject`, { rejection_reason: reason })).data,
};

export default api;
