import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
    size?: 'sm' | 'md' | 'lg';
    children: React.ReactNode;
}

export function Button({
    variant = 'primary',
    size = 'md',
    className = '',
    children,
    ...props
}: ButtonProps) {
    const baseStyles = 'font-bold rounded-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed';

    const variants = {
        primary: 'bg-gradient-to-r from-[#DC143C] to-[#A01028] text-white hover:shadow-lg hover:shadow-red-500/30',
        secondary: 'bg-gradient-to-r from-[#3B82F6] to-[#2563EB] text-white hover:shadow-lg hover:shadow-blue-500/30',
        outline: 'border-2 border-[#DC143C] text-[#DC143C] hover:bg-[#DC143C] hover:text-white',
        ghost: 'text-gray-700 hover:bg-gray-100',
    };

    const sizes = {
        sm: 'px-4 py-2 text-sm',
        md: 'px-6 py-3 text-base',
        lg: 'px-8 py-4 text-lg',
    };

    return (
        <button
            className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
            {...props}
        >
            {children}
        </button>
    );
}

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
    label?: string;
    error?: string;
}

export function Input({ label, error, className = '', ...props }: InputProps) {
    return (
        <div className="w-full">
            {label && (
                <label className="block text-sm font-bold text-gray-700 mb-2">
                    {label}
                </label>
            )}
            <input
                className={`w-full px-4 py-3 rounded-xl border-2 border-gray-200 focus:border-[#DC143C] focus:outline-none transition-colors ${className}`}
                {...props}
            />
            {error && <p className="mt-1 text-sm text-red-500">{error}</p>}
        </div>
    );
}

interface CardProps {
    children: React.ReactNode;
    className?: string;
    hoverable?: boolean;
}

export function Card({ children, className = '', hoverable = false }: CardProps) {
    return (
        <div
            className={`bg-white rounded-2xl shadow-lg p-6 ${hoverable ? 'card-hover' : ''
                } ${className}`}
        >
            {children}
        </div>
    );
}

interface BadgeProps {
    children: React.ReactNode;
    variant?: 'default' | 'success' | 'warning' | 'error';
}

export function Badge({ children, variant = 'default' }: BadgeProps) {
    const variants = {
        default: 'bg-gray-100 text-gray-800',
        success: 'bg-green-100 text-green-800',
        warning: 'bg-yellow-100 text-yellow-800',
        error: 'bg-red-100 text-red-800',
    };

    return (
        <span className={`inline-block px-3 py-1 rounded-full text-xs font-bold ${variants[variant]}`}>
            {children}
        </span>
    );
}
