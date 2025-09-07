from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.user import User, UserOutput
import google.generativeai as genai
from app.core.config import settings
import json
import random
import logging

logger = logging.getLogger(__name__)


class ReviewContentType:
    QUIZ = "quiz"
    SUMMARY = "summary"
    REFLECTION = "reflection"
    AI_PROBLEMS = "ai_problems"


class ReviewContentGenerator:
    """AI-powered review content generation using Gemini API"""
    
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')
    
    async def generate_review_content(
        self, 
        user: User, 
        output: UserOutput, 
        content_types: List[str] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive review content for an output"""
        
        if not content_types:
            content_types = [
                ReviewContentType.QUIZ,
                ReviewContentType.SUMMARY,
                ReviewContentType.REFLECTION,
                ReviewContentType.AI_PROBLEMS
            ]
        
        logger.info(f"Generating review content for output {output.id}, types: {content_types}")
        
        review_content = {
            'output_id': str(output.id),
            'framework_name': output.output_data.get('framework_name', 'Framework'),
            'output_type': output.output_data.get('type', 'analysis'),
            'generated_at': str(output.created_at),
            'content': {}
        }
        
        # Generate each requested content type
        for content_type in content_types:
            try:
                if content_type == ReviewContentType.QUIZ:
                    review_content['content']['quiz'] = await self._generate_quiz(output)
                elif content_type == ReviewContentType.SUMMARY:
                    review_content['content']['summary'] = await self._generate_summary(output)
                elif content_type == ReviewContentType.REFLECTION:
                    review_content['content']['reflection'] = await self._generate_reflection_questions(output)
                elif content_type == ReviewContentType.AI_PROBLEMS:
                    review_content['content']['ai_problems'] = await self._generate_application_problems(output)
                    
            except Exception as e:
                logger.error(f"Failed to generate {content_type} for output {output.id}: {str(e)}")
                review_content['content'][content_type] = {'error': str(e)}
        
        return review_content
    
    async def _generate_quiz(self, output: UserOutput) -> Dict[str, Any]:
        """Generate a quiz with 5 questions about the framework output"""
        
        framework_name = output.output_data.get('framework_name', 'Framework')
        output_type = output.output_data.get('type', 'analysis')
        content = json.dumps(output.output_data, indent=2)
        
        prompt = f"""
Based on the following {framework_name} {output_type}, create a quiz with 5 multiple-choice questions 
to test understanding and retention of the key concepts.

{framework_name} {output_type}:
{content}

Please respond with a JSON object containing:
{{
    "quiz_title": "Review Quiz: {framework_name}",
    "instructions": "Select the best answer for each question based on your {framework_name} analysis.",
    "questions": [
        {{
            "question_number": 1,
            "question": "question text here",
            "options": ["A) option 1", "B) option 2", "C) option 3", "D) option 4"],
            "correct_answer": "A",
            "explanation": "Brief explanation of why this is correct"
        }}
    ],
    "total_questions": 5,
    "estimated_time_minutes": 3
}}

Make sure questions test:
1. Key framework concepts
2. Specific insights from the analysis
3. Application knowledge
4. Critical thinking about the content
5. Memory of important details
"""

        try:
            response = self.model.generate_content(prompt)
            quiz_data = self._parse_json_response(response.text)
            
            if not quiz_data or 'questions' not in quiz_data:
                return self._generate_fallback_quiz(framework_name, output_type)
            
            return quiz_data
            
        except Exception as e:
            logger.error(f"Failed to generate quiz: {str(e)}")
            return self._generate_fallback_quiz(framework_name, output_type)
    
    async def _generate_summary(self, output: UserOutput) -> Dict[str, Any]:
        """Generate key points summary of the framework output"""
        
        framework_name = output.output_data.get('framework_name', 'Framework')
        output_type = output.output_data.get('type', 'analysis')
        content = json.dumps(output.output_data, indent=2)
        
        prompt = f"""
Analyze the following {framework_name} {output_type} and create a comprehensive summary 
highlighting the most important insights and key takeaways.

{framework_name} {output_type}:
{content}

Please respond with a JSON object containing:
{{
    "summary_title": "Key Insights: {framework_name}",
    "main_findings": [
        "Primary insight 1",
        "Primary insight 2",
        "Primary insight 3"
    ],
    "key_points": [
        {{
            "category": "category name",
            "points": ["point 1", "point 2", "point 3"]
        }}
    ],
    "critical_insights": [
        "Most important insight 1",
        "Most important insight 2"
    ],
    "action_items": [
        "Actionable item 1",
        "Actionable item 2",
        "Actionable item 3"
    ],
    "review_focus_areas": [
        "Area that needs more attention",
        "Concept to reinforce"
    ]
}}

Focus on extracting actionable insights and memorable key points.
"""

        try:
            response = self.model.generate_content(prompt)
            summary_data = self._parse_json_response(response.text)
            
            if not summary_data:
                return self._generate_fallback_summary(framework_name, output_type)
            
            return summary_data
            
        except Exception as e:
            logger.error(f"Failed to generate summary: {str(e)}")
            return self._generate_fallback_summary(framework_name, output_type)
    
    async def _generate_reflection_questions(self, output: UserOutput) -> Dict[str, Any]:
        """Generate reflection questions for deeper learning"""
        
        framework_name = output.output_data.get('framework_name', 'Framework')
        output_type = output.output_data.get('type', 'analysis')
        content = json.dumps(output.output_data, indent=2)
        
        prompt = f"""
Based on the following {framework_name} {output_type}, create thoughtful reflection questions 
that encourage deeper thinking and personal application of the insights.

{framework_name} {output_type}:
{content}

Please respond with a JSON object containing:
{{
    "reflection_title": "Reflection on Your {framework_name}",
    "instructions": "Take time to thoughtfully consider each question and write detailed responses.",
    "questions": [
        {{
            "question_number": 1,
            "category": "Self-Assessment",
            "question": "reflection question here",
            "prompts": ["sub-question 1", "sub-question 2"],
            "estimated_time_minutes": 5
        }}
    ],
    "categories": [
        "Self-Assessment",
        "Application",
        "Future Planning",
        "Lessons Learned"
    ],
    "total_estimated_time_minutes": 20
}}

Include questions that cover:
- What worked well in your analysis?
- What would you do differently?
- How can you apply these insights?
- What surprised you most?
- What needs further investigation?
"""

        try:
            response = self.model.generate_content(prompt)
            reflection_data = self._parse_json_response(response.text)
            
            if not reflection_data:
                return self._generate_fallback_reflection(framework_name, output_type)
            
            return reflection_data
            
        except Exception as e:
            logger.error(f"Failed to generate reflection questions: {str(e)}")
            return self._generate_fallback_reflection(framework_name, output_type)
    
    async def _generate_application_problems(self, output: UserOutput) -> Dict[str, Any]:
        """Generate application problems using AI for practical learning"""
        
        framework_name = output.output_data.get('framework_name', 'Framework')
        output_type = output.output_data.get('type', 'analysis')
        content = json.dumps(output.output_data, indent=2)
        
        prompt = f"""
Based on the {framework_name} {output_type} analysis, create practical application problems 
that test the ability to apply the framework to new scenarios.

{framework_name} {output_type}:
{content}

Please respond with a JSON object containing:
{{
    "problems_title": "Apply Your {framework_name} Knowledge",
    "instructions": "Use your understanding of {framework_name} to solve these practical scenarios.",
    "problems": [
        {{
            "problem_number": 1,
            "title": "Problem title",
            "scenario": "Detailed scenario description",
            "task": "What you need to accomplish",
            "difficulty": "beginner|intermediate|advanced",
            "estimated_time_minutes": 10,
            "hints": ["helpful hint 1", "helpful hint 2"],
            "learning_objectives": ["objective 1", "objective 2"]
        }}
    ],
    "total_problems": 3,
    "difficulty_distribution": {{"beginner": 1, "intermediate": 1, "advanced": 1}},
    "total_estimated_time_minutes": 30
}}

Create problems that:
1. Apply the framework to different industries/contexts
2. Test decision-making using framework insights
3. Challenge assumptions from the original analysis
4. Require creative problem-solving
"""

        try:
            response = self.model.generate_content(prompt)
            problems_data = self._parse_json_response(response.text)
            
            if not problems_data:
                return self._generate_fallback_problems(framework_name, output_type)
            
            return problems_data
            
        except Exception as e:
            logger.error(f"Failed to generate application problems: {str(e)}")
            return self._generate_fallback_problems(framework_name, output_type)
    
    def _parse_json_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse AI response and extract JSON"""
        try:
            # Try to extract JSON from the response
            if '{' in response_text and '}' in response_text:
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                json_str = response_text[start:end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        return None
    
    def _generate_fallback_quiz(self, framework_name: str, output_type: str) -> Dict[str, Any]:
        """Generate a fallback quiz when AI generation fails"""
        return {
            "quiz_title": f"Review Quiz: {framework_name}",
            "instructions": f"Test your understanding of the {framework_name} {output_type}.",
            "questions": [
                {
                    "question_number": 1,
                    "question": f"What is the primary purpose of the {framework_name} framework?",
                    "options": [
                        "A) Strategic analysis and planning",
                        "B) Financial forecasting",
                        "C) Marketing optimization",
                        "D) Operational efficiency"
                    ],
                    "correct_answer": "A",
                    "explanation": f"The {framework_name} framework is primarily used for strategic analysis."
                }
            ],
            "total_questions": 1,
            "estimated_time_minutes": 2,
            "fallback": True
        }
    
    def _generate_fallback_summary(self, framework_name: str, output_type: str) -> Dict[str, Any]:
        """Generate a fallback summary when AI generation fails"""
        return {
            "summary_title": f"Key Insights: {framework_name}",
            "main_findings": [
                f"Completed {framework_name} {output_type}",
                "Identified key strategic factors",
                "Developed actionable insights"
            ],
            "key_points": [
                {
                    "category": "Analysis",
                    "points": [
                        f"Applied {framework_name} methodology",
                        "Gathered relevant data",
                        "Structured findings logically"
                    ]
                }
            ],
            "critical_insights": [
                "Framework application successful",
                "Ready for next learning phase"
            ],
            "action_items": [
                "Review framework concepts",
                "Practice with different scenarios",
                "Apply learnings to real situations"
            ],
            "review_focus_areas": [
                "Framework methodology",
                "Practical applications"
            ],
            "fallback": True
        }
    
    def _generate_fallback_reflection(self, framework_name: str, output_type: str) -> Dict[str, Any]:
        """Generate fallback reflection questions"""
        return {
            "reflection_title": f"Reflection on Your {framework_name}",
            "instructions": "Consider your experience with this framework analysis.",
            "questions": [
                {
                    "question_number": 1,
                    "category": "Self-Assessment",
                    "question": f"How well do you feel you applied the {framework_name} framework?",
                    "prompts": [
                        "What aspects did you handle well?",
                        "What was challenging?"
                    ],
                    "estimated_time_minutes": 5
                },
                {
                    "question_number": 2,
                    "category": "Application",
                    "question": "How will you apply these insights in practice?",
                    "prompts": [
                        "What specific actions will you take?",
                        "How will you measure success?"
                    ],
                    "estimated_time_minutes": 5
                }
            ],
            "categories": ["Self-Assessment", "Application"],
            "total_estimated_time_minutes": 10,
            "fallback": True
        }
    
    def _generate_fallback_problems(self, framework_name: str, output_type: str) -> Dict[str, Any]:
        """Generate fallback application problems"""
        return {
            "problems_title": f"Apply Your {framework_name} Knowledge",
            "instructions": f"Practice applying the {framework_name} framework to new scenarios.",
            "problems": [
                {
                    "problem_number": 1,
                    "title": f"New {framework_name} Challenge",
                    "scenario": f"You need to apply {framework_name} to a different business context.",
                    "task": "Complete a new framework analysis using the same methodology.",
                    "difficulty": "intermediate",
                    "estimated_time_minutes": 15,
                    "hints": [
                        "Follow the same structure as your previous analysis",
                        "Consider how context affects the framework application"
                    ],
                    "learning_objectives": [
                        "Reinforce framework methodology",
                        "Practice adaptability"
                    ]
                }
            ],
            "total_problems": 1,
            "difficulty_distribution": {"intermediate": 1},
            "total_estimated_time_minutes": 15,
            "fallback": True
        }
    
    def get_review_content_statistics(self, review_content: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate statistics about generated review content"""
        
        stats = {
            'total_content_types': 0,
            'estimated_total_time_minutes': 0,
            'content_breakdown': {},
            'difficulty_levels': {},
            'learning_objectives_count': 0
        }
        
        content = review_content.get('content', {})
        
        for content_type, data in content.items():
            if 'error' in data:
                continue
                
            stats['total_content_types'] += 1
            
            if content_type == 'quiz':
                questions = data.get('questions', [])
                stats['content_breakdown']['quiz'] = {
                    'questions_count': len(questions),
                    'estimated_time': data.get('estimated_time_minutes', 0)
                }
                stats['estimated_total_time_minutes'] += data.get('estimated_time_minutes', 0)
            
            elif content_type == 'summary':
                stats['content_breakdown']['summary'] = {
                    'main_findings_count': len(data.get('main_findings', [])),
                    'key_points_categories': len(data.get('key_points', [])),
                    'action_items_count': len(data.get('action_items', []))
                }
            
            elif content_type == 'reflection':
                questions = data.get('questions', [])
                stats['content_breakdown']['reflection'] = {
                    'questions_count': len(questions),
                    'categories_count': len(data.get('categories', [])),
                    'estimated_time': data.get('total_estimated_time_minutes', 0)
                }
                stats['estimated_total_time_minutes'] += data.get('total_estimated_time_minutes', 0)
            
            elif content_type == 'ai_problems':
                problems = data.get('problems', [])
                stats['content_breakdown']['ai_problems'] = {
                    'problems_count': len(problems),
                    'estimated_time': data.get('total_estimated_time_minutes', 0)
                }
                stats['estimated_total_time_minutes'] += data.get('total_estimated_time_minutes', 0)
                
                # Count difficulty levels
                for problem in problems:
                    difficulty = problem.get('difficulty', 'unknown')
                    stats['difficulty_levels'][difficulty] = stats['difficulty_levels'].get(difficulty, 0) + 1
                    
                # Count learning objectives
                for problem in problems:
                    stats['learning_objectives_count'] += len(problem.get('learning_objectives', []))
        
        return stats