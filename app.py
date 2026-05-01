# app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random
from logic import KnowledgeBase

app = FastAPI()

# Allow cross-origin requests for the frontend GUI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global game state (for simplicity in this demonstration)
game_state = {}

class InitRequest(BaseModel):
    rows: int
    cols: int

class MoveRequest(BaseModel):
    x: int
    y: int

@app.post("/init")
def initialize_grid(req: InitRequest):
    """Initializes the grid with dynamic sizing and random hazards."""
    global game_state
    
    # Place Wumpus randomly (not at 0,0)
    wumpus = (random.randint(0, req.rows-1), random.randint(0, req.cols-1))
    while wumpus == (0, 0):
        wumpus = (random.randint(0, req.rows-1), random.randint(0, req.cols-1))
        
    # Place Pits randomly (~20% probability, not at 0,0)
    pits = []
    for r in range(req.rows):
        for c in range(req.cols):
            if (r, c) != (0, 0) and (r, c) != wumpus and random.random() < 0.2:
                pits.append((r, c))

    game_state = {
        "rows": req.rows,
        "cols": req.cols,
        "wumpus": wumpus,
        "pits": pits,
        "kb": KnowledgeBase(),
        "visited": [(0, 0)]
    }
    
    return {"message": "Grid initialized"}

@app.post("/move")
def move_agent(req: MoveRequest):
    """Processes an agent's move, generates percepts, and updates KB."""
    if not game_state:
        return {"error": "Game not initialized"}
        
    x, y = req.x, req.y
    state = game_state
    
    # Check if agent died
    if (x, y) == state["wumpus"] or (x, y) in state["pits"]:
        return {"status": "dead", "percepts": [], "safe_cells": []}

    state["visited"].append((x, y))

    # Generate Percepts based on actual hidden grid
    breeze = any(abs(x - px) + abs(y - py) == 1 for px, py in state["pits"])
    wx, wy = state["wumpus"]
    stench = abs(x - wx) + abs(y - wy) == 1

    percepts = []
    if breeze: percepts.append("Breeze")
    if stench: percepts.append("Stench")

    # Update Knowledge Base and trigger inference
    kb = state["kb"]
    kb.add_percept_rules(x, y, breeze, stench, state["rows"], state["cols"])

    # Determine safe cells using Resolution Refutation
    safe_cells = []
    for r in range(state["rows"]):
        for c in range(state["cols"]):
            if (r, c) not in state["visited"] and kb.is_safe(r, c):
                safe_cells.append({"x": r, "y": c})

    return {
        "status": "alive",
        "percepts": percepts,
        "safe_cells": safe_cells,
        "inference_steps": kb.inference_steps
    }