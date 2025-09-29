#!/usr/bin/env python3
"""
FastAPI Server for Drug-Surfactant Optimization

This provides a cloud-hosted API for executing drug-surfactant optimization protocols
via Railway or similar cloud platforms. It uses opentrons.execute instead of Jupyter notebook.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Optional, Union
import json
import os
import asyncio
import uuid
from datetime import datetime
import pandas as pd

from protocol_executor import ProtocolExecutor

app = FastAPI(
    title="Drug-Surfactant Optimization API",
    description="Cloud-hosted API for executing Opentrons protocols for drug-surfactant optimization",
    version="1.0.0"
)

# Global storage for experiment states (in production, use a proper database)
experiment_states = {}


class ExperimentConfig(BaseModel):
    """Configuration for an optimization experiment."""
    remote_user: str = "root"
    remote_host: str = "192.168.10.143"
    remote_folder: str = "/var/lib/jupyter/notebooks/Zeqing_Bao/drug_surfactant"
    optimization_trials: int = 5
    batch_size: int = 1
    simulate: bool = True


class OptimizationParameters(BaseModel):
    """Parameters for a single optimization trial."""
    s1: float = 0.0
    s2: float = 0.0
    s3: float = 0.0
    s4: float = 0.0
    s5: float = 0.0
    s6: float = 0.0
    s7: float = 0.0
    s8: float = 0.0
    s9: float = 0.0
    s10: float = 0.0
    s11: float = 0.0
    s12: float = 0.0
    surfactant_conc: float = 25.0
    drug_conc: float = 25.0


class ExperimentRequest(BaseModel):
    """Request to start a new optimization experiment."""
    config: Optional[ExperimentConfig] = None
    parameters: Optional[OptimizationParameters] = None


class ExperimentResponse(BaseModel):
    """Response with experiment information."""
    experiment_id: str
    status: str
    message: str
    created_at: str


class ExperimentStatus(BaseModel):
    """Status of an ongoing experiment."""
    experiment_id: str
    status: str
    progress: Dict
    results: Optional[Dict] = None
    error: Optional[str] = None


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Drug-Surfactant Optimization API",
        "version": "1.0.0",
        "description": "Cloud-hosted API for executing Opentrons protocols",
        "endpoints": [
            "/experiments/start - Start a new optimization experiment",
            "/experiments/{experiment_id}/status - Check experiment status",
            "/experiments/{experiment_id}/results - Get experiment results",
            "/experiments/list - List all experiments",
            "/health - Health check"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/experiments/start", response_model=ExperimentResponse)
async def start_experiment(
    request: ExperimentRequest,
    background_tasks: BackgroundTasks
):
    """Start a new optimization experiment."""
    experiment_id = str(uuid.uuid4())
    
    # Initialize experiment state
    experiment_states[experiment_id] = {
        "status": "initializing",
        "progress": {"current_trial": 0, "total_trials": 0},
        "results": None,
        "error": None,
        "created_at": datetime.now().isoformat(),
        "config": request.config.dict() if request.config else ExperimentConfig().dict()
    }
    
    # Start experiment in background
    background_tasks.add_task(run_experiment, experiment_id, request)
    
    return ExperimentResponse(
        experiment_id=experiment_id,
        status="started",
        message="Optimization experiment started",
        created_at=experiment_states[experiment_id]["created_at"]
    )


@app.get("/experiments/{experiment_id}/status", response_model=ExperimentStatus)
async def get_experiment_status(experiment_id: str):
    """Get the status of an experiment."""
    if experiment_id not in experiment_states:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    state = experiment_states[experiment_id]
    return ExperimentStatus(
        experiment_id=experiment_id,
        status=state["status"],
        progress=state["progress"],
        results=state["results"],
        error=state["error"]
    )


@app.get("/experiments/{experiment_id}/results")
async def get_experiment_results(experiment_id: str):
    """Get the results of a completed experiment."""
    if experiment_id not in experiment_states:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    state = experiment_states[experiment_id]
    
    if state["status"] != "completed":
        raise HTTPException(
            status_code=400, 
            detail=f"Experiment not completed. Current status: {state['status']}"
        )
    
    return {
        "experiment_id": experiment_id,
        "results": state["results"],
        "pareto_optimal": state.get("pareto_optimal", {}),
        "completed_at": state.get("completed_at")
    }


@app.get("/experiments/list")
async def list_experiments():
    """List all experiments with their basic information."""
    return [
        {
            "experiment_id": exp_id,
            "status": state["status"],
            "created_at": state["created_at"],
            "progress": state["progress"]
        }
        for exp_id, state in experiment_states.items()
    ]


@app.delete("/experiments/{experiment_id}")
async def delete_experiment(experiment_id: str):
    """Delete an experiment and its data."""
    if experiment_id not in experiment_states:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    del experiment_states[experiment_id]
    return {"message": f"Experiment {experiment_id} deleted"}


@app.post("/protocols/execute")
async def execute_single_protocol(
    parameters: OptimizationParameters,
    config: Optional[ExperimentConfig] = None
):
    """Execute a single protocol with given parameters."""
    try:
        # Create executor
        executor_config = config.dict() if config else None
        executor = ProtocolExecutor(config=executor_config)
        
        # Convert parameters to dict
        params_dict = parameters.dict()
        
        # Generate and execute protocol
        protocol_file = executor.generate_protocol_with_parameters(params_dict)
        
        simulate = config.simulate if config else True
        result = executor.execute_protocol(protocol_file, simulate=simulate)
        
        # Clean up
        if os.path.exists(protocol_file):
            os.unlink(protocol_file)
        
        return {
            "status": "success",
            "execution_result": result,
            "parameters": params_dict
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def run_experiment(experiment_id: str, request: ExperimentRequest):
    """Background task to run an optimization experiment."""
    try:
        # Update status
        experiment_states[experiment_id]["status"] = "running"
        
        # Create executor
        config = request.config.dict() if request.config else None
        executor = ProtocolExecutor(config=config)
        
        # Initialize optimizer for optimization experiments
        executor.ax_client = executor.initialize_optimizer()
        
        # Update progress
        total_trials = experiment_states[experiment_id]["config"]["optimization_trials"]
        experiment_states[experiment_id]["progress"]["total_trials"] = total_trials
        
        # Run optimization loop
        results_df = None
        if request.parameters:
            # Single protocol execution
            params_dict = request.parameters.dict()
            protocol_file = executor.generate_protocol_with_parameters(params_dict)
            
            simulate = experiment_states[experiment_id]["config"]["simulate"]
            result = executor.execute_protocol(protocol_file, simulate=simulate)
            
            experiment_states[experiment_id]["results"] = {
                "execution_result": result,
                "parameters": params_dict
            }
            
            # Clean up
            if os.path.exists(protocol_file):
                os.unlink(protocol_file)
        else:
            # Full optimization loop
            simulate = experiment_states[experiment_id]["config"]["simulate"]
            results_df = executor.run_optimization_loop(
                num_trials=total_trials,
                simulate=simulate
            )
            
            # Get Pareto optimal parameters
            pareto_params = executor.get_pareto_optimal_parameters()
            
            # Store results
            experiment_states[experiment_id]["results"] = results_df.to_dict("records")
            experiment_states[experiment_id]["pareto_optimal"] = pareto_params
        
        # Update final status
        experiment_states[experiment_id]["status"] = "completed"
        experiment_states[experiment_id]["completed_at"] = datetime.now().isoformat()
        
    except Exception as e:
        experiment_states[experiment_id]["status"] = "failed"
        experiment_states[experiment_id]["error"] = str(e)


# Add middleware for CORS if needed
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment (Railway sets this)
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )