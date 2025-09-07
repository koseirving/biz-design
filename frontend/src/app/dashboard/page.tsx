'use client';

import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function DashboardPage() {
  const { user, loading, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.push('/auth/login');
    }
  }, [user, loading, router]);

  const handleLogout = async () => {
    await logout();
    router.push('/');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white dark:from-gray-900 dark:to-gray-800 flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white dark:from-gray-900 dark:to-gray-800">
      <nav className="bg-white dark:bg-gray-800 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                Biz Design
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-gray-700 dark:text-gray-300">
                {user.email}
              </span>
              <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full text-xs font-semibold uppercase">
                {user.subscription_tier}
              </span>
              <button
                onClick={handleLogout}
                className="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white dark:bg-gray-800 shadow-lg rounded-lg p-6 mb-8">
          <h2 className="text-3xl font-bold text-gray-800 dark:text-white mb-4">
            Welcome to your Dashboard!
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Start your AI-powered business framework learning journey.
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="bg-blue-50 dark:bg-blue-900 p-6 rounded-lg">
              <h3 className="text-xl font-semibold text-blue-800 dark:text-blue-200 mb-2">
                SWOT Analysis
              </h3>
              <p className="text-blue-600 dark:text-blue-300 mb-4">
                Analyze your strengths, weaknesses, opportunities, and threats with AI guidance.
              </p>
              <a href="/frameworks" className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded inline-block text-center">
                Start Analysis
              </a>
            </div>
            
            <div className="bg-green-50 dark:bg-green-900 p-6 rounded-lg">
              <h3 className="text-xl font-semibold text-green-800 dark:text-green-200 mb-2">
                User Journey Map
              </h3>
              <p className="text-green-600 dark:text-green-300 mb-4">
                Map your customer's journey with AI-powered insights.
              </p>
              <a href="/frameworks" className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded inline-block text-center">
                Create Journey
              </a>
            </div>
            
            <div className="bg-purple-50 dark:bg-purple-900 p-6 rounded-lg">
              <h3 className="text-xl font-semibold text-purple-800 dark:text-purple-200 mb-2">
                Business Model Canvas
              </h3>
              <p className="text-purple-600 dark:text-purple-300 mb-4">
                Design and validate your business model with AI assistance.
              </p>
              <button className="bg-purple-500 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded">
                Coming Soon
              </button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="bg-white dark:bg-gray-800 shadow-lg rounded-lg p-6">
            <h3 className="text-xl font-semibold text-gray-800 dark:text-white mb-4">
              Your Progress
            </h3>
            <div className="space-y-4">
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Frameworks Completed</span>
                <span className="font-semibold">0</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">AI Interactions</span>
                <span className="font-semibold">0</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Points Earned</span>
                <span className="font-semibold">0</span>
              </div>
            </div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 shadow-lg rounded-lg p-6">
            <h3 className="text-xl font-semibold text-gray-800 dark:text-white mb-4">
              Recent Activity
            </h3>
            <div className="text-center text-gray-500 dark:text-gray-400 py-8">
              No activity yet. Start with your first framework!
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}