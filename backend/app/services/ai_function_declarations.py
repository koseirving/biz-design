from typing import Dict, Any, List


def get_swot_function_declaration() -> Dict[str, Any]:
    """SWOT分析用のFunction Declarationを返す"""
    return {
        "name": "analyze_swot",
        "description": "企業の内部環境である「強み」「弱み」と、外部環境である「機会」「脅威」を特定し、企業の現状を分析する。4つの象限それぞれについて情報を収集する。",
        "parameters": {
            "type": "object",
            "properties": {
                "strengths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "自社が持つ、競合に対する優位性や特長。具体的で測定可能な強みを3-5項目程度"
                },
                "weaknesses": {
                    "type": "array", 
                    "items": {"type": "string"},
                    "description": "自社が持つ、競合に対する不利な点や課題。改善可能な弱みを3-5項目程度"
                },
                "opportunities": {
                    "type": "array",
                    "items": {"type": "string"}, 
                    "description": "市場成長や規制緩和など、自社にとって追い風となる外部要因。3-5項目程度"
                },
                "threats": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "競合の台頭や技術革新など、自社にとって逆風となる外部要因。3-5項目程度"
                }
            },
            "required": ["strengths", "weaknesses", "opportunities", "threats"]
        }
    }


def get_user_journey_function_declaration() -> Dict[str, Any]:
    """User Journey Map作成用のFunction Declarationを返す"""
    return {
        "name": "create_user_journey",
        "description": "特定のペルソナが製品やサービスを認知し、利用し、最終的なゴールに至るまでの一連の体験を時系列で可視化する。各ステージでの行動、思考、感情、課題点を明らかにする。",
        "parameters": {
            "type": "object",
            "properties": {
                "persona": {
                    "type": "string",
                    "description": "このジャーニーを体験するユーザーペルソナの名前や特徴。年齢、職業、課題など具体的に"
                },
                "goal": {
                    "type": "string", 
                    "description": "ユーザーが達成したい最終的な目標や成果"
                },
                "context": {
                    "type": "string",
                    "description": "ジャーニーが発生する背景や状況、きっかけ"
                },
                "stages": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "stage_name": {
                                "type": "string",
                                "description": "ジャーニーの段階名（例: 認知、検討、購入、利用、推奨）"
                            },
                            "user_actions": {
                                "type": "string", 
                                "description": "この段階でユーザーが具体的に行う行動"
                            },
                            "user_thoughts": {
                                "type": "string",
                                "description": "この段階でユーザーが考えていること、関心事"
                            },
                            "emotions": {
                                "type": "string",
                                "description": "この段階でユーザーが感じる感情（不安、期待、満足など）"
                            },
                            "pain_points": {
                                "type": "string",
                                "description": "この段階でユーザーが感じる不満や課題、障害"
                            },
                            "touchpoints": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "この段階でのタッチポイント（WebサイトやアプリなどUserと接点）"
                            },
                            "opportunities": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "この段階での体験改善の機会や施策案"
                            }
                        },
                        "required": ["stage_name", "user_actions", "pain_points"]
                    },
                    "description": "ジャーニーの各段階。認知→検討→購入→利用→推奨のような流れで3-7段階程度"
                }
            },
            "required": ["persona", "stages"]
        }
    }


def get_business_model_canvas_function_declaration() -> Dict[str, Any]:
    """Business Model Canvas作成用のFunction Declarationを返す"""
    return {
        "name": "create_business_model_canvas",
        "description": "ビジネスモデルの9つの要素を整理し、事業の全体像を一枚のキャンバスで可視化する。価値提案を中心に、顧客、提供方法、収益構造を明確化する。",
        "parameters": {
            "type": "object",
            "properties": {
                "value_propositions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "顧客に提供する価値や解決する課題。独自性のある価値提案"
                },
                "customer_segments": {
                    "type": "array", 
                    "items": {"type": "string"},
                    "description": "ターゲットとする顧客セグメント。具体的なペルソナや市場"
                },
                "channels": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "顧客にリーチし価値を届けるためのチャネル"
                },
                "customer_relationships": {
                    "type": "array",
                    "items": {"type": "string"}, 
                    "description": "顧客との関係性の種類やアプローチ方法"
                },
                "revenue_streams": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "収益を生み出す方法や仕組み"
                },
                "key_resources": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "事業運営に必要な重要なリソース"
                },
                "key_activities": {
                    "type": "array", 
                    "items": {"type": "string"},
                    "description": "価値提供のために実行すべき重要な活動"
                },
                "key_partnerships": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "事業成功のための重要なパートナーや協力関係"
                },
                "cost_structure": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "事業運営にかかる主要なコスト構造"
                }
            },
            "required": ["value_propositions", "customer_segments", "revenue_streams"]
        }
    }


