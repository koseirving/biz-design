import os
import json
import asyncio
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime
import uuid

import google.generativeai as genai
from google.generativeai.types import GenerateContentResponse
from sqlalchemy.orm import Session

from app.services.ai_function_declarations import (
    get_tool_by_framework,
    get_framework_system_prompt,
    get_function_handler_mapping
)
from app.services.swot_analyzer import SwotAnalyzer, SwotData
from app.services.journey_analyzer import JourneyAnalyzer, UserJourneyData
from app.services.output_service import OutputService
from app.models.user import User, BusinessFramework, UserOutput


class AIConversationService:
    """AI対話機能を管理するサービスクラス"""
    
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.function_handlers = get_function_handler_mapping()
    
    async def process_ai_interaction(
        self,
        db: Session,
        user: User,
        framework: BusinessFramework,
        conversation_history: List[Dict[str, Any]],
        user_input: str,
        session_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """AI対話を処理し、ストリーミングで結果を返す"""
        
        try:
            # システムプロンプトとツール設定
            system_prompt = get_framework_system_prompt(framework.name.lower().replace(' ', '_'))
            tool = get_tool_by_framework(framework.name.lower().replace(' ', '_'))
            
            # 会話履歴を準備
            conversation = self._prepare_conversation(conversation_history, user_input)
            
            # Gemini APIコール
            response = await self._call_gemini_api(
                system_prompt=system_prompt,
                conversation=conversation,
                tools=[tool]
            )
            
            # Function Callの処理
            if response.candidates[0].content.parts[0].function_call:
                function_call = response.candidates[0].content.parts[0].function_call
                
                # Function Callを実行
                function_result = await self._handle_function_call(
                    db=db,
                    user=user,
                    framework=framework,
                    function_call=function_call
                )
                
                yield {
                    "type": "function_call",
                    "function_name": function_call.name,
                    "arguments": dict(function_call.args),
                    "result": function_result,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Function Callの結果をGeminiに送信して最終応答を取得
                final_response = await self._call_gemini_with_function_result(
                    system_prompt=system_prompt,
                    conversation=conversation,
                    function_call=function_call,
                    function_result=function_result,
                    tools=[tool]
                )
                
                yield {
                    "type": "ai_response",
                    "content": final_response.text,
                    "is_complete": True,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
            else:
                # 通常のテキスト応答
                yield {
                    "type": "ai_response", 
                    "content": response.text,
                    "is_complete": False,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            yield {
                "type": "error",
                "message": f"AI処理エラー: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _prepare_conversation(
        self, 
        conversation_history: List[Dict[str, Any]], 
        user_input: str
    ) -> List[Dict[str, str]]:
        """会話履歴をGemini API用にフォーマット"""
        conversation = []
        
        # 履歴を追加
        for message in conversation_history:
            role = "user" if message.get("role") == "user" else "model"
            conversation.append({
                "role": role,
                "parts": [message.get("content", "")]
            })
        
        # 新しいユーザー入力を追加
        conversation.append({
            "role": "user",
            "parts": [user_input]
        })
        
        return conversation
    
    async def _call_gemini_api(
        self,
        system_prompt: str,
        conversation: List[Dict[str, Any]],
        tools: List[Any]
    ) -> GenerateContentResponse:
        """Gemini APIを呼び出す"""
        
        # システムプロンプトを最初に挿入
        full_conversation = [
            {"role": "user", "parts": [system_prompt]},
            {"role": "model", "parts": ["承知いたしました。お手伝いさせていただきます。"]},
            *conversation
        ]
        
        return await asyncio.to_thread(
            self.model.generate_content,
            full_conversation,
            tools=tools,
            tool_config={'function_calling_config': {'mode': 'AUTO'}}
        )
    
    async def _call_gemini_with_function_result(
        self,
        system_prompt: str,
        conversation: List[Dict[str, Any]],
        function_call: Any,
        function_result: Dict[str, Any],
        tools: List[Any]
    ) -> GenerateContentResponse:
        """Function Call実行後のGemini API呼び出し"""
        
        # Function Callの結果を会話に追加
        updated_conversation = [
            {"role": "user", "parts": [system_prompt]},
            {"role": "model", "parts": ["承知いたしました。お手伝いさせていただきます。"]},
            *conversation,
            {
                "role": "model", 
                "parts": [function_call]
            },
            {
                "role": "function",
                "parts": [{"function_response": {
                    "name": function_call.name,
                    "response": function_result
                }}]
            }
        ]
        
        return await asyncio.to_thread(
            self.model.generate_content,
            updated_conversation,
            tools=tools,
            tool_config={'function_calling_config': {'mode': 'AUTO'}}
        )
    
    async def _handle_function_call(
        self,
        db: Session,
        user: User,
        framework: BusinessFramework,
        function_call: Any
    ) -> Dict[str, Any]:
        """Function Callを実行し、結果を返す"""
        
        function_name = function_call.name
        function_args = dict(function_call.args)
        
        if function_name == "analyze_swot":
            return await self._handle_swot_analysis(db, user, framework, function_args)
        elif function_name == "create_user_journey":
            return await self._handle_user_journey_creation(db, user, framework, function_args)
        elif function_name == "create_business_model_canvas":
            return await self._handle_business_model_canvas_creation(db, user, framework, function_args)
        else:
            raise ValueError(f"Unsupported function: {function_name}")
    
    async def _handle_swot_analysis(
        self,
        db: Session,
        user: User,
        framework: BusinessFramework,
        function_args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """SWOT分析Function Callの処理"""
        
        try:
            # SWOT データの検証
            swot_data = SwotAnalyzer.validate_swot_data(function_args)
            
            # 分析結果の作成
            analysis_result = SwotAnalyzer.create_analysis_result(
                framework_id=str(framework.id),
                user_id=str(user.id),
                swot_data=swot_data
            )
            
            # アウトプットの保存
            output_data = SwotAnalyzer.format_swot_output(swot_data)
            output = OutputService.create_user_output(
                db=db,
                user_id=str(user.id),
                framework_id=str(framework.id),
                output_data=output_data,
                title=f"SWOT分析結果_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            
            # 完成度評価
            completeness = SwotAnalyzer.validate_completeness(swot_data)
            strategic_insights = SwotAnalyzer.get_strategic_insights(swot_data)
            
            return {
                "success": True,
                "analysis_id": analysis_result.id,
                "output_id": str(output.id),
                "summary": analysis_result.analysis_summary,
                "completeness": completeness,
                "strategic_insights": strategic_insights,
                "swot_data": swot_data.dict()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "SWOT分析の処理中にエラーが発生しました"
            }
    
    async def _handle_user_journey_creation(
        self,
        db: Session,
        user: User,
        framework: BusinessFramework,
        function_args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """User Journey Map作成Function Callの処理"""
        
        try:
            # Journey データの検証
            journey_data = JourneyAnalyzer.validate_journey_data(function_args)
            
            # 分析結果の作成
            analysis_result = JourneyAnalyzer.create_analysis_result(
                framework_id=str(framework.id),
                user_id=str(user.id),
                journey_data=journey_data
            )
            
            # アウトプットの保存
            output_data = JourneyAnalyzer.format_journey_output(journey_data)
            output = OutputService.create_user_output(
                db=db,
                user_id=str(user.id),
                framework_id=str(framework.id),
                output_data=output_data,
                title=f"ユーザージャーニーマップ_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            
            # 完成度評価
            completeness = JourneyAnalyzer.validate_completeness(journey_data)
            pain_points = JourneyAnalyzer.extract_pain_points(journey_data)
            opportunities = JourneyAnalyzer.extract_opportunities(journey_data)
            touchpoint_analysis = JourneyAnalyzer.get_touchpoint_analysis(journey_data)
            
            return {
                "success": True,
                "analysis_id": analysis_result.id,
                "output_id": str(output.id),
                "summary": analysis_result.analysis_summary,
                "completeness": completeness,
                "pain_points": pain_points,
                "opportunities": opportunities,
                "touchpoint_analysis": touchpoint_analysis,
                "journey_data": journey_data.dict()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "User Journey Map作成中にエラーが発生しました"
            }
    
    async def _handle_business_model_canvas_creation(
        self,
        db: Session,
        user: User,
        framework: BusinessFramework,
        function_args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Business Model Canvas作成Function Callの処理"""
        
        try:
            # 基本的なバリデーション
            required_fields = ["value_propositions", "customer_segments", "revenue_streams"]
            for field in required_fields:
                if field not in function_args or not function_args[field]:
                    raise ValueError(f"Required field missing: {field}")
            
            # アウトプットの保存
            output_data = {
                "type": "business_model_canvas",
                "canvas": function_args,
                "created_at": datetime.utcnow().isoformat()
            }
            
            output = OutputService.create_user_output(
                db=db,
                user_id=str(user.id),
                framework_id=str(framework.id),
                output_data=output_data,
                title=f"ビジネスモデルキャンバス_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            
            return {
                "success": True,
                "output_id": str(output.id),
                "summary": f"ビジネスモデルキャンバスが作成されました",
                "canvas_data": function_args
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Business Model Canvas作成中にエラーが発生しました"
            }