'use client';

import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function CreateCompanyProfilePage() {
  const { user } = useAuth();
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    profile_name: '',
    type: 'own' as 'own' | 'competitor',
    industry: '',
    size: '',
    revenue: '',
    description: '',
    strengths: [''],
    weaknesses: ['']
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    // Clean up empty strengths and weaknesses
    const cleanStrengths = formData.strengths.filter(s => s.trim() !== '');
    const cleanWeaknesses = formData.weaknesses.filter(w => w.trim() !== '');

    const profileData = {
      profile_name: formData.profile_name,
      profile_data: {
        type: formData.type,
        industry: formData.industry || undefined,
        size: formData.size || undefined,
        revenue: formData.revenue || undefined,
        description: formData.description || undefined,
        strengths: cleanStrengths.length > 0 ? cleanStrengths : undefined,
        weaknesses: cleanWeaknesses.length > 0 ? cleanWeaknesses : undefined
      }
    };

    try {
      const response = await fetch('/api/proxy/company-profiles', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(profileData)
      });

      if (response.ok) {
        router.push('/company-profiles');
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to create company profile');
      }
    } catch (error) {
      setError('Error creating company profile');
    } finally {
      setLoading(false);
    }
  };

  const updateStrength = (index: number, value: string) => {
    const newStrengths = [...formData.strengths];
    newStrengths[index] = value;
    setFormData({ ...formData, strengths: newStrengths });
  };

  const addStrength = () => {
    setFormData({ ...formData, strengths: [...formData.strengths, ''] });
  };

  const removeStrength = (index: number) => {
    const newStrengths = formData.strengths.filter((_, i) => i !== index);
    setFormData({ ...formData, strengths: newStrengths });
  };

  const updateWeakness = (index: number, value: string) => {
    const newWeaknesses = [...formData.weaknesses];
    newWeaknesses[index] = value;
    setFormData({ ...formData, weaknesses: newWeaknesses });
  };

  const addWeakness = () => {
    setFormData({ ...formData, weaknesses: [...formData.weaknesses, ''] });
  };

  const removeWeakness = (index: number) => {
    const newWeaknesses = formData.weaknesses.filter((_, i) => i !== index);
    setFormData({ ...formData, weaknesses: newWeaknesses });
  };

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
              <Link href="/dashboard" className="text-gray-600 dark:text-gray-400 hover:text-blue-600">
                Dashboard
              </Link>
              <Link href="/company-profiles" className="text-gray-600 dark:text-gray-400 hover:text-blue-600">
                Company Profiles
              </Link>
              <span className="text-gray-700 dark:text-gray-300">{user?.email}</span>
              <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full text-xs font-semibold uppercase">
                {user?.subscription_tier}
              </span>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Breadcrumb */}
        <div className="mb-6">
          <nav className="text-sm">
            <Link href="/company-profiles" className="text-blue-600 hover:text-blue-800">
              Company Profiles
            </Link>
            <span className="mx-2 text-gray-500">/</span>
            <span className="text-gray-600 dark:text-gray-400">Create Profile</span>
          </nav>
        </div>

        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-800 dark:text-white">Create Company Profile</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Add a new company profile for analysis and strategic planning
          </p>
        </div>

        {error && (
          <div className="bg-red-50 dark:bg-red-900 border border-red-200 dark:border-red-700 text-red-700 dark:text-red-200 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {/* Form */}
        <div className="bg-white dark:bg-gray-800 shadow-lg rounded-lg p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Basic Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-gray-700 dark:text-gray-300 font-bold mb-2">
                  Company Name *
                </label>
                <input
                  type="text"
                  required
                  value={formData.profile_name}
                  onChange={(e) => setFormData({ ...formData, profile_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter company name"
                />
              </div>

              <div>
                <label className="block text-gray-700 dark:text-gray-300 font-bold mb-2">
                  Profile Type *
                </label>
                <select
                  value={formData.type}
                  onChange={(e) => setFormData({ ...formData, type: e.target.value as 'own' | 'competitor' })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="own">Own Company</option>
                  <option value="competitor">Competitor</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <label className="block text-gray-700 dark:text-gray-300 font-bold mb-2">
                  Industry
                </label>
                <input
                  type="text"
                  value={formData.industry}
                  onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., Technology, Healthcare"
                />
              </div>

              <div>
                <label className="block text-gray-700 dark:text-gray-300 font-bold mb-2">
                  Company Size
                </label>
                <select
                  value={formData.size}
                  onChange={(e) => setFormData({ ...formData, size: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select size</option>
                  <option value="startup">Startup (1-10)</option>
                  <option value="small">Small (11-50)</option>
                  <option value="medium">Medium (51-250)</option>
                  <option value="large">Large (251-1000)</option>
                  <option value="enterprise">Enterprise (1000+)</option>
                </select>
              </div>

              <div>
                <label className="block text-gray-700 dark:text-gray-300 font-bold mb-2">
                  Annual Revenue
                </label>
                <input
                  type="text"
                  value={formData.revenue}
                  onChange={(e) => setFormData({ ...formData, revenue: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., $1M, $50M, $1B"
                />
              </div>
            </div>

            {/* Description */}
            <div>
              <label className="block text-gray-700 dark:text-gray-300 font-bold mb-2">
                Description
              </label>
              <textarea
                rows={4}
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Describe the company's business model, key products/services, and market position"
              />
            </div>

            {/* Strengths */}
            <div>
              <div className="flex justify-between items-center mb-3">
                <label className="block text-gray-700 dark:text-gray-300 font-bold">
                  Key Strengths
                </label>
                <button
                  type="button"
                  onClick={addStrength}
                  className="text-blue-600 hover:text-blue-800 dark:text-blue-400 text-sm"
                >
                  + Add Strength
                </button>
              </div>
              <div className="space-y-2">
                {formData.strengths.map((strength, index) => (
                  <div key={index} className="flex gap-2">
                    <input
                      type="text"
                      value={strength}
                      onChange={(e) => updateStrength(index, e.target.value)}
                      className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="e.g., Strong brand recognition, Advanced technology"
                    />
                    {formData.strengths.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeStrength(index)}
                        className="text-red-600 hover:text-red-800 px-2"
                      >
                        ×
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Weaknesses */}
            <div>
              <div className="flex justify-between items-center mb-3">
                <label className="block text-gray-700 dark:text-gray-300 font-bold">
                  Key Weaknesses
                </label>
                <button
                  type="button"
                  onClick={addWeakness}
                  className="text-blue-600 hover:text-blue-800 dark:text-blue-400 text-sm"
                >
                  + Add Weakness
                </button>
              </div>
              <div className="space-y-2">
                {formData.weaknesses.map((weakness, index) => (
                  <div key={index} className="flex gap-2">
                    <input
                      type="text"
                      value={weakness}
                      onChange={(e) => updateWeakness(index, e.target.value)}
                      className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="e.g., Limited market share, High operational costs"
                    />
                    {formData.weaknesses.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeWeakness(index)}
                        className="text-red-600 hover:text-red-800 px-2"
                      >
                        ×
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Submit Buttons */}
            <div className="flex justify-end space-x-4 pt-6">
              <Link
                href="/company-profiles"
                className="bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-6 rounded focus:outline-none focus:shadow-outline"
              >
                Cancel
              </Link>
              <button
                type="submit"
                disabled={loading}
                className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-6 rounded focus:outline-none focus:shadow-outline disabled:opacity-50"
              >
                {loading ? 'Creating...' : 'Create Profile'}
              </button>
            </div>
          </form>
        </div>
      </main>
    </div>
  );
}