def get_available_tools() -> List[Dict[str, Any]]:
    """利用可能なFunction Declaration toolsのリストを返す"""
    return [
        {"function_declarations": [get_swot_function_declaration()]},
        {"function_declarations": [get_user_journey_function_declaration()]},
        {"function_declarations": [get_business_model_canvas_function_declaration()]}
    ]


def get_function_declaration_by_framework(framework_name: str) -> Dict[str, Any]:
    """フレームワーク名に基づいてFunction Declarationを返す"""
    framework_mapping = {
        "swot_analysis": get_swot_function_declaration(),
        "user_journey_map": get_user_journey_function_declaration(), 
        "business_model_canvas": get_business_model_canvas_function_declaration()
    }
    
    if framework_name.lower() not in framework_mapping:
        raise ValueError(f"Unsupported framework: {framework_name}")
    
    return framework_mapping[framework_name.lower()]


def get_tool_by_framework(framework_name: str) -> Dict[str, Any]:
    """フレームワーク名に基づいてToolを返す"""
    function_declaration = get_function_declaration_by_framework(framework_name)
    return {"function_declarations": [function_declaration]}


def get_framework_system_prompt(framework_name: str) -> str:
    """フレームワーク別のシステムプロンプトを返す"""
    prompts = {
        "swot_analysis": """あなたはSWOT分析の専門家です。ユーザーの企業や事業について質問を通じて情報を収集し、
        強み・弱み・機会・脅威の4つの観点から分析をサポートします。
        
        以下の流れで進めてください：
        1. まず企業/事業の基本情報（業界、規模、主力商品/サービス）を確認
        2. 内部環境（強み・弱み）について質問
        3. 外部環境（機会・脅威）について質問
        4. 十分な情報が集まったらanalyze_swot関数を呼び出し
        
        質問は1度に1-2項目に絞り、具体的で答えやすい内容にしてください。""",
        
        "user_journey_map": """あなたはカスタマーエクスペリエンスの専門家です。ユーザーの製品・サービスについて質問し、
        顧客の体験ジャーニーを明確化するお手伝いをします。
        
        以下の流れで進めてください：
        1. 対象の製品・サービスと主要ペルソナを確認
        2. カスタマージャーニーの起点（認知のきっかけ）を確認
        3. 各段階での行動、感情、課題を順次確認
        4. 十分な情報が集まったらcreate_user_journey関数を呼び出し
        
        ユーザーの立場に立った共感的なアプローチで質問してください。""",
        
        "business_model_canvas": """あなたはビジネスモデル設計の専門家です。事業の9つの要素を整理し、
        持続可能なビジネスモデルの構築をサポートします。
        
        以下の流れで進めてください：
        1. 中核となる価値提案を確認
        2. ターゲット顧客セグメントを明確化
        3. 収益モデルを検討
        4. その他の要素（チャネル、リソース、パートナーなど）を順次確認
        5. 十分な情報が集まったらcreate_business_model_canvas関数を呼び出し
        
        実現可能性を考慮した現実的な提案を心がけてください。"""
    }
    
    return prompts.get(framework_name.lower(), 
                      "あなたはビジネスフレームワークの専門家です。ユーザーの事業分析をサポートしてください。")


def get_function_handler_mapping() -> Dict[str, str]:
    """Function Call名とハンドラー関数のマッピングを返す"""
    return {
        "analyze_swot": "handle_swot_analysis",
        "create_user_journey": "handle_user_journey_creation", 
        "create_business_model_canvas": "handle_business_model_canvas_creation"
    }