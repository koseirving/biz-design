'use client'

import React, { useState, useEffect } from 'react'
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { format, subDays, startOfDay, endOfDay } from 'date-fns'

interface PointsData {
  date: string
  points: number
  cumulative_points: number
  breakdown: {
    content_view: number
    framework_completion: number
    ai_interaction: number
    output_creation: number
    streak_bonus: number
    review_completion: number
    other: number
  }
}

interface PointsChartProps {
  userId?: string
  period?: 'week' | 'month' | 'quarter' | 'year'
  chartType?: 'line' | 'area' | 'bar'
  showBreakdown?: boolean
  height?: number
}

const eventTypeColors = {
  content_view: '#8B5CF6',
  framework_completion: '#10B981',
  ai_interaction: '#F59E0B',
  output_creation: '#EF4444',
  streak_bonus: '#F97316',
  review_completion: '#3B82F6',
  other: '#6B7280'
}

const eventTypeLabels = {
  content_view: 'Content Views',
  framework_completion: 'Framework Completion',
  ai_interaction: 'AI Interactions',
  output_creation: 'Output Creation',
  streak_bonus: 'Streak Bonuses',
  review_completion: 'Review Completion',
  other: 'Other'
}

export default function PointsChart({
  userId,
  period = 'month',
  chartType = 'area',
  showBreakdown = true,
  height = 400
}: PointsChartProps) {
  const [pointsData, setPointsData] = useState<PointsData[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedPeriod, setSelectedPeriod] = useState(period)
  const [selectedChartType, setSelectedChartType] = useState(chartType)
  const [totalPoints, setTotalPoints] = useState(0)
  const [averageDaily, setAverageDaily] = useState(0)
  const [bestDay, setBestDay] = useState<{ date: string; points: number } | null>(null)

  useEffect(() => {
    fetchPointsData()
  }, [userId, selectedPeriod])

  const fetchPointsData = async () => {
    try {
      setLoading(true)
      const response = await fetch(`/api/proxy/users/me/points/history?period=${selectedPeriod}`, {
        method: 'GET',
        credentials: 'include'
      })
      
      if (!response.ok) {
        throw new Error('Failed to fetch points data')
      }
      
      const data = await response.json()
      const formattedData = data.points_history?.map((item: any) => ({
        ...item,
        date: format(new Date(item.date), 'MMM dd')
      })) || []
      
      setPointsData(formattedData)
      calculateStats(formattedData)
    } catch (error) {
      console.error('Error fetching points data:', error)
      // Fallback to mock data for demonstration
      generateMockData()
    } finally {
      setLoading(false)
    }
  }

  const generateMockData = () => {
    const days = selectedPeriod === 'week' ? 7 : selectedPeriod === 'month' ? 30 : selectedPeriod === 'quarter' ? 90 : 365
    const mockData: PointsData[] = []
    let cumulativePoints = 0

    for (let i = days - 1; i >= 0; i--) {
      const date = subDays(new Date(), i)
      const dailyPoints = Math.floor(Math.random() * 150) + 10
      cumulativePoints += dailyPoints

      mockData.push({
        date: format(date, 'MMM dd'),
        points: dailyPoints,
        cumulative_points: cumulativePoints,
        breakdown: {
          content_view: Math.floor(Math.random() * 30),
          framework_completion: Math.floor(Math.random() * 50),
          ai_interaction: Math.floor(Math.random() * 20),
          output_creation: Math.floor(Math.random() * 100),
          streak_bonus: Math.floor(Math.random() * 25),
          review_completion: Math.floor(Math.random() * 30),
          other: Math.floor(Math.random() * 15)
        }
      })
    }

    setPointsData(mockData)
    calculateStats(mockData)
  }

  const calculateStats = (data: PointsData[]) => {
    const total = data.reduce((sum, item) => sum + item.points, 0)
    const average = data.length > 0 ? total / data.length : 0
    const best = data.reduce((max, item) => 
      item.points > (max?.points || 0) ? item : max, 
      null as { date: string; points: number } | null
    )

    setTotalPoints(total)
    setAverageDaily(Math.round(average))
    setBestDay(best)
  }

  const getBreakdownData = () => {
    const totals = pointsData.reduce((acc, day) => {
      Object.entries(day.breakdown).forEach(([key, value]) => {
        acc[key] = (acc[key] || 0) + value
      })
      return acc
    }, {} as Record<string, number>)

    return Object.entries(totals).map(([key, value]) => ({
      name: eventTypeLabels[key as keyof typeof eventTypeLabels] || key,
      value,
      color: eventTypeColors[key as keyof typeof eventTypeColors] || '#6B7280'
    }))
  }

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3 shadow-lg">
          <p className="font-medium text-gray-900 dark:text-white">{`${label}`}</p>
          <p className="text-blue-600">
            {`Points: ${payload[0].value}`}
          </p>
          {payload[0].payload.breakdown && (
            <div className="mt-2 text-xs">
              {Object.entries(payload[0].payload.breakdown).map(([key, value]) => (
                <div key={key} className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">
                    {eventTypeLabels[key as keyof typeof eventTypeLabels] || key}:
                  </span>
                  <span className="ml-2 font-medium" style={{ color: eventTypeColors[key as keyof typeof eventTypeColors] }}>
                    {value}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )
    }
    return null
  }

  const renderChart = () => {
    const commonProps = {
      data: pointsData,
      height,
      margin: { top: 5, right: 30, left: 20, bottom: 5 }
    }

    switch (selectedChartType) {
      case 'line':
        return (
          <LineChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
            <XAxis dataKey="date" className="text-xs" />
            <YAxis className="text-xs" />
            <Tooltip content={<CustomTooltip />} />
            <Line 
              type="monotone" 
              dataKey="points" 
              stroke="#3B82F6" 
              strokeWidth={3}
              dot={{ fill: '#3B82F6', strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6, stroke: '#3B82F6', strokeWidth: 2 }}
            />
          </LineChart>
        )
      
      case 'area':
        return (
          <AreaChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
            <XAxis dataKey="date" className="text-xs" />
            <YAxis className="text-xs" />
            <Tooltip content={<CustomTooltip />} />
            <Area 
              type="monotone" 
              dataKey="points" 
              stroke="#3B82F6" 
              fill="#3B82F6" 
              fillOpacity={0.6}
            />
          </AreaChart>
        )
      
      case 'bar':
        return (
          <BarChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
            <XAxis dataKey="date" className="text-xs" />
            <YAxis className="text-xs" />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="points" fill="#3B82F6" radius={[4, 4, 0, 0]} />
          </BarChart>
        )
      
      default:
        return null
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  const breakdownData = getBreakdownData()

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4 sm:mb-0">
          Points History
        </h2>
        
        <div className="flex flex-col sm:flex-row gap-2">
          <select
            value={selectedPeriod}
            onChange={(e) => setSelectedPeriod(e.target.value as any)}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700"
          >
            <option value="week">Last Week</option>
            <option value="month">Last Month</option>
            <option value="quarter">Last Quarter</option>
            <option value="year">Last Year</option>
          </select>
          
          <select
            value={selectedChartType}
            onChange={(e) => setSelectedChartType(e.target.value as any)}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700"
          >
            <option value="area">Area Chart</option>
            <option value="line">Line Chart</option>
            <option value="bar">Bar Chart</option>
          </select>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
          <h3 className="text-sm font-medium text-blue-600 dark:text-blue-400">Total Points</h3>
          <p className="text-2xl font-bold text-blue-700 dark:text-blue-300">{totalPoints.toLocaleString()}</p>
        </div>
        
        <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
          <h3 className="text-sm font-medium text-green-600 dark:text-green-400">Daily Average</h3>
          <p className="text-2xl font-bold text-green-700 dark:text-green-300">{averageDaily}</p>
        </div>
        
        <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4">
          <h3 className="text-sm font-medium text-purple-600 dark:text-purple-400">Best Day</h3>
          <p className="text-lg font-bold text-purple-700 dark:text-purple-300">
            {bestDay ? `${bestDay.points} pts` : 'N/A'}
          </p>
          {bestDay && (
            <p className="text-xs text-purple-600 dark:text-purple-400">{bestDay.date}</p>
          )}
        </div>
      </div>

      {/* Main Chart */}
      <div className="mb-6">
        <ResponsiveContainer width="100%" height={height}>
          {renderChart()}
        </ResponsiveContainer>
      </div>

      {/* Points Breakdown */}
      {showBreakdown && breakdownData.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Breakdown Pie Chart */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Points Breakdown
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={breakdownData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {breakdownData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Breakdown List */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Activity Details
            </h3>
            <div className="space-y-3">
              {breakdownData
                .sort((a, b) => b.value - a.value)
                .map((item) => (
                  <div key={item.name} className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div 
                        className="w-4 h-4 rounded-full"
                        style={{ backgroundColor: item.color }}
                      />
                      <span className="text-sm text-gray-700 dark:text-gray-300">
                        {item.name}
                      </span>
                    </div>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {item.value} pts
                    </span>
                  </div>
                ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}