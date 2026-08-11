export enum UserRole {
    CLIENT = 'client',
    WORKER = 'worker',
    ADMIN = 'admin',
}

export interface User {
    id: number;
    email: string;
    phone?: string;
    role: UserRole;
    verified: boolean;
    created_at: string;
}

export interface JobOffer {
    id: number;
    client_id: number;
    title: string;
    description: string;
    category: string;
    location: string;
    budget_min?: number;
    budget_max?: number;
    status: 'open' | 'closed';
    boost_until?: string;
    created_at: string;
    application_count: number;
}

export interface Message {
    id: number;
    sender_id: number;
    receiver_id: number;
    job_id: number;
    content: string;
    created_at: string;
    read: boolean;
}

export interface WalletBalance {
    balance: number;
}

export interface SubscriptionPlan {
    id: number;
    name: string;
    price: number;
    duration_days: number;
    features: string[];
}
