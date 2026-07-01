import json
import logging
import os
from typing import Dict, Any, Optional
from langchain_groq import ChatGroq

logger = logging.getLogger(__name__)

REFLECTION_SYSTEM_PROMPT = """
You are an advanced meta-cognitive analyst responsible for evaluating an AI agent's execution output.
Given the task details and the generated output, you must extract key technical decisions, their reasoning, and generalizable lessons learned.

You must return your output strictly in JSON format matching this schema:
{
  "learned_info": "A concise, actionable general coding guideline or lesson learned that applies globally. E.g. 'Use asyncpg's acquire context manager inside FastAPI routes to prevent connection leaks.'",
  "decision": "The primary design decision or technical implementation choice made. E.g. 'Implement asyncpg connection pooling.'",
  "reasoning": "The rationale behind this decision. E.g. 'Standard single connections block under concurrent loads, whereas pooling allows reusing active connections.'",
  "outcome": "A short summary of the execution outcome. E.g. 'Successfully configured asyncpg connection pool and exposed CRUD endpoints.'"
}

Do not include any thinking block, markdown code blocks, or text surrounding the JSON. Output only the raw valid JSON.
"""

class MemoryReflectionEngine:
    @staticmethod
    async def extract_reflections(
        task_input: str,
        output_code: str,
        error_logs: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Uses an LLM call to dynamically reflect on an agent execution, extracting
        concrete lessons, design decisions, and outcomes. Falls back to structured
        heuristics if the LLM fails.
        """
        # Define fallback response first
        fallback_data = {
            "learned_info": f"Generated implementation patterns for task: '{task_input}'. Focus on modular code components and clear interface separation.",
            "decision": f"Implemented solution matching task specifications: '{task_input[:100]}...'",
            "reasoning": "Executed tasks based on repository context and requirements passed during planning.",
            "outcome": "Completed code generation steps successfully."
        }
        if error_logs:
            fallback_data["outcome"] = f"Failed during execution. Error: {error_logs[:150]}"
            fallback_data["learned_info"] = f"Avoid patterns leading to error: {error_logs[:150]}. Debug and verify imports/dependencies."

        api_key = os.environ.get("GROQ_API_KEY_1")
        if not api_key:
            logger.warning("[ReflectionEngine] GROQ_API_KEY_1 not set. Using fallback heuristic reflections.")
            return fallback_data

        try:
            llm = ChatGroq(
                model="llama-3.3-70b-versatile",
                api_key=api_key,
                temperature=0.1,
                max_tokens=1024,
            )

            prompt_user = f"""
            Task requested: {task_input}
            
            Agent code output:
            {output_code}
            
            Error logs (if any):
            {error_logs or "None"}
            """

            messages = [
                {"role": "system", "content": REFLECTION_SYSTEM_PROMPT},
                {"role": "user", "content": prompt_user}
            ]

            response = await llm.ainvoke(messages)
            raw = response.content.strip()

            # Clean markdown code block wraps if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip().rstrip("```").strip()

            data = json.loads(raw)
            # Ensure all required keys exist
            required_keys = ["learned_info", "decision", "reasoning", "outcome"]
            if all(k in data and isinstance(data[k], str) and data[k].strip() for k in required_keys):
                return {k: data[k].strip() for k in required_keys}
            
            logger.warning("[ReflectionEngine] LLM response lacked required keys or format: %s", raw)
            return fallback_data

        except Exception as e:
            logger.warning("[ReflectionEngine] LLM reflection failed: %s. Using fallbacks.", e)
            return fallback_data

memory_reflection_engine = MemoryReflectionEngine()
