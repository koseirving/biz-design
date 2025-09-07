from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, ValidationError
from datetime import datetime
import uuid


class JourneyStage(BaseModel):
    stage_name: str = Field(..., description="ジャーニーの段階名（例: 認知、検討、購入）")
    user_actions: str = Field(..., description="この段階でユーザーが具体的に行う行動")
    user_thoughts: Optional[str] = Field(None, description="この段階でユーザーが考えていること")
    emotions: Optional[str] = Field(None, description="この段階でユーザーが感じる感情")
    pain_points: str = Field(..., description="この段階でユーザーが感じる不満や課題")
    touchpoints: Optional[List[str]] = Field(None, description="この段階でのタッチポイント")
    opportunities: Optional[List[str]] = Field(None, description="この段階での改善機会")


class UserJourneyData(BaseModel):
    persona: str = Field(..., description="このジャーニーを体験するユーザーペルソナの名前や特徴")
    goal: Optional[str] = Field(None, description="ユーザーの最終的な目標")
    context: Optional[str] = Field(None, description="ジャーニーの背景や状況")
    stages: List[JourneyStage] = Field(..., min_items=1, description="ジャーニーの各段階")


class UserJourneyResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    framework_id: str
    user_id: str
    journey_data: UserJourneyData
    analysis_summary: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None


class JourneyAnalyzer:
    """User Journey Map分析のビジネスロジックを管理するサービスクラス"""
    
    @staticmethod
    def validate_journey_data(data: Dict[str, Any]) -> UserJourneyData:
        """User Journey Mapデータの検証とフォーマット"""
        try:
            return UserJourneyData(**data)
        except ValidationError as e:
            raise ValueError(f"Invalid User Journey data format: {e}")
    
    @staticmethod
    def format_journey_output(journey_data: UserJourneyData) -> Dict[str, Any]:
        """User Journey Map結果を表示用にフォーマット"""
        return {
            "type": "user_journey_map",
            "persona": {
                "name": journey_data.persona,
                "goal": journey_data.goal,
                "context": journey_data.context
            },
            "timeline": [
                {
                    "stage_id": f"stage_{i+1}",
                    "stage_name": stage.stage_name,
                    "user_actions": stage.user_actions,
                    "user_thoughts": stage.user_thoughts,
                    "emotions": stage.emotions,
                    "pain_points": stage.pain_points,
                    "touchpoints": stage.touchpoints or [],
                    "opportunities": stage.opportunities or [],
                    "order": i + 1
                }
                for i, stage in enumerate(journey_data.stages)
            ],
            "summary": {
                "total_stages": len(journey_data.stages),
                "key_pain_points": [stage.pain_points for stage in journey_data.stages if stage.pain_points],
                "improvement_opportunities": [
                    opp for stage in journey_data.stages 
                    if stage.opportunities
                    for opp in stage.opportunities
                ]
            }
        }
    
    @staticmethod
    def generate_analysis_summary(journey_data: UserJourneyData) -> str:
        """User Journey Mapの概要サマリーを生成"""
        persona_name = journey_data.persona
        stage_count = len(journey_data.stages)
        stage_names = [stage.stage_name for stage in journey_data.stages]
        
        summary = f"{persona_name}のカスタマージャーニー（{stage_count}段階）: "
        summary += " → ".join(stage_names)
        
        if journey_data.goal:
            summary += f" | 目標: {journey_data.goal}"
            
        return summary
    
    @staticmethod
    def create_analysis_result(
        framework_id: str,
        user_id: str,
        journey_data: UserJourneyData,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UserJourneyResult:
        """完全なUser Journey Map分析結果オブジェクトを作成"""
        analysis_summary = JourneyAnalyzer.generate_analysis_summary(journey_data)
        
        return UserJourneyResult(
            framework_id=framework_id,
            user_id=user_id,
            journey_data=journey_data,
            analysis_summary=analysis_summary,
            metadata=metadata or {}
        )
    
    @staticmethod
    def extract_pain_points(journey_data: UserJourneyData) -> List[Dict[str, str]]:
        """全ステージからペインポイントを抽出"""
        pain_points = []
        for i, stage in enumerate(journey_data.stages):
            if stage.pain_points:
                pain_points.append({
                    "stage": stage.stage_name,
                    "stage_order": i + 1,
                    "pain_point": stage.pain_points
                })
        return pain_points
    
    @staticmethod
    def extract_opportunities(journey_data: UserJourneyData) -> List[Dict[str, Any]]:
        """全ステージから改善機会を抽出"""
        opportunities = []
        for i, stage in enumerate(journey_data.stages):
            if stage.opportunities:
                for opp in stage.opportunities:
                    opportunities.append({
                        "stage": stage.stage_name,
                        "stage_order": i + 1,
                        "opportunity": opp,
                        "related_pain_point": stage.pain_points
                    })
        return opportunities
    
    @staticmethod
    def get_touchpoint_analysis(journey_data: UserJourneyData) -> Dict[str, Any]:
        """タッチポイント分析を実行"""
        all_touchpoints = []
        touchpoint_frequency = {}
        
        for stage in journey_data.stages:
            if stage.touchpoints:
                all_touchpoints.extend(stage.touchpoints)
                for tp in stage.touchpoints:
                    touchpoint_frequency[tp] = touchpoint_frequency.get(tp, 0) + 1
        
        return {
            "total_touchpoints": len(set(all_touchpoints)),
            "touchpoint_frequency": touchpoint_frequency,
            "most_common_touchpoints": sorted(
                touchpoint_frequency.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
        }
    
    @staticmethod
    def validate_completeness(journey_data: UserJourneyData) -> Dict[str, Any]:
        """User Journey Mapの完成度を評価"""
        completeness = {
            "has_persona": bool(journey_data.persona),
            "has_goal": bool(journey_data.goal),
            "stage_count": len(journey_data.stages),
            "stages_with_actions": sum(1 for stage in journey_data.stages if stage.user_actions),
            "stages_with_pain_points": sum(1 for stage in journey_data.stages if stage.pain_points),
            "stages_with_touchpoints": sum(1 for stage in journey_data.stages if stage.touchpoints),
            "is_complete": True,
            "recommendations": []
        }
        
        if not journey_data.persona:
            completeness["recommendations"].append("ペルソナ情報を追加してください")
            completeness["is_complete"] = False
            
        if not journey_data.goal:
            completeness["recommendations"].append("ユーザーの最終目標を明確にしてください")
            
        if completeness["stage_count"] < 3:
            completeness["recommendations"].append("より詳細な分析のため、3段階以上を検討してください")
            
        if completeness["stages_with_pain_points"] < completeness["stage_count"]:
            completeness["recommendations"].append("各段階のペインポイントを特定してください")
            completeness["is_complete"] = False
            
        return completeness