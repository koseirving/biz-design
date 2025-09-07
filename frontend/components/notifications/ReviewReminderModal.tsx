'use client'

import React, { useState, useEffect } from 'react'
import { format } from 'date-fns'

interface QuizQuestion {
  id: string
  question: string
  options: string[]
  correct_answer: number
  explanation?: string
}

interface ReviewContent {
  quiz: {
    questions: QuizQuestion[]
    total_questions: number
  }
  summary: {
    key_points: string[]
    main_takeaways: string[]
  }
  reflection: {
    questions: string[]
  }
  application: {
    problems: Array<{
      scenario: string
      task: string
      suggested_approach?: string
    }>
  }
}

interface ReviewReminderModalProps {
  isOpen: boolean
  outputId: string
  frameworkName: string
  daysAfterCompletion: number
  onComplete: (sessionData: any) => void
  onSkip: () => void
  onClose: () => void
}

type ReviewSection = 'quiz' | 'summary' | 'reflection' | 'application'

export default function ReviewReminderModal({
  isOpen,
  outputId,
  frameworkName,
  daysAfterCompletion,
  onComplete,
  onSkip,
  onClose
}: ReviewReminderModalProps) {
  const [reviewContent, setReviewContent] = useState<ReviewContent | null>(null)
  const [loading, setLoading] = useState(false)
  const [currentSection, setCurrentSection] = useState<ReviewSection>('quiz')
  const [quizAnswers, setQuizAnswers] = useState<Record<string, number>>({})
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [showQuizResults, setShowQuizResults] = useState(false)
  const [reflectionAnswers, setReflectionAnswers] = useState<Record<number, string>>({})
  const [sessionStartTime] = useState(new Date())
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    if (isOpen) {
      fetchReviewContent()
    }
  }, [isOpen, outputId])

  useEffect(() => {
    // Calculate progress based on current section and completion
    let sectionProgress = 0
    const totalSections = 4

    switch (currentSection) {
      case 'quiz':
        if (showQuizResults) {
          sectionProgress = 1
        } else {
          sectionProgress = Object.keys(quizAnswers).length / (reviewContent?.quiz.questions.length || 1)
        }
        setProgress((sectionProgress / totalSections) * 100)
        break
      case 'summary':
        setProgress(25 + (25 / totalSections))
        break
      case 'reflection':
        const answeredReflections = Object.keys(reflectionAnswers).length
        const totalReflections = reviewContent?.reflection.questions.length || 1
        sectionProgress = answeredReflections / totalReflections
        setProgress(50 + (sectionProgress / totalSections) * 100)
        break
      case 'application':
        setProgress(75 + (25 / totalSections))
        break
    }
  }, [currentSection, quizAnswers, showQuizResults, reflectionAnswers, reviewContent])

  const fetchReviewContent = async () => {
    try {
      setLoading(true)
      const response = await fetch(`/api/proxy/reviews/outputs/${outputId}/content`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({
          content_types: ['quiz', 'summary', 'reflection', 'application']
        })
      })
      
      if (!response.ok) {
        throw new Error('Failed to fetch review content')
      }
      
      const data = await response.json()
      setReviewContent(data.review_content)
    } catch (error) {
      console.error('Error fetching review content:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleQuizAnswer = (questionId: string, answerIndex: number) => {
    setQuizAnswers(prev => ({
      ...prev,
      [questionId]: answerIndex
    }))
  }

  const handleQuizSubmit = () => {
    setShowQuizResults(true)
  }

  const handleReflectionAnswer = (questionIndex: number, answer: string) => {
    setReflectionAnswers(prev => ({
      ...prev,
      [questionIndex]: answer
    }))
  }

  const calculateQuizScore = () => {
    if (!reviewContent?.quiz.questions) return 0
    
    let correct = 0
    reviewContent.quiz.questions.forEach(question => {
      if (quizAnswers[question.id] === question.correct_answer) {
        correct++
      }
    })
    
    return Math.round((correct / reviewContent.quiz.questions.length) * 100)
  }

  const handleComplete = async () => {
    const sessionData = {
      output_id: outputId,
      framework_name: frameworkName,
      review_type: 'ebbinghaus_review',
      days_after_completion: daysAfterCompletion,
      session_duration_minutes: Math.round((Date.now() - sessionStartTime.getTime()) / 60000),
      quiz_score: calculateQuizScore(),
      sections_completed: [currentSection],
      quiz_answers: quizAnswers,
      reflection_answers: reflectionAnswers,
      completion_rate: progress / 100
    }

    try {
      await fetch(`/api/proxy/reviews/outputs/${outputId}/session`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify(sessionData)
      })
      
      onComplete(sessionData)
    } catch (error) {
      console.error('Error recording review session:', error)
      onComplete(sessionData) // Still complete on frontend even if backend fails
    }
  }

  const nextSection = () => {
    const sections: ReviewSection[] = ['quiz', 'summary', 'reflection', 'application']
    const currentIndex = sections.indexOf(currentSection)
    if (currentIndex < sections.length - 1) {
      setCurrentSection(sections[currentIndex + 1])
    } else {
      handleComplete()
    }
  }

  const renderProgressBar = () => (
    <div className="mb-6">
      <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400 mb-2">
        <span>Review Progress</span>
        <span>{Math.round(progress)}% Complete</span>
      </div>
      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
        <div 
          className="bg-blue-500 h-2 rounded-full transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  )

  const renderQuizSection = () => {
    if (!reviewContent?.quiz.questions) return null

    if (showQuizResults) {
      const score = calculateQuizScore()
      return (
        <div className="text-center">
          <div className="text-6xl mb-4">
            {score >= 80 ? '🎉' : score >= 60 ? '👍' : '📚'}
          </div>
          <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            Quiz Complete!
          </h3>
          <p className="text-lg text-gray-600 dark:text-gray-400 mb-4">
            You scored {score}% ({Object.keys(quizAnswers).filter(qId => 
              quizAnswers[qId] === reviewContent.quiz.questions.find(q => q.id === qId)?.correct_answer
            ).length}/{reviewContent.quiz.questions.length})
          </p>
          
          {/* Show detailed results */}
          <div className="text-left max-h-64 overflow-y-auto mb-6">
            {reviewContent.quiz.questions.map((question, index) => {
              const userAnswer = quizAnswers[question.id]
              const isCorrect = userAnswer === question.correct_answer
              
              return (
                <div key={question.id} className="mb-4 p-3 border rounded-lg">
                  <p className="font-medium text-sm mb-2">{index + 1}. {question.question}</p>
                  <p className={`text-sm ${isCorrect ? 'text-green-600' : 'text-red-600'}`}>
                    Your answer: {question.options[userAnswer]} {isCorrect ? '✓' : '✗'}
                  </p>
                  {!isCorrect && (
                    <p className="text-sm text-green-600">
                      Correct: {question.options[question.correct_answer]}
                    </p>
                  )}
                  {question.explanation && (
                    <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                      {question.explanation}
                    </p>
                  )}
                </div>
              )
            })}
          </div>
          
          <button
            onClick={nextSection}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Continue to Summary
          </button>
        </div>
      )
    }

    const currentQuestion = reviewContent.quiz.questions[currentQuestionIndex]
    const allQuestionsAnswered = reviewContent.quiz.questions.every(q => q.id in quizAnswers)

    return (
      <div>
        <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
          📝 Knowledge Check
        </h3>
        
        <div className="mb-4">
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
            Question {currentQuestionIndex + 1} of {reviewContent.quiz.questions.length}
          </p>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1">
            <div 
              className="bg-blue-500 h-1 rounded-full transition-all"
              style={{ width: `${((currentQuestionIndex + 1) / reviewContent.quiz.questions.length) * 100}%` }}
            />
          </div>
        </div>

        <div className="mb-6">
          <h4 className="font-semibold text-gray-900 dark:text-white mb-4">
            {currentQuestion.question}
          </h4>
          
          <div className="space-y-2">
            {currentQuestion.options.map((option, index) => (
              <button
                key={index}
                onClick={() => handleQuizAnswer(currentQuestion.id, index)}
                className={`w-full text-left p-3 border rounded-lg transition-colors ${
                  quizAnswers[currentQuestion.id] === index
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-750'
                }`}
              >
                <span className="font-medium mr-3">{String.fromCharCode(65 + index)}.</span>
                {option}
              </button>
            ))}
          </div>
        </div>

        <div className="flex justify-between">
          <button
            onClick={() => setCurrentQuestionIndex(Math.max(0, currentQuestionIndex - 1))}
            disabled={currentQuestionIndex === 0}
            className="px-4 py-2 text-gray-600 dark:text-gray-400 disabled:opacity-50"
          >
            Previous
          </button>
          
          {currentQuestionIndex < reviewContent.quiz.questions.length - 1 ? (
            <button
              onClick={() => setCurrentQuestionIndex(currentQuestionIndex + 1)}
              disabled={!(currentQuestion.id in quizAnswers)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Next
            </button>
          ) : (
            <button
              onClick={handleQuizSubmit}
              disabled={!allQuestionsAnswered}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Submit Quiz
            </button>
          )}
        </div>
      </div>
    )
  }

  const renderSummarySection = () => (
    <div>
      <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
        📋 Key Points Summary
      </h3>
      
      <div className="mb-6">
        <h4 className="font-semibold text-gray-900 dark:text-white mb-3">Key Points:</h4>
        <ul className="space-y-2 mb-6">
          {reviewContent?.summary.key_points.map((point, index) => (
            <li key={index} className="flex items-start space-x-2">
              <span className="text-blue-500 mt-1">•</span>
              <span className="text-gray-700 dark:text-gray-300">{point}</span>
            </li>
          ))}
        </ul>
        
        <h4 className="font-semibold text-gray-900 dark:text-white mb-3">Main Takeaways:</h4>
        <ul className="space-y-2">
          {reviewContent?.summary.main_takeaways.map((takeaway, index) => (
            <li key={index} className="flex items-start space-x-2">
              <span className="text-green-500 mt-1">✓</span>
              <span className="text-gray-700 dark:text-gray-300">{takeaway}</span>
            </li>
          ))}
        </ul>
      </div>
      
      <button
        onClick={nextSection}
        className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors"
      >
        Continue to Reflection
      </button>
    </div>
  )

  const renderReflectionSection = () => (
    <div>
      <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
        🤔 Reflection Questions
      </h3>
      
      <div className="space-y-4 mb-6">
        {reviewContent?.reflection.questions.map((question, index) => (
          <div key={index} className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
            <label className="block font-medium text-gray-900 dark:text-white mb-2">
              {index + 1}. {question}
            </label>
            <textarea
              value={reflectionAnswers[index] || ''}
              onChange={(e) => handleReflectionAnswer(index, e.target.value)}
              className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg resize-none h-24 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="Share your thoughts..."
            />
          </div>
        ))}
      </div>
      
      <button
        onClick={nextSection}
        className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors"
      >
        Continue to Application
      </button>
    </div>
  )

  const renderApplicationSection = () => (
    <div>
      <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
        🎯 Real-World Application
      </h3>
      
      <div className="space-y-4 mb-6">
        {reviewContent?.application.problems.map((problem, index) => (
          <div key={index} className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
            <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
              Scenario {index + 1}
            </h4>
            <p className="text-gray-700 dark:text-gray-300 mb-3">{problem.scenario}</p>
            <p className="text-blue-600 dark:text-blue-400 mb-2">
              <strong>Task:</strong> {problem.task}
            </p>
            {problem.suggested_approach && (
              <details className="mt-2">
                <summary className="cursor-pointer text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200">
                  View suggested approach
                </summary>
                <p className="mt-2 text-sm text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-750 p-3 rounded">
                  {problem.suggested_approach}
                </p>
              </details>
            )}
          </div>
        ))}
      </div>
      
      <button
        onClick={handleComplete}
        className="w-full bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 transition-colors"
      >
        Complete Review
      </button>
    </div>
  )

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                📚 Review Time!
              </h2>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                {frameworkName} • Day {daysAfterCompletion} Review
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
            >
              ✕
            </button>
          </div>
          
          {renderProgressBar()}
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-96">
          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600 dark:text-gray-400">Generating your review content...</p>
            </div>
          ) : (
            <>
              {currentSection === 'quiz' && renderQuizSection()}
              {currentSection === 'summary' && renderSummarySection()}
              {currentSection === 'reflection' && renderReflectionSection()}
              {currentSection === 'application' && renderApplicationSection()}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-750">
          <div className="flex justify-between">
            <button
              onClick={onSkip}
              className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
            >
              Skip for now
            </button>
            
            <div className="text-sm text-gray-500 dark:text-gray-400">
              ⏱ Started {format(sessionStartTime, 'HH:mm')}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}