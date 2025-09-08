from typing import Dict, Any, Optional, List
from datetime import datetime
from app.models.user import User
import logging

logger = logging.getLogger(__name__)


class EmailTemplateService:
    """Service for managing email templates and content generation"""
    
    def __init__(self):
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load email templates for different notification types"""
        
        return {
            'review_reminder': {
                'subject': '📚 Time to Review: {framework_name}',
                'html_template': '''
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Review Reminder - Biz Design</title>
                    <style>
                        body {{
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                            line-height: 1.6;
                            color: #333;
                            max-width: 600px;
                            margin: 0 auto;
                            padding: 20px;
                            background-color: #f8f9fa;
                        }}
                        .container {{
                            background: white;
                            border-radius: 12px;
                            padding: 40px;
                            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                        }}
                        .header {{
                            text-align: center;
                            margin-bottom: 30px;
                        }}
                        .logo {{
                            font-size: 24px;
                            font-weight: bold;
                            color: #2563eb;
                            margin-bottom: 10px;
                        }}
                        .title {{
                            font-size: 28px;
                            margin: 20px 0;
                            color: #1f2937;
                        }}
                        .highlight-box {{
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            color: white;
                            padding: 25px;
                            border-radius: 8px;
                            margin: 25px 0;
                            text-align: center;
                        }}
                        .benefits {{
                            background: #f3f4f6;
                            padding: 20px;
                            border-radius: 8px;
                            margin: 20px 0;
                        }}
                        .benefits ul {{
                            margin: 10px 0;
                            padding-left: 20px;
                        }}
                        .benefits li {{
                            margin: 8px 0;
                        }}
                        .cta-button {{
                            display: inline-block;
                            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                            color: white;
                            padding: 15px 30px;
                            text-decoration: none;
                            border-radius: 8px;
                            font-weight: 600;
                            margin: 20px 0;
                            text-align: center;
                        }}
                        .cta-button:hover {{
                            background: linear-gradient(135deg, #059669 0%, #047857 100%);
                        }}
                        .stats {{
                            display: flex;
                            justify-content: space-around;
                            margin: 25px 0;
                            text-align: center;
                        }}
                        .stat {{
                            flex: 1;
                            padding: 15px;
                        }}
                        .stat-number {{
                            font-size: 24px;
                            font-weight: bold;
                            color: #2563eb;
                            display: block;
                        }}
                        .footer {{
                            text-align: center;
                            margin-top: 40px;
                            padding-top: 30px;
                            border-top: 1px solid #e5e7eb;
                            color: #6b7280;
                            font-size: 14px;
                        }}
                        @media (max-width: 600px) {{
                            body {{ padding: 10px; }}
                            .container {{ padding: 20px; }}
                            .stats {{ flex-direction: column; }}
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <div class="logo">🎯 Biz Design</div>
                            <h1 class="title">Time for Your Review!</h1>
                        </div>
                        
                        <div class="highlight-box">
                            <h2 style="margin: 0 0 10px 0;">📚 {framework_name}</h2>
                            <p style="margin: 0; font-size: 18px;">It's been <strong>{days_since_completion} days</strong> since you completed this {output_type}</p>
                        </div>
                        
                        <p>Hello <strong>{user_name}</strong>,</p>
                        
                        <p>Based on the <strong>Ebbinghaus forgetting curve</strong>, now is the optimal time to review your {framework_name} analysis to strengthen your long-term retention.</p>
                        
                        <div class="benefits">
                            <h3>🌟 Why Review Now?</h3>
                            <ul>
                                <li><strong>Strengthen memory retention</strong> - Combat natural forgetting</li>
                                <li><strong>Identify knowledge gaps</strong> - See what needs more focus</li>
                                <li><strong>Earn bonus points</strong> - Get rewarded for consistent learning</li>
                                <li><strong>Build expertise</strong> - Deepen your framework mastery</li>
                            </ul>
                        </div>
                        
                        <div style="text-align: center;">
                            <a href="{action_url}" class="cta-button">
                                🚀 Start Review Session
                            </a>
                        </div>
                        
                        <div class="stats">
                            <div class="stat">
                                <span class="stat-number">{interval_days}</span>
                                <span>Day Review</span>
                            </div>
                            <div class="stat">
                                <span class="stat-number">30+</span>
                                <span>Points Available</span>
                            </div>
                            <div class="stat">
                                <span class="stat-number">5-15</span>
                                <span>Minutes</span>
                            </div>
                        </div>
                        
                        <p><em>Consistent reviews help you retain 80% more information compared to single-time learning!</em></p>
                        
                        <div class="footer">
                            <p>Keep learning and growing! 🌱</p>
                            <p>The Biz Design Team</p>
                            <p style="margin-top: 20px;">
                                <a href="{unsubscribe_url}" style="color: #6b7280;">Unsubscribe</a> | 
                                <a href="{preferences_url}" style="color: #6b7280;">Notification Preferences</a>
                            </p>
                        </div>
                    </div>
                </body>
                </html>
                ''',
                'text_template': '''
                Time for Your Review! - Biz Design

                Hello {user_name},

                It's been {days_since_completion} days since you completed your {framework_name} {output_type}.

                Based on the Ebbinghaus forgetting curve, now is the optimal time to review this content to strengthen your long-term retention.

                Why Review Now?
                • Strengthen memory retention - Combat natural forgetting
                • Identify knowledge gaps - See what needs more focus
                • Earn bonus points - Get rewarded for consistent learning
                • Build expertise - Deepen your framework mastery

                Start your review session: {action_url}

                This {interval_days}-day review should take only 5-15 minutes and can earn you 30+ points!

                Consistent reviews help you retain 80% more information compared to single-time learning!

                Keep learning and growing!
                The Biz Design Team

                Unsubscribe: {unsubscribe_url}
                Notification Preferences: {preferences_url}
                '''
            },
            
            'achievement_unlock': {
                'subject': '🎉 Achievement Unlocked: {achievement_name}!',
                'html_template': '''
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Achievement Unlocked - Biz Design</title>
                    <style>
                        body {{
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                            line-height: 1.6;
                            color: #333;
                            max-width: 600px;
                            margin: 0 auto;
                            padding: 20px;
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            min-height: 100vh;
                        }}
                        .container {{
                            background: white;
                            border-radius: 12px;
                            padding: 40px;
                            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                            text-align: center;
                        }}
                        .achievement-badge {{
                            font-size: 80px;
                            margin: 20px 0;
                        }}
                        .title {{
                            font-size: 32px;
                            margin: 20px 0;
                            color: #1f2937;
                        }}
                        .celebration {{
                            font-size: 60px;
                            margin: 20px 0;
                            animation: bounce 2s infinite;
                        }}
                        @keyframes bounce {{
                            0%, 20%, 50%, 80%, 100% {{ transform: translateY(0); }}
                            40% {{ transform: translateY(-30px); }}
                            60% {{ transform: translateY(-15px); }}
                        }}
                        .stats {{
                            background: #f8f9fa;
                            padding: 25px;
                            border-radius: 8px;
                            margin: 25px 0;
                        }}
                        .cta-button {{
                            display: inline-block;
                            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                            color: white;
                            padding: 15px 30px;
                            text-decoration: none;
                            border-radius: 8px;
                            font-weight: 600;
                            margin: 20px 0;
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="celebration">🎉</div>
                        <h1 class="title">Achievement Unlocked!</h1>
                        
                        <div class="achievement-badge">{achievement_icon}</div>
                        <h2>{achievement_name}</h2>
                        <p>{achievement_description}</p>
                        
                        <div class="stats">
                            <h3>🏆 Your Progress</h3>
                            <p><strong>Points Earned:</strong> {points_earned}</p>
                            <p><strong>Total Points:</strong> {total_points}</p>
                            <p><strong>Your Rank:</strong> #{user_rank}</p>
                        </div>
                        
                        <p>Keep up the excellent work, <strong>{user_name}</strong>!</p>
                        
                        <a href="{dashboard_url}" class="cta-button">
                            View Your Dashboard
                        </a>
                    </div>
                </body>
                </html>
                ''',
                'text_template': '''
                🎉 Achievement Unlocked! - {achievement_name}

                Congratulations {user_name}!

                You've just unlocked: {achievement_name}
                {achievement_description}

                Your Progress:
                • Points Earned: {points_earned}
                • Total Points: {total_points}  
                • Your Rank: #{user_rank}

                Keep up the excellent work!

                View your dashboard: {dashboard_url}

                The Biz Design Team
                '''
            },
            
            'weekly_summary': {
                'subject': '📊 Your Weekly Learning Summary',
                'html_template': '''
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Weekly Summary - Biz Design</title>
                    <style>
                        body {{
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                            line-height: 1.6;
                            color: #333;
                            max-width: 600px;
                            margin: 0 auto;
                            padding: 20px;
                            background-color: #f8f9fa;
                        }}
                        .container {{
                            background: white;
                            border-radius: 12px;
                            padding: 40px;
                            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                        }}
                        .header {{
                            text-align: center;
                            margin-bottom: 30px;
                        }}
                        .stats-grid {{
                            display: grid;
                            grid-template-columns: repeat(2, 1fr);
                            gap: 20px;
                            margin: 30px 0;
                        }}
                        .stat-card {{
                            background: #f8f9fa;
                            padding: 20px;
                            border-radius: 8px;
                            text-align: center;
                        }}
                        .stat-number {{
                            font-size: 28px;
                            font-weight: bold;
                            color: #2563eb;
                            display: block;
                        }}
                        .progress-bar {{
                            background: #e5e7eb;
                            height: 8px;
                            border-radius: 4px;
                            margin: 15px 0;
                        }}
                        .progress-fill {{
                            background: linear-gradient(90deg, #10b981, #059669);
                            height: 100%;
                            border-radius: 4px;
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>📊 Your Weekly Summary</h1>
                            <p>Week of {week_start} - {week_end}</p>
                        </div>
                        
                        <p>Hello <strong>{user_name}</strong>,</p>
                        <p>Here's your learning progress from this week:</p>
                        
                        <div class="stats-grid">
                            <div class="stat-card">
                                <span class="stat-number">{points_earned}</span>
                                <span>Points Earned</span>
                            </div>
                            <div class="stat-card">
                                <span class="stat-number">{frameworks_completed}</span>
                                <span>Frameworks Completed</span>
                            </div>
                            <div class="stat-card">
                                <span class="stat-number">{reviews_completed}</span>
                                <span>Reviews Done</span>
                            </div>
                            <div class="stat-card">
                                <span class="stat-number">{login_streak}</span>
                                <span>Day Login Streak</span>
                            </div>
                        </div>
                        
                        <h3>🎯 This Week's Highlights</h3>
                        <ul>
                            {highlights}
                        </ul>
                        
                        <h3>📈 Goals for Next Week</h3>
                        <ul>
                            {next_week_goals}
                        </ul>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{dashboard_url}" class="cta-button">View Full Dashboard</a>
                        </div>
                    </div>
                </body>
                </html>
                ''',
                'text_template': '''
                📊 Your Weekly Summary - Biz Design

                Week of {week_start} - {week_end}

                Hello {user_name},

                Here's your learning progress from this week:

                📈 Your Stats:
                • Points Earned: {points_earned}
                • Frameworks Completed: {frameworks_completed}
                • Reviews Done: {reviews_completed}
                • Login Streak: {login_streak} days

                🎯 This Week's Highlights:
                {highlights_text}

                📈 Goals for Next Week:
                {next_week_goals_text}

                Keep up the great work!

                View your full dashboard: {dashboard_url}

                The Biz Design Team
                '''
            },
            
            'welcome_series': {
                'subject': '👋 Welcome to Biz Design - Let\'s Get Started!',
                'html_template': '''
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Welcome to Biz Design</title>
                    <style>
                        body {{
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                            line-height: 1.6;
                            color: #333;
                            max-width: 600px;
                            margin: 0 auto;
                            padding: 20px;
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        }}
                        .container {{
                            background: white;
                            border-radius: 12px;
                            padding: 40px;
                            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                        }}
                        .welcome-header {{
                            text-align: center;
                            margin-bottom: 30px;
                        }}
                        .logo {{
                            font-size: 48px;
                            margin-bottom: 20px;
                        }}
                        .features {{
                            display: grid;
                            grid-template-columns: repeat(2, 1fr);
                            gap: 20px;
                            margin: 30px 0;
                        }}
                        .feature {{
                            padding: 20px;
                            border: 1px solid #e5e7eb;
                            border-radius: 8px;
                            text-align: center;
                        }}
                        .feature-icon {{
                            font-size: 32px;
                            margin-bottom: 10px;
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="welcome-header">
                            <div class="logo">🎯</div>
                            <h1>Welcome to Biz Design!</h1>
                            <p>Your AI-powered business framework learning platform</p>
                        </div>
                        
                        <p>Hello <strong>{user_name}</strong>,</p>
                        
                        <p>Welcome to the future of business learning! We're excited to have you join thousands of professionals who are mastering business frameworks with AI assistance.</p>
                        
                        <div class="features">
                            <div class="feature">
                                <div class="feature-icon">🧠</div>
                                <h3>AI Copilot</h3>
                                <p>Get personalized guidance through every framework</p>
                            </div>
                            <div class="feature">
                                <div class="feature-icon">📚</div>
                                <h3>Smart Reviews</h3>
                                <p>Spaced repetition based on science</p>
                            </div>
                            <div class="feature">
                                <div class="feature-icon">🏆</div>
                                <h3>Gamified Learning</h3>
                                <p>Earn points, badges, and track progress</p>
                            </div>
                            <div class="feature">
                                <div class="feature-icon">🎯</div>
                                <h3>Practical Focus</h3>
                                <p>Real business scenarios and applications</p>
                            </div>
                        </div>
                        
                        <h3>🚀 Ready to Get Started?</h3>
                        <ol>
                            <li>Complete your first SWOT Analysis</li>
                            <li>Try the AI Copilot for guidance</li>
                            <li>Set up your notification preferences</li>
                            <li>Explore other frameworks</li>
                        </ol>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{dashboard_url}" class="cta-button">Start Learning Now</a>
                        </div>
                        
                        <p>Questions? Just reply to this email - we'd love to help!</p>
                        
                        <p>Happy learning!<br>The Biz Design Team</p>
                    </div>
                </body>
                </html>
                ''',
                'text_template': '''
                👋 Welcome to Biz Design!

                Hello {user_name},

                Welcome to the future of business learning! We're excited to have you join thousands of professionals who are mastering business frameworks with AI assistance.

                What You'll Love:
                🧠 AI Copilot - Get personalized guidance through every framework
                📚 Smart Reviews - Spaced repetition based on science  
                🏆 Gamified Learning - Earn points, badges, and track progress
                🎯 Practical Focus - Real business scenarios and applications

                Ready to Get Started?
                1. Complete your first SWOT Analysis
                2. Try the AI Copilot for guidance
                3. Set up your notification preferences
                4. Explore other frameworks

                Start learning now: {dashboard_url}

                Questions? Just reply to this email - we'd love to help!

                Happy learning!
                The Biz Design Team
                '''
            }
        }
    
    def render_template(
        self, 
        template_name: str, 
        user: User, 
        variables: Dict[str, Any],
        format_type: str = 'html'
    ) -> Dict[str, str]:
        """Render an email template with provided variables"""
        
        if template_name not in self.templates:
            logger.error(f"Template not found: {template_name}")
            return self._get_fallback_template(format_type)
        
        template = self.templates[template_name]
        
        # Base variables available to all templates
        base_variables = {
            'user_name': user.email.split('@')[0].title(),
            'user_email': user.email,
            'current_date': datetime.utcnow().strftime('%B %d, %Y'),
            'dashboard_url': 'https://bizdesign.ai/dashboard',
            'preferences_url': 'https://bizdesign.ai/settings/notifications',
            'unsubscribe_url': f'https://bizdesign.ai/unsubscribe?token={self._generate_unsubscribe_token(user)}',
            'company_name': 'Biz Design',
            'support_email': 'support@bizdesign.ai'
        }
        
        # Merge with provided variables
        template_variables = {**base_variables, **variables}
        
        try:
            if format_type == 'html':
                content = template['html_template'].format(**template_variables)
            else:
                content = template['text_template'].format(**template_variables)
            
            subject = template['subject'].format(**template_variables)
            
            return {
                'subject': subject,
                'content': content,
                'format': format_type
            }
            
        except KeyError as e:
            logger.error(f"Missing template variable: {e}")
            return self._get_fallback_template(format_type, str(e))
        except Exception as e:
            logger.error(f"Template rendering error: {e}")
            return self._get_fallback_template(format_type, str(e))
    
    def _get_fallback_template(self, format_type: str = 'html', error: str = '') -> Dict[str, str]:
        """Get fallback template when rendering fails"""
        
        if format_type == 'html':
            content = f'''
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h1>Notification from Biz Design</h1>
                <p>We have an important update for you, but encountered an issue displaying the full content.</p>
                <p>Please visit your dashboard to see the latest information.</p>
                <p><a href="https://bizdesign.ai/dashboard">Go to Dashboard</a></p>
                {f"<p><small>Error: {error}</small></p>" if error else ""}
            </body>
            </html>
            '''
        else:
            content = f'''
            Notification from Biz Design
            
            We have an important update for you, but encountered an issue displaying the full content.
            
            Please visit your dashboard to see the latest information: https://bizdesign.ai/dashboard
            
            {f"Error: {error}" if error else ""}
            '''
        
        return {
            'subject': 'Notification from Biz Design',
            'content': content,
            'format': format_type
        }
    
    def _generate_unsubscribe_token(self, user: User) -> str:
        """Generate unsubscribe token for user (simplified)"""
        import hashlib
        
        # In production, use proper JWT or secure token generation
        token_data = f"{user.id}:{user.email}:{datetime.utcnow().date()}"
        return hashlib.md5(token_data.encode()).hexdigest()[:16]
    
    def get_available_templates(self) -> List[Dict[str, str]]:
        """Get list of available email templates"""
        
        template_info = []
        for template_name, template_data in self.templates.items():
            # Extract sample subject (without variables)
            sample_subject = template_data['subject'].replace('{', '[').replace('}', ']')
            
            template_info.append({
                'name': template_name,
                'display_name': template_name.replace('_', ' ').title(),
                'sample_subject': sample_subject,
                'description': self._get_template_description(template_name)
            })
        
        return template_info
    
    def _get_template_description(self, template_name: str) -> str:
        """Get description for template type"""
        
        descriptions = {
            'review_reminder': 'Reminds users to review completed frameworks based on Ebbinghaus intervals',
            'achievement_unlock': 'Celebrates when users unlock achievements or badges',
            'weekly_summary': 'Weekly progress summary with stats and highlights',
            'welcome_series': 'Welcome email for new users with platform introduction'
        }
        
        return descriptions.get(template_name, 'Email template for user notifications')
    
    def preview_template(
        self, 
        template_name: str, 
        sample_variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """Generate a preview of an email template with sample data"""
        
        from app.models.user import User
        
        # Create sample user
        sample_user = User()
        sample_user.email = "john.doe@example.com"
        sample_user.id = "sample-id"
        
        # Default sample variables
        default_variables = {
            'framework_name': 'SWOT Analysis',
            'output_type': 'analysis',
            'days_since_completion': 3,
            'interval_days': 3,
            'action_url': 'https://bizdesign.ai/outputs/sample/review',
            'achievement_name': 'First Framework Master',
            'achievement_icon': '🏆',
            'achievement_description': 'Completed your first business framework analysis',
            'points_earned': 150,
            'total_points': 750,
            'user_rank': 42,
            'week_start': 'January 1, 2024',
            'week_end': 'January 7, 2024',
            'frameworks_completed': 2,
            'reviews_completed': 5,
            'login_streak': 7,
            'highlights': '<li>Completed SWOT Analysis with 95% score</li><li>Maintained 7-day login streak</li>',
            'highlights_text': '• Completed SWOT Analysis with 95% score\n• Maintained 7-day login streak',
            'next_week_goals': '<li>Try User Journey Mapping</li><li>Complete 3 review sessions</li>',
            'next_week_goals_text': '• Try User Journey Mapping\n• Complete 3 review sessions'
        }
        
        # Merge with provided sample variables
        if sample_variables:
            default_variables.update(sample_variables)
        
        # Render both HTML and text versions
        html_version = self.render_template(template_name, sample_user, default_variables, 'html')
        text_version = self.render_template(template_name, sample_user, default_variables, 'text')
        
        return {
            'template_name': template_name,
            'html': html_version,
            'text': text_version,
            'sample_variables': default_variables
        }