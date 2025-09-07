'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import RegisterForm from '@/components/auth/RegisterForm';
import { useAuth } from '@/contexts/AuthContext';

export default function RegisterPage() {
  const router = useRouter();
  const { register, loading } = useAuth();
  const [error, setError] = useState<string>('');

  const handleRegister = async (email: string, password: string) => {
    try {
      setError('');
      await register(email, password);
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Registration failed');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white dark:from-gray-900 dark:to-gray-800 flex items-center justify-center px-4 py-12 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-blue-600 dark:text-blue-400 mb-2">
            Biz Design
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            AI-powered Business Framework Learning
          </p>
        </div>
        
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}
        
        <RegisterForm onSubmit={handleRegister} loading={loading} />
      </div>
    </div>
  );
}