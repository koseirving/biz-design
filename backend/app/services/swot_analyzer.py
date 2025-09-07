from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, ValidationError
from datetime import datetime
import uuid


class SwotData(BaseModel):
    strengths: List[str] = Field(..., description="自社が持つ、競合に対する優位性や特長")
    weaknesses: List[str] = Field(..., description="自社が持つ、競合に対する不利な点や課題")
    opportunities: List[str] = Field(..., description="市場成長や規制緩和など、自社にとって追い風となる外部要因")
    threats: List[str] = Field(..., description="競合の台頭や技術革新など、自社にとって逆風となる外部要因")


class SwotAnalysisResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    framework_id: str
    user_id: str
    swot_data: SwotData
    analysis_summary: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None


class SwotAnalyzer:
    """SWOT分析のビジネスロジックを管理するサービスクラス"""
    
    @staticmethod
    def validate_swot_data(data: Dict[str, Any]) -> SwotData:
        """SWOT分析データの検証とフォーマット"""
        try:
            return SwotData(**data)
        except ValidationError as e:
            raise ValueError(f"Invalid SWOT data format: {e}")
    
    @staticmethod
    def format_swot_output(swot_data: SwotData, company_name: Optional[str] = None) -> Dict[str, Any]:
        """SWOT分析結果を表示用にフォーマット"""
        return {
            "type": "swot_analysis",
            "company_name": company_name,
            "quadrants": {
                "strengths": {
                    "title": "強み (Strengths)",
                    "description": "内部環境 - プラス要因",
                    "items": swot_data.strengths,
                    "color": "green"
                },
                "weaknesses": {
                    "title": "弱み (Weaknesses)", 
                    "description": "内部環境 - マイナス要因",
                    "items": swot_data.weaknesses,
                    "color": "red"
                },
                "opportunities": {
                    "title": "機会 (Opportunities)",
                    "description": "外部環境 - プラス要因",
                    "items": swot_data.opportunities,
                    "color": "blue"
                },
                "threats": {
                    "title": "脅威 (Threats)",
                    "description": "外部環境 - マイナス要因", 
                    "items": swot_data.threats,
                    "color": "orange"
                }
            },
            "matrix_layout": {
                "top_left": "strengths",
                "top_right": "weaknesses", 
                "bottom_left": "opportunities",
                "bottom_right": "threats"
            }
        }
    
    @staticmethod
    def generate_analysis_summary(swot_data: SwotData, company_name: Optional[str] = None) -> str:
        """SWOT分析の概要サマリーを生成"""
        company_ref = f"{company_name}の" if company_name else ""
        
        summary_parts = []
        
        if swot_data.strengths:
            summary_parts.append(f"主要な強み: {', '.join(swot_data.strengths[:3])}")
        
        if swot_data.weaknesses:
            summary_parts.append(f"改善すべき弱み: {', '.join(swot_data.weaknesses[:3])}")
            
        if swot_data.opportunities:
            summary_parts.append(f"活用可能な機会: {', '.join(swot_data.opportunities[:3])}")
            
        if swot_data.threats:
            summary_parts.append(f"注意すべき脅威: {', '.join(swot_data.threats[:3])}")
        
        return f"{company_ref}SWOT分析結果 - " + " | ".join(summary_parts)
    
    @staticmethod
    def create_analysis_result(
        framework_id: str,
        user_id: str, 
        swot_data: SwotData,
        company_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SwotAnalysisResult:
        """完全なSWOT分析結果オブジェクトを作成"""
        analysis_summary = SwotAnalyzer.generate_analysis_summary(swot_data, company_name)
        
        return SwotAnalysisResult(
            framework_id=framework_id,
            user_id=user_id,
            swot_data=swot_data,
            analysis_summary=analysis_summary,
            metadata=metadata or {}
        )
    
    @staticmethod
    def get_strategic_insights(swot_data: SwotData) -> List[str]:
        """SWOT分析から戦略的インサイトを生成"""
        insights = []
        
        if len(swot_data.strengths) > 0 and len(swot_data.opportunities) > 0:
            insights.append("SO戦略: 強みを活かして機会を最大化する戦略を検討してください")
            
        if len(swot_data.strengths) > 0 and len(swot_data.threats) > 0:
            insights.append("ST戦略: 強みを使って脅威に対抗する戦略を検討してください")
            
        if len(swot_data.weaknesses) > 0 and len(swot_data.opportunities) > 0:
            insights.append("WO戦略: 弱みを改善して機会を活用する戦略を検討してください")
            
        if len(swot_data.weaknesses) > 0 and len(swot_data.threats) > 0:
            insights.append("WT戦略: 弱みと脅威の影響を最小化する戦略を検討してください")
        
        return insights
    
    @staticmethod
    def validate_completeness(swot_data: SwotData) -> Dict[str, Any]:
        """SWOT分析の完成度を評価"""
        completeness = {
            "total_items": len(swot_data.strengths) + len(swot_data.weaknesses) + 
                          len(swot_data.opportunities) + len(swot_data.threats),
            "quadrant_balance": {
                "strengths": len(swot_data.strengths),
                "weaknesses": len(swot_data.weaknesses), 
                "opportunities": len(swot_data.opportunities),
                "threats": len(swot_data.threats)
            },
            "is_complete": all([
                len(swot_data.strengths) >= 1,
                len(swot_data.weaknesses) >= 1,
                len(swot_data.opportunities) >= 1,
                len(swot_data.threats) >= 1
            ]),
            "recommendations": []
        }
        
        if completeness["quadrant_balance"]["strengths"] == 0:
            completeness["recommendations"].append("強みを少なくとも1つ以上特定してください")
        if completeness["quadrant_balance"]["weaknesses"] == 0:
            completeness["recommendations"].append("弱みを少なくとも1つ以上特定してください")
        if completeness["quadrant_balance"]["opportunities"] == 0:
            completeness["recommendations"].append("機会を少なくとも1つ以上特定してください")
        if completeness["quadrant_balance"]["threats"] == 0:
            completeness["recommendations"].append("脅威を少なくとも1つ以上特定してください")
            
        return completeness