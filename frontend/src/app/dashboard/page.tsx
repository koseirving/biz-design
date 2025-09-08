'use client';

import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import Link from 'next/link';

interface ProgressData {
  total_points: number;
  earned_badges: Array<{
    type: string;
    name: string;
    description: string;
    icon: string;
    color: string;
    earned_at: string;
  }>;
  completed_frameworks: number;
  ai_interactions: number;
  outputs_created: number;
  current_streak: number;
  ranking: {
    rank: number;
    total_users: number;
    percentile: number;
  };
  badge_progress: Record<string, {
    current: number;
    required: number;
    percentage: number;
  }>;
  daily_points: Array<{
    date: string;
    points: number;
  }>;
}

export default function DashboardPage() {
  const { user, loading, logout } = useAuth();
  const router = useRouter();
  const [progressData, setProgressData] = useState<ProgressData | null>(null);
  const [progressLoading, setProgressLoading] = useState(true);

  useEffect(() => {
    if (!loading && !user) {
      router.push('/auth/login');
      return;
    }

    if (user) {
      fetchProgressData();
    }
  }, [user, loading, router]);

  const fetchProgressData = async () => {
    try {
      const response = await fetch('/api/proxy/users/me/progress');
      if (response.ok) {
        const data = await response.json();
        setProgressData(data);
      }
    } catch (error) {
      console.error('Error fetching progress data:', error);
    } finally {
      setProgressLoading(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    router.push('/');
  };

  const getProgressColor = (percentage: number) => {
    if (percentage >= 100) return 'bg-green-500';
    if (percentage >= 75) return 'bg-blue-500';
    if (percentage >= 50) return 'bg-yellow-500';
    if (percentage >= 25) return 'bg-orange-500';
    return 'bg-red-500';
  };

  const getBadgeColorClasses = (color: string) => {
    const colorMap: Record<string, string> = {
      green: 'bg-green-100 text-green-800 border-green-200',
      blue: 'bg-blue-100 text-blue-800 border-blue-200',
      gold: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      purple: 'bg-purple-100 text-purple-800 border-purple-200',
      orange: 'bg-orange-100 text-orange-800 border-orange-200',
      cyan: 'bg-cyan-100 text-cyan-800 border-cyan-200',
      royal: 'bg-indigo-100 text-indigo-800 border-indigo-200',
      diamond: 'bg-pink-100 text-pink-800 border-pink-200'
    };
    return colorMap[color] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  if (loading || progressLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-primary-portage/20 to-neutral-background-light flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-tory-blue"></div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-primary-portage/20 to-neutral-background-light">
      {/* Navigation */}
      <nav className="bg-white  shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-blue-600 ">
                Biz Design
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <Link href="/frameworks" className="text-gray-600  hover:text-blue-600">
                Frameworks
              </Link>
              <Link href="/company-profiles" className="text-gray-600  hover:text-blue-600">
                Company Profiles
              </Link>
              <div className="flex items-center space-x-2">
                {progressData && (
                  <div className="flex items-center space-x-1 px-2 py-1 bg-yellow-100  text-yellow-800  rounded-full text-xs font-semibold">
                    <span>⭐</span>
                    <span>{progressData.total_points}</span>
                  </div>
                )}
                <span className="text-gray-700 ">{user.email}</span>
                <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-semibold uppercase">
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
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Header with Stats */}
        <div className="bg-white  shadow-lg rounded-lg p-6 mb-8">
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-3xl font-bold text-gray-800  mb-2">
                おかえりなさい！ 👋
              </h2>
              <p className="text-gray-600 ">
                AI活用ビジネスフレームワーク学習を続けましょう
              </p>
            </div>
            
            {progressData && (
              <div className="flex items-center space-x-6">
                {progressData.current_streak > 0 && (
                  <div className="text-center">
                    <div className="text-2xl font-bold text-orange-600">
                      🔥 {progressData.current_streak}
                    </div>
                    <div className="text-sm text-gray-500 ">日連続</div>
                  </div>
                )}
                
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600 ">
                    #{progressData.ranking.rank}
                  </div>
                  <div className="text-sm text-gray-500 ">
                    上位 {progressData.ranking.percentile}%
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Quick Stats Cards */}
        {progressData && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-white  shadow-lg rounded-lg p-6 text-center">
              <div className="text-3xl font-bold text-yellow-600 mb-2">
                ⭐ {progressData.total_points}
              </div>
              <div className="text-sm text-gray-500 ">合計ポイント</div>
            </div>
            
            <div className="bg-white  shadow-lg rounded-lg p-6 text-center">
              <div className="text-3xl font-bold text-green-600 mb-2">
                🏆 {progressData.earned_badges.length}
              </div>
              <div className="text-sm text-gray-500 ">獲得バッジ</div>
            </div>
            
            <div className="bg-white  shadow-lg rounded-lg p-6 text-center">
              <div className="text-3xl font-bold text-blue-600  mb-2">
                📋 {progressData.completed_frameworks}
              </div>
              <div className="text-sm text-gray-500 ">完了フレームワーク</div>
            </div>
            
            <div className="bg-white  shadow-lg rounded-lg p-6 text-center">
              <div className="text-3xl font-bold text-purple-600 mb-2">
                🤖 {progressData.ai_interactions}
              </div>
              <div className="text-sm text-gray-500 ">AIチャット</div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content - Framework Cards */}
          <div className="lg:col-span-2">
            <div className="bg-white  shadow-lg rounded-lg p-6 mb-8">
              <h3 className="text-xl font-semibold text-gray-800  mb-6">
                学習を始める 🚀
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-6 rounded-lg border border-blue-200">
                  <div className="flex items-center mb-4">
                    <div className="text-3xl mr-3">📊</div>
                    <div>
                      <h4 className="text-lg font-semibold text-blue-800">
                        SWOT分析
                      </h4>
                      <p className="text-sm text-blue-600">
                        完了で100ポイント
                      </p>
                    </div>
                  </div>
                  <p className="text-blue-600 mb-4 text-sm">
                    AIガイダンスで強み、弱み、機会、脅威を分析。
                  </p>
                  <Link href="/frameworks" className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded text-sm inline-block">
                    分析を開始
                  </Link>
                </div>
                
                <div className="bg-gradient-to-br from-green-50 to-green-100 p-6 rounded-lg border border-green-200">
                  <div className="flex items-center mb-4">
                    <div className="text-3xl mr-3">🗺️</div>
                    <div>
                      <h4 className="text-lg font-semibold text-green-800">
                        カスタマージャーニーマップ
                      </h4>
                      <p className="text-sm text-green-600">
                        完了で100ポイント
                      </p>
                    </div>
                  </div>
                  <p className="text-green-600 mb-4 text-sm">
                    AIインサイトで顧客のジャーニーをマッピング。
                  </p>
                  <Link href="/frameworks" className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded text-sm inline-block">
                    ジャーニー作成
                  </Link>
                </div>
              </div>
            </div>

            {/* Badge Progress */}
            {progressData && (
              <div className="bg-white  shadow-lg rounded-lg p-6">
                <h3 className="text-xl font-semibold text-gray-800  mb-6">
                  バッジ進捗 🎯
                </h3>
                
                <div className="space-y-4">
                  {Object.entries(progressData.badge_progress).slice(0, 4).map(([badgeType, progress]) => (
                    <div key={badgeType} className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex justify-between items-center mb-1">
                          <span className="text-sm font-medium text-gray-700  capitalize">
                            {badgeType.replace('_', ' ')}
                          </span>
                          <span className="text-sm text-gray-500 ">
                            {progress.current}/{progress.required}
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full transition-all duration-300 ${getProgressColor(progress.percentage)}`}
                            style={{ width: `${Math.min(progress.percentage, 100)}%` }}
                          ></div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Earned Badges */}
            {progressData && progressData.earned_badges.length > 0 && (
              <div className="bg-white  shadow-lg rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-800  mb-4">
                  獲得バッジ 🏆
                </h3>
                <div className="grid grid-cols-2 gap-3">
                  {progressData.earned_badges.slice(0, 6).map((badge, index) => (
                    <div
                      key={index}
                      className={`p-3 rounded-lg border text-center ${getBadgeColorClasses(badge.color)}`}
                      title={badge.description}
                    >
                      <div className="text-2xl mb-1">{badge.icon}</div>
                      <div className="text-xs font-semibold">{badge.name}</div>
                    </div>
                  ))}
                </div>
                {progressData.earned_badges.length > 6 && (
                  <div className="text-center mt-4">
                    <span className="text-sm text-gray-500 ">
                      +{progressData.earned_badges.length - 6} 個のバッジ
                    </span>
                  </div>
                )}
              </div>
            )}

            {/* Quick Actions */}
            <div className="bg-white  shadow-lg rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-800  mb-4">
                クイックアクション ⚡
              </h3>
              <div className="space-y-3">
                <Link
                  href="/company-profiles"
                  className="flex items-center p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="text-lg mr-3">🏢</div>
                  <div>
                    <div className="font-medium text-gray-800  text-sm">
                      企業管理
                    </div>
                    <div className="text-xs text-gray-500 ">
                      企業プロファイルを追加
                    </div>
                  </div>
                </Link>
                
                <Link
                  href="/frameworks"
                  className="flex items-center p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="text-lg mr-3">📚</div>
                  <div>
                    <div className="font-medium text-gray-800  text-sm">
                      フレームワーク一覧
                    </div>
                    <div className="text-xs text-gray-500 ">
                      新しいツールを発見
                    </div>
                  </div>
                </Link>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="bg-white  shadow-lg rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-800  mb-4">
                最近のアクティビティ 📈
              </h3>
              {progressData && progressData.daily_points.length > 0 ? (
                <div className="space-y-3">
                  {progressData.daily_points.slice(-5).reverse().map((day, index) => (
                    day.points > 0 && (
                      <div key={index} className="flex justify-between items-center">
                        <span className="text-sm text-gray-600 ">
                          {new Date(day.date).toLocaleDateString()}
                        </span>
                        <span className="text-sm font-semibold text-yellow-600">
                          +{day.points} pts
                        </span>
                      </div>
                    )
                  ))}
                </div>
              ) : (
                <div className="text-center text-gray-500  py-4">
                  <div className="text-3xl mb-2">🌟</div>
                  <p className="text-sm">学習を始めてアクティビティを確認しましょう！</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}