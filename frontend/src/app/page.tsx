'use client';

import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function Home() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && user) {
      router.push('/dashboard');
    }
  }, [user, loading, router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-blue-50 to-white dark:from-gray-900 dark:to-gray-800">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-b from-blue-50 to-white dark:from-gray-900 dark:to-gray-800">
      <main className="text-center space-y-8 p-8">
        <h1 className="text-6xl font-bold text-blue-600 dark:text-blue-400 mb-4">
          Biz Design
        </h1>
        <h2 className="text-2xl font-semibold text-gray-800 dark:text-gray-200">
          AI-powered Business Framework Learning Platform
        </h2>
        <p className="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
          Transform your business thinking with AI-guided framework learning. Master SWOT analysis, user journey mapping, and more with intelligent guidance.
        </p>
        
        {!user && (
          <div className="space-y-4">
            <div className="space-x-4">
              <Link
                href="/auth/register"
                className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg text-lg transition-colors duration-200"
              >
                Get Started Free
              </Link>
              <Link
                href="/auth/login"
                className="bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-200 font-bold py-3 px-6 rounded-lg text-lg transition-colors duration-200"
              >
                Sign In
              </Link>
            </div>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Start with our free plan. No credit card required.
            </p>
          </div>
        )}
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12 max-w-4xl">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg">
            <div className="text-3xl mb-4">🧠</div>
            <h3 className="text-xl font-semibold mb-2 text-gray-800 dark:text-white">AI-Guided Learning</h3>
            <p className="text-gray-600 dark:text-gray-400">
              Interactive AI conversations help you apply business frameworks to real scenarios.
            </p>
          </div>
          
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg">
            <div className="text-3xl mb-4">📊</div>
            <h3 className="text-xl font-semibold mb-2 text-gray-800 dark:text-white">Visual Outputs</h3>
            <p className="text-gray-600 dark:text-gray-400">
              Generate professional business analysis documents and visualizations.
            </p>
          </div>
          
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg">
            <div className="text-3xl mb-4">🎯</div>
            <h3 className="text-xl font-semibold mb-2 text-gray-800 dark:text-white">Practical Focus</h3>
            <p className="text-gray-600 dark:text-gray-400">
              Move beyond theory to create actionable business insights and strategies.
            </p>
          </div>
        </div>
      </main>
      
      <footer className="absolute bottom-4 text-sm text-gray-500">
        Biz Design v2.0.0 - Module 2: Authentication Complete
      </footer>
    </div>
  );
}
