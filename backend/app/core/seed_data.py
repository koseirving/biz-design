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
            "micro_content": {
                "overview": "SWOT analysis is a strategic planning and strategic management technique used to help a person or organization identify Strengths, Weaknesses, Opportunities, and Threats related to business competition or project planning.",
                "components": {
                    "strengths": "Internal positive attributes and advantages",
                    "weaknesses": "Internal negative factors that detract from value",
                    "opportunities": "External factors that could provide competitive advantage",
                    "threats": "External factors that could cause trouble for the business"
                },
                "use_cases": ["Strategic planning", "Competitive analysis", "Business development", "Project planning"]
            }
        },
        {
            "name": "User Journey Map",
            "description": "A visualization of the process that a person goes through in order to accomplish a goal with your product or service.",
            "micro_content": {
                "overview": "User journey mapping is the process of creating a user journey map, a visualization used to understand and address customer needs and pain points.",
                "components": {
                    "persona": "The user type for whom the journey is being mapped",
                    "timeline": "The sequence of user actions over time",
                    "touchpoints": "All the points of interaction with your product/service",
                    "emotions": "User feelings and emotions throughout the journey"
                },
                "use_cases": ["Product development", "Service design", "Customer experience", "Digital transformation"]
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