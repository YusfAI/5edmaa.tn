export type UserRole = 'worker' | 'client' | 'admin';
export type VerificationStatus = 'pending' | 'approved' | 'rejected';

export interface User {
    id: number;
    email: string;
    phone: string;
    role: UserRole;
}

export interface WorkerMe {
    id: number;
    email: string;
    phone: string;
    role: 'worker';
    bio?: string | null;
    categories?: string[] | null;
    hourly_rate?: number | null;
    location?: string | null;
    availability?: Record<string, unknown> | null;
    portfolio_urls?: string[] | null;
    verified: boolean;
    status: VerificationStatus;
    rejection_reason?: string | null;
    premium_until?: string | null;
    rating?: number | null;
}

export interface ClientMe {
    id: number;
    email: string;
    phone: string;
    role: 'client';
    full_name?: string | null;
    company_name?: string | null;
    bio?: string | null;
    location?: string | null;
    verified: boolean;
    status: VerificationStatus;
    rejection_reason?: string | null;
}

export interface PendingProfile {
    user_id: number;
    email: string;
    phone: string;
    location?: string | null;
    verified: boolean;
    status: VerificationStatus;
    rejection_reason?: string | null;
    // worker-only
    bio?: string | null;
    categories?: string[] | null;
    // client-only
    full_name?: string | null;
    company_name?: string | null;
}

// === Jobs & Applications ===

export type JobStatus = 'open' | 'closed';
export type ApplicationStatus = 'pending' | 'accepted' | 'rejected';

export interface JobOffer {
    id: number;
    title: string;
    description: string;
    category: string;
    location: string;
    budget_min?: number | null;
    budget_max?: number | null;
    status: JobStatus;
    boost_until?: string | null;
    client_id: number;
    created_at: string;
    application_count: number;
}

export interface JobApplication {
    id: number;
    job_id: number;
    worker_id: number;
    cover_message?: string | null;
    status: ApplicationStatus;
    created_at: string;
}

export interface MyApplication extends JobApplication {
    job_title: string;
    job_status: JobStatus;
}

// === Services & Bookings ===

export interface Service {
    id: number;
    provider_id: number;
    title: string;
    description: string;
    category: string;
    location: string;
    base_price?: number | null;
    is_premium: boolean;
    created_at: string;
}

export type BookingStatus = 'pending' | 'confirmed' | 'cancelled' | 'completed';

export interface Booking {
    id: number;
    service_id: number;
    customer_id: number;
    provider_id: number;
    scheduled_for: string;
    status: BookingStatus;
    note?: string | null;
    created_at: string;
}

// === Reviews ===

export interface Review {
    id: number;
    booking_id?: number | null;
    job_application_id?: number | null;
    reviewer_id: number;
    reviewee_id: number;
    rating: number;
    comment?: string | null;
    created_at: string;
}

// === Wallet ===

export type TransactionType = 'topup' | 'payment' | 'withdrawal' | 'refund' | 'fee' | 'release';
export type TransactionStatus = 'pending' | 'completed' | 'failed' | 'cancelled';

export interface Wallet {
    user_id: number;
    balance: number;
    currency: string;
    updated_at: string;
}

export interface Transaction {
    id: number;
    user_id: number;
    type: TransactionType;
    amount: number;
    status: TransactionStatus;
    reference?: string | null;
    description?: string | null;
    created_at: string;
}

// === Chat ===

export interface ChatMessage {
    id: number;
    job_id: number;
    sender_id: number;
    receiver_id: number;
    content: string;
    attachments?: string[] | null;
    created_at: string;
    read_at?: string | null;
}

// === Subscriptions ===

export interface SubscriptionPlan {
    id: number;
    name: string;
    description?: string | null;
    price: number;
    duration_days: number;
    features?: Record<string, unknown> | null;
}
