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
from app.utils.parsers import extract_text_from_file
from datetime import datetime
import uuid

router = APIRouter(prefix="/api", tags=["cases"])

# In-memory storage for evaluated cases (ephemeral)
evaluated_cases = {}
evaluated_case_texts = {}
evaluator = CaseEvaluator()


@router.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint."""
    return HealthCheck(status="ok", message="Law Assistant backend is running")


@router.post("/debug/seed-case")
async def seed_case(title: str = "Seed Case for Chat Testing"):
    """DEV-ONLY: Insert a synthetic evaluated case for testing chat UI and endpoints.

    This endpoint creates a mock `CaseEvaluation` object and stores it in the
    in-memory `evaluated_cases` and `evaluated_case_texts` structures.
    """
    case_id = uuid.uuid4().hex[:8]
    now = datetime.utcnow()

    # Simple mock explanations
    legal = {
        "score": 7.0,
        "reasoning": "Reasonable legal grounds based on regulatory ambiguity and referral to the CJEU.",
        "key_factors": [
            "Referral to CJEU indicates non-trivial legal question",
            "Specific regulatory ambiguity (PRIIPs)"
        ]
    }
    damages = {
        "score": 0.0,
        "reasoning": "Preliminary ruling proceedings do not typically produce direct monetary awards.",
        "key_factors": ["Preliminary ruling procedure", "No claimed damages"]
    }
    complexity = {
        "score": 7.0,
        "reasoning": "Complex EU regulatory interpretation and technical valuation issues.",
        "key_factors": ["EU regulatory interpretation", "Technical valuation methodology"]
    }

    priority_score = round((legal["score"] * 0.4) + (damages["score"] * 0.4) - (complexity["score"] * 0.2), 3)
    if priority_score >= 7:
        rank = "High"
    elif priority_score >= 4:
        rank = "Medium"
    else:
        rank = "Low"

    eval_obj = CaseEvaluation(
        case_id=case_id,
        case_title=title,
        legal_merit=legal,
        damages_potential=damages,
        case_complexity=complexity,
        priority_score=priority_score,
        priority_rank=rank,
        priority_reasoning=f"Computed for testing: legal {legal['score']}, damages {damages['score']}, complexity {complexity['score']}",
        created_at=now
    )

    evaluated_cases[case_id] = eval_obj
    evaluated_case_texts[case_id] = "(seeded test case content)"

    return {"case_id": case_id, "case_title": title}


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

        # Extract text once (avoid double work) and create metadata
        case_text = extract_text_from_file(file_bytes, file.filename)

        metadata = CaseMetadata(
            title=title,
            jurisdiction=jurisdiction,
            case_type=case_type,
            claimed_damages=claimed_damages
        )

        # Evaluate
        try:
            evaluation = await evaluator.evaluate_case_from_text(case_text, metadata)
            # Store in memory (ephemeral)
            evaluated_cases[evaluation.case_id] = evaluation
            evaluated_case_texts[evaluation.case_id] = case_text
            return evaluation
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            err_str = str(e)
            raise HTTPException(status_code=500, detail=f"Evaluation failed: {err_str}")
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


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
        evaluated_case_texts[evaluation.case_id] = case_text

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


@router.post("/cases/{case_id}/chat")
async def chat_case(case_id: str, message: str = Form(...)):
    """
    Chat with LLM about a specific evaluated case.
    Accepts a single-form field `message` and returns a text reply from the LLM.
    """
    if case_id not in evaluated_cases:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    # Get stored case text (may be empty if original not saved)
    case_text = evaluated_case_texts.get(case_id, "")
    evaluation: CaseEvaluation = evaluated_cases[case_id]

    # Build a compact context prompt for the chat
    prompt_parts = []
    prompt_parts.append(f"You are a helpful legal analyst. The user will ask questions about a previously evaluated case.")
    prompt_parts.append(f"Case title: {evaluation.case_title}")
    prompt_parts.append(f"Summary evaluation:\nLegal merit: {evaluation.legal_merit.score} - {evaluation.legal_merit.reasoning}\nDamages potential: {evaluation.damages_potential.score} - {evaluation.damages_potential.reasoning}\nComplexity: {evaluation.case_complexity.score} - {evaluation.case_complexity.reasoning}")
    if case_text:
        prompt_parts.append(f"Case document (first 4000 chars):\n{case_text[:4000]}")
    prompt_parts.append(f"User question: {message}")
    prompt_parts.append("Answer succinctly, and when useful cite the evaluation key factors. Keep responses factual and avoid legal advice phrasing.")

    prompt = "\n\n".join(prompt_parts)

    # Use evaluator's provider to generate a text reply
    provider = evaluator.llm_provider
    try:
        # If this is a seeded debug case, synthesize a local reply to avoid external LLM calls
        if evaluation.case_title and (evaluation.case_title.lower().startswith('seed') or 'seed' in evaluation.case_title.lower()):
            # Build a concise, professional reply from the stored evaluation
            assumed_pct = int(round((evaluation.legal_merit.score / 10.0) * 100))
            reply_parts = []
            reply_parts.append(f"Assumed success probability: {assumed_pct}%.")
            reply_parts.append(f"Rationale: {evaluation.legal_merit.reasoning}")
            reply_parts.append("Key factors considered:")
            for k in evaluation.legal_merit.key_factors[:5]:
                reply_parts.append(f"- {k}")
            reply = "\n\n".join(reply_parts)
        else:
            # Prefer provider-specific fast text generation; allow larger responses
            reply = await provider.generate_text(prompt, max_tokens=1024)
        # If the reply looks truncated, attempt up to two short continuation calls and append
        attempts = 0
        while attempts < 2:
            attempts += 1
            try:
                if hasattr(provider, '_looks_truncated') and provider._looks_truncated(reply):
                    cont_prompt = "Continue the previous answer only. Continue from where you left off and provide the remaining text without commentary."
                    cont = await provider.generate_text(cont_prompt, max_tokens=512)
                    if cont and cont.strip():
                        reply = reply + cont
                        # If continuation no longer looks truncated, stop
                        if not provider._looks_truncated(reply):
                            break
                        else:
                            continue
                # Also treat abrupt sentence ending as potential truncation
                if reply and not reply.strip().endswith(('.', '!', '?', '"')):
                    cont_prompt = "Continue the previous answer only. Continue from where you left off and provide the remaining text without commentary."
                    cont = await provider.generate_text(cont_prompt, max_tokens=512)
                    if cont and cont.strip():
                        reply = reply + cont
                        if not provider._looks_truncated(reply):
                            break
                        else:
                            continue
                break
            except Exception:
                # If continuation attempt fails, stop trying further to avoid long delays
                break
    except AttributeError:
        # If provider doesn't implement generate_text, fall back to evaluate_case (not ideal)
        raise HTTPException(status_code=500, detail="LLM provider does not support conversational chat")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat generation failed: {str(e)}")

    return {"answer": reply}


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


@router.post("/evaluate-batch")
async def evaluate_batch(
    files: List[UploadFile] = File(...),
    titles: str = Form(...),
    jurisdictions: str = Form(...),
    case_types: str = Form(...),
    claimed_damages_list: Optional[str] = Form(None)
):
    """
    Evaluate multiple cases in parallel (batch upload).
    
    Returns batch evaluation results with detailed error reporting.
    """
    try:
        # Validate files first
        num_files = len(files)
        if num_files == 0:
            raise HTTPException(status_code=400, detail="No files provided")
        
        # Check each file has content
        file_sizes = []
        for i, file in enumerate(files):
            file_bytes = await file.read()
            if not file_bytes:
                raise HTTPException(
                    status_code=400,
                    detail=f"File {i} ({file.filename}) is empty. Please ensure files contain data before uploading."
                )
            file_sizes.append(len(file_bytes))
        
        # Reset file pointers after reading for size check
        for file in files:
            await file.seek(0)
        
        # Parse array inputs - handle both JSON arrays and comma-separated strings
        def parse_json_or_csv(value: str, is_numeric: bool = False) -> list:
            """Parse JSON array or comma-separated values."""
            if not value:
                return []
            value = value.strip()
            if value.startswith('['):
                try:
                    parsed = json.loads(value)
                    if is_numeric:
                        # Convert to float, handling null values
                        return [float(v) if v is not None else None for v in parsed]
                    else:
                        # Strip whitespace from strings
                        return [str(v).strip() if v is not None else None for v in parsed]
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON format: {str(e)}")
            else:
                if is_numeric:
                    return [float(d.strip()) if d.strip() else None for d in value.split(',')]
                else:
                    return [v.strip() for v in value.split(',')]
        
        titles_list = parse_json_or_csv(titles)
        jurisdictions_list = parse_json_or_csv(jurisdictions)
        case_types_list = parse_json_or_csv(case_types)
        damages_list = parse_json_or_csv(claimed_damages_list, is_numeric=True) if claimed_damages_list else []
        
        # Validate counts
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
            
            # Read file bytes
            file_bytes = await file.read()
            if not file_bytes:
                raise HTTPException(
                    status_code=400,
                    detail=f"File {i} ({file.filename}) is empty or could not be read"
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
                file_bytes,
                file.filename,
                metadata
            )
            tasks.append(task)
        
        # Execute all evaluations in parallel
        evaluations = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any failures, always return a result for every file
        successful_evaluations = []
        errors = []
        for idx, result in enumerate(evaluations):
            if isinstance(result, Exception):
                # Try to extract raw LLM output if present in the exception
                raw_llm = None
                err_str = str(result)
                # If the exception has a 'response_text' or similar, include it
                if hasattr(result, 'response_text'):
                    raw_llm = getattr(result, 'response_text')
                # If the error string contains a preview, try to extract it
                preview = None
                if 'Response preview:' in err_str:
                    preview = err_str.split('Response preview:')[-1].strip()
                errors.append({
                    "index": idx,
                    "file": files[idx].filename,
                    "error": err_str,
                    "raw_llm_response": raw_llm or preview
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

        # Always return a detailed response with error information
        response = {
            "cases": [case.dict() for case in sorted_cases],
            "total_cases": len(sorted_cases),
            "successful_count": len(successful_evaluations),
            "failed_count": len(errors),
            "errors": errors
        }

        return response
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"Batch evaluation failed: {str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)
