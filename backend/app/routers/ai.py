from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import json
import asyncio
from datetime import datetime

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.middleware import require_premium
from app.models.user import User, BusinessFramework
from app.services.ai_service import AIConversationService
from app.services.framework_service import FrameworkService


router = APIRouter()


class ConversationMessage(BaseModel):
    role: str = Field(..., description="メッセージの送信者: 'user' または 'assistant'")
    content: str = Field(..., description="メッセージの内容")
    timestamp: Optional[str] = Field(None, description="メッセージのタイムスタンプ")


class AIInteractionRequest(BaseModel):
    framework_id: str = Field(..., description="使用するビジネスフレームワークのID")
    user_input: str = Field(..., description="ユーザーの入力内容")
    conversation_history: List[ConversationMessage] = Field(
        default=[],
        description="これまでの会話履歴"
    )
    session_id: Optional[str] = Field(None, description="学習セッションID（オプション）")
    context: Optional[Dict[str, Any]] = Field(None, description="追加のコンテキスト情報")


class AIInteractionResponse(BaseModel):
    type: str = Field(..., description="レスポンスタイプ: 'ai_response', 'function_call', 'error'")
    content: Optional[str] = Field(None, description="AI応答内容")
    function_name: Optional[str] = Field(None, description="実行された関数名")
    function_result: Optional[Dict[str, Any]] = Field(None, description="関数実行結果")
    is_complete: Optional[bool] = Field(None, description="分析が完了したかどうか")
    timestamp: str = Field(..., description="レスポンスのタイムスタンプ")
    error_message: Optional[str] = Field(None, description="エラーメッセージ")


@router.post("/interact")
@require_premium
async def ai_interact(
    request: AIInteractionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    AIコパイロットとの対話エンドポイント
    
    プレミアムユーザー限定機能として、指定されたフレームワークに基づいて
    AIが対話形式で分析をサポートします。
    """
    
    try:
        # フレームワークの存在確認
        framework = FrameworkService.get_framework_by_id(db, request.framework_id)
        if not framework:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定されたフレームワークが見つかりません"
            )
        
        # AI対話サービスを初期化
        ai_service = AIConversationService()
        
        # 会話履歴をフォーマット
        conversation_history = [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp
            }
            for msg in request.conversation_history
        ]
        
        # ストリーミング応答のジェネレータ
        async def generate_response():
            try:
                async for response_chunk in ai_service.process_ai_interaction(
                    db=db,
                    user=current_user,
                    framework=framework,
                    conversation_history=conversation_history,
                    user_input=request.user_input,
                    session_id=request.session_id
                ):
                    # レスポンスをJSON形式でストリーミング
                    yield f"data: {json.dumps(response_chunk, ensure_ascii=False)}\n\n"
                
                # ストリーム終了を示すメッセージ
                yield f"data: {json.dumps({'type': 'stream_end', 'timestamp': datetime.utcnow().isoformat()}, ensure_ascii=False)}\n\n"
                
            except Exception as e:
                error_response = {
                    "type": "error",
                    "error_message": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
                yield f"data: {json.dumps(error_response, ensure_ascii=False)}\n\n"
        
        # Server-Sent Events形式でストリーミングレスポンスを返す
        return StreamingResponse(
            generate_response(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI対話処理中にエラーが発生しました: {str(e)}"
        )


@router.get("/frameworks/{framework_id}/prompt")
async def get_framework_system_prompt(
    framework_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    指定されたフレームワークのシステムプロンプトを取得
    
    開発・デバッグ用途のエンドポイント
    """
    
    # フレームワークの存在確認
    framework = FrameworkService.get_framework_by_id(db, framework_id)
    if not framework:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="指定されたフレームワークが見つかりません"
        )
    
    try:
        from app.services.ai_function_declarations import get_framework_system_prompt
        
        framework_name = framework.name.lower().replace(' ', '_')
        system_prompt = get_framework_system_prompt(framework_name)
        
        return {
            "framework_id": framework_id,
            "framework_name": framework.name,
            "system_prompt": system_prompt,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"システムプロンプト取得中にエラーが発生しました: {str(e)}"
        )


@router.get("/supported-frameworks")
async def get_supported_frameworks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    AI対話がサポートされているフレームワークの一覧を取得
    """
    
    supported_frameworks = [
        {
            "name": "SWOT Analysis",
            "key": "swot_analysis",
            "description": "強み・弱み・機会・脅威の4象限で企業分析を行います"
        },
        {
            "name": "User Journey Map",
            "key": "user_journey_map", 
            "description": "顧客の体験プロセスを時系列で可視化します"
        },
        {
            "name": "Business Model Canvas",
            "key": "business_model_canvas",
            "description": "ビジネスモデルの9つの要素を整理します"
        }
    ]
    
    # データベースから実際のフレームワークと照合
    available_frameworks = []
    for fw_info in supported_frameworks:
        framework = db.query(BusinessFramework).filter(
            BusinessFramework.name.ilike(f"%{fw_info['name']}%")
        ).first()
        
        if framework:
            available_frameworks.append({
                "id": str(framework.id),
                "name": framework.name,
                "key": fw_info["key"],
                "description": fw_info["description"],
                "category": framework.category,
                "difficulty_level": framework.difficulty_level,
                "is_premium": framework.is_premium
            })
    
    return {
        "supported_frameworks": available_frameworks,
        "total_count": len(available_frameworks),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/test-function-call")
@require_premium
async def test_function_call(
    framework_name: str,
    test_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Function Callのテスト用エンドポイント
    
    開発・デバッグ用途
    """
    
    try:
        from app.services.ai_function_declarations import get_function_declaration_by_framework
        
        # Function Declarationを取得
        function_declaration = get_function_declaration_by_framework(framework_name)
        
        # テストデータの検証（実際の関数呼び出しはしない）
        if framework_name.lower() == "swot_analysis":
            from app.services.swot_analyzer import SwotAnalyzer
            swot_data = SwotAnalyzer.validate_swot_data(test_data)
            formatted_output = SwotAnalyzer.format_swot_output(swot_data)
            
            return {
                "success": True,
                "framework": framework_name,
                "function_declaration": {
                    "name": function_declaration.name,
                    "description": function_declaration.description
                },
                "validated_data": swot_data.dict(),
                "formatted_output": formatted_output
            }
        
        elif framework_name.lower() == "user_journey_map":
            from app.services.journey_analyzer import JourneyAnalyzer
            journey_data = JourneyAnalyzer.validate_journey_data(test_data)
            formatted_output = JourneyAnalyzer.format_journey_output(journey_data)
            
            return {
                "success": True,
                "framework": framework_name,
                "function_declaration": {
                    "name": function_declaration.name,
                    "description": function_declaration.description
                },
                "validated_data": journey_data.dict(),
                "formatted_output": formatted_output
            }
        
        else:
            return {
                "success": True,
                "framework": framework_name,
                "function_declaration": {
                    "name": function_declaration.name,
                    "description": function_declaration.description
                },
                "message": "基本的な検証のみ実行されました"
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Function Call テスト中にエラーが発生しました: {str(e)}"
        )