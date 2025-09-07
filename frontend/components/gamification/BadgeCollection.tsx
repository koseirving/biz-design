'use client'

import React, { useState, useEffect } from 'react'
import { format } from 'date-fns'

interface Badge {
  id: string
  badge_type: string
  badge_name: string
  description: string
  icon: string
  tier: 'bronze' | 'silver' | 'gold' | 'platinum'
  earned_at?: string
  is_earned: boolean
  unlock_condition: string
  progress_current?: number
  progress_total?: number
}

interface BadgeCollectionProps {
  userId?: string
  showProgress?: boolean
  filterBy?: 'all' | 'earned' | 'locked'
  gridCols?: number
}

const badgeTypeLabels: Record<string, string> = {
  'beginner': 'Getting Started',
  'explorer': 'Learning Explorer',
  'expert': 'Subject Expert',
  'consistency': 'Consistency Master',
  'achievement': 'Special Achievement',
  'milestone': 'Milestone'
}

const tierColors = {
  bronze: 'from-amber-600 to-amber-800',
  silver: 'from-gray-400 to-gray-600',
  gold: 'from-yellow-400 to-yellow-600',
  platinum: 'from-purple-400 to-purple-600'
}

const tierGlows = {
  bronze: 'shadow-amber-500/50',
  silver: 'shadow-gray-500/50',
  gold: 'shadow-yellow-500/50',
  platinum: 'shadow-purple-500/50'
}

