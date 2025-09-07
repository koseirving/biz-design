'use client';

import React, { createContext, useContext, useState, ReactNode } from 'react';

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

interface FrameworkListResponse {
  frameworks: Framework[];
  total: number;
  page: number;
  limit: number;
}

interface FrameworkContextType {
  frameworks: Framework[];
  loading: boolean;
  currentFramework: Framework | null;
  categories: string[];
  difficultyLevels: string[];
  searchQuery: string;
  selectedCategory: string | null;
  selectedDifficulty: string | null;
  fetchFrameworks: (params?: FrameworkSearchParams) => Promise<void>;
  fetchFramework: (id: string) => Promise<void>;
  fetchCategories: () => Promise<void>;
  setSearchQuery: (query: string) => void;
  setSelectedCategory: (category: string | null) => void;
  setSelectedDifficulty: (difficulty: string | null) => void;
  clearFilters: () => void;
}

interface FrameworkSearchParams {
  skip?: number;
  limit?: number;
  category?: string;
  difficulty_level?: string;
  search?: string;
}

const FrameworkContext = createContext<FrameworkContextType | undefined>(undefined);

interface FrameworkProviderProps {
  children: ReactNode;
}

export function FrameworkProvider({ children }: FrameworkProviderProps) {
  const [frameworks, setFrameworks] = useState<Framework[]>([]);
  const [loading, setLoading] = useState(false);
  const [currentFramework, setCurrentFramework] = useState<Framework | null>(null);
  const [categories, setCategories] = useState<string[]>([]);
  const [difficultyLevels, setDifficultyLevels] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [selectedDifficulty, setSelectedDifficulty] = useState<string | null>(null);

  const fetchFrameworks = async (params: FrameworkSearchParams = {}) => {
    setLoading(true);
    try {
      const searchParams = new URLSearchParams();
      
      if (params.skip) searchParams.append('skip', params.skip.toString());
      if (params.limit) searchParams.append('limit', params.limit.toString());
      if (params.category || selectedCategory) {
        searchParams.append('category', params.category || selectedCategory!);
      }
      if (params.difficulty_level || selectedDifficulty) {
        searchParams.append('difficulty_level', params.difficulty_level || selectedDifficulty!);
      }
      if (params.search || searchQuery) {
        searchParams.append('search', params.search || searchQuery);
      }

      const response = await fetch(`/api/proxy/frameworks?${searchParams.toString()}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch frameworks');
      }

      const data: FrameworkListResponse = await response.json();
      setFrameworks(data.frameworks);
    } catch (error) {
      console.error('Error fetching frameworks:', error);
      setFrameworks([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchFramework = async (id: string) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/proxy/frameworks/${id}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch framework');
      }

      const framework: Framework = await response.json();
      setCurrentFramework(framework);
    } catch (error) {
      console.error('Error fetching framework:', error);
      setCurrentFramework(null);
    } finally {
      setLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await fetch('/api/proxy/frameworks/categories');
      
      if (!response.ok) {
        throw new Error('Failed to fetch categories');
      }

      const data = await response.json();
      setCategories(data.categories || []);
    } catch (error) {
      console.error('Error fetching categories:', error);
      setCategories([]);
    }

    try {
      const response = await fetch('/api/proxy/frameworks/difficulty-levels');
      
      if (!response.ok) {
        throw new Error('Failed to fetch difficulty levels');
      }

      const data = await response.json();
      setDifficultyLevels(data.difficulty_levels || []);
    } catch (error) {
      console.error('Error fetching difficulty levels:', error);
      setDifficultyLevels([]);
    }
  };

  const clearFilters = () => {
    setSearchQuery('');
    setSelectedCategory(null);
    setSelectedDifficulty(null);
  };

  const value: FrameworkContextType = {
    frameworks,
    loading,
    currentFramework,
    categories,
    difficultyLevels,
    searchQuery,
    selectedCategory,
    selectedDifficulty,
    fetchFrameworks,
    fetchFramework,
    fetchCategories,
    setSearchQuery,
    setSelectedCategory,
    setSelectedDifficulty,
    clearFilters,
  };

  return (
    <FrameworkContext.Provider value={value}>
      {children}
    </FrameworkContext.Provider>
  );
}

export function useFramework() {
  const context = useContext(FrameworkContext);
  if (context === undefined) {
    throw new Error('useFramework must be used within a FrameworkProvider');
  }
  return context;
}