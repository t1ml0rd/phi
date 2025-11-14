from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import json
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Any, Dict
import uuid
from datetime import datetime, timezone
import sympy as sp
import math
import re
#from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Initialize LLM Chat
llm_api_key = os.environ.get('EMERGENT_LLM_KEY')

# Physics Topics and Subtopics
PHYSICS_TOPICS = {
    "Mechanics": {
        "subtopics": ["Newton's Laws", "Kinematics", "Dynamics", "Energy", "Momentum"],
        "units": ["m/s²", "m/s", "N", "J", "kg⋅m/s"]
    },
    "Electricity": {
        "subtopics": ["Ohm's Law", "Circuits", "Electric Field", "Current", "Voltage"],
        "units": ["V", "A", "Ω", "W", "C"]
    },
    "Optics": {
        "subtopics": ["Reflection", "Refraction", "Lenses", "Interference", "Diffraction"],
        "units": ["m", "°", "rad", "Hz", "nm"]
    },
    "Thermodynamics": {
        "subtopics": ["Heat Transfer", "Gas Laws", "Entropy", "Temperature", "Internal Energy"],
        "units": ["J", "K", "Pa", "mol", "cal"]
    }
}

# Pydantic Models
class PhysicsTask(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_text: str
    topic: str
    subtopic: Optional[str] = None
    difficulty: str
    parameters: Dict[str, float] = {}
    check_expression: str
    numerical_answer: float
    units: str
    solution_steps: List[str] = []
    latex: str
    diagram_svg: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TaskGenerationRequest(BaseModel):
    topic: str
    difficulty: str
    count: int = 1
    subtopic: Optional[str] = None

class AnswerCheckRequest(BaseModel):
    task_id: str
    user_answer: float
    tolerance: float = 1e-3

class AnswerCheckResponse(BaseModel):
    correct: bool
    feedback: str
    correct_answer: float
    explanation: Optional[str] = None

# Helper Functions
def validate_json_response(response_text: str) -> dict:
    """Extract and validate JSON from LLM response"""
    try:
        # Try to parse the entire response as JSON first
        return json.loads(response_text.strip())
    except json.JSONDecodeError:
        # Look for JSON within the response
        json_pattern = r'```json\s*(.*?)\s*```'
        match = re.search(json_pattern, response_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass
        
        # Look for JSON between braces
        brace_pattern = r'(\{.*\})'
        match = re.search(brace_pattern, response_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass
        
        raise ValueError("No valid JSON found in response")

def validate_physics_task(task_data: dict) -> bool:
    """Validate that the task data contains all required fields"""
    required_fields = ["task_text", "topic", "difficulty", "parameters", 
                      "check_expression", "numerical_answer", "units", 
                      "solution_steps", "latex"]
    
    for field in required_fields:
        if field not in task_data:
            return False
    
    # Validate numerical answer using sympy
    try:
        expr = sp.sympify(task_data["check_expression"])
        params = task_data["parameters"]
        
        # Substitute parameters into expression
        substituted = expr.subs(params)
        calculated_value = float(substituted.evalf())
        
        # Check if calculated value matches expected answer within tolerance
        return abs(calculated_value - task_data["numerical_answer"]) < 1e-6
        
    except Exception as e:
        logging.error(f"Validation error: {e}")
        return False

async def generate_physics_problem(topic: str, difficulty: str, subtopic: Optional[str] = None) -> dict:
    """Generate a physics problem using LLM"""
    
    subtopic_info = ""
    if subtopic and topic in PHYSICS_TOPICS:
        subtopic_info = f" focusing on {subtopic}"
    
    difficulty_guide = {
        "easy": "Basic concepts with simple numbers and straightforward calculations",
        "medium": "Intermediate concepts requiring multiple steps and moderate calculations", 
        "hard": "Advanced concepts with complex scenarios and challenging calculations"
    }
    
    system_message = f"""You are an expert physics problem generator. Generate physics problems that are educational, accurate, and solvable.

CRITICAL REQUIREMENTS:
1. Return ONLY valid JSON - no explanations, no markdown, no extra text
2. The JSON must follow this exact schema:
{{
  "task_text": "Clear problem statement with given values",
  "topic": "{topic}",
  "difficulty": "{difficulty}",
  "parameters": {{"variable1": value1, "variable2": value2}},
  "check_expression": "symbolic_expression",
  "numerical_answer": exact_numerical_result,
  "units": "appropriate_SI_units",
  "solution_steps": ["step1", "step2", "step3"],
  "latex": "\\\\displaystyle formula"
}}

3. The check_expression must be a valid SymPy expression using the parameter names
4. All parameter values must be realistic for {difficulty} level
5. The numerical_answer must be the exact result of evaluating check_expression with the given parameters
6. Include 2-4 solution steps that explain the physics concepts
7. Use LaTeX notation for the main formula

EXAMPLE for Mechanics/easy:
{{
  "task_text": "A car accelerates from rest with a constant acceleration of 3.0 m/s². What is the velocity after 5.0 seconds?",
  "topic": "Mechanics",
  "difficulty": "easy",
  "parameters": {{"a": 3.0, "t": 5.0, "v0": 0.0}},
  "check_expression": "v0 + a*t",
  "numerical_answer": 15.0,
  "units": "m/s",
  "solution_steps": ["Use the kinematic equation v = v₀ + at", "Substitute the given values", "v = 0 + (3.0)(5.0) = 15.0 m/s"],
  "latex": "\\\\displaystyle v = v_0 + at"
}}"""

    user_prompt = f"Generate a {difficulty} level {topic} physics problem{subtopic_info}. {difficulty_guide[difficulty]}. Return ONLY the JSON."
    
    chat = LlmChat(
        api_key=llm_api_key,
        session_id=f"physics_gen_{uuid.uuid4()}",
        system_message=system_message
    ).with_model("openai", "gpt-5")
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = await chat.send_message(UserMessage(text=user_prompt))
            task_data = validate_json_response(response)
            
            if validate_physics_task(task_data):
                return task_data
            else:
                logging.warning(f"Invalid task generated on attempt {attempt + 1}")
                
        except Exception as e:
            logging.error(f"Generation attempt {attempt + 1} failed: {e}")
            
        if attempt < max_retries - 1:
            user_prompt = "Please output valid JSON only. " + user_prompt
    
    # Fallback problem if generation fails
    return {
        "task_text": "A 2 kg object is acted upon by a force of 10 N. Calculate the acceleration.",
        "topic": "Mechanics",
        "difficulty": "easy",
        "parameters": {"m": 2.0, "F": 10.0},
        "check_expression": "F/m",
        "numerical_answer": 5.0,
        "units": "m/s²",
        "solution_steps": ["Apply Newton's second law: F = ma", "Rearrange to solve for a: a = F/m", "Substitute values: a = 10/2 = 5.0 m/s²"],
        "latex": "\\\\displaystyle a = \\\\frac{F}{m}"
    }

def generate_simple_diagram_svg(topic: str, task_text: str) -> str:
    """Generate a simple SVG diagram for visualization"""
    
    if "force" in task_text.lower() or topic == "Mechanics":
        # Force diagram
        return '''<svg width="200" height="150" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <marker id="arrowhead" markerWidth="10" markerHeight="7" 
                        refX="0" refY="3.5" orient="auto">
                    <polygon points="0 0, 10 3.5, 0 7" fill="#00E5FF" />
                </marker>
            </defs>
            <rect x="80" y="100" width="40" height="30" fill="#9AA7B2" stroke="#00E5FF" stroke-width="2"/>
            <text x="100" y="120" text-anchor="middle" fill="#00E5FF" font-size="12">m</text>
            <line x1="100" y1="100" x2="100" y2="50" stroke="#00E5FF" stroke-width="3" marker-end="url(#arrowhead)"/>
            <text x="110" y="75" fill="#00E5FF" font-size="14">F</text>
        </svg>'''
    
    elif "circuit" in task_text.lower() or topic == "Electricity":
        # Simple circuit diagram
        return '''<svg width="200" height="150" xmlns="http://www.w3.org/2000/svg">
            <line x1="50" y1="50" x2="150" y2="50" stroke="#00E5FF" stroke-width="2"/>
            <line x1="50" y1="50" x2="50" y2="100" stroke="#00E5FF" stroke-width="2"/>
            <line x1="150" y1="50" x2="150" y2="100" stroke="#00E5FF" stroke-width="2"/>
            <line x1="50" y1="100" x2="150" y2="100" stroke="#00E5FF" stroke-width="2"/>
            <rect x="90" y="40" width="20" height="20" fill="none" stroke="#00E5FF" stroke-width="2"/>
            <text x="100" y="55" text-anchor="middle" fill="#00E5FF" font-size="10">R</text>
            <text x="30" y="75" fill="#00E5FF" font-size="12">V</text>
        </svg>'''
    
    elif "lens" in task_text.lower() or "light" in task_text.lower() or topic == "Optics":
        # Lens diagram
        return '''<svg width="200" height="150" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <marker id="arrow" markerWidth="10" markerHeight="7" 
                        refX="0" refY="3.5" orient="auto">
                    <polygon points="0 0, 10 3.5, 0 7" fill="#A259FF" />
                </marker>
            </defs>
            <ellipse cx="100" cy="75" rx="5" ry="30" fill="none" stroke="#00E5FF" stroke-width="2"/>
            <line x1="30" y1="75" x2="90" y2="75" stroke="#A259FF" stroke-width="2" marker-end="url(#arrow)"/>
            <line x1="110" y1="75" x2="170" y2="75" stroke="#A259FF" stroke-width="2" marker-end="url(#arrow)"/>
            <text x="100" y="45" text-anchor="middle" fill="#00E5FF" font-size="12">Lens</text>
        </svg>'''
    
    else:
        # Generic physics diagram
        return '''<svg width="200" height="150" xmlns="http://www.w3.org/2000/svg">
            <circle cx="100" cy="75" r="30" fill="none" stroke="#00E5FF" stroke-width="2"/>
            <text x="100" y="80" text-anchor="middle" fill="#00E5FF" font-size="14">Physics</text>
            <line x1="70" y1="75" x2="130" y2="75" stroke="#A259FF" stroke-width="2"/>
        </svg>'''

# API Routes
@api_router.post("/generate", response_model=List[PhysicsTask])
async def generate_tasks(request: TaskGenerationRequest):
    """Generate physics problems"""
    try:
        # Validate request parameters
        if request.topic not in PHYSICS_TOPICS:
            raise HTTPException(status_code=400, detail=f"Invalid topic. Must be one of: {list(PHYSICS_TOPICS.keys())}")
        
        if request.difficulty not in ["easy", "medium", "hard"]:
            raise HTTPException(status_code=400, detail="Invalid difficulty. Must be 'easy', 'medium', or 'hard'")
        
        if request.count < 1 or request.count > 10:
            raise HTTPException(status_code=400, detail="Count must be between 1 and 10")
        
        tasks = []
        for _ in range(request.count):
            task_data = await generate_physics_problem(
                request.topic, 
                request.difficulty, 
                request.subtopic
            )
            
            # Generate diagram
            task_data["diagram_svg"] = generate_simple_diagram_svg(
                request.topic, 
                task_data["task_text"]
            )
            
            # Create task object
            task = PhysicsTask(**task_data)
            
            # Save to database
            task_dict = task.model_dump()
            task_dict['created_at'] = task_dict['created_at'].isoformat()
            await db.physics_tasks.insert_one(task_dict)
            
            tasks.append(task)
        
        return tasks
        
    except Exception as e:
        logging.error(f"Task generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate tasks: {str(e)}")

@api_router.post("/check", response_model=AnswerCheckResponse)
async def check_answer(request: AnswerCheckRequest):
    """Check if user's answer is correct"""
    try:
        # Validate request parameters
        if not request.task_id:
            raise HTTPException(status_code=400, detail="Task ID is required")
        
        if request.tolerance < 0 or request.tolerance > 1:
            raise HTTPException(status_code=400, detail="Tolerance must be between 0 and 1")
        
        # Retrieve task from database
        task_doc = await db.physics_tasks.find_one({"id": request.task_id}, {"_id": 0})
        
        if not task_doc:
            raise HTTPException(status_code=404, detail="Task not found")
        
        task = PhysicsTask(**task_doc)
        
        # Check if answer is within tolerance
        difference = abs(request.user_answer - task.numerical_answer)
        is_correct = difference <= request.tolerance * abs(task.numerical_answer)
        
        # Generate feedback
        if is_correct:
            feedback = "✅ Correct! Well done!"
            explanation = f"Your answer {request.user_answer} {task.units} is correct."
        else:
            feedback = "❌ Incorrect. Try again!"
            explanation = f"Your answer {request.user_answer} {task.units} is not correct. The expected answer is {task.numerical_answer} {task.units}."
            
            # Provide helpful hints based on the difference
            if difference > task.numerical_answer * 0.5:
                explanation += " Check your calculation method and unit conversions."
            elif difference > task.numerical_answer * 0.1:
                explanation += " You're close! Double-check your arithmetic."
        
        return AnswerCheckResponse(
            correct=is_correct,
            feedback=feedback,
            correct_answer=task.numerical_answer,
            explanation=explanation
        )
        
    except Exception as e:
        logging.error(f"Answer check error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check answer: {str(e)}")

@api_router.get("/history", response_model=List[PhysicsTask])
async def get_task_history(limit: int = 20):
    """Get recent physics tasks"""
    try:
        tasks = await db.physics_tasks.find({}, {"_id": 0}).sort([("created_at", -1)]).limit(limit).to_list(limit)
        
        # Convert ISO strings back to datetime objects
        for task in tasks:
            if isinstance(task.get('created_at'), str):
                task['created_at'] = datetime.fromisoformat(task['created_at'])
        
        return [PhysicsTask(**task) for task in tasks]
        
    except Exception as e:
        logging.error(f"History retrieval error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history: {str(e)}")

@api_router.get("/topics")
async def get_topics():
    """Get available physics topics and subtopics"""
    return PHYSICS_TOPICS

# Health check
@api_router.get("/")
async def root():
    return {"message": "AI Physics Task Generator API", "status": "active"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()