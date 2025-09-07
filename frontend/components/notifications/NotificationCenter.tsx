'use client'

import React, { useState, useEffect, useRef } from 'react'
import { io, Socket } from 'socket.io-client'
import { format, formatDistanceToNow } from 'date-fns'

interface Notification {
  id: string
  type: 'notification' | 'system_announcement' | 'achievement_unlock' | 'review_reminder' | 'progress_update'
  title: string
  message: string
  content?: any
  read: boolean
  created_at: string
  priority: 'low' | 'normal' | 'high'
  action_url?: string
  dismissible: boolean
}

interface NotificationCenterProps {
  userId: string
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left'
  maxNotifications?: number
  autoConnect?: boolean
}

const notificationIcons = {
  notification: '📢',
  system_announcement: '🔔',
  achievement_unlock: '🏆',
  review_reminder: '📚',
  progress_update: '🎯'
}

const priorityColors = {
  low: 'border-gray-300 bg-gray-50',
  normal: 'border-blue-300 bg-blue-50',
  high: 'border-red-300 bg-red-50'
}

export default function NotificationCenter({
  userId,
  position = 'top-right',
  maxNotifications = 10,
  autoConnect = true
}: NotificationCenterProps) {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [isOpen, setIsOpen] = useState(false)
  const [filter, setFilter] = useState<'all' | 'unread' | 'achievements' | 'reviews'>('all')
  const [loading, setLoading] = useState(true)
  const [connected, setConnected] = useState(false)
  
  const socketRef = useRef<Socket | null>(null)
  const bellRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    fetchNotifications()
    if (autoConnect) {
      connectWebSocket()
    }

    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect()
      }
    }
  }, [userId])

  const connectWebSocket = async () => {
    try {
      // Get auth token from cookies or session
      const response = await fetch('/api/auth/token', {
        method: 'GET',
        credentials: 'include'
      })
      
      if (!response.ok) {
        throw new Error('Failed to get auth token')
      }
      
      const { token } = await response.json()
      
      // Connect to WebSocket
      const socket = io(`ws://localhost:8000/realtime/ws/${userId}`, {
        query: { token },
        transports: ['websocket']
      })

      socket.on('connect', () => {
        setConnected(true)
        console.log('Connected to notification WebSocket')
      })

      socket.on('disconnect', () => {
        setConnected(false)
        console.log('Disconnected from notification WebSocket')
      })

      socket.on('notification', (data) => {
        handleNewNotification(data)
      })

      socket.on('system_announcement', (data) => {
        handleNewNotification({
          ...data,
          type: 'system_announcement'
        })
      })

      socketRef.current = socket

    } catch (error) {
      console.error('Failed to connect to WebSocket:', error)
    }
  }

  const fetchNotifications = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/proxy/realtime/notifications/unread', {
        method: 'GET',
        credentials: 'include'
      })
      
      if (!response.ok) {
        throw new Error('Failed to fetch notifications')
      }
      
      const data = await response.json()
      setNotifications(data.unread_notifications || [])
      setUnreadCount(data.total_count || 0)
    } catch (error) {
      console.error('Error fetching notifications:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleNewNotification = (notification: any) => {
    const newNotification: Notification = {
      id: notification.id || `temp-${Date.now()}`,
      type: notification.type || 'notification',
      title: notification.content?.title || 'New Notification',
      message: notification.content?.message || notification.message || '',
      content: notification.content,
      read: false,
      created_at: notification.timestamp || new Date().toISOString(),
      priority: notification.content?.priority || 'normal',
      action_url: notification.content?.action_url,
      dismissible: notification.content?.dismissible !== false
    }

    setNotifications(prev => [newNotification, ...prev.slice(0, maxNotifications - 1)])
    setUnreadCount(prev => prev + 1)

    // Show browser notification if permission granted
    if (Notification.permission === 'granted') {
      new Notification(newNotification.title, {
        body: newNotification.message,
        icon: '/favicon.ico'
      })
    }

    // Animate bell icon
    if (bellRef.current) {
      bellRef.current.classList.add('animate-bounce')
      setTimeout(() => {
        bellRef.current?.classList.remove('animate-bounce')
      }, 1000)
    }
  }

  const markAsRead = async (notificationId: string) => {
    try {
      await fetch(`/api/proxy/realtime/notifications/${notificationId}/read`, {
        method: 'POST',
        credentials: 'include'
      })
      
      setNotifications(prev => 
        prev.map(notif => 
          notif.id === notificationId 
            ? { ...notif, read: true }
            : notif
        )
      )
      
      setUnreadCount(prev => Math.max(0, prev - 1))
    } catch (error) {
      console.error('Error marking notification as read:', error)
    }
  }

  const markAllAsRead = async () => {
    try {
      const unreadNotifications = notifications.filter(n => !n.read)
      
      await Promise.all(
        unreadNotifications.map(notif => 
          fetch(`/api/proxy/realtime/notifications/${notif.id}/read`, {
            method: 'POST',
            credentials: 'include'
          })
        )
      )
      
      setNotifications(prev => prev.map(notif => ({ ...notif, read: true })))
      setUnreadCount(0)
    } catch (error) {
      console.error('Error marking all notifications as read:', error)
    }
  }

  const dismissNotification = (notificationId: string) => {
    setNotifications(prev => prev.filter(notif => notif.id !== notificationId))
    setUnreadCount(prev => {
      const notification = notifications.find(n => n.id === notificationId)
      return notification && !notification.read ? Math.max(0, prev - 1) : prev
    })
  }

  const handleNotificationClick = (notification: Notification) => {
    if (!notification.read) {
      markAsRead(notification.id)
    }
    
    if (notification.action_url) {
      window.location.href = notification.action_url
    }
  }

  const requestNotificationPermission = async () => {
    if (Notification.permission === 'default') {
      await Notification.requestPermission()
    }
  }

  const filteredNotifications = notifications.filter(notification => {
    switch (filter) {
      case 'unread':
        return !notification.read
      case 'achievements':
        return notification.type === 'achievement_unlock'
      case 'reviews':
        return notification.type === 'review_reminder'
      default:
        return true
    }
  })

  const getPositionClasses = () => {
    const baseClasses = 'fixed z-50'
    switch (position) {
      case 'top-right':
        return `${baseClasses} top-4 right-4`
      case 'top-left':
        return `${baseClasses} top-4 left-4`
      case 'bottom-right':
        return `${baseClasses} bottom-4 right-4`
      case 'bottom-left':
        return `${baseClasses} bottom-4 left-4`
      default:
        return `${baseClasses} top-4 right-4`
    }
  }

  return (
    <div className={getPositionClasses()}>
      {/* Notification Bell */}
      <button
        ref={bellRef}
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-3 bg-white dark:bg-gray-800 rounded-full shadow-lg border border-gray-200 dark:border-gray-700 hover:shadow-xl transition-all duration-200"
      >
        <svg className="w-6 h-6 text-gray-700 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-4.5-4.5M9 17H4l4.5-4.5M12 17V7a5 5 0 00-10 0v10a1 1 0 001 1h2m4-11v10a1 1 0 001 1h2m-4-11a5 5 0 0110 0v10" />
        </svg>
        
        {/* Unread Badge */}
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
        
        {/* Connection Status */}
        <div className={`absolute -bottom-1 -right-1 w-3 h-3 rounded-full ${
          connected ? 'bg-green-400' : 'bg-gray-400'
        }`} />
      </button>

      {/* Notification Panel */}
      {isOpen && (
        <div className="absolute top-16 right-0 w-96 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 max-h-96 overflow-hidden">
          {/* Header */}
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Notifications
              </h3>
              <div className="flex space-x-2">
                <button
                  onClick={requestNotificationPermission}
                  className="text-xs text-blue-600 hover:text-blue-700"
                  title="Enable browser notifications"
                >
                  🔔
                </button>
                <button
                  onClick={() => setIsOpen(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
            </div>
            
            {/* Filters */}
            <div className="flex space-x-2 text-xs">
              {['all', 'unread', 'achievements', 'reviews'].map(filterOption => (
                <button
                  key={filterOption}
                  onClick={() => setFilter(filterOption as any)}
                  className={`px-2 py-1 rounded-full transition-colors ${
                    filter === filterOption
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                  }`}
                >
                  {filterOption.charAt(0).toUpperCase() + filterOption.slice(1)}
                </button>
              ))}
            </div>
            
            {unreadCount > 0 && (
              <button
                onClick={markAllAsRead}
                className="mt-2 text-xs text-blue-600 hover:text-blue-700"
              >
                Mark all as read
              </button>
            )}
          </div>

          {/* Notifications List */}
          <div className="max-h-64 overflow-y-auto">
            {loading ? (
              <div className="p-4 text-center">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
              </div>
            ) : filteredNotifications.length === 0 ? (
              <div className="p-4 text-center text-gray-500 dark:text-gray-400">
                No notifications found
              </div>
            ) : (
              filteredNotifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`p-4 border-b border-gray-100 dark:border-gray-700 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors ${
                    !notification.read ? 'bg-blue-50 dark:bg-blue-900/10' : ''
                  }`}
                  onClick={() => handleNotificationClick(notification)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3">
                      <div className="text-lg">
                        {notificationIcons[notification.type] || '📢'}
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <p className={`text-sm font-medium ${
                          !notification.read 
                            ? 'text-gray-900 dark:text-white' 
                            : 'text-gray-700 dark:text-gray-300'
                        }`}>
                          {notification.title}
                        </p>
                        
                        <p className="text-xs text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">
                          {notification.message}
                        </p>
                        
                        <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                          {formatDistanceToNow(new Date(notification.created_at), { addSuffix: true })}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-1">
                      {!notification.read && (
                        <div className="w-2 h-2 bg-blue-500 rounded-full" />
                      )}
                      
                      {notification.dismissible && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            dismissNotification(notification.id)
                          }}
                          className="text-gray-400 hover:text-gray-600 text-xs p-1"
                        >
                          ✕
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}