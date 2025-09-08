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
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-primary-portage/20 to-neutral-background-light ">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-tory-blue"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-b from-primary-portage/20 to-neutral-background-light ">
      <main className="text-center space-y-8 p-8">
        <h1 className="text-6xl font-bold text-primary-tory-blue  mb-4">
          Biz Design
        </h1>
        <h2 className="text-2xl font-semibold text-neutral-text-dark ">
          AI-powered Business Framework Learning Platform
        </h2>
        <p className="text-lg text-neutral-text-light  max-w-2xl mx-auto">
          Transform your business thinking with AI-guided framework learning. Master SWOT analysis, user journey mapping, and more with intelligent guidance.
        </p>

        {!user && (
          <div className="space-y-4">
            <div className="space-x-4">
              <Link
                href="/auth/register"
                className="bg-accent-corn hover:bg-accent-corn/90 text-white font-bold py-3 px-6 rounded-lg text-lg transition-colors duration-200 shadow-lg"
              >
                無料で始める
              </Link>
              <Link
                href="/auth/login"
                className="bg-primary-royal-blue hover:bg-primary-tory-blue  text-white font-bold py-3 px-6 rounded-lg text-lg transition-colors duration-200"
              >
                ログイン
              </Link>
            </div>
            <p className="text-sm text-neutral-text-light ">
              無料プランで始めましょう。クレジットカードは不要です。
            </p>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12 max-w-4xl">
          <div className="bg-white  p-6 rounded-lg shadow-lg">
            <div className="text-3xl mb-4">🧠</div>
            <h3 className="text-xl font-semibold mb-2 text-neutral-text-dark ">AIガイド学習</h3>
            <p className="text-neutral-text-light ">
              インタラクティブなAI対話が、実際のシナリオにビジネスフレームワークを適用するお手伝いをします。
            </p>
          </div>

          <div className="bg-white  p-6 rounded-lg shadow-lg">
            <div className="text-3xl mb-4">📊</div>
            <h3 className="text-xl font-semibold mb-2 text-neutral-text-dark ">ビジュアルアウトプット</h3>
            <p className="text-neutral-text-light ">
              プロフェッショナルなビジネス分析ドキュメントと可視化を生成。
            </p>
          </div>

          <div className="bg-white  p-6 rounded-lg shadow-lg">
            <div className="text-3xl mb-4">🎯</div>
            <h3 className="text-xl font-semibold mb-2 text-neutral-text-dark ">実践的アプローチ</h3>
            <p className="text-neutral-text-light ">
              理論を超えて、実行可能なビジネスインサイトと戦略を作成。
            </p>
          </div>
        </div>
      </main>

      <footer className="absolute bottom-4 text-sm text-neutral-text-light">
        Biz Design v2.0.0 - モジュール2: 認証完了
      </footer>
    </div>
  );
}
