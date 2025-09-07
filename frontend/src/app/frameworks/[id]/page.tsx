'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useFramework } from '@/contexts/FrameworkContext';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

interface FrameworkContent {
  id: string;
  name: string;
  description: string;
  category: string;
  difficulty_level: string;
  estimated_duration: number;
  is_premium: boolean;
  micro_content: {
    overview: string;
    components: any;
    use_cases: string[];
    steps: string[];
  };
  access_level: 'full' | 'preview';
}

export default function FrameworkDetailPage({ params }: { params: { id: string } }) {
  const { user, loading: authLoading } = useAuth();
  const { loading } = useFramework();
  const router = useRouter();
  const [framework, setFramework] = useState<FrameworkContent | null>(null);
  const [contentLoading, setContentLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/auth/login');
      return;
    }

    if (user && params.id) {
      fetchFrameworkContent();
    }
  }, [user, authLoading, params.id]);

  const fetchFrameworkContent = async () => {
    setContentLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`/api/proxy/frameworks/${params.id}/content`);
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to fetch framework content');
      }

      const data = await response.json();
      setFramework(data);
    } catch (error: any) {
      console.error('Error fetching framework content:', error);
      setError(error.message);
    } finally {
      setContentLoading(false);
    }
  };

  const getDifficultyColor = (level: string) => {
    switch (level?.toLowerCase()) {
      case 'beginner':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'intermediate':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'advanced':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  const getCategoryColor = (category: string) => {
    const colors = {
      strategy: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
      design: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
      analysis: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
      planning: 'bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-200',
    };
    return colors[category as keyof typeof colors] || 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
  };

  if (authLoading || loading || contentLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white dark:from-gray-900 dark:to-gray-800 flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white dark:from-gray-900 dark:to-gray-800 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-red-600 mb-4">Error</h2>
          <p className="text-gray-600 dark:text-gray-400 mb-4">{error}</p>
          <Link href="/frameworks" className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
            Back to Frameworks
          </Link>
        </div>
      </div>
    );
  }

  if (!framework) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white dark:from-gray-900 dark:to-gray-800 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-600 dark:text-gray-400 mb-4">Framework not found</h2>
          <Link href="/frameworks" className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
            Back to Frameworks
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white dark:from-gray-900 dark:to-gray-800">
      {/* Navigation */}
      <nav className="bg-white dark:bg-gray-800 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link href="/dashboard" className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                Biz Design
              </Link>
            </div>
            <div className="flex items-center space-x-4">
              <Link href="/frameworks" className="text-gray-600 dark:text-gray-400 hover:text-blue-600">
                Frameworks
              </Link>
              <span className="text-gray-700 dark:text-gray-300">{user.email}</span>
              <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full text-xs font-semibold uppercase">
                {user.subscription_tier}
              </span>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Breadcrumb */}
        <div className="mb-6">
          <nav className="text-sm">
            <Link href="/frameworks" className="text-blue-600 hover:text-blue-800">
              Frameworks
            </Link>
            <span className="mx-2 text-gray-500">/</span>
            <span className="text-gray-600 dark:text-gray-400">{framework.name}</span>
          </nav>
        </div>

        {/* Header */}
        <div className="bg-white dark:bg-gray-800 shadow-lg rounded-lg p-8 mb-8">
          <div className="flex justify-between items-start mb-6">
            <div>
              <div className="flex items-center gap-3 mb-4">
                <h1 className="text-3xl font-bold text-gray-800 dark:text-white">
                  {framework.name}
                </h1>
                {framework.is_premium && (
                  <span className="px-3 py-1 bg-yellow-100 text-yellow-800 text-sm font-semibold rounded-full">
                    Premium
                  </span>
                )}
              </div>
              
              <p className="text-gray-600 dark:text-gray-400 text-lg mb-4">
                {framework.description}
              </p>
              
              {/* Tags */}
              <div className="flex flex-wrap gap-3 mb-6">
                <span className={`px-3 py-1 text-sm font-semibold rounded-full ${getCategoryColor(framework.category)}`}>
                  {framework.category.charAt(0).toUpperCase() + framework.category.slice(1)}
                </span>
                <span className={`px-3 py-1 text-sm font-semibold rounded-full ${getDifficultyColor(framework.difficulty_level)}`}>
                  {framework.difficulty_level.charAt(0).toUpperCase() + framework.difficulty_level.slice(1)}
                </span>
                <span className="px-3 py-1 bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200 text-sm font-semibold rounded-full flex items-center">
                  <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  {framework.estimated_duration} min
                </span>
              </div>
            </div>

            {/* Action Button */}
            <div className="flex-shrink-0">
              {framework.is_premium && user.subscription_tier !== 'premium' ? (
                <div className="text-center">
                  <button
                    disabled
                    className="bg-gray-300 text-gray-500 font-bold py-3 px-6 rounded cursor-not-allowed mb-2"
                  >
                    Premium Required
                  </button>
                  <p className="text-sm text-gray-500">Upgrade to access</p>
                </div>
              ) : (
                <Link
                  href={`/frameworks/${framework.id}/start`}
                  className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded focus:outline-none focus:shadow-outline inline-block text-center"
                >
                  Start Framework
                </Link>
              )}
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-8">
            {/* Overview */}
            {framework.micro_content?.overview && (
              <div className="bg-white dark:bg-gray-800 shadow-lg rounded-lg p-6">
                <h2 className="text-xl font-semibold text-gray-800 dark:text-white mb-4">
                  Overview
                </h2>
                <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                  {framework.micro_content.overview}
                </p>
              </div>
            )}

            {/* Components */}
            {framework.micro_content?.components && framework.access_level === 'full' && (
              <div className="bg-white dark:bg-gray-800 shadow-lg rounded-lg p-6">
                <h2 className="text-xl font-semibold text-gray-800 dark:text-white mb-6">
                  Key Components
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {Object.entries(framework.micro_content.components).map(([key, component]: [string, any]) => (
                    <div key={key} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                      <h3 className="font-semibold text-gray-800 dark:text-white mb-2">
                        {component.title || key.charAt(0).toUpperCase() + key.slice(1)}
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                        {component.description}
                      </p>
                      {component.examples && (
                        <div>
                          <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Examples:</p>
                          <ul className="text-xs text-gray-600 dark:text-gray-300 list-disc list-inside">
                            {component.examples.slice(0, 3).map((example: string, idx: number) => (
                              <li key={idx}>{example}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Steps */}
            {framework.micro_content?.steps && framework.access_level === 'full' && (
              <div className="bg-white dark:bg-gray-800 shadow-lg rounded-lg p-6">
                <h2 className="text-xl font-semibold text-gray-800 dark:text-white mb-6">
                  Implementation Steps
                </h2>
                <div className="space-y-4">
                  {framework.micro_content.steps.map((step: string, index: number) => (
                    <div key={index} className="flex items-start">
                      <div className="flex-shrink-0 w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm font-semibold mr-4">
                        {index + 1}
                      </div>
                      <p className="text-gray-600 dark:text-gray-400 pt-1">{step}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Preview Message for Free Users */}
            {framework.access_level === 'preview' && (
              <div className="bg-yellow-50 dark:bg-yellow-900 border border-yellow-200 dark:border-yellow-700 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-yellow-800 dark:text-yellow-200 mb-2">
                  Premium Content Preview
                </h3>
                <p className="text-yellow-700 dark:text-yellow-300 mb-4">
                  This is a preview of premium content. Upgrade to access the full framework including:
                </p>
                <ul className="list-disc list-inside text-yellow-700 dark:text-yellow-300 mb-4">
                  <li>Detailed component breakdowns</li>
                  <li>Step-by-step implementation guide</li>
                  <li>AI-powered interactive assistance</li>
                  <li>Progress tracking and analytics</li>
                </ul>
                <button className="bg-yellow-500 hover:bg-yellow-600 text-white font-bold py-2 px-4 rounded">
                  Upgrade to Premium
                </button>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Use Cases */}
            {framework.micro_content?.use_cases && (
              <div className="bg-white dark:bg-gray-800 shadow-lg rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">
                  Use Cases
                </h3>
                <ul className="space-y-2">
                  {framework.micro_content.use_cases.map((useCase: string, index: number) => (
                    <li key={index} className="text-gray-600 dark:text-gray-400 flex items-center">
                      <svg className="w-4 h-4 text-green-500 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      {useCase}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Quick Info */}
            <div className="bg-white dark:bg-gray-800 shadow-lg rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">
                Quick Info
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Duration:</span>
                  <span className="font-medium">{framework.estimated_duration} min</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Level:</span>
                  <span className="font-medium">{framework.difficulty_level}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Category:</span>
                  <span className="font-medium">{framework.category}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Access:</span>
                  <span className={`font-medium ${framework.is_premium ? 'text-yellow-600' : 'text-green-600'}`}>
                    {framework.is_premium ? 'Premium' : 'Free'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}