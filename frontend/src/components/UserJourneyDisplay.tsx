'use client';

import React, { useState } from 'react';

interface JourneyStage {
  stage_id: string;
  stage_name: string;
  user_actions: string;
  user_thoughts?: string;
  emotions?: string;
  pain_points: string;
  touchpoints: string[];
  opportunities: string[];
  order: number;
}

interface JourneyPersona {
  name: string;
  goal?: string;
  context?: string;
}

interface UserJourneyData {
  type: string;
  persona: JourneyPersona;
  timeline: JourneyStage[];
  summary: {
    total_stages: number;
    key_pain_points: string[];
    improvement_opportunities: string[];
  };
}

interface UserJourneyDisplayProps {
  journeyData: UserJourneyData;
  title?: string;
  showExportOptions?: boolean;
  className?: string;
}

export default function UserJourneyDisplay({
  journeyData,
  title,
  showExportOptions = true,
  className = ''
}: UserJourneyDisplayProps) {
  const [selectedStage, setSelectedStage] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'timeline' | 'detailed'>('timeline');

  const getEmotionColor = (emotions?: string) => {
    if (!emotions) return 'text-gray-500';
    
    const emotionLower = emotions.toLowerCase();
    if (emotionLower.includes('満足') || emotionLower.includes('喜') || emotionLower.includes('楽し')) {
      return 'text-green-600 dark:text-green-400';
    } else if (emotionLower.includes('不安') || emotionLower.includes('困') || emotionLower.includes('イライラ')) {
      return 'text-red-600 dark:text-red-400';
    } else if (emotionLower.includes('期待') || emotionLower.includes('関心')) {
      return 'text-blue-600 dark:text-blue-400';
    }
    return 'text-yellow-600 dark:text-yellow-400';
  };

  const getStageIcon = (index: number) => {
    const icons = [
      '👁️', '🤔', '🛒', '📱', '💬', '⭐', '🔄'
    ];
    return icons[index] || '📍';
  };

  const renderTimelineView = () => (
    <div className="relative">
      {/* Timeline Line */}
      <div className="absolute left-8 top-16 bottom-0 w-0.5 bg-gray-300 dark:bg-gray-600"></div>

      <div className="space-y-8">
        {journeyData.timeline.map((stage, index) => (
          <div key={stage.stage_id} className="relative flex items-start">
            {/* Timeline Dot */}
            <div className="flex-shrink-0 w-16 h-16 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold text-lg shadow-lg">
              <span>{getStageIcon(index)}</span>
            </div>

            {/* Stage Content */}
            <div className="ml-6 flex-1 bg-white dark:bg-gray-700 rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow cursor-pointer"
                 onClick={() => setSelectedStage(selectedStage === stage.stage_id ? null : stage.stage_id)}>
              
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-lg font-bold text-gray-800 dark:text-white">
                  {stage.order}. {stage.stage_name}
                </h3>
                <button className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
                  <svg className={`w-5 h-5 transform transition-transform ${selectedStage === stage.stage_id ? 'rotate-180' : ''}`} 
                       fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <h4 className="font-medium text-gray-700 dark:text-gray-300 mb-2">ユーザーの行動</h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{stage.user_actions}</p>
                </div>
                
                {stage.emotions && (
                  <div>
                    <h4 className="font-medium text-gray-700 dark:text-gray-300 mb-2">感情</h4>
                    <p className={`text-sm font-medium ${getEmotionColor(stage.emotions)}`}>
                      {stage.emotions}
                    </p>
                  </div>
                )}
              </div>

              {/* Expanded Content */}
              {selectedStage === stage.stage_id && (
                <div className="border-t border-gray-200 dark:border-gray-600 pt-4 space-y-4">
                  
                  {stage.user_thoughts && (
                    <div>
                      <h4 className="font-medium text-gray-700 dark:text-gray-300 mb-2">ユーザーの思考</h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400 italic">
                        "{stage.user_thoughts}"
                      </p>
                    </div>
                  )}

                  <div>
                    <h4 className="font-medium text-red-700 dark:text-red-400 mb-2">ペインポイント</h4>
                    <p className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900 p-3 rounded">
                      {stage.pain_points}
                    </p>
                  </div>

                  {stage.touchpoints.length > 0 && (
                    <div>
                      <h4 className="font-medium text-gray-700 dark:text-gray-300 mb-2">タッチポイント</h4>
                      <div className="flex flex-wrap gap-2">
                        {stage.touchpoints.map((touchpoint, idx) => (
                          <span key={idx} className="px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-sm rounded-full">
                            {touchpoint}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {stage.opportunities.length > 0 && (
                    <div>
                      <h4 className="font-medium text-green-700 dark:text-green-400 mb-2">改善機会</h4>
                      <ul className="space-y-1">
                        {stage.opportunities.map((opportunity, idx) => (
                          <li key={idx} className="text-sm text-green-600 dark:text-green-400 flex items-start">
                            <svg className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                            </svg>
                            {opportunity}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderDetailedView = () => (
    <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
      {journeyData.timeline.map((stage, index) => (
        <div key={stage.stage_id} className="bg-white dark:bg-gray-700 rounded-lg shadow-md p-6">
          <div className="flex items-center mb-4">
            <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white mr-3">
              <span>{getStageIcon(index)}</span>
            </div>
            <div>
              <h3 className="font-bold text-gray-800 dark:text-white">{stage.stage_name}</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">ステージ {stage.order}</p>
            </div>
          </div>

          <div className="space-y-3">
            <div>
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">行動</h4>
              <p className="text-sm text-gray-600 dark:text-gray-400">{stage.user_actions}</p>
            </div>

            {stage.emotions && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">感情</h4>
                <p className={`text-sm ${getEmotionColor(stage.emotions)}`}>{stage.emotions}</p>
              </div>
            )}

            <div>
              <h4 className="text-sm font-medium text-red-700 dark:text-red-400">ペインポイント</h4>
              <p className="text-sm text-red-600 dark:text-red-400">{stage.pain_points}</p>
            </div>

            {stage.opportunities.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-green-700 dark:text-green-400">改善機会</h4>
                <p className="text-sm text-green-600 dark:text-green-400">
                  {stage.opportunities.join(', ')}
                </p>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );

  return (
    <div className={`bg-white dark:bg-gray-800 shadow-lg rounded-lg overflow-hidden ${className}`}>
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-xl font-bold text-gray-800 dark:text-white">
              {title || 'カスタマージャーニーマップ'}
            </h2>
            <div className="mt-2 space-y-1">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                <span className="font-medium">ペルソナ:</span> {journeyData.persona.name}
              </p>
              {journeyData.persona.goal && (
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  <span className="font-medium">目標:</span> {journeyData.persona.goal}
                </p>
              )}
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <div className="flex bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
              <button
                onClick={() => setViewMode('timeline')}
                className={`px-3 py-1 text-sm rounded ${viewMode === 'timeline' 
                  ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow' 
                  : 'text-gray-600 dark:text-gray-400'}`}
              >
                タイムライン
              </button>
              <button
                onClick={() => setViewMode('detailed')}
                className={`px-3 py-1 text-sm rounded ${viewMode === 'detailed' 
                  ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow' 
                  : 'text-gray-600 dark:text-gray-400'}`}
              >
                詳細
              </button>
            </div>

            {showExportOptions && (
              <button className="px-3 py-1 bg-blue-500 text-white text-sm rounded hover:bg-blue-600">
                エクスポート
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {viewMode === 'timeline' ? renderTimelineView() : renderDetailedView()}
      </div>

      {/* Summary */}
      <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-medium text-gray-800 dark:text-white mb-2">主要なペインポイント</h4>
            <ul className="space-y-1">
              {journeyData.summary.key_pain_points.slice(0, 3).map((pain, index) => (
                <li key={index} className="text-sm text-red-600 dark:text-red-400 flex items-start">
                  <svg className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5C2.962 18.333 3.924 20 5.464 20z" />
                  </svg>
                  {pain}
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h4 className="font-medium text-gray-800 dark:text-white mb-2">改善機会サマリー</h4>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              <p>総ステージ数: {journeyData.summary.total_stages}</p>
              <p>改善機会: {journeyData.summary.improvement_opportunities.length}件</p>
              <p>主要課題: {journeyData.summary.key_pain_points.length}件</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}