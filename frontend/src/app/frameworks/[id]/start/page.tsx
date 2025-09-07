'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useFramework } from '@/contexts/FrameworkContext';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import AiInteractionPanel from '@/components/AiInteractionPanel';
import SwotOutputDisplay from '@/components/SwotOutputDisplay';
import UserJourneyDisplay from '@/components/UserJourneyDisplay';

interface FrameworkContent {
  id: string;
  name: string;
  description: string;
  category: string;
  difficulty_level: string;
  estimated_duration: number;
  is_premium: boolean;
  micro_content: any;
}

interface GeneratedOutput {
  id: string;
  type: string;
  data: any;
  created_at: string;
}

export default function FrameworkStartPage({ params }: { params: { id: string } }) {
  const { user, loading: authLoading } = useAuth();
  const { loading } = useFramework();
  const router = useRouter();
  const [framework, setFramework] = useState<FrameworkContent | null>(null);
  const [contentLoading, setContentLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [generatedOutputs, setGeneratedOutputs] = useState<GeneratedOutput[]>([]);
  const [activeTab, setActiveTab] = useState<'chat' | 'output'>('chat');

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

  const fetchGeneratedOutput = async (outputId: string) => {
    try {
      const response = await fetch(`/api/proxy/outputs/${outputId}`);
      
      if (response.ok) {
        const outputData = await response.json();
        
        const newOutput: GeneratedOutput = {
          id: outputData.id,
          type: outputData.output_data.type,
          data: outputData.output_data,
          created_at: outputData.created_at
        };
        
        setGeneratedOutputs(prev => {
          const exists = prev.some(output => output.id === outputId);
          if (!exists) {
            return [...prev, newOutput];
          }
          return prev;
        });
        
        setActiveTab('output');
      }
    } catch (error) {
      console.error('Error fetching output:', error);
    }
  };

  const renderOutputVisualization = (output: GeneratedOutput) => {
    switch (output.type) {
      case 'swot_analysis':
        return (
          <SwotOutputDisplay
            key={output.id}
            swotData={output.data}
            title={`SWOT分析結果 - ${new Date(output.created_at).toLocaleString()}`}
            className="mb-6"
          />
        );
      case 'user_journey_map':
        return (
          <UserJourneyDisplay
            key={output.id}
            journeyData={output.data}
            title={`カスタマージャーニーマップ - ${new Date(output.created_at).toLocaleString()}`}
            className="mb-6"
          />
        );
      default:
        return (
          <div key={output.id} className="bg-white dark:bg-gray-800 shadow-lg rounded-lg p-6 mb-6">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">
              アウトプット結果
            </h3>
            <pre className="bg-gray-100 dark:bg-gray-700 p-4 rounded text-sm overflow-auto">
              {JSON.stringify(output.data, null, 2)}
            </pre>
          </div>
        );
    }
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
          <h2 className="text-2xl font-bold text-red-600 mb-4">エラー</h2>
          <p className="text-gray-600 dark:text-gray-400 mb-4">{error}</p>
          <Link href="/frameworks" className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
            フレームワーク一覧に戻る
          </Link>
        </div>
      </div>
    );
  }

  if (!framework) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white dark:from-gray-900 dark:to-gray-800 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-600 dark:text-gray-400 mb-4">フレームワークが見つかりません</h2>
          <Link href="/frameworks" className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
            フレームワーク一覧に戻る
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
                フレームワーク一覧
              </Link>
              <span className="text-gray-700 dark:text-gray-300">{user.email}</span>
              <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full text-xs font-semibold uppercase">
                {user.subscription_tier}
              </span>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Breadcrumb */}
        <div className="mb-6">
          <nav className="text-sm">
            <Link href="/frameworks" className="text-blue-600 hover:text-blue-800">
              フレームワーク一覧
            </Link>
            <span className="mx-2 text-gray-500">/</span>
            <Link href={`/frameworks/${framework.id}`} className="text-blue-600 hover:text-blue-800">
              {framework.name}
            </Link>
            <span className="mx-2 text-gray-500">/</span>
            <span className="text-gray-600 dark:text-gray-400">学習開始</span>
          </nav>
        </div>

        {/* Header */}
        <div className="bg-white dark:bg-gray-800 shadow-lg rounded-lg p-6 mb-8">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-2xl font-bold text-gray-800 dark:text-white mb-2">
                {framework.name} - AI分析セッション
              </h1>
              <p className="text-gray-600 dark:text-gray-400">
                AIコパイロットと対話しながら{framework.name}を実践してみましょう
              </p>
            </div>
            
            {framework.is_premium && user.subscription_tier !== 'premium' && (
              <div className="bg-yellow-50 dark:bg-yellow-900 border border-yellow-200 dark:border-yellow-700 rounded-lg p-4">
                <p className="text-yellow-800 dark:text-yellow-200 text-sm">
                  このフレームワークはプレミアム限定です
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* AI Interaction Panel */}
          <div className="lg:col-span-1">
            <div className="sticky top-8">
              <AiInteractionPanel 
                frameworkId={params.id}
                frameworkName={framework.name}
                onOutputGenerated={fetchGeneratedOutput}
              />
            </div>
          </div>

          {/* Results Panel */}
          <div className="lg:col-span-1">
            <div className="bg-white dark:bg-gray-800 shadow-lg rounded-lg">
              {/* Tab Headers */}
              <div className="flex border-b border-gray-200 dark:border-gray-700">
                <button
                  onClick={() => setActiveTab('chat')}
                  className={`px-6 py-3 font-medium text-sm ${activeTab === 'chat'
                    ? 'border-b-2 border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                  }`}
                >
                  ガイド
                </button>
                <button
                  onClick={() => setActiveTab('output')}
                  className={`px-6 py-3 font-medium text-sm ${activeTab === 'output'
                    ? 'border-b-2 border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                  }`}
                >
                  アウトプット ({generatedOutputs.length})
                </button>
              </div>

              {/* Tab Content */}
              <div className="p-6 max-h-96 lg:max-h-screen overflow-y-auto">
                {activeTab === 'chat' && (
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold text-gray-800 dark:text-white">
                      {framework.name}を始める前に
                    </h3>
                    
                    <div className="bg-blue-50 dark:bg-blue-900 border border-blue-200 dark:border-blue-700 rounded-lg p-4">
                      <h4 className="font-medium text-blue-800 dark:text-blue-200 mb-2">
                        AIコパイロットの使い方
                      </h4>
                      <ul className="text-sm text-blue-700 dark:text-blue-300 space-y-1">
                        <li>• 質問に答えながら分析を進めます</li>
                        <li>• いつでも詳細を聞き直すことができます</li>
                        <li>• 分析が完了すると自動で結果が表示されます</li>
                      </ul>
                    </div>

                    {framework.micro_content?.overview && (
                      <div>
                        <h4 className="font-medium text-gray-800 dark:text-white mb-2">フレームワーク概要</h4>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          {framework.micro_content.overview}
                        </p>
                      </div>
                    )}

                    <div className="text-center">
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        左のチャットパネルで「始めましょう」と入力してスタートしてください
                      </p>
                    </div>
                  </div>
                )}

                {activeTab === 'output' && (
                  <div>
                    {generatedOutputs.length === 0 ? (
                      <div className="text-center py-12">
                        <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center">
                          <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                        </div>
                        <p className="text-gray-500 dark:text-gray-400">
                          まだアウトプットが生成されていません
                        </p>
                        <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">
                          AIとの対話を通じて分析を完了すると、ここに結果が表示されます
                        </p>
                      </div>
                    ) : (
                      <div className="space-y-6">
                        {generatedOutputs.map(renderOutputVisualization)}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}