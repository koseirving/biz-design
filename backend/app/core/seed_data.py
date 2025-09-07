from app.core.database import SessionLocal
from app.models.user import BusinessFramework
import uuid

def seed_business_frameworks():
    """Seed initial business frameworks data"""
    db = SessionLocal()
    
    frameworks = [
        {
            "name": "SWOT Analysis",
            "description": "Strategic planning technique to evaluate Strengths, Weaknesses, Opportunities, and Threats involved in a project or business venture.",
            "category": "strategy",
            "difficulty_level": "beginner",
            "estimated_duration": 45,
            "is_premium": True,
            "micro_content": {
                "overview": "SWOT analysis is a strategic planning and strategic management technique used to help a person or organization identify Strengths, Weaknesses, Opportunities, and Threats related to business competition or project planning.",
                "components": {
                    "strengths": {
                        "title": "Strengths",
                        "description": "Internal positive attributes and advantages",
                        "examples": ["Strong brand recognition", "Skilled workforce", "Financial resources", "Unique technology"]
                    },
                    "weaknesses": {
                        "title": "Weaknesses", 
                        "description": "Internal negative factors that detract from value",
                        "examples": ["Limited resources", "Poor location", "Lack of expertise", "Weak online presence"]
                    },
                    "opportunities": {
                        "title": "Opportunities",
                        "description": "External factors that could provide competitive advantage",
                        "examples": ["Market growth", "New technology", "Regulatory changes", "Partnership potential"]
                    },
                    "threats": {
                        "title": "Threats",
                        "description": "External factors that could cause trouble for the business",
                        "examples": ["Economic downturn", "New competitors", "Regulatory changes", "Changing consumer preferences"]
                    }
                },
                "use_cases": ["Strategic planning", "Competitive analysis", "Business development", "Project planning"],
                "steps": [
                    "Identify internal strengths",
                    "Identify internal weaknesses", 
                    "Identify external opportunities",
                    "Identify external threats",
                    "Analyze relationships between elements"
                ]
            }
        },
        {
            "name": "User Journey Map",
            "description": "A visualization of the process that a person goes through in order to accomplish a goal with your product or service.",
            "category": "design",
            "difficulty_level": "intermediate",
            "estimated_duration": 60,
            "is_premium": False,
            "micro_content": {
                "overview": "User journey mapping is the process of creating a user journey map, a visualization used to understand and address customer needs and pain points.",
                "components": {
                    "persona": {
                        "title": "User Persona",
                        "description": "The user type for whom the journey is being mapped",
                        "examples": ["Demographics", "Goals", "Motivations", "Pain points"]
                    },
                    "timeline": {
                        "title": "Timeline/Stages",
                        "description": "The sequence of user actions over time",
                        "examples": ["Awareness", "Consideration", "Purchase", "Usage", "Advocacy"]
                    },
                    "touchpoints": {
                        "title": "Touchpoints",
                        "description": "All the points of interaction with your product/service",
                        "examples": ["Website", "Mobile app", "Customer service", "Social media", "Email"]
                    },
                    "emotions": {
                        "title": "Emotions",
                        "description": "User feelings and emotions throughout the journey",
                        "examples": ["Excited", "Confused", "Frustrated", "Satisfied", "Delighted"]
                    }
                },
                "use_cases": ["Product development", "Service design", "Customer experience", "Digital transformation"],
                "steps": [
                    "Define user persona and goals",
                    "Map out journey stages",
                    "Identify touchpoints at each stage",
                    "Document user emotions and pain points",
                    "Find opportunities for improvement"
                ]
            }
        }
    ]
    
    for framework_data in frameworks:
        # Check if framework already exists
        existing = db.query(BusinessFramework).filter(
            BusinessFramework.name == framework_data["name"]
        ).first()
        
        if not existing:
            framework = BusinessFramework(
                id=uuid.uuid4(),
                **framework_data
            )
            db.add(framework)
    
    db.commit()
    db.close()
    print("Business frameworks seeded successfully!")

if __name__ == "__main__":
    seed_business_frameworks()