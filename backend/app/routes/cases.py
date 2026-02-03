"""
API routes for case uploads and evaluation.
"""

from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from typing import Optional, List
import json
import uuid
import asyncio

from app.models.case import CaseMetadata, CaseEvaluation, CaseRanking, HealthCheck
from app.services.evaluator import CaseEvaluator

router = APIRouter(prefix="/api", tags=["cases"])

# In-memory storage for evaluated cases (ephemeral)
evaluated_cases = {}
evaluator = CaseEvaluator()


@router.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint."""
    return HealthCheck(status="ok", message="Law Assistant backend is running")


@router.post("/evaluate-from-file", response_model=CaseEvaluation)
async def evaluate_from_file(
    file: UploadFile = File(...),
    title: str = Form(...),
    jurisdiction: str = Form(...),
    case_type: str = Form(...),
    claimed_damages: Optional[float] = Form(None)
):
    """
    Upload a case file and evaluate it.
    
    Supported file types: PDF, DOCX, TXT
    
    Args:
        file: Case document file
        title: Case title
        jurisdiction: Jurisdiction
        case_type: Type of case (Civil, Criminal, Commercial, Arbitration)
        claimed_damages: Optional claimed damages amount
        
    Returns:
        CaseEvaluation with scores and reasoning
    """
    try:
        # Validate inputs
        if case_type not in ["Civil", "Criminal", "Commercial", "Arbitration"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid case_type. Must be one of: Civil, Criminal, Commercial, Arbitration"
            )
        
        # Read file
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="File is empty")
        
        # Create metadata
        metadata = CaseMetadata(
            title=title,
            jurisdiction=jurisdiction,
            case_type=case_type,
            claimed_damages=claimed_damages
        )
        
        # Evaluate
        evaluation = await evaluator.evaluate_case_from_file(file_bytes, file.filename, metadata)
        
        # Store in memory (ephemeral)
        evaluated_cases[evaluation.case_id] = evaluation
        
        return evaluation
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


@router.post("/evaluate-text", response_model=CaseEvaluation)
async def evaluate_text(
    title: str = Form(...),
    jurisdiction: str = Form(...),
    case_type: str = Form(...),
    claimed_damages: Optional[float] = Form(None),
    case_text: str = Form(...)
):
    """
    Evaluate a case from raw text (no file upload).
    
    Args:
        title: Case title
        jurisdiction: Jurisdiction
        case_type: Type of case (Civil, Criminal, Commercial, Arbitration)
        claimed_damages: Optional claimed damages amount
        case_text: Case document text
        
    Returns:
        CaseEvaluation with scores and reasoning
    """
    try:
        # Validate inputs
        if case_type not in ["Civil", "Criminal", "Commercial", "Arbitration"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid case_type. Must be one of: Civil, Criminal, Commercial, Arbitration"
            )
        
        if not case_text.strip():
            raise HTTPException(status_code=400, detail="Case text cannot be empty")
        
        # Create metadata
        metadata = CaseMetadata(
            title=title,
            jurisdiction=jurisdiction,
            case_type=case_type,
            claimed_damages=claimed_damages
        )
        
        # Evaluate
        evaluation = await evaluator.evaluate_case_from_text(case_text, metadata)
        
        # Store in memory (ephemeral)
        evaluated_cases[evaluation.case_id] = evaluation
        
        return evaluation
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


@router.get("/cases", response_model=CaseRanking)
async def get_all_cases():
    """
    Get all evaluated cases ranked by priority score (highest first).
    
    Returns:
        List of cases ranked by priority_score descending
    """
    # Sort by priority_score descending
    sorted_cases = sorted(
        evaluated_cases.values(),
        key=lambda x: x.priority_score,
        reverse=True
    )
    
    return CaseRanking(
        cases=sorted_cases,
        total_cases=len(sorted_cases)
    )


@router.get("/cases/{case_id}", response_model=CaseEvaluation)
async def get_case(case_id: str):
    """
    Get a specific case by ID.
    
    Args:
        case_id: Unique case identifier
        
    Returns:
        CaseEvaluation
    """
    if case_id not in evaluated_cases:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
    
    return evaluated_cases[case_id]


@router.delete("/cases/{case_id}")
async def delete_case(case_id: str):
    """
    Delete a case from memory.
    
    Args:
        case_id: Unique case identifier
        
    Returns:
        Success message
    """
    if case_id not in evaluated_cases:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
    
    del evaluated_cases[case_id]
    return {"message": f"Case {case_id} deleted"}


@router.delete("/cases")
async def clear_all_cases():
    """Clear all evaluated cases."""
    global evaluated_cases
    count = len(evaluated_cases)
    evaluated_cases.clear()
    return {"message": f"Cleared {count} cases"}


@router.get("/disclaimer")
async def get_disclaimer():
    """Get legal disclaimer for all evaluations."""
    return {"disclaimer": CaseEvaluator.get_disclaimer()}


@router.post("/evaluate-batch", response_model=CaseRanking)
async def evaluate_batch(
    files: List[UploadFile] = File(...),
    titles: str = Form(...),
    jurisdictions: str = Form(...),
    case_types: str = Form(...),
    claimed_damages_list: Optional[str] = Form(None)
):
    """
    Evaluate multiple cases in parallel (batch upload).
    
    Args:
        files: List of case document files
        titles: JSON array of case titles (comma-separated or JSON)
        jurisdictions: JSON array of jurisdictions (comma-separated or JSON)
        case_types: JSON array of case types (comma-separated or JSON)
        claimed_damages_list: Optional JSON array of damages amounts
        
    Returns:
        CaseRanking with all cases evaluated and ranked
    """
    try:
        # Parse array inputs
        titles_list = json.loads(titles) if titles.startswith('[') else [t.strip() for t in titles.split(',')]
        jurisdictions_list = json.loads(jurisdictions) if jurisdictions.startswith('[') else [j.strip() for j in jurisdictions.split(',')]
        case_types_list = json.loads(case_types) if case_types.startswith('[') else [ct.strip() for ct in case_types.split(',')]
        damages_list = json.loads(claimed_damages_list) if claimed_damages_list and claimed_damages_list.startswith('[') else (
            [float(d) if d.strip() else None for d in claimed_damages_list.split(',')] if claimed_damages_list else []
        )
        
        # Validate counts
        num_files = len(files)
        if num_files == 0:
            raise HTTPException(status_code=400, detail="No files provided")
        if len(titles_list) != num_files or len(jurisdictions_list) != num_files or len(case_types_list) != num_files:
            raise HTTPException(
                status_code=400,
                detail=f"Mismatch: {num_files} files but {len(titles_list)} titles, {len(jurisdictions_list)} jurisdictions, {len(case_types_list)} case types"
            )
        
        # Pad damages list if needed
        while len(damages_list) < num_files:
            damages_list.append(None)
        
        # Create evaluation tasks
        tasks = []
        for i, file in enumerate(files):
            # Validate case type
            if case_types_list[i] not in ["Civil", "Criminal", "Commercial", "Arbitration"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid case_type at index {i}: {case_types_list[i]}"
                )
            
            # Create metadata
            metadata = CaseMetadata(
                title=titles_list[i],
                jurisdiction=jurisdictions_list[i],
                case_type=case_types_list[i],
                claimed_damages=damages_list[i]
            )
            
            # Create task
            task = evaluator.evaluate_case_from_file(
                await file.read(),
                file.filename,
                metadata
            )
            tasks.append(task)
        
        # Execute all evaluations in parallel
        evaluations = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any failures
        successful_evaluations = []
        errors = []
        for idx, result in enumerate(evaluations):
            if isinstance(result, Exception):
                errors.append({
                    "index": idx,
                    "file": files[idx].filename,
                    "error": str(result)
                })
            else:
                successful_evaluations.append(result)
                # Store in memory
                evaluated_cases[result.case_id] = result
        
        # Sort by priority score (descending)
        sorted_cases = sorted(
            successful_evaluations,
            key=lambda x: x.priority_score,
            reverse=True
        )
        
        # Return ranking with errors if any
        ranking = CaseRanking(
            cases=sorted_cases,
            total_cases=len(sorted_cases)
        )
        
        # If there were errors, include them in response
        if errors:
            return {
                **ranking.dict(),
                "errors": errors,
                "successful_count": len(successful_evaluations),
                "failed_count": len(errors)
            }
        
        return ranking
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch evaluation failed: {str(e)}")
