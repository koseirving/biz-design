'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useAI } from '@/contexts/AIContext';
import { useAuth } from '@/contexts/AuthContext';

interface AiInteractionPanelProps {
  frameworkId: string;
  frameworkName: string;
  sessionId?: string;
  onOutputGenerated?: (outputId: string) => void;
}

export default function AiInteractionPanel({ 
  frameworkId, 
  frameworkName, 
  sessionId,
  onOutputGenerated 
}: AiInteractionPanelProps) {
  const { user } = useAuth();
  const { 
    currentConversation, 
    isLoading, 
    isConnected, 
    lastResponse,
    sendMessage, 
    clearConversation 
  } = useAI();

  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [currentConversation]);

  useEffect(() => {
    // Function call完了時の処理
    if (lastResponse?.type === 'function_call' && lastResponse.function_result) {
      if (lastResponse.function_result.success && lastResponse.function_result.output_id) {
        onOutputGenerated?.(lastResponse.function_result.output_id);
      }
    }
  }, [lastResponse, onOutputGenerated]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!inputMessage.trim() || isLoading) return;

    const message = inputMessage.trim();
    setInputMessage('');
    setIsTyping(true);

    try {
      await sendMessage(frameworkId, message, sessionId);
    } catch (error) {
      console.error('メッセージ送信エラー:', error);
    } finally {
      setIsTyping(false);
    }
  };

  const handleClearConversation = () => {
    if (confirm('会話をクリアしますか？これまでの対話内容が削除されます。')) {
      clearConversation();
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('ja-JP', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="bg-white dark:bg-gray-800 shadow-lg rounded-lg overflow-hidden h-full flex flex-col">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex justify-between items-center">
          <div>
            <h3 className="text-lg font-semibold text-gray-800 dark:text-white">
              AIコパイロット
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {frameworkName}での分析をサポートします
            </p>
          </div>
          <div className="flex items-center space-x-2">
            {isConnected && (
              <div className="flex items-center text-green-600 text-sm">
                <div className="w-2 h-2 bg-green-600 rounded-full animate-pulse mr-2"></div>
                接続中
              </div>
            )}
            <button
              onClick={handleClearConversation}
              disabled={currentConversation.length === 0}
              className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 disabled:opacity-50"
              title="会話をクリア"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {currentConversation.length === 0 ? (
          <div className="text-center text-gray-500 dark:text-gray-400 py-8">
            <div className="w-16 h-16 mx-auto mb-4 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <p>AIコパイロットとの対話を開始しましょう</p>
            <p className="text-sm mt-1">質問や分析したい内容を入力してください</p>
          </div>
        ) : (
          currentConversation.map((message, index) => (
            <div
              key={index}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                  message.role === 'user'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200'
                }`}
              >
                <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                <p className={`text-xs mt-1 ${
                  message.role === 'user' 
                    ? 'text-blue-100' 
                    : 'text-gray-500 dark:text-gray-400'
                }`}>
                  {formatTimestamp(message.timestamp)}
                </p>
              </div>
            </div>
          ))
        )}
        
        {(isLoading || isTyping) && (
          <div className="flex justify-start">
            <div className="bg-gray-200 dark:bg-gray-700 px-4 py-2 rounded-lg">
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
            </div>
          </div>
        )}

        {/* Function Call結果の表示 */}
        {lastResponse?.type === 'function_call' && lastResponse.function_result && (
          <div className="bg-green-50 dark:bg-green-900 border border-green-200 dark:border-green-700 rounded-lg p-4">
            <div className="flex items-center mb-2">
              <svg className="w-5 h-5 text-green-600 dark:text-green-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h4 className="text-sm font-semibold text-green-800 dark:text-green-200">
                分析完了
              </h4>
            </div>
            <p className="text-sm text-green-700 dark:text-green-300">
              {lastResponse.function_result.summary || '分析が正常に完了しました'}
            </p>
            {lastResponse.function_result.output_id && (
              <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                アウトプットID: {lastResponse.function_result.output_id}
              </p>
            )}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700">
        {user?.subscription_tier !== 'premium' && (
          <div className="mb-4 p-3 bg-yellow-50 dark:bg-yellow-900 border border-yellow-200 dark:border-yellow-700 rounded-lg">
            <p className="text-sm text-yellow-800 dark:text-yellow-200">
              AIコパイロット機能はプレミアムプラン限定です。
              <button className="ml-2 text-yellow-600 dark:text-yellow-400 underline hover:text-yellow-700">
                アップグレード
              </button>
            </p>
          </div>
        )}

        <form onSubmit={handleSendMessage} className="flex space-x-2">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            disabled={isLoading || user?.subscription_tier !== 'premium'}
            placeholder={
              user?.subscription_tier !== 'premium' 
                ? 'プレミアムプランが必要です' 
                : 'メッセージを入力...'
            }
            className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white disabled:bg-gray-100 dark:disabled:bg-gray-800 disabled:cursor-not-allowed"
          />
          <button
            type="submit"
            disabled={!inputMessage.trim() || isLoading || user?.subscription_tier !== 'premium'}
            className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-300 dark:disabled:bg-gray-600 disabled:cursor-not-allowed"
          >
            {isLoading ? '送信中...' : '送信'}
          </button>
        </form>
      </div>
    </div>
  );
}