export default function BadgeCollection({
  userId,
  showProgress = true,
  filterBy = 'all',
  gridCols = 4
}: BadgeCollectionProps) {
  const [badges, setBadges] = useState<Badge[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedBadge, setSelectedBadge] = useState<Badge | null>(null)
  const [animatingBadges, setAnimatingBadges] = useState<Set<string>>(new Set())

  useEffect(() => {
    fetchBadges()
  }, [userId])

  const fetchBadges = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/proxy/users/me/badges', {
        method: 'GET',
        credentials: 'include'
      })
      
      if (!response.ok) {
        throw new Error('Failed to fetch badges')
      }
      
      const data = await response.json()
      setBadges(data.badges || [])
    } catch (error) {
      console.error('Error fetching badges:', error)
    } finally {
      setLoading(false)
    }
  }

  const filteredBadges = badges.filter(badge => {
    switch (filterBy) {
      case 'earned':
        return badge.is_earned
      case 'locked':
        return !badge.is_earned
      default:
        return true
    }
  })

  const triggerUnlockAnimation = (badgeId: string) => {
    setAnimatingBadges(prev => new Set(prev).add(badgeId))
    setTimeout(() => {
      setAnimatingBadges(prev => {
        const newSet = new Set(prev)
        newSet.delete(badgeId)
        return newSet
      })
    }, 2000)
  }

  const getBadgeIcon = (badge: Badge) => {
    // Use emoji or return a default based on badge type
    const icons: Record<string, string> = {
      'beginner': '🌟',
      'explorer': '🔍',
      'expert': '🎓',
      'consistency': '🔥',
      'achievement': '🏆',
      'milestone': '🎯'
    }
    return icons[badge.badge_type] || badge.icon || '🏅'
  }

  const getProgressPercentage = (badge: Badge) => {
    if (!badge.progress_current || !badge.progress_total) return 0
    return Math.min((badge.progress_current / badge.progress_total) * 100, 100)
  }

  const renderBadge = (badge: Badge, index: number) => {
    const isAnimating = animatingBadges.has(badge.id)
    const progressPercent = getProgressPercentage(badge)
    
    return (
      <div
        key={badge.id}
        className={`relative group cursor-pointer transition-all duration-300 hover:scale-105 ${
          isAnimating ? 'animate-bounce' : ''
        }`}
        onClick={() => setSelectedBadge(badge)}
        style={{ animationDelay: `${index * 0.1}s` }}
      >
        {/* Badge Container */}
        <div
          className={`aspect-square rounded-2xl p-4 flex flex-col items-center justify-center relative overflow-hidden ${
            badge.is_earned
              ? `bg-gradient-to-br ${tierColors[badge.tier]} text-white shadow-lg ${tierGlows[badge.tier]}`
              : 'bg-gray-200 dark:bg-gray-700 text-gray-400 dark:text-gray-500'
          }`}
        >
          {/* Unlock Animation Overlay */}
          {isAnimating && (
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-pulse" />
          )}
          
          {/* Badge Icon */}
          <div className={`text-4xl mb-2 ${badge.is_earned ? '' : 'grayscale opacity-50'}`}>
            {getBadgeIcon(badge)}
          </div>
          
          {/* Badge Name */}
          <h3 className={`text-sm font-bold text-center leading-tight ${
            badge.is_earned ? 'text-white' : 'text-gray-500 dark:text-gray-400'
          }`}>
            {badge.badge_name}
          </h3>
          
          {/* Tier Indicator */}
          {badge.is_earned && (
            <div className="absolute top-2 right-2">
              <div className={`w-3 h-3 rounded-full bg-white/30 ring-2 ring-white/60`} />
            </div>
          )}
          
          {/* Lock Icon for unearned badges */}
          {!badge.is_earned && (
            <div className="absolute top-2 left-2 text-gray-400">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
              </svg>
            </div>
          )}
        </div>
        
        {/* Progress Bar */}
        {showProgress && !badge.is_earned && badge.progress_current !== undefined && (
          <div className="mt-2">
            <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-1.5">
              <div
                className="bg-blue-500 h-1.5 rounded-full transition-all duration-500"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 text-center">
              {badge.progress_current}/{badge.progress_total}
            </p>
          </div>
        )}
        
        {/* Earned Date */}
        {badge.is_earned && badge.earned_at && (
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2 text-center">
            Earned {format(new Date(badge.earned_at), 'MMM dd, yyyy')}
          </p>
        )}
      </div>
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div>
      {/* Badge Grid */}
      <div 
        className={`grid gap-6 ${gridCols === 3 ? 'grid-cols-3' : gridCols === 4 ? 'grid-cols-4' : gridCols === 5 ? 'grid-cols-5' : 'grid-cols-2'}`}
        style={{ gridTemplateColumns: `repeat(${gridCols}, minmax(0, 1fr))` }}
      >
        {filteredBadges.map((badge, index) => renderBadge(badge, index))}
      </div>

      {/* Empty State */}
      {filteredBadges.length === 0 && (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">🏅</div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            {filterBy === 'earned' ? 'No badges earned yet' : 'No badges available'}
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            {filterBy === 'earned' 
              ? 'Complete activities to start earning badges!' 
              : 'Check back later for new badges to unlock.'}
          </p>
        </div>
      )}

      {/* Badge Detail Modal */}
      {selectedBadge && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl max-w-md w-full p-6">
            <div className="text-center">
              {/* Badge Icon Large */}
              <div className={`text-8xl mb-4 ${selectedBadge.is_earned ? '' : 'grayscale opacity-50'}`}>
                {getBadgeIcon(selectedBadge)}
              </div>
              
              {/* Badge Info */}
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                {selectedBadge.badge_name}
              </h2>
              
              <div className={`inline-block px-3 py-1 rounded-full text-sm font-medium mb-4 ${
                selectedBadge.is_earned
                  ? `bg-gradient-to-r ${tierColors[selectedBadge.tier]} text-white`
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
              }`}>
                {selectedBadge.tier.charAt(0).toUpperCase() + selectedBadge.tier.slice(1)} Badge
              </div>
              
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                {selectedBadge.description}
              </p>
              
              {/* Unlock Condition */}
              <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 mb-6">
                <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                  {selectedBadge.is_earned ? 'Unlocked by:' : 'Unlock condition:'}
                </h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {selectedBadge.unlock_condition}
                </p>
              </div>
              
              {/* Progress or Earned Date */}
              {selectedBadge.is_earned && selectedBadge.earned_at ? (
                <p className="text-green-600 dark:text-green-400 font-medium">
                  ✓ Earned on {format(new Date(selectedBadge.earned_at), 'MMMM dd, yyyy')}
                </p>
              ) : selectedBadge.progress_current !== undefined && (
                <div>
                  <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400 mb-2">
                    <span>Progress</span>
                    <span>{selectedBadge.progress_current}/{selectedBadge.progress_total}</span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${getProgressPercentage(selectedBadge)}%` }}
                    />
                  </div>
                </div>
              )}
              
              {/* Close Button */}
              <button
                onClick={() => setSelectedBadge(null)}
                className="mt-6 w-full px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}