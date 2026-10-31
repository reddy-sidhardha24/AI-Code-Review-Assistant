# ============================================================
# AI CODE REVIEW ASSISTANT
# backend/services/llm_service.py
# Unified Multi-Provider LLM Service (Groq, OpenAI, Gemini, Anthropic, Ollama)
# ============================================================

import os
import json
import requests
from typing import Dict, Any, Optional, Tuple


class LLMService:
    """
    Unified multi-provider LLM client. Dynamically routes review prompts
    to Groq, OpenAI, Gemini, Anthropic, or local Ollama instances.
    """

    def __init__(self, fallback_groq_key: Optional[str] = None):
        self.fallback_groq_key = fallback_groq_key or os.getenv("GROQ_API_KEY", "")

    def call(
        self,
        config: Optional[Dict[str, Any]],
        system_prompt: str,
        user_prompt: str,
        json_schema: Optional[Dict[str, Any]] = None,
        use_json_mode: bool = True,
    ) -> str:
        """
        Executes a completion using the provided config dictionary.
        If config is None, falls back to Groq with environment GROQ_API_KEY.
        """
        if not config:
            return self._call_fallback_groq(system_prompt, user_prompt, json_schema, use_json_mode)

        provider = (config.get("provider") or "groq").lower().strip()
        model_name = config.get("model_name") or "qwen/qwen3.8-27b"
        api_key = config.get("api_key") or ""
        base_url = config.get("base_url") or ""
        temperature = float(config.get("temperature", 0.1))
        max_tokens = int(config.get("max_tokens", 4096))

        try:
            if provider == "groq":
                return self._call_groq(api_key or self.fallback_groq_key, model_name, system_prompt, user_prompt, temperature, max_tokens, json_schema, use_json_mode)
            elif provider == "openai":
                return self._call_openai(api_key, model_name, base_url, system_prompt, user_prompt, temperature, max_tokens, json_schema, use_json_mode)
            elif provider == "gemini":
                return self._call_gemini(api_key, model_name, system_prompt, user_prompt, temperature, max_tokens)
            elif provider == "anthropic":
                return self._call_anthropic(api_key, model_name, system_prompt, user_prompt, temperature, max_tokens)
            elif provider == "ollama":
                return self._call_ollama(base_url or "http://localhost:11434", model_name, system_prompt, user_prompt, temperature, max_tokens)
            else:
                raise ValueError(f"Unsupported LLM provider: {provider}")
        except Exception as e:
            # Automatic graceful failover to Groq if local/external provider fails or times out
            if self.fallback_groq_key and provider != "groq":
                print(f"[LLMService] Provider '{provider}' encountered an error or timeout ({e}). Seamlessly failing over to cloud Groq (qwen/qwen3.8-27b)...")
                try:
                    return self._call_fallback_groq(system_prompt, user_prompt, json_schema, use_json_mode)
                except Exception as fallback_err:
                    print(f"[LLMService] Cloud Groq fallback also encountered: {fallback_err}")
            raise

    def test_connection(
        self,
        provider: str,
        model_name: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Sends a minimal verification prompt to validate credentials and connectivity.
        """
        try:
            sys_msg = "You are a test ping assistant."
            user_msg = "Respond ONLY with the single word: OK"
            prov = provider.lower().strip()

            if prov == "groq":
                resp = self._call_groq(api_key or self.fallback_groq_key, model_name or "llama-3.3-70b-versatile", sys_msg, user_msg, 0.1, 50, None)
            elif prov == "openai":
                resp = self._call_openai(api_key or "", model_name or "gpt-4o-mini", base_url, sys_msg, user_msg, 0.1, 50, None)
            elif prov == "gemini":
                resp = self._call_gemini(api_key or "", model_name or "gemini-2.5-flash", sys_msg, user_msg, 0.1, 50)
            elif prov == "anthropic":
                resp = self._call_anthropic(api_key or "", model_name or "claude-3-5-haiku-20241022", sys_msg, user_msg, 0.1, 50)
            elif prov == "ollama":
                resp = self._call_ollama(base_url or "http://localhost:11434", model_name, sys_msg, user_msg, 0.1, 50)
            else:
                return False, f"Unknown provider: {provider}"

            return True, f"Connection successful! Response: {resp[:60].strip()}"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

    # --------------------------------------------------------
    # GROQ IMPLEMENTATION
    # --------------------------------------------------------
    def _call_groq(
        self,
        api_key: str,
        model_name: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
        json_schema: Optional[Dict[str, Any]],
        use_json_mode: bool = True,
    ) -> str:
        from groq import Groq
        client = Groq(api_key=api_key)

        chosen_model = model_name or "qwen/qwen3.8-27b"
        if any(bad in chosen_model.lower() for bad in ["llama", "gpt-oss"]):
            chosen_model = "qwen/qwen3.8-27b"

        # qwen/qwen3.8-27b on Groq free tier enforces a strict 1000 OTPM (output tokens per minute) limit.
        # Keeping max_completion_tokens <= 900 guarantees Groq never rejects with 'Request too large'.
        if "qwen" in chosen_model.lower():
            max_comp = min(max_tokens, 900) if max_tokens else 900
        else:
            max_comp = min(max_tokens, 2048) if max_tokens else 1800

        kwargs: Dict[str, Any] = {
            "model": chosen_model,
            "temperature": temperature,
            "max_completion_tokens": max_comp,
            "messages": [
                {"role": "system", "content": f"{system_prompt}\n\nCRITICAL: Output a valid raw JSON object matching the required structure only."},
                {"role": "user", "content": user_prompt}
            ]
        }
        if use_json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        try:
            response = client.chat.completions.create(**kwargs)
            return response.choices[0].message.content or "{}"
        except Exception as groq_err:
            err_str = str(groq_err).lower()
            if use_json_mode and ("json_validate_failed" in err_str or "failed to validate json" in err_str or "400" in err_str):
                print(f"[LLMService] Groq json_object validation warning ({groq_err}). Retrying without response_format...")
                kwargs.pop("response_format", None)
                response = client.chat.completions.create(**kwargs)
                return response.choices[0].message.content or "{}"
            raise

    def _call_fallback_groq(
        self,
        system_prompt: str,
        user_prompt: str,
        json_schema: Optional[Dict[str, Any]],
        use_json_mode: bool = True,
    ) -> str:
        return self._call_groq(
            api_key=self.fallback_groq_key,
            model_name="qwen/qwen3.8-27b",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.1,
            max_tokens=900,
            json_schema=json_schema,
            use_json_mode=use_json_mode,
        )

    # --------------------------------------------------------
    # OPENAI IMPLEMENTATION
    # --------------------------------------------------------
    def _call_openai(
        self,
        api_key: str,
        model_name: str,
        base_url: Optional[str],
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
        json_schema: Optional[Dict[str, Any]],
        use_json_mode: bool = True,
    ) -> str:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url if base_url else None)

        kwargs: Dict[str, Any] = {
            "model": model_name,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }

        if not use_json_mode:
            pass
        elif json_schema:
            kwargs["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "structured_code_review",
                    "strict": True,
                    "schema": json_schema
                }
            }
        else:
            kwargs["response_format"] = {"type": "json_object"}

        response = client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or "{}"

    # --------------------------------------------------------
    # GOOGLE GEMINI IMPLEMENTATION
    # --------------------------------------------------------
    def _call_gemini(
        self,
        api_key: str,
        model_name: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            full_content = f"{system_prompt}\n\nIMPORTANT: Return pure JSON ONLY without markdown fences.\n\n{user_prompt}"
            response = client.models.generate_content(
                model=model_name or "gemini-2.5-flash",
                contents=full_content,
            )
            return response.text or "{}"
        except Exception as e:
            # Fallback to direct REST endpoint if SDK error occurs
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
            payload = {
                "contents": [
                    {"parts": [{"text": f"{system_prompt}\n\n{user_prompt}\n\nReturn strict JSON format only."}]}
                ],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                    "responseMimeType": "application/json"
                }
            }
            res = requests.post(url, json=payload, timeout=60)
            if res.status_code != 200:
                raise RuntimeError(f"Gemini API error ({res.status_code}): {res.text}")
            data = res.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    # --------------------------------------------------------
    # ANTHROPIC CLAUDE IMPLEMENTATION
    # --------------------------------------------------------
    def _call_anthropic(
        self,
        api_key: str,
        model_name: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        enhanced_system = f"{system_prompt}\n\nCRITICAL INSTRUCTION: Your response MUST be valid, raw JSON only. Do NOT wrap in ```json markdown codeblocks. Output only the pure JSON string."

        message = client.messages.create(
            model=model_name or "claude-3-5-sonnet-20241022",
            max_tokens=max_tokens,
            temperature=temperature,
            system=enhanced_system,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        return message.content[0].text or "{}"

    # --------------------------------------------------------
    # OLLAMA (LOCAL REST API) IMPLEMENTATION
    # --------------------------------------------------------
    def _call_ollama(
        self,
        base_url: str,
        model_name: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        clean_url = base_url.rstrip("/")
        endpoint = f"{clean_url}/api/chat"

        # Optimize context length and predict tokens for CPU/GPU efficiency
        options = {
            "temperature": temperature,
            "num_predict": min(max_tokens, 1024),
            "num_ctx": 2048
        }

        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": f"{system_prompt}\nOutput valid JSON only."},
                {"role": "user", "content": user_prompt[:7500]}
            ],
            "stream": False,
            "format": "json",
            "options": options
        }

        try:
            res = requests.post(endpoint, json=payload, timeout=75)
            if res.status_code != 200:
                err_body = res.text
                if "out-of-memory" in err_body or "allocate buffer" in err_body:
                    print(f"[Ollama] Memory tight for {model_name}, retrying with num_ctx=1024...")
                    payload["options"]["num_ctx"] = 1024
                    retry_res = requests.post(endpoint, json=payload, timeout=75)
                    if retry_res.status_code == 200:
                        data = retry_res.json()
                        return data.get("message", {}).get("content", "{}")
                    raise RuntimeError(f"Ollama ran out of memory loading '{model_name}'.")
                raise RuntimeError(f"Ollama returned HTTP {res.status_code}: {err_body}")
            data = res.json()
            return data.get("message", {}).get("content", "{}")
        except requests.exceptions.Timeout:
            raise RuntimeError(f"Ollama request timed out after 75s for model '{model_name}'.")
        except requests.exceptions.ConnectionError:
            raise RuntimeError(f"Cannot connect to Ollama at {clean_url}. Is Ollama running?")


llm_service = LLMService()

