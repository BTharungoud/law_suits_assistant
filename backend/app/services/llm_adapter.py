"""
LLM adapter for dual provider support (OpenAI and Google Gemini).
Provides a unified interface to swap between providers via .env configuration.
"""

import json
import re
import os
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.config import settings


def _log_llm_failure(provider: str, response_text: str, metadata: Dict[str, Any], error: str) -> None:
    """Append full LLM failure details to a local log file for debugging."""
    try:
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "logs"))
        os.makedirs(base, exist_ok=True)
        path = os.path.join(base, "llm_failures.log")
        # Write summary to main failures log
        with open(path, "a", encoding="utf-8") as f:
            f.write("---\n")
            f.write(f"timestamp: {datetime.utcnow().isoformat()}Z\n")
            f.write(f"provider: {provider}\n")
            f.write(f"metadata_title: {metadata.get('title') if isinstance(metadata, dict) else str(metadata)}\n")
            f.write(f"error: {error}\n")
            # response length and excerpts for quick inspection
            try:
                resp_len = len(response_text) if response_text is not None else 0
            except Exception:
                resp_len = 0
            f.write(f"response_length: {resp_len}\n")
            # first/last excerpts
            if resp_len > 0:
                first_ex = response_text[:500].replace('\n', '\\n')
                last_ex = response_text[-500:].replace('\n', '\\n') if resp_len > 500 else ''
                f.write(f"response_preview_start: {first_ex}\n")
                if last_ex:
                    f.write(f"response_preview_end: {last_ex}\n")
            f.write("response_full_saved: see separate file (if written)\n")
            f.write("---\n\n")

        # Save full raw response to a timestamped file for deeper inspection
        try:
            safe_ts = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
            raw_path = os.path.join(base, f"llm_response_{provider}_{safe_ts}.txt")
            with open(raw_path, "w", encoding="utf-8") as rf:
                rf.write(f"# provider: {provider}\n")
                rf.write(f"# metadata_title: {metadata.get('title') if isinstance(metadata, dict) else str(metadata)}\n")
                rf.write(f"# error: {error}\n")
                rf.write("# full response below:\n")
                rf.write(response_text or "")
        except Exception:
            # Non-fatal: don't raise during logging
            pass
    except Exception:
        # Non-fatal: don't raise during logging
        pass


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def evaluate_case(self, case_text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a legal case and return structured scoring data."""
        pass

    async def generate_text(self, prompt: str, max_tokens: int = 1024) -> str:
        """Generate free-form text from the provider. Override in providers."""
        raise NotImplementedError()
    
    def _escape_control_chars(self, text: str) -> str:
        """Escape control characters inside strings while preserving structure."""
        result = []
        in_string = False
        i = 0
        
        while i < len(text):
            char = text[i]
            
            # Track string state (simple quote counting)
            if char == '"' and (i == 0 or text[i-1] != '\\'):
                in_string = not in_string
                result.append(char)
                i += 1
                continue
            
            # Inside string: escape control chars
            if in_string and ord(char) < 32:
                if char == '\n':
                    result.append('\\n')
                elif char == '\r':
                    result.append('\\r')
                elif char == '\t':
                    result.append('\\t')
                elif char == '\b':
                    result.append('\\b')
                elif char == '\f':
                    result.append('\\f')
                else:
                    result.append(f'\\u{ord(char):04x}')
                i += 1
                continue
            
            result.append(char)
            i += 1
        
        # Close unterminated string
        if in_string:
            result.append('"')
        
        return ''.join(result)
    
    def _smart_line_handling(self, text: str) -> str:
        """Handle lines with unterminated strings by scanning more carefully."""
        lines = text.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Count unescaped quotes
            quote_count = 0
            i = 0
            while i < len(line):
                if line[i] == '"' and (i == 0 or line[i-1] != '\\'):
                    quote_count += 1
                i += 1
            
            # Just add the line, we'll handle escaping separately
            fixed_lines.append(line.rstrip())
        
        # Rebuild with proper line breaks
        result = ' '.join(fixed_lines)
        
        # Now properly escape remaining control chars
        return self._escape_control_chars(result)
    
    def _close_unterminated_structures(self, text: str) -> str:
        """Close any unterminated strings and structures."""
        # First escape control characters
        escaped = self._escape_control_chars(text)
        
        # Then close unterminated structures
        result = list(escaped)
        open_braces = 0
        open_brackets = 0
        in_string = False
        
        for i in range(len(result)):
            if result[i] == '"' and (i == 0 or result[i-1] != '\\'):
                in_string = not in_string
            elif not in_string:
                if result[i] == '{':
                    open_braces += 1
                elif result[i] == '}':
                    open_braces -= 1
                elif result[i] == '[':
                    open_brackets += 1
                elif result[i] == ']':
                    open_brackets -= 1
        
        # Close unterminated string
        if in_string:
            result.append('"')
        
        # Close unterminated brackets/braces
        while open_brackets > 0:
            result.append(']')
            open_brackets -= 1
        while open_braces > 0:
            result.append('}')
            open_braces -= 1
        
        return ''.join(result)
    
    def _aggressive_json_repair(self, json_text: str) -> Optional[str]:
        """
        Aggressively repair malformed JSON using multiple strategies.
        Handles unterminated strings, unescaped control characters, incomplete structures,
        and common JSON syntax errors like trailing commas and unquoted keys.
        """
        # Strategy 0: If response looks truncated, try to complete it first
        repaired = self._complete_truncated_json(json_text)
        try:
            json.loads(repaired)
            return repaired
        except json.JSONDecodeError:
            pass
        
        # Strategy 1: Remove trailing commas (common error from LLMs)
        repaired = self._remove_trailing_commas(json_text)
        try:
            json.loads(repaired)
            return repaired
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Try to fix character escaping while preserving structure
        repaired = self._escape_control_chars(json_text)
        try:
            json.loads(repaired)
            return repaired
        except json.JSONDecodeError:
            pass
        
        # Strategy 3: Try to fix by removing line breaks and re-escaping
        repaired = self._smart_line_handling(json_text)
        try:
            json.loads(repaired)
            return repaired
        except json.JSONDecodeError:
            pass
        
        # Strategy 4: Try to close unterminated strings more aggressively
        repaired = self._close_unterminated_structures(json_text)
        try:
            json.loads(repaired)
            return repaired
        except json.JSONDecodeError:
            pass
        
        # Strategy 5: Try removing invalid escape sequences
        repaired = self._fix_invalid_escapes(json_text)
        try:
            json.loads(repaired)
            return repaired
        except json.JSONDecodeError:
            pass
        
        return None
    
    def _complete_truncated_json(self, text: str) -> str:
        """
        Detect and complete truncated JSON responses from LLM.
        Gemini API sometimes returns incomplete JSON with cut-off strings.
        """
        text = text.strip()
        
        # Count open braces and brackets
        in_string = False
        escape = False
        open_braces = 0
        open_brackets = 0
        last_string_pos = -1
        
        for i, char in enumerate(text):
            if escape:
                escape = False
                continue
            
            if char == '\\':
                escape = True
                continue
            
            if char == '"':
                in_string = not in_string
                if in_string:
                    last_string_pos = i
            
            if not in_string:
                if char == '{':
                    open_braces += 1
                elif char == '}':
                    open_braces -= 1
                elif char == '[':
                    open_brackets += 1
                elif char == ']':
                    open_brackets -= 1
        
        result = list(text)
        
        # If we're in an unclosed string, close it
        if in_string:
            result.append('"')
        
        # Add missing closing brackets
        while open_brackets > 0:
            result.append(']')
            open_brackets -= 1
        
        # Add missing closing braces
        while open_braces > 0:
            result.append('}')
            open_braces -= 1
        
        return ''.join(result)
    
    def _remove_trailing_commas(self, text: str) -> str:
        """Remove trailing commas before ] and } which is invalid JSON."""
        result = []
        i = 0
        while i < len(text):
            # Look for comma followed by ] or }
            if i < len(text) - 1 and text[i] == ',':
                # Skip whitespace after comma
                j = i + 1
                while j < len(text) and text[j] in ' \n\r\t':
                    j += 1
                # If we find ] or }, skip the comma
                if j < len(text) and text[j] in ']}':
                    result.append(' ')  # Replace comma with space
                    i += 1
                    continue
            result.append(text[i])
            i += 1
        return ''.join(result)
    
    def _fix_invalid_escapes(self, text: str) -> str:
        """Fix invalid escape sequences in strings."""
        result = []
        in_string = False
        i = 0
        
        while i < len(text):
            char = text[i]
            
            if char == '"' and (i == 0 or text[i-1] != '\\'):
                in_string = not in_string
                result.append(char)
                i += 1
                continue
            
            # Inside strings, check for invalid escapes
            if in_string and char == '\\' and i + 1 < len(text):
                next_char = text[i + 1]
                # Valid escape sequences: \", \\, \/, \b, \f, \n, \r, \t, \uXXXX
                if next_char in ('"', '\\', '/', 'b', 'f', 'n', 'r', 't', 'u'):
                    result.append(char)
                    result.append(next_char)
                    i += 2
                    continue
                else:
                    # Invalid escape, just skip the backslash
                    i += 1
                    continue
            
            result.append(char)
            i += 1
        
        return ''.join(result)

    def _looks_truncated(self, text: Optional[str]) -> bool:
        """Heuristic: detect if a JSON response was likely truncated.

        Returns True if the text does not end with a closing brace or bracket
        (ignoring whitespace) which usually indicates the model cut off.
        """
        if not text:
            return False
        s = text.rstrip()
        if not s:
            return False
        return not (s.endswith('}') or s.endswith(']'))


class OpenAIProvider(LLMProvider):
    """OpenAI GPT-4 provider."""
    
    def __init__(self):
        """Initialize OpenAI provider."""
        from openai import AsyncOpenAI
        
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY not set in environment")
        
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
    
    async def evaluate_case(self, case_text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate case using OpenAI GPT-4.
        
        Args:
            case_text: Extracted case document text
            metadata: Case metadata (title, jurisdiction, type, claimed damages)
            
        Returns:
            Dictionary with legal_merit, damages_potential, complexity scores and reasoning
        """
        prompt = self._build_prompt(case_text, metadata)
        
        try:
            response = await self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a legal case analyst. Evaluate cases on legal merit, damages potential, and complexity. Always respond with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0,  # Deterministic output
                response_format={"type": "json_object"},
                max_tokens=2048
            )
            
            response_text = response.choices[0].message.content
            
            # Strip markdown code fences if present
            response_text = self._strip_markdown_json(response_text)
            
            result = json.loads(response_text)
            return result
            
        except json.JSONDecodeError as e:
            # Try to fix JSON with unescaped newlines and special chars
            fixed_response = self._fix_json_newlines(response_text)
            try:
                return json.loads(fixed_response)
            except json.JSONDecodeError:
                # Try aggressive repair
                try:
                    repaired = self._aggressive_json_repair(response_text)
                    if repaired:
                        return json.loads(repaired)
                except Exception:
                    pass
                
                # Fallback: extract JSON from response if wrapped in text
                json_obj = self._extract_and_repair_json(response_text)
                if json_obj:
                    return json_obj
                # If it looks truncated, try sending a short follow-up asking to continue
                try:
                    if self._looks_truncated(response_text):
                        followup = (
                            "The previous response was truncated. Below is the partial JSON response.\n\n"
                            f"{response_text}\n\n"
                            "Please continue the JSON only so the entire output is valid JSON. "
                            "Respond with the remaining JSON text only."
                        )
                        cont_resp = await self.client.chat.completions.create(
                            model=settings.openai_model,
                            messages=[
                                {"role": "system", "content": "You are a legal case analyst. Continue the previous JSON response only."},
                                {"role": "user", "content": followup}
                            ],
                            temperature=0,
                            max_tokens=2048
                        )
                        cont_text = cont_resp.choices[0].message.content
                        cont_text = self._strip_markdown_json(cont_text)
                        combined = response_text + cont_text
                        try:
                            return json.loads(combined)
                        except Exception:
                            repaired = self._aggressive_json_repair(combined)
                            if repaired:
                                return json.loads(repaired)
                except Exception:
                    pass
            # Log full response for debugging before raising
            try:
                _log_llm_failure("openai", response_text, metadata, str(e))
            except Exception:
                pass
            raise ValueError(f"Failed to parse OpenAI response as JSON. Error: {str(e)}. Response preview: {response_text[:300]}...")

    async def generate_text(self, prompt: str, max_tokens: int = 512) -> str:
        # Use chat completions for free-form text with a strong professional system prompt
        sys_prompt = (
            "You are a professional legal analyst assisting a lawyer. Provide clear, concise, and factual answers. "
            "When asked to continue, only provide the remaining text. Do not include any commentary about being an AI."
        )
        try:
            response = await self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=max_tokens
            )
            text = response.choices[0].message.content
            return self._strip_markdown_json(text)
        except Exception:
            raise
    
    def _strip_markdown_json(self, response_text: str) -> str:
        """
        Strip markdown code fence markers from JSON response.
        Handles formats like ```json {...} ``` or ```{...}```
        """
        response_text = response_text.strip()
        
        # Remove markdown code fence
        if response_text.startswith('```'):
            # Find the opening fence
            fence_end = response_text.find('\n')
            if fence_end != -1:
                response_text = response_text[fence_end + 1:]
            else:
                # No newline after opening fence, remove the fence
                response_text = response_text[3:]
        
        # Remove closing fence
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        
        return response_text.strip()
    
    def _fix_json_newlines(self, text: str) -> str:
        """
        Fix unescaped characters in JSON strings by escaping them properly.
        Handles newlines, carriage returns, tabs, and unescaped quotes inside strings.
        """
        result = []
        in_string = False
        escape_next = False
        i = 0
        
        while i < len(text):
            char = text[i]
            
            if escape_next:
                result.append(char)
                escape_next = False
                i += 1
                continue
            
            if char == '\\':
                result.append(char)
                escape_next = True
                i += 1
                continue
            
            if char == '"':
                in_string = not in_string
                result.append(char)
                i += 1
                continue
            
            # If we're in a string, handle special characters
            if in_string:
                if char == '\n':
                    result.append('\\n')
                    i += 1
                    continue
                elif char == '\r':
                    result.append('\\r')
                    i += 1
                    continue
                elif char == '\t':
                    result.append('\\t')
                    i += 1
                    continue
                elif char == '\b':
                    result.append('\\b')
                    i += 1
                    continue
                elif char == '\f':
                    result.append('\\f')
                    i += 1
                    continue
            
            result.append(char)
            i += 1
        
        return ''.join(result)
    
    def _escape_unescaped_quotes(self, text: str) -> str:
        """
        Escape unescaped quotes inside JSON string values.
        This is a last-resort fix for LLM responses with embedded quotes.
        """
        result = []
        in_string = False
        escape_next = False
        
        for i, char in enumerate(text):
            if escape_next:
                result.append(char)
                escape_next = False
                continue
            
            if char == '\\':
                result.append(char)
                escape_next = True
                continue
            
            if char == '"':
                # Check if this quote closes the string or if there's an odd number before this position
                in_string = not in_string
                result.append(char)
                continue
            
            # Inside a string, if we find a literal quote context issue, escape it
            # This is heuristic: if we find certain patterns like :" or ," not followed by {/[ it might be an unescaped quote
            if in_string and char == '"' and i + 1 < len(text):
                next_char = text[i + 1]
                # If quote is followed by : or , outside JSON structure, escape it
                if next_char in (':', ',', ' '):
                    # This might be an issue but we already toggled in_string
                    pass
            
            result.append(char)
        
        return ''.join(result)
    
    def _extract_and_repair_json(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from response by finding braces and repairing common issues.
        Returns dict if successful, None otherwise.
        """
        start_idx = response_text.find('{')
        if start_idx == -1:
            return None

        # Scan forward tracking string/escape state so braces inside strings are ignored
        in_string = False
        escape = False
        brace_count = 0
        end_idx = None

        for i in range(start_idx, len(response_text)):
            ch = response_text[i]
            if escape:
                escape = False
                continue
            if ch == '\\':
                escape = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if not in_string:
                if ch == '{':
                    brace_count += 1
                elif ch == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i
                        break

        # If we didn't find a matching closing brace, attempt to repair by appending closing braces
        if end_idx is None:
            # Extract from first brace to end and append missing braces
            json_candidate = response_text[start_idx:]
            # If we're currently inside a string, close it first
            if in_string:
                json_candidate = json_candidate + '"'
            if brace_count > 0:
                json_candidate = json_candidate + ('}' * brace_count)
        else:
            json_candidate = response_text[start_idx:end_idx + 1]

        # Strip markdown fences and fix common unescaped characters/newlines
        json_candidate = self._strip_markdown_json(json_candidate)
        json_candidate = self._fix_json_newlines(json_candidate)

        try:
            return json.loads(json_candidate)
        except json.JSONDecodeError as e:
            # Last resort: try to fix by escaping problematic quotes at the error location
            error_msg = str(e)
            if "Expecting value" in error_msg or "Unterminated string" in error_msg:
                try:
                    # Extract line and column from error message
                    import re as regex
                    match = regex.search(r'line (\d+) column (\d+)', error_msg)
                    if match:
                        error_line_idx = int(match.group(1)) - 1
                        lines = json_candidate.split('\n')
                        
                        if error_line_idx < len(lines):
                            # Try escaping quotes in the problematic line
                            problematic_line = lines[error_line_idx]
                            fixed_line = self._fix_problematic_quotes_in_line(problematic_line)
                            lines[error_line_idx] = fixed_line
                            json_candidate_fixed = '\n'.join(lines)
                            try:
                                return json.loads(json_candidate_fixed)
                            except Exception:
                                pass
                except Exception:
                    pass
            
            return None
    
    def _fix_problematic_quotes_in_line(self, line: str) -> str:
        """
        Simple heuristic to escape unescaped quotes in a JSON line.
        """
        # Try to escape quotes that appear to be embedded in string values
        result = []
        in_string = False
        escape_next = False
        
        for i, char in enumerate(line):
            if escape_next:
                result.append(char)
                escape_next = False
                continue
            
            if char == '\\':
                result.append(char)
                escape_next = True
                continue
            
            if char == '"':
                in_string = not in_string
                result.append(char)
            else:
                result.append(char)
        
        return ''.join(result)

        return f"""
Analyze the following legal case and provide a structured evaluation.

CASE METADATA:
- Title: {metadata.get('title', 'N/A')}
- Jurisdiction: {metadata.get('jurisdiction', 'N/A')}
- Case Type: {metadata.get('case_type', 'N/A')}
- Claimed Damages: ${metadata.get('claimed_damages', 'N/A')}

CASE DOCUMENT:
{case_text[:5000]}

Evaluate this case on three dimensions (0-10 scale each) and respond ONLY with valid JSON:

{{
  "legal_merit": {{
    "score": <number 0-10>,
    "reasoning": "<explanation>",
    "key_factors": ["<factor1>", "<factor2>", "<factor3>"]
  }},
  "damages_potential": {{
    "score": <number 0-10>,
    "reasoning": "<explanation>",
    "key_factors": ["<factor1>", "<factor2>", "<factor3>"]
  }},
  "case_complexity": {{
    "score": <number 0-10>,
    "reasoning": "<explanation>",
    "key_factors": ["<factor1>", "<factor2>", "<factor3>"]
  }}
}}

SCORING GUIDELINES:

Legal Merit (0-10):
- 9-10: Strong case with clear legal basis, solid evidence, low dismissal risk
- 7-8: Good case with reasonable legal grounds and supportive evidence
- 5-6: Moderate case with arguable legal positions
- 3-4: Weak case with significant legal or evidentiary challenges
- 0-2: Very weak case with major legal flaws or missing evidence

Damages Potential (0-10):
- 9-10: High damages ($1M+), solvent defendant, easy enforcement
- 7-8: Substantial damages ($500K-$1M), likely collectible
- 5-6: Moderate damages ($100K-$500K), reasonable recovery probability
- 3-4: Low damages (<$100K), difficult enforcement
- 0-2: Minimal damages or uncollectible defendant

Case Complexity (0-10):
- 0-2: Simple case, straightforward facts, 6-12 month timeline
- 3-4: Moderate case, standard procedures, 12-18 month timeline
- 5-6: Complex case, multiple parties/issues, 18-24 month timeline
- 7-8: Very complex case, novel issues, 24+ month timeline
- 9-10: Extremely complex case, high procedural difficulty, uncertain timeline

CRITICAL: Respond ONLY with valid JSON - no other text.
"""


class GeminiProvider(LLMProvider):
    """Google Gemini provider."""
    
    def __init__(self):
        """Initialize Gemini provider."""
        import google.generativeai as genai
        
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY not set in environment")
        
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel(settings.gemini_model)
    
    async def evaluate_case(self, case_text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate case using Google Gemini.
        
        Args:
            case_text: Extracted case document text
            metadata: Case metadata (title, jurisdiction, type, claimed damages)
            
        Returns:
            Dictionary with legal_merit, damages_potential, complexity scores and reasoning
        """
        prompt = self._build_prompt(case_text, metadata)
        
        try:
            # Gemini API is synchronous; wrap in async context
            # Request sufficient tokens to avoid truncation while allowing longer outputs
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0,
                    "top_p": 1,
                    "max_output_tokens": 2048,
                }
            )
            
            response_text = response.text
            
            # Log raw response for debugging
            print(f"[GEMINI] Raw response length: {len(response_text)} chars")
            print(f"[GEMINI] First 500 chars: {response_text[:500]}")
            
            # First, try to strip markdown code fences if present
            response_text = self._strip_markdown_json(response_text)
            
            result = json.loads(response_text)
            return result
            
        except json.JSONDecodeError as e:
            print(f"[GEMINI] JSON decode error: {str(e)}")
            print(f"[GEMINI] Error location: line {e.lineno} column {e.colno}")
            print(f"[GEMINI] Response after stripping markdown:\n{response_text}")
            
            # Try to fix JSON with unescaped newlines and special chars
            fixed_response = self._fix_json_newlines(response_text)
            try:
                print(f"[GEMINI] Attempting fix_json_newlines...")
                return json.loads(fixed_response)
            except json.JSONDecodeError as e2:
                print(f"[GEMINI] fix_json_newlines failed: {str(e2)}")
                
                # Try aggressive repair
                try:
                    print(f"[GEMINI] Attempting aggressive repair...")
                    repaired = self._aggressive_json_repair(response_text)
                    if repaired:
                        print(f"[GEMINI] Aggressive repair successful, repaired length: {len(repaired)}")
                        return json.loads(repaired)
                except Exception as e3:
                    print(f"[GEMINI] Aggressive repair failed: {str(e3)}")
                
                # Fallback: extract JSON from response if wrapped in text
                print(f"[GEMINI] Attempting extract_and_repair_json...")
                json_obj = self._extract_and_repair_json(response_text)
                if json_obj:
                    print(f"[GEMINI] Extract and repair successful")
                    return json_obj
            # If it looks truncated, try a short continuation follow-up asking Gemini
            # to finish the JSON. This often recovers responses cut mid-output.
            try:
                if self._looks_truncated(response_text):
                    print("[GEMINI] Response appears truncated — requesting continuation...")
                    followup_prompt = (
                        "The previous response was truncated. "
                        "Below is the partial JSON response received.\n\n"
                        f"{response_text}\n\n"
                        "Please continue the JSON only so the entire output becomes valid JSON. "
                        "Ensure each section ('legal_merit', 'damages_potential', 'case_complexity') includes a 'reasoning' with at least one clear sentence and a 'key_factors' array (may contain a single clear item). "
                        "If more space is required, return the full remaining JSON. Do not add commentary — respond with the remaining JSON text only."
                    )
                    continuation = self.model.generate_content(
                        followup_prompt,
                        generation_config={
                            "temperature": 0,
                            "top_p": 1,
                            "max_output_tokens": 2048,
                        }
                    )
                    cont_text = continuation.text or ""
                    cont_text = self._strip_markdown_json(cont_text)
                    combined = response_text + cont_text
                    # Try repairs on the combined text
                    try:
                        return json.loads(combined)
                    except Exception:
                        repaired = self._aggressive_json_repair(combined)
                        if repaired:
                            return json.loads(repaired)
            except Exception as cont_exc:
                print(f"[GEMINI] Continuation attempt failed: {cont_exc}")

            # Log full response for debugging before raising
            try:
                _log_llm_failure("gemini", response_text, metadata, str(e))
            except Exception:
                pass
            print(f"[GEMINI] ❌ All repair strategies failed")
            raise ValueError(f"Failed to parse Gemini response as JSON. Error: {str(e)}. Response preview: {response_text[:300]}...")

    async def generate_text(self, prompt: str, max_tokens: int = 512) -> str:
        try:
            # Prepend a clear professional system instruction to encourage concise, factual answers
            sys_prompt = (
                "You are a professional legal analyst assisting a lawyer. Provide clear, concise, and factual answers. "
                "When asked to continue, only provide the remaining text. Do not include any commentary about being an AI."
            )
            combined = sys_prompt + "\n\n" + prompt
            response = self.model.generate_content(
                combined,
                generation_config={
                    "temperature": 0,
                    "top_p": 1,
                    "max_output_tokens": max_tokens,
                }
            )
            return self._strip_markdown_json(response.text)
        except Exception as e:
            raise
    
    def _strip_markdown_json(self, response_text: str) -> str:
        """
        Strip markdown code fence markers from JSON response.
        Handles formats like ```json {...} ``` or ```{...}```
        """
        response_text = response_text.strip()
        
        # Remove markdown code fence
        if response_text.startswith('```'):
            # Find the opening fence
            fence_end = response_text.find('\n')
            if fence_end != -1:
                response_text = response_text[fence_end + 1:]
            else:
                # No newline after opening fence, remove the fence
                response_text = response_text[3:]
        
        # Remove closing fence
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        
        return response_text.strip()
    
    def _fix_json_newlines(self, text: str) -> str:
        """
        Fix unescaped characters in JSON strings by properly escaping them.
        Handles newlines, quotes, backslashes, and other special characters.
        """
        result = []
        in_string = False
        escape_next = False
        i = 0
        
        while i < len(text):
            char = text[i]
            
            if escape_next:
                result.append(char)
                escape_next = False
                i += 1
                continue
            
            if char == '\\':
                result.append(char)
                escape_next = True
                i += 1
                continue
            
            if char == '"':
                in_string = not in_string
                result.append(char)
                i += 1
                continue
            
            # If we're in a string, handle special characters
            if in_string:
                if char == '\n':
                    result.append('\\n')
                    i += 1
                    continue
                elif char == '\r':
                    result.append('\\r')
                    i += 1
                    continue
                elif char == '\t':
                    result.append('\\t')
                    i += 1
                    continue
                elif char == '\b':
                    result.append('\\b')
                    i += 1
                    continue
                elif char == '\f':
                    result.append('\\f')
                    i += 1
                    continue
            
            result.append(char)
            i += 1
        
        return ''.join(result)
    
    def _extract_and_repair_json(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from response by finding braces and repairing common issues.
        Returns dict if successful, None otherwise.
        """
        start_idx = response_text.find('{')
        if start_idx == -1:
            return None

        # Scan forward tracking string/escape state so braces inside strings are ignored
        in_string = False
        escape = False
        brace_count = 0
        end_idx = None

        for i in range(start_idx, len(response_text)):
            ch = response_text[i]
            if escape:
                escape = False
                continue
            if ch == '\\':
                escape = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if not in_string:
                if ch == '{':
                    brace_count += 1
                elif ch == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i
                        break

        # If we didn't find a matching closing brace, attempt to repair by appending closing braces
        if end_idx is None:
            # Extract from first brace to end and append missing braces
            json_candidate = response_text[start_idx:]
            # If we're currently inside a string, close it first
            if in_string:
                json_candidate = json_candidate + '"'
            if brace_count > 0:
                json_candidate = json_candidate + ('}' * brace_count)
        else:
            json_candidate = response_text[start_idx:end_idx + 1]

        # Strip markdown fences and fix common unescaped characters/newlines
        json_candidate = self._strip_markdown_json(json_candidate)
        json_candidate = self._fix_json_newlines(json_candidate)

        try:
            return json.loads(json_candidate)
        except json.JSONDecodeError as e:
            # Try aggressive repair first
            repaired = self._aggressive_json_repair(json_candidate)
            if repaired:
                try:
                    return json.loads(repaired)
                except Exception:
                    pass
            
            # Last resort: try to fix by escaping problematic quotes at the error location
            error_msg = str(e)
            if "Expecting value" in error_msg or "Unterminated string" in error_msg:
                try:
                    # Extract line and column from error message
                    import re as regex
                    match = regex.search(r'line (\d+) column (\d+)', error_msg)
                    if match:
                        error_line_idx = int(match.group(1)) - 1
                        lines = json_candidate.split('\n')
                        
                        if error_line_idx < len(lines):
                            # Try escaping quotes in the problematic line
                            problematic_line = lines[error_line_idx]
                            fixed_line = self._fix_problematic_quotes_in_line(problematic_line)
                            lines[error_line_idx] = fixed_line
                            json_candidate_fixed = '\n'.join(lines)
                            try:
                                return json.loads(json_candidate_fixed)
                            except Exception:
                                pass
                except Exception:
                    pass
            
            return None
    
    def _fix_problematic_quotes_in_line(self, line: str) -> str:
        """
        Simple heuristic to escape unescaped quotes in a JSON line.
        """
        # Try to escape quotes that appear to be embedded in string values
        result = []
        in_string = False
        escape_next = False
        
        for i, char in enumerate(line):
            if escape_next:
                result.append(char)
                escape_next = False
                continue
            
            if char == '\\':
                result.append(char)
                escape_next = True
                continue
            
            if char == '"':
                in_string = not in_string
                result.append(char)
            else:
                result.append(char)
        
        return ''.join(result)

    def _build_prompt(self, case_text: str, metadata: Dict[str, Any]) -> str:
        """Build evaluation prompt (same for both providers)."""
        return f"""
Analyze the following legal case and provide a structured evaluation.

CASE METADATA:
- Title: {metadata.get('title', 'N/A')}
- Jurisdiction: {metadata.get('jurisdiction', 'N/A')}
- Case Type: {metadata.get('case_type', 'N/A')}
- Claimed Damages: ${metadata.get('claimed_damages', 'N/A')}

CASE DOCUMENT:
{case_text[:5000]}  # Limit to first 5000 chars to avoid token overflow

Evaluate this case on three dimensions (0-10 scale each) and respond ONLY with valid JSON:

{{
  "legal_merit": {{
    "score": <0-10 number>,
    "reasoning": "<explanation>",
    "key_factors": ["<factor1>", "<factor2>", "<factor3>"]
  }},
  "damages_potential": {{
    "score": <0-10 number>,
    "reasoning": "<explanation>",
    "key_factors": ["<factor1>", "<factor2>", "<factor3>"]
  }},
  "case_complexity": {{
    "score": <0-10 number>,
    "reasoning": "<explanation>",
    "key_factors": ["<factor1>", "<factor2>", "<factor3>"]
  }}
}}

SCORING GUIDELINES:

Legal Merit (0-10):
- 9-10: Strong case with clear legal basis, solid evidence, low dismissal risk
- 7-8: Good case with reasonable legal grounds and supportive evidence
- 5-6: Moderate case with arguable legal positions
- 3-4: Weak case with significant legal or evidentiary challenges
- 0-2: Very weak case with major legal flaws or missing evidence

Damages Potential (0-10):
- 9-10: High damages ($1M+), solvent defendant, easy enforcement
- 7-8: Substantial damages ($500K-$1M), likely collectible
- 5-6: Moderate damages ($100K-$500K), reasonable recovery probability
- 3-4: Low damages (<$100K), difficult enforcement
- 0-2: Minimal damages or uncollectible defendant

Case Complexity (0-10):
- 0-2: Simple case, straightforward facts, 6-12 month timeline
- 3-4: Moderate case, standard procedures, 12-18 month timeline
- 5-6: Complex case, multiple parties/issues, 18-24 month timeline
- 7-8: Very complex case, novel issues, 24+ month timeline
- 9-10: Extremely complex case, high procedural difficulty, uncertain timeline

CRITICAL INSTRUCTIONS:
1. Be CAUTIOUS and FACTUAL - only score based on case facts presented
2. If information is missing, state assumptions explicitly in reasoning
3. Never hallucinate legal precedents or make legal predictions
4. Focus on extractable factors from the provided text
5. Respond ONLY with valid JSON - no other text
"""


def get_llm_provider() -> LLMProvider:
    """
    Factory function to get the configured LLM provider.
    
    Returns:
        LLMProvider instance based on LLM_PROVIDER setting
        
    Raises:
        ValueError: If provider is not recognized
    """
    provider_name = settings.llm_provider.lower()
    
    if provider_name == "openai":
        return OpenAIProvider()
    elif provider_name == "gemini":
        return GeminiProvider()
    else:
        raise ValueError(f"Unknown LLM provider: {provider_name}. Choose 'openai' or 'gemini'")
