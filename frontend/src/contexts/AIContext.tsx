'use client';

import React, { createContext, useContext, useState, ReactNode } from 'react';

interface ConversationMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

interface AIResponse {
  type: 'ai_response' | 'function_call' | 'error' | 'stream_end';
  content?: string;
  function_name?: string;
  function_result?: any;
  is_complete?: boolean;
  timestamp: string;
  error_message?: string;
}

interface SupportedFramework {
  id: string;
  name: string;
  key: string;
  description: string;
  category: string;
  difficulty_level: string;
  is_premium: boolean;
}

interface AIContextType {
  currentConversation: ConversationMessage[];
  isLoading: boolean;
  isConnected: boolean;
  supportedFrameworks: SupportedFramework[];
  currentFramework: SupportedFramework | null;
  lastResponse: AIResponse | null;
  
  // Methods
  sendMessage: (frameworkId: string, message: string, sessionId?: string) => Promise<void>;
  clearConversation: () => void;
  setCurrentFramework: (framework: SupportedFramework | null) => void;
  fetchSupportedFrameworks: () => Promise<void>;
  addMessage: (message: ConversationMessage) => void;
}

const AIContext = createContext<AIContextType | undefined>(undefined);

interface AIProviderProps {
  children: ReactNode;
}

export function AIProvider({ children }: AIProviderProps) {
  const [currentConversation, setCurrentConversation] = useState<ConversationMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [supportedFrameworks, setSupportedFrameworks] = useState<SupportedFramework[]>([]);
  const [currentFramework, setCurrentFramework] = useState<SupportedFramework | null>(null);
  const [lastResponse, setLastResponse] = useState<AIResponse | null>(null);

  const sendMessage = async (frameworkId: string, message: string, sessionId?: string) => {
    setIsLoading(true);
    setIsConnected(false);

    try {
      // ユーザーメッセージをすぐに会話に追加
      const userMessage: ConversationMessage = {
        role: 'user',
        content: message,
        timestamp: new Date().toISOString()
      };
      
      setCurrentConversation(prev => [...prev, userMessage]);

      const response = await fetch('/api/proxy/ai/interact', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          framework_id: frameworkId,
          user_input: message,
          conversation_history: currentConversation,
          session_id: sessionId
        }),
      });

      if (!response.ok) {
        throw new Error('AI対話の開始に失敗しました');
      }

      setIsConnected(true);

      // Server-Sent Eventsを読み取り
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('ストリーミング応答の読み取りに失敗しました');
      }

      let assistantMessage = '';
      let isComplete = false;

      while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const jsonData = line.slice(6);
              if (jsonData.trim()) {
                const aiResponse: AIResponse = JSON.parse(jsonData);
                setLastResponse(aiResponse);

                if (aiResponse.type === 'ai_response') {
                  assistantMessage += aiResponse.content || '';
                  isComplete = aiResponse.is_complete || false;
                } else if (aiResponse.type === 'function_call') {
                  // Function Call結果の処理
                  console.log('Function call executed:', aiResponse);
                } else if (aiResponse.type === 'error') {
                  console.error('AI Error:', aiResponse.error_message);
                  throw new Error(aiResponse.error_message || 'AI処理エラー');
                } else if (aiResponse.type === 'stream_end') {
                  break;
                }
              }
            } catch (e) {
              console.error('JSON parse error:', e);
            }
          }
        }
      }

      // AIの応答を会話に追加
      if (assistantMessage) {
        const aiMessage: ConversationMessage = {
          role: 'assistant',
          content: assistantMessage,
          timestamp: new Date().toISOString()
        };
        setCurrentConversation(prev => [...prev, aiMessage]);
      }

    } catch (error) {
      console.error('AI対話エラー:', error);
      const errorMessage: ConversationMessage = {
        role: 'assistant',
        content: `エラーが発生しました: ${error instanceof Error ? error.message : '不明なエラー'}`,
        timestamp: new Date().toISOString()
      };
      setCurrentConversation(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setIsConnected(false);
    }
  };

  const clearConversation = () => {
    setCurrentConversation([]);
    setLastResponse(null);
  };

  const addMessage = (message: ConversationMessage) => {
    setCurrentConversation(prev => [...prev, message]);
  };

  const fetchSupportedFrameworks = async () => {
    try {
      const response = await fetch('/api/proxy/ai/supported-frameworks');
      
      if (!response.ok) {
        throw new Error('サポートされているフレームワークの取得に失敗しました');
      }

      const data = await response.json();
      setSupportedFrameworks(data.supported_frameworks || []);
    } catch (error) {
      console.error('サポートフレームワーク取得エラー:', error);
      setSupportedFrameworks([]);
    }
  };

  const value: AIContextType = {
    currentConversation,
    isLoading,
    isConnected,
    supportedFrameworks,
    currentFramework,
    lastResponse,
    sendMessage,
    clearConversation,
    setCurrentFramework,
    fetchSupportedFrameworks,
    addMessage,
  };

  return (
    <AIContext.Provider value={value}>
      {children}
    </AIContext.Provider>
  );
}

export function useAI() {
  const context = useContext(AIContext);
  if (context === undefined) {
    throw new Error('useAI must be used within an AIProvider');
  }
  return context;
}