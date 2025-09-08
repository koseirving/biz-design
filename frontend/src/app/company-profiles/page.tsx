'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

interface CompanyProfile {
  id: string;
  profile_name: string;
  profile_data: {
    type: 'own' | 'competitor';
    industry?: string;
    size?: string;
    revenue?: string;
    description?: string;
    strengths?: string[];
    weaknesses?: string[];
  };
  created_at: string;
  updated_at: string;
}

export default function CompanyProfilesPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [profiles, setProfiles] = useState<CompanyProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/auth/login');
      return;
    }

    if (user) {
      fetchProfiles();
    }
  }, [user, authLoading]);

  const fetchProfiles = async () => {
    try {
      const response = await fetch('/api/proxy/company-profiles');
      if (response.ok) {
        const data = await response.json();
        setProfiles(data.profiles || []);
      } else {
        setError('Failed to fetch company profiles');
      }
    } catch (error) {
      setError('Error fetching company profiles');
    } finally {
      setLoading(false);
    }
  };

  const deleteProfile = async (profileId: string) => {
    if (!confirm('Are you sure you want to delete this profile?')) return;

    try {
      const response = await fetch(`/api/proxy/company-profiles/${profileId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        setProfiles(profiles.filter(p => p.id !== profileId));
      } else {
        setError('Failed to delete profile');
      }
    } catch (error) {
      setError('Error deleting profile');
    }
  };

  const getProfileTypeColor = (type: string) => {
    switch (type) {
      case 'own':
        return 'bg-blue-100 text-blue-800
      case 'competitor':
        return 'bg-red-100 text-red-800
      default:
        return 'bg-gray-100 text-gray-800
    }
  };

  if (authLoading || loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      {/* Navigation */}
      <nav className="bg-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link href="/dashboard" className="text-2xl font-bold text-blue-600">
                Biz Design
              </Link>
            </div>
            <div className="flex items-center space-x-4">
              <Link href="/dashboard" className="text-gray-600 hover:text-blue-600">
                ダッシュボード
              </Link>
              <Link href="/frameworks" className="text-gray-600 hover:text-blue-600">
                フレームワーク
              </Link>
              <span className="text-gray-700">{user.email}</span>
              <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-semibold uppercase">
                {user.subscription_tier}
              </span>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-800">企業プロファイル</h1>
            <p className="text-gray-600 mt-2">
              自社と競合他社のプロファイルを管理し、包括的な分析を実施
            </p>
          </div>
          <button
            onClick={() => router.push('/company-profiles/create')}
            className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg focus:outline-none focus:shadow-outline"
          >
            企業プロファイルを追加
          </button>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {/* Profiles Grid */}
        {profiles.length === 0 ? (
          <div className="bg-white shadow-lg rounded-lg p-12 text-center">
            <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H5m0 0v-5a2 2 0 012-2h10a2 2 0 012 2v5" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-gray-800 mb-2">
              まだ企業プロファイルがありません
            </h3>
            <p className="text-gray-600 mb-6">
              最初の企業プロファイルを作成して、ビジネス環境の分析を開始しましょう
            </p>
            <button
              onClick={() => router.push('/company-profiles/create')}
              className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
            >
              最初のプロファイルを作成
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {profiles.map((profile) => (
              <div key={profile.id} className="bg-white shadow-lg rounded-lg p-6">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-800 mb-2">
                      {profile.profile_name}
                    </h3>
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`px-2 py-1 text-xs rounded-full ${getProfileTypeColor(profile.profile_data?.type || 'unknown')}`}>
                        {profile.profile_data?.type === 'own' ? '自社' : '競合他社'}
                      </span>
                      {profile.profile_data?.industry && (
                        <span className="px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded-full">
                          {profile.profile_data.industry}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => router.push(`/company-profiles/${profile.id}/edit`)}
                      className="text-blue-600 hover:text-blue-800"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                    </button>
                    <button
                      onClick={() => deleteProfile(profile.id)}
                      className="text-red-600 hover:text-red-800"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>

                {profile.profile_data?.description && (
                  <p className="text-gray-600 text-sm mb-4">
                    {profile.profile_data.description.length > 100
                      ? `${profile.profile_data.description.substring(0, 100)}...`
                      : profile.profile_data.description}
                  </p>
                )}

                <div className="space-y-2">
                  {profile.profile_data?.size && (
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Size:</span>
                      <span className="text-gray-700">{profile.profile_data.size}</span>
                    </div>
                  )}
                  {profile.profile_data?.revenue && (
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Revenue:</span>
                      <span className="text-gray-700">{profile.profile_data.revenue}</span>
                    </div>
                  )}
                </div>

                <div className="mt-4 pt-4 border-t border-gray-200">
                  <p className="text-xs text-gray-500">
                    Created: {new Date(profile.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
