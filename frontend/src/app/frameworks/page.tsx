'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useFramework } from '@/contexts/FrameworkContext';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

interface Framework {
  id: string;
  name: string;
  description: string;
  category: string;
  difficulty_level: string;
  estimated_duration: number;
  is_premium: boolean;
  micro_content: any;
  created_at: string;
}

export default function FrameworksPage() {
  const { user, loading: authLoading } = useAuth();
  const { 
    frameworks, 
    loading, 
    categories, 
    difficultyLevels,
    searchQuery,
    selectedCategory,
    selectedDifficulty,
    fetchFrameworks, 
    fetchCategories,
    setSearchQuery,
    setSelectedCategory,
    setSelectedDifficulty,
    clearFilters
  } = useFramework();
  const router = useRouter();
  const [searchInput, setSearchInput] = useState('');

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/auth/login');
      return;
    }

    if (user) {
      fetchCategories();
      fetchFrameworks();
    }
  }, [user, authLoading]);

  useEffect(() => {
    if (user) {
      fetchFrameworks();
    }
  }, [selectedCategory, selectedDifficulty, searchQuery]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearchQuery(searchInput);
  };

  const handleClearFilters = () => {
    setSearchInput('');
    clearFilters();
  };

  const getDifficultyColor = (level: string) => {
    switch (level.toLowerCase()) {
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

  if (authLoading || loading) {
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
              <span className="text-gray-700 dark:text-gray-300">{user.email}</span>
              <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full text-xs font-semibold uppercase">
                {user.subscription_tier}
              </span>
              <Link
                href="/dashboard"
                className="bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
              >
                Dashboard
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-800 dark:text-white mb-2">
            Business Frameworks
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Discover and master essential business frameworks with AI guidance
          </p>
        </div>

        {/* Search and Filters */}
        <div className="bg-white dark:bg-gray-800 shadow-lg rounded-lg p-6 mb-8">
          <div className="flex flex-col md:flex-row gap-4 items-center">
            {/* Search */}
            <form onSubmit={handleSearch} className="flex-1">
              <div className="relative">
                <input
                  type="text"
                  placeholder="Search frameworks..."
                  value={searchInput}
                  onChange={(e) => setSearchInput(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                />
                <button
                  type="submit"
                  className="absolute right-2 top-2 text-gray-500 hover:text-blue-500"
                >
                  🔍
                </button>
              </div>
            </form>

            {/* Category Filter */}
            <select
              value={selectedCategory || ''}
              onChange={(e) => setSelectedCategory(e.target.value || null)}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
            >
              <option value="">All Categories</option>
              {categories.map(category => (
                <option key={category} value={category}>
                  {category.charAt(0).toUpperCase() + category.slice(1)}
                </option>
              ))}
            </select>

            {/* Difficulty Filter */}
            <select
              value={selectedDifficulty || ''}
              onChange={(e) => setSelectedDifficulty(e.target.value || null)}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
            >
              <option value="">All Levels</option>
              {difficultyLevels.map(level => (
                <option key={level} value={level}>
                  {level.charAt(0).toUpperCase() + level.slice(1)}
                </option>
              ))}
            </select>

            {/* Clear Filters */}
            <button
              onClick={handleClearFilters}
              className="px-4 py-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            >
              Clear Filters
            </button>
          </div>
        </div>

        {/* Framework Grid */}
        {frameworks.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500 dark:text-gray-400 text-lg">
              No frameworks found. Try adjusting your search criteria.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {frameworks.map((framework: Framework) => (
              <div
                key={framework.id}
                className="bg-white dark:bg-gray-800 shadow-lg rounded-lg overflow-hidden hover:shadow-xl transition-shadow"
              >
                <div className="p-6">
                  {/* Header */}
                  <div className="flex items-start justify-between mb-4">
                    <h3 className="text-xl font-semibold text-gray-800 dark:text-white">
                      {framework.name}
                    </h3>
                    {framework.is_premium && (
                      <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs font-semibold rounded-full">
                        Premium
                      </span>
                    )}
                  </div>

                  {/* Description */}
                  <p className="text-gray-600 dark:text-gray-400 mb-4 line-clamp-3">
                    {framework.description}
                  </p>

                  {/* Tags */}
                  <div className="flex flex-wrap gap-2 mb-4">
                    <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getCategoryColor(framework.category)}`}>
                      {framework.category.charAt(0).toUpperCase() + framework.category.slice(1)}
                    </span>
                    <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getDifficultyColor(framework.difficulty_level)}`}>
                      {framework.difficulty_level.charAt(0).toUpperCase() + framework.difficulty_level.slice(1)}
                    </span>
                  </div>

                  {/* Duration */}
                  <div className="flex items-center text-sm text-gray-500 dark:text-gray-400 mb-4">
                    <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {framework.estimated_duration} minutes
                  </div>

                  {/* Action Button */}
                  <div className="flex justify-between items-center">
                    <Link
                      href={`/frameworks/${framework.id}`}
                      className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline flex-1 text-center mr-2"
                    >
                      Learn More
                    </Link>
                    {framework.is_premium && user.subscription_tier !== 'premium' ? (
                      <button
                        disabled
                        className="bg-gray-300 text-gray-500 font-bold py-2 px-4 rounded cursor-not-allowed"
                      >
                        Premium
                      </button>
                    ) : (
                      <Link
                        href={`/frameworks/${framework.id}/start`}
                        className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
                      >
                        Start
                      </Link>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}