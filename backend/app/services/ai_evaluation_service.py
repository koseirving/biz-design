from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from uuid import UUID
import google.generativeai as genai
from app.core.config import settings
from app.models.user import User, UserOutput
from app.services.points_service import PointsService, EventType
from app.services.badge_service import BadgeService
import json


class AIEvaluationService:
    """Service for AI-powered evaluation of user outputs"""
    
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')
    
    async def evaluate_output(
        self,
        db: Session,
        user: User,
        output: UserOutput
    ) -> Dict[str, Any]:
        """Evaluate a user output using Gemini AI and award bonus points for high quality"""
        
        try:
            # Create evaluation prompt based on output type
            prompt = self._create_evaluation_prompt(output)
            
            # Get AI evaluation
            response = self.model.generate_content(prompt)
            evaluation_text = response.text
            
            # Parse the evaluation (expect JSON response)
            evaluation_data = self._parse_evaluation_response(evaluation_text)
            
            # Award bonus points for high-quality outputs
            score = evaluation_data.get('overall_score', 0)
            bonus_awarded = False
            
            if score >= 80:
                # Award high quality bonus points
                points_awarded = PointsService.award_points(
                    db, user, EventType.HIGH_QUALITY_OUTPUT,
                    entity_id=output.id,
                    metadata={
                        'ai_score': score,
                        'evaluation_summary': evaluation_data.get('summary', ''),
                        'output_type': output.output_data.get('type', 'unknown')
                    }
                )
                bonus_awarded = points_awarded > 0
                
                # Check for quality analyst badge
                BadgeService.check_and_award_badges(db, user)
            
            # Store evaluation in output metadata
            updated_output_data = output.output_data.copy()
            updated_output_data['ai_evaluation'] = {
                'score': score,
                'feedback': evaluation_data,
                'evaluated_at': evaluation_data.get('evaluated_at'),
                'bonus_awarded': bonus_awarded
            }
            
            # Update output with evaluation
            output.output_data = updated_output_data
            db.commit()
            
            return {
                'success': True,
                'score': score,
                'evaluation': evaluation_data,
                'bonus_awarded': bonus_awarded,
                'points_awarded': points_awarded if bonus_awarded else 0
            }
            
        except Exception as e:
            print(f"Error evaluating output: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'score': 0,
                'evaluation': {},
                'bonus_awarded': False,
                'points_awarded': 0
            }
    
    def _create_evaluation_prompt(self, output: UserOutput) -> str:
        """Create appropriate evaluation prompt based on output type"""
        
        output_type = output.output_data.get('type', 'unknown')
        content = json.dumps(output.output_data, indent=2)
        
        if output_type == 'swot_analysis':
            return f"""
Please evaluate the following SWOT analysis output on a scale of 0-100 points. 
Consider comprehensiveness, clarity, relevance, and actionability of the analysis.

SWOT Analysis to evaluate:
{content}

Please respond with a JSON object containing:
{{
    "overall_score": <number 0-100>,
    "summary": "<brief evaluation summary>",
    "strengths_quality": <number 0-100>,
    "weaknesses_quality": <number 0-100>,
    "opportunities_quality": <number 0-100>,
    "threats_quality": <number 0-100>,
    "comprehensiveness": <number 0-100>,
    "actionability": <number 0-100>,
    "feedback": "specific areas for improvement",
    "evaluated_at": "{output.created_at.isoformat()}"
}}
"""
        
        elif output_type == 'user_journey_map':
            return f"""
Please evaluate the following User Journey Map on a scale of 0-100 points.
Consider completeness, insight quality, pain point identification, and improvement opportunities.

User Journey Map to evaluate:
{content}

Please respond with a JSON object containing:
{{
    "overall_score": <number 0-100>,
    "summary": "<brief evaluation summary>",
    "persona_clarity": <number 0-100>,
    "journey_completeness": <number 0-100>,
    "pain_point_identification": <number 0-100>,
    "improvement_opportunities": <number 0-100>,
    "touchpoint_analysis": <number 0-100>,
    "feedback": "specific areas for improvement",
    "evaluated_at": "{output.created_at.isoformat()}"
}}
"""
        
        else:
            return f"""
Please evaluate the following business framework output on a scale of 0-100 points.
Consider quality, completeness, clarity, and practical applicability.

Output to evaluate:
{content}

Please respond with a JSON object containing:
{{
    "overall_score": <number 0-100>,
    "summary": "<brief evaluation summary>",
    "quality": <number 0-100>,
    "completeness": <number 0-100>,
    "clarity": <number 0-100>,
    "applicability": <number 0-100>,
    "feedback": "specific areas for improvement",
    "evaluated_at": "{output.created_at.isoformat()}"
}}
"""
    
    def _parse_evaluation_response(self, response_text: str) -> Dict[str, Any]:
        """Parse AI evaluation response into structured data"""
        try:
            # Try to extract JSON from the response
            if '{' in response_text and '}' in response_text:
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                json_str = response_text[start:end]
                return json.loads(json_str)
            else:
                # Fallback: create basic evaluation from text
                return {
                    'overall_score': 70,  # Default moderate score
                    'summary': response_text[:200] + '...' if len(response_text) > 200 else response_text,
                    'feedback': 'AI evaluation completed',
                    'evaluated_at': None
                }
        except json.JSONDecodeError:
            # Fallback for invalid JSON
            return {
                'overall_score': 60,
                'summary': 'Evaluation completed with parsing issues',
                'feedback': 'Unable to parse detailed evaluation',
                'evaluated_at': None
            }
    
    @staticmethod
    def get_output_evaluation(output: UserOutput) -> Optional[Dict[str, Any]]:
        """Get existing AI evaluation for an output"""
        return output.output_data.get('ai_evaluation')
    
    @staticmethod
    def should_evaluate_output(output: UserOutput) -> bool:
        """Check if output should be evaluated (not already evaluated)"""
        existing_evaluation = AIEvaluationService.get_output_evaluation(output)
        return existing_evaluation is None