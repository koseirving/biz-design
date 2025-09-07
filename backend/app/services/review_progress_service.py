from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from app.models.user import User, UserOutput, UserProgress
from app.services.points_service import PointsService, EventType
import statistics
import logging

logger = logging.getLogger(__name__)


class ReviewProgressService:
    """Service for tracking and analyzing review progress and effectiveness"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def record_review_session(
        self,
        user: User,
        output: UserOutput,
        session_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Record a completed review session with detailed progress tracking"""
        
        logger.info(f"Recording review session for output {output.id} by user {user.id}")
        
        # Extract session information
        session_type = session_data.get('session_type', 'mixed')  # quiz, reflection, problems, mixed
        content_types = session_data.get('content_types', [])
        scores = session_data.get('scores', {})
        time_spent_minutes = session_data.get('time_spent_minutes', 0)
        completion_percentage = session_data.get('completion_percentage', 100)
        difficulty_rating = session_data.get('difficulty_rating', 3)  # 1-5 scale
        
        # Calculate overall session score
        overall_score = self._calculate_overall_score(scores, completion_percentage)
        
        # Update output with review session data
        output_data = output.output_data.copy()
        if 'review_sessions' not in output_data:
            output_data['review_sessions'] = []
        
        review_session = {
            'session_id': f"review_{datetime.utcnow().timestamp()}",
            'session_date': datetime.utcnow().isoformat(),
            'session_type': session_type,
            'content_types': content_types,
            'scores': scores,
            'overall_score': overall_score,
            'time_spent_minutes': time_spent_minutes,
            'completion_percentage': completion_percentage,
            'difficulty_rating': difficulty_rating,
            'performance_insights': self._analyze_session_performance(scores, time_spent_minutes)
        }
        
        output_data['review_sessions'].append(review_session)
        output.output_data = output_data
        self.db.commit()
        
        # Award points based on performance
        points_awarded = self._award_review_points(user, output, overall_score, session_type)
        
        # Track review streak
        streak_info = self._update_review_streak(user)
        
        # Calculate progress improvements
        progress_analysis = self._analyze_progress_trend(output_data['review_sessions'])
        
        return {
            'session_id': review_session['session_id'],
            'overall_score': overall_score,
            'points_awarded': points_awarded,
            'streak_info': streak_info,
            'progress_analysis': progress_analysis,
            'next_review_recommended': self._calculate_next_review_date(
                output_data['review_sessions'], overall_score
            ),
            'performance_insights': review_session['performance_insights']
        }
    
    def get_user_review_analytics(self, user: User, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive review analytics for a user"""
        
        # Get all user outputs with review sessions
        user_outputs = self.db.query(UserOutput).filter(
            UserOutput.user_id == user.id
        ).all()
        
        # Extract review sessions from all outputs
        all_sessions = []
        outputs_reviewed = 0
        
        for output in user_outputs:
            sessions = output.output_data.get('review_sessions', [])
            if sessions:
                outputs_reviewed += 1
                for session in sessions:
                    session['output_id'] = str(output.id)
                    session['framework_name'] = output.output_data.get('framework_name', 'Unknown')
                    session['output_type'] = output.output_data.get('type', 'unknown')
                    all_sessions.append(session)
        
        # Filter sessions by date range
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        recent_sessions = [
            s for s in all_sessions
            if datetime.fromisoformat(s['session_date']) >= cutoff_date
        ]
        
        # Calculate analytics
        analytics = {
            'time_period_days': days,
            'total_outputs': len(user_outputs),
            'outputs_reviewed': outputs_reviewed,
            'review_coverage_percentage': round((outputs_reviewed / max(len(user_outputs), 1)) * 100, 1),
            'total_review_sessions': len(recent_sessions),
            'average_sessions_per_week': round((len(recent_sessions) / (days / 7)), 1),
            'total_time_spent_hours': round(sum(s.get('time_spent_minutes', 0) for s in recent_sessions) / 60, 1),
            'performance_trends': self._calculate_performance_trends(recent_sessions),
            'content_type_preferences': self._analyze_content_preferences(recent_sessions),
            'difficulty_comfort_zone': self._analyze_difficulty_preferences(recent_sessions),
            'learning_effectiveness': self._calculate_learning_effectiveness(all_sessions),
            'streak_analysis': self._analyze_review_streaks(user),
            'improvement_areas': self._identify_improvement_areas(recent_sessions),
            'achievements': self._calculate_review_achievements(all_sessions)
        }
        
        return analytics
    
    def get_framework_review_progress(self, user: User, framework_name: str) -> Dict[str, Any]:
        """Get review progress for a specific framework"""
        
        # Get all outputs for this framework
        framework_outputs = self.db.query(UserOutput).filter(
            and_(
                UserOutput.user_id == user.id,
                UserOutput.output_data.op('->>')('framework_name') == framework_name
            )
        ).all()
        
        if not framework_outputs:
            return {
                'framework_name': framework_name,
                'error': 'No outputs found for this framework'
            }
        
        # Analyze review sessions across all outputs
        all_sessions = []
        for output in framework_outputs:
            sessions = output.output_data.get('review_sessions', [])
            for session in sessions:
                session['output_id'] = str(output.id)
                all_sessions.append(session)
        
        # Calculate framework-specific metrics
        if all_sessions:
            avg_score = statistics.mean([s.get('overall_score', 0) for s in all_sessions])
            score_trend = self._calculate_score_trend([s.get('overall_score', 0) for s in all_sessions])
        else:
            avg_score = 0
            score_trend = 0
        
        return {
            'framework_name': framework_name,
            'total_outputs': len(framework_outputs),
            'outputs_reviewed': len([o for o in framework_outputs if o.output_data.get('review_sessions')]),
            'total_review_sessions': len(all_sessions),
            'average_score': round(avg_score, 1),
            'score_trend': score_trend,
            'mastery_level': self._calculate_mastery_level(avg_score, len(all_sessions)),
            'time_investment_hours': round(sum(s.get('time_spent_minutes', 0) for s in all_sessions) / 60, 1),
            'strong_areas': self._identify_framework_strengths(all_sessions),
            'improvement_opportunities': self._identify_framework_weaknesses(all_sessions),
            'next_review_priority': self._calculate_framework_review_priority(framework_outputs)
        }
    
    def get_learning_effectiveness_report(self, user: User) -> Dict[str, Any]:
        """Generate a comprehensive learning effectiveness report"""
        
        # Get all review sessions
        user_outputs = self.db.query(UserOutput).filter(UserOutput.user_id == user.id).all()
        all_sessions = []
        
        for output in user_outputs:
            sessions = output.output_data.get('review_sessions', [])
            for session in sessions:
                session['output_id'] = str(output.id)
                session['framework_name'] = output.output_data.get('framework_name', 'Unknown')
                session['days_since_creation'] = (
                    datetime.fromisoformat(session['session_date']) - output.created_at
                ).days
                all_sessions.append(session)
        
        if not all_sessions:
            return {
                'error': 'No review sessions found',
                'recommendations': ['Complete some framework analyses first', 'Start reviewing completed outputs']
            }
        
        # Calculate effectiveness metrics
        effectiveness_report = {
            'overall_effectiveness_score': self._calculate_overall_effectiveness(all_sessions),
            'retention_analysis': self._analyze_retention_patterns(all_sessions),
            'optimal_review_timing': self._find_optimal_review_intervals(all_sessions),
            'content_type_effectiveness': self._analyze_content_effectiveness(all_sessions),
            'learning_velocity': self._calculate_learning_velocity(all_sessions),
            'knowledge_retention_curve': self._model_retention_curve(all_sessions),
            'personalized_recommendations': self._generate_personalized_recommendations(all_sessions),
            'benchmark_comparison': self._compare_with_benchmarks(all_sessions)
        }
        
        return effectiveness_report
    
    def _calculate_overall_score(self, scores: Dict[str, Any], completion_percentage: float) -> float:
        """Calculate overall score for a review session"""
        
        if not scores:
            return completion_percentage
        
        # Weight different content types
        weights = {
            'quiz': 0.4,
            'reflection': 0.2,
            'problems': 0.3,
            'summary': 0.1
        }
        
        weighted_score = 0
        total_weight = 0
        
        for content_type, score in scores.items():
            weight = weights.get(content_type, 0.25)
            weighted_score += score * weight
            total_weight += weight
        
        if total_weight > 0:
            base_score = weighted_score / total_weight
        else:
            base_score = sum(scores.values()) / len(scores)
        
        # Factor in completion percentage
        return round(base_score * (completion_percentage / 100), 1)
    
    def _analyze_session_performance(self, scores: Dict[str, Any], time_spent: int) -> Dict[str, str]:
        """Analyze performance patterns in a review session"""
        
        insights = {}
        
        if scores:
            avg_score = sum(scores.values()) / len(scores)
            
            if avg_score >= 85:
                insights['performance'] = 'excellent'
            elif avg_score >= 70:
                insights['performance'] = 'good'
            elif avg_score >= 55:
                insights['performance'] = 'average'
            else:
                insights['performance'] = 'needs_improvement'
            
            # Identify strong and weak content types
            best_type = max(scores.keys(), key=lambda k: scores[k])
            worst_type = min(scores.keys(), key=lambda k: scores[k])
            
            insights['strongest_area'] = best_type
            insights['improvement_area'] = worst_type
        
        # Analyze time efficiency
        if time_spent > 0:
            if time_spent <= 10:
                insights['efficiency'] = 'very_efficient'
            elif time_spent <= 20:
                insights['efficiency'] = 'efficient'
            elif time_spent <= 30:
                insights['efficiency'] = 'average'
            else:
                insights['efficiency'] = 'needs_more_focus'
        
        return insights
    
    def _award_review_points(self, user: User, output: UserOutput, overall_score: float, session_type: str) -> int:
        """Award points based on review performance"""
        
        base_points = PointsService.POINTS_MAPPING[EventType.FRAMEWORK_REVIEW]
        
        # Bonus points for high performance
        if overall_score >= 90:
            bonus_multiplier = 1.5
        elif overall_score >= 80:
            bonus_multiplier = 1.25
        elif overall_score >= 70:
            bonus_multiplier = 1.1
        else:
            bonus_multiplier = 1.0
        
        total_points = int(base_points * bonus_multiplier)
        
        # Award the points
        points_awarded = PointsService.award_points(
            db=self.db,
            user=user,
            event_type=EventType.FRAMEWORK_REVIEW,
            entity_id=output.id,
            metadata={
                'overall_score': overall_score,
                'session_type': session_type,
                'bonus_multiplier': bonus_multiplier
            },
            custom_points=total_points
        )
        
        return points_awarded
    
    def _update_review_streak(self, user: User) -> Dict[str, Any]:
        """Update and track user's review streak"""
        
        # Get recent review activity
        recent_activity = self.db.query(UserProgress).filter(
            and_(
                UserProgress.user_id == user.id,
                UserProgress.event_type == EventType.FRAMEWORK_REVIEW.value,
                UserProgress.created_at >= datetime.utcnow() - timedelta(days=30)
            )
        ).order_by(desc(UserProgress.created_at)).all()
        
        if not recent_activity:
            return {'current_streak': 0, 'longest_streak': 0}
        
        # Calculate current streak
        current_streak = 1  # Today's review
        yesterday = datetime.utcnow().date() - timedelta(days=1)
        
        for activity in recent_activity[1:]:  # Skip today's activity
            activity_date = activity.created_at.date()
            if activity_date == yesterday:
                current_streak += 1
                yesterday -= timedelta(days=1)
            else:
                break
        
        # Award streak bonus points if applicable
        if current_streak >= 3:
            PointsService.award_points(
                db=self.db,
                user=user,
                event_type=EventType.REVIEW_STREAK,
                metadata={'review_streak_days': current_streak}
            )
        
        return {
            'current_streak': current_streak,
            'longest_streak': self._calculate_longest_streak(recent_activity),
            'streak_bonus_awarded': current_streak >= 3
        }
    
    def _analyze_progress_trend(self, sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze progress trend across review sessions"""
        
        if len(sessions) < 2:
            return {'trend': 'insufficient_data', 'improvement': 0}
        
        # Sort sessions by date
        sorted_sessions = sorted(sessions, key=lambda x: x['session_date'])
        scores = [s.get('overall_score', 0) for s in sorted_sessions]
        
        # Calculate trend
        if len(scores) >= 3:
            recent_avg = statistics.mean(scores[-3:])
            early_avg = statistics.mean(scores[:3])
            improvement = recent_avg - early_avg
        else:
            improvement = scores[-1] - scores[0]
        
        if improvement > 10:
            trend = 'improving_strongly'
        elif improvement > 5:
            trend = 'improving'
        elif improvement > -5:
            trend = 'stable'
        elif improvement > -10:
            trend = 'declining'
        else:
            trend = 'declining_significantly'
        
        return {
            'trend': trend,
            'improvement': round(improvement, 1),
            'consistency': self._calculate_score_consistency(scores)
        }
    
    def _calculate_next_review_date(self, sessions: List[Dict[str, Any]], latest_score: float) -> str:
        """Calculate optimal next review date based on performance"""
        
        base_interval_days = 7  # Default weekly review
        
        # Adjust based on latest performance
        if latest_score >= 90:
            interval_days = 14  # Extended interval for excellent performance
        elif latest_score >= 80:
            interval_days = 10  # Slightly extended
        elif latest_score >= 70:
            interval_days = 7   # Standard interval
        elif latest_score >= 60:
            interval_days = 5   # Shortened interval
        else:
            interval_days = 3   # Frequent reviews needed
        
        # Consider review frequency
        if len(sessions) >= 3:
            avg_improvement = self._calculate_improvement_rate(sessions)
            if avg_improvement > 5:
                interval_days = min(interval_days + 2, 14)  # Extend if improving well
            elif avg_improvement < -5:
                interval_days = max(interval_days - 2, 3)   # Shorten if declining
        
        next_review_date = datetime.utcnow() + timedelta(days=interval_days)
        return next_review_date.isoformat()
    
    def _calculate_performance_trends(self, sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate performance trends across sessions"""
        
        if not sessions:
            return {}
        
        scores = [s.get('overall_score', 0) for s in sessions]
        times = [s.get('time_spent_minutes', 0) for s in sessions]
        
        return {
            'average_score': round(statistics.mean(scores), 1),
            'score_improvement': self._calculate_score_trend(scores),
            'consistency': round(100 - (statistics.stdev(scores) if len(scores) > 1 else 0), 1),
            'efficiency_trend': self._calculate_efficiency_trend(scores, times),
            'best_performance': max(scores),
            'most_recent_score': scores[-1] if scores else 0
        }
    
    def _calculate_score_trend(self, scores: List[float]) -> float:
        """Calculate the trend in scores (positive = improving)"""
        
        if len(scores) < 2:
            return 0
        
        # Simple linear trend calculation
        n = len(scores)
        sum_x = sum(range(n))
        sum_y = sum(scores)
        sum_xy = sum(i * scores[i] for i in range(n))
        sum_x2 = sum(i * i for i in range(n))
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        return round(slope, 2)
    
    def _calculate_score_consistency(self, scores: List[float]) -> float:
        """Calculate consistency score (0-100, higher is more consistent)"""
        
        if len(scores) < 2:
            return 100
        
        std_dev = statistics.stdev(scores)
        mean_score = statistics.mean(scores)
        
        # Convert to consistency percentage
        if mean_score > 0:
            consistency = max(0, 100 - (std_dev / mean_score) * 100)
        else:
            consistency = 0
        
        return round(consistency, 1)
    
    def _calculate_improvement_rate(self, sessions: List[Dict[str, Any]]) -> float:
        """Calculate rate of improvement across sessions"""
        
        if len(sessions) < 2:
            return 0
        
        scores = [s.get('overall_score', 0) for s in sessions]
        first_half = scores[:len(scores)//2]
        second_half = scores[len(scores)//2:]
        
        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)
        
        return second_avg - first_avg
    
    def _calculate_efficiency_trend(self, scores: List[float], times: List[int]) -> str:
        """Calculate efficiency trend (score per minute)"""
        
        if not scores or not times:
            return 'unknown'
        
        efficiencies = [s/max(t, 1) for s, t in zip(scores, times)]
        
        if len(efficiencies) < 2:
            return 'insufficient_data'
        
        trend = self._calculate_score_trend(efficiencies)
        
        if trend > 0.1:
            return 'improving'
        elif trend < -0.1:
            return 'declining'
        else:
            return 'stable'
    
    def _analyze_content_preferences(self, sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze user preferences for different content types"""
        
        content_stats = {}
        
        for session in sessions:
            for content_type in session.get('content_types', []):
                if content_type not in content_stats:
                    content_stats[content_type] = {'count': 0, 'total_score': 0}
                
                content_stats[content_type]['count'] += 1
                content_stats[content_type]['total_score'] += session.get('overall_score', 0)
        
        # Calculate averages and preferences
        preferences = {}
        for content_type, stats in content_stats.items():
            preferences[content_type] = {
                'frequency': stats['count'],
                'average_score': round(stats['total_score'] / stats['count'], 1),
                'preference_score': stats['count'] * (stats['total_score'] / stats['count'])
            }
        
        return preferences
    
    def _analyze_difficulty_preferences(self, sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze user's comfort with different difficulty levels"""
        
        difficulty_stats = {1: [], 2: [], 3: [], 4: [], 5: []}
        
        for session in sessions:
            difficulty = session.get('difficulty_rating', 3)
            score = session.get('overall_score', 0)
            difficulty_stats[difficulty].append(score)
        
        comfort_zone = {}
        for level, scores in difficulty_stats.items():
            if scores:
                comfort_zone[f'level_{level}'] = {
                    'average_score': round(statistics.mean(scores), 1),
                    'session_count': len(scores),
                    'comfort_level': 'high' if statistics.mean(scores) > 75 else 'medium' if statistics.mean(scores) > 60 else 'low'
                }
        
        return comfort_zone
    
    def _calculate_learning_effectiveness(self, sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall learning effectiveness metrics"""
        
        if not sessions:
            return {'effectiveness_score': 0, 'insights': []}
        
        # Sort sessions chronologically
        sorted_sessions = sorted(sessions, key=lambda x: x['session_date'])
        
        # Calculate various effectiveness metrics
        score_progression = [s.get('overall_score', 0) for s in sorted_sessions]
        time_efficiency = [s.get('overall_score', 0) / max(s.get('time_spent_minutes', 1), 1) for s in sorted_sessions]
        
        effectiveness_score = (
            statistics.mean(score_progression) * 0.4 +  # Overall performance
            self._calculate_score_trend(score_progression) * 10 * 0.3 +  # Improvement trend
            statistics.mean(time_efficiency) * 10 * 0.3  # Efficiency
        )
        
        insights = []
        if self._calculate_score_trend(score_progression) > 2:
            insights.append("Strong learning progression detected")
        if statistics.mean(time_efficiency) > 3:
            insights.append("Efficient learning approach")
        if len(sorted_sessions) >= 10:
            insights.append("Consistent review practice established")
        
        return {
            'effectiveness_score': round(max(0, min(100, effectiveness_score)), 1),
            'insights': insights,
            'total_sessions': len(sessions),
            'average_score': round(statistics.mean(score_progression), 1),
            'improvement_rate': round(self._calculate_score_trend(score_progression), 2)
        }
    
    def _analyze_review_streaks(self, user: User) -> Dict[str, Any]:
        """Analyze review streak patterns"""
        
        # Get all review activities
        activities = self.db.query(UserProgress).filter(
            and_(
                UserProgress.user_id == user.id,
                UserProgress.event_type == EventType.FRAMEWORK_REVIEW.value
            )
        ).order_by(UserProgress.created_at.desc()).all()
        
        if not activities:
            return {'current_streak': 0, 'longest_streak': 0, 'streak_pattern': 'none'}
        
        # Calculate streaks
        current_streak = self._calculate_current_streak(activities)
        longest_streak = self._calculate_longest_streak(activities)
        
        # Analyze pattern
        if current_streak >= 7:
            pattern = 'excellent_consistency'
        elif current_streak >= 3:
            pattern = 'good_consistency'
        elif longest_streak >= 7:
            pattern = 'intermittent_but_capable'
        else:
            pattern = 'needs_consistency'
        
        return {
            'current_streak': current_streak,
            'longest_streak': longest_streak,
            'streak_pattern': pattern,
            'total_review_days': len(set(a.created_at.date() for a in activities))
        }
    
    def _calculate_current_streak(self, activities: List[UserProgress]) -> int:
        """Calculate current consecutive review streak"""
        
        if not activities:
            return 0
        
        today = datetime.utcnow().date()
        streak = 0
        current_date = today
        
        # Group activities by date
        activity_dates = set(a.created_at.date() for a in activities)
        
        # Count consecutive days backwards from today
        while current_date in activity_dates:
            streak += 1
            current_date -= timedelta(days=1)
        
        return streak
    
    def _calculate_longest_streak(self, activities: List[UserProgress]) -> int:
        """Calculate longest review streak ever"""
        
        if not activities:
            return 0
        
        # Get unique activity dates
        activity_dates = sorted(set(a.created_at.date() for a in activities))
        
        if not activity_dates:
            return 0
        
        longest_streak = 1
        current_streak = 1
        
        for i in range(1, len(activity_dates)):
            if (activity_dates[i] - activity_dates[i-1]).days == 1:
                current_streak += 1
                longest_streak = max(longest_streak, current_streak)
            else:
                current_streak = 1
        
        return longest_streak
    
    def _identify_improvement_areas(self, sessions: List[Dict[str, Any]]) -> List[str]:
        """Identify areas where user can improve"""
        
        areas = []
        
        if not sessions:
            return ['Start completing review sessions']
        
        # Analyze performance patterns
        avg_score = statistics.mean([s.get('overall_score', 0) for s in sessions])
        if avg_score < 70:
            areas.append('Overall performance needs improvement')
        
        # Analyze consistency
        scores = [s.get('overall_score', 0) for s in sessions]
        if len(scores) > 1 and statistics.stdev(scores) > 20:
            areas.append('Work on consistency across sessions')
        
        # Analyze time efficiency
        avg_time = statistics.mean([s.get('time_spent_minutes', 0) for s in sessions])
        if avg_time > 30:
            areas.append('Consider more focused review sessions')
        
        # Analyze content type performance
        content_scores = {}
        for session in sessions:
            for content_type, score in session.get('scores', {}).items():
                if content_type not in content_scores:
                    content_scores[content_type] = []
                content_scores[content_type].append(score)
        
        for content_type, scores in content_scores.items():
            if statistics.mean(scores) < 60:
                areas.append(f'Focus on improving {content_type} performance')
        
        return areas
    
    def _calculate_review_achievements(self, sessions: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Calculate achievements based on review activity"""
        
        achievements = []
        
        if len(sessions) >= 1:
            achievements.append({
                'title': 'First Review',
                'description': 'Completed your first review session'
            })
        
        if len(sessions) >= 10:
            achievements.append({
                'title': 'Dedicated Reviewer',
                'description': 'Completed 10 review sessions'
            })
        
        scores = [s.get('overall_score', 0) for s in sessions]
        if scores and max(scores) >= 95:
            achievements.append({
                'title': 'Perfect Score',
                'description': 'Achieved a perfect review score'
            })
        
        if len(scores) > 5 and statistics.mean(scores[-5:]) >= 85:
            achievements.append({
                'title': 'Consistent Excellence',
                'description': 'Maintained high performance over recent sessions'
            })
        
        return achievements