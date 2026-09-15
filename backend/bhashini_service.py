"""
SAMVAD AI — Bhashini Speech-to-Text Integration Layer
Provides an adapter for Digital India BHASHINI Automatic Speech Recognition (ASR).

IMPORTANT NOTICE:
- Never hardcode credentials, tokens, or secrets.
- Speech recognition accuracy depends on audio quality, background noise, language,
  dialect, and provider performance. AI-assisted transcript only.
- If credentials are not configured, the service cleanly reports status: "not_configured"
  without attempting live API calls.
"""

import base64
import logging
import os
from typing import Any, Dict, List, Optional
import httpx

logger = logging.getLogger("samvad.bhashini")

# Language mapping: English, Hindi, and Marathi
SUPPORTED_LANGUAGES: Dict[str, str] = {
    "en": "en",
    "english": "en",
    "hi": "hi",
    "hindi": "hi",
    "mr": "mr",
    "marathi": "mr",
}

# Standard audio extensions and mime types supported
SUPPORTED_AUDIO_EXTENSIONS = {
    ".wav", ".mp3", ".ogg", ".webm", ".flac", ".m4a", ".aac"
}
SUPPORTED_MIME_PREFIXES = ("audio/", "video/webm")

DEFAULT_CONFIG_URL = "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline"
DEFAULT_INFERENCE_URL = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"
DEFAULT_PIPELINE_ID = "64392f96daac503b137db368"

DISCLAIMER_TEXT = (
    "Speech recognition accuracy depends on audio quality, language, dialect, "
    "and provider performance. AI-assisted transcript only."
)


class BhashiniService:
    """
    Adapter for Digital India BHASHINI ASR (Speech-to-Text).
    Manages authentication, pipeline resolution, audio encoding, and transcription parsing.
    """

    DISCLAIMER = DISCLAIMER_TEXT

    def __init__(self):
        # Read from environment variables ONLY
        self.api_key: Optional[str] = os.environ.get("BHASHINI_API_KEY")
        self.user_id: Optional[str] = os.environ.get("BHASHINI_USER_ID")
        self.pipeline_id: str = os.environ.get("BHASHINI_PIPELINE_ID", DEFAULT_PIPELINE_ID)
        self.inference_api_key: Optional[str] = os.environ.get("BHASHINI_INFERENCE_API_KEY")
        self.api_url: str = os.environ.get("BHASHINI_API_URL", DEFAULT_INFERENCE_URL)
        self.config_url: str = os.environ.get("BHASHINI_CONFIG_URL", DEFAULT_CONFIG_URL)

    def is_configured(self) -> bool:
        """
        Returns True only if valid Bhashini credentials are present in the environment.
        """
        # Minimum required: either BHASHINI_API_KEY with BHASHINI_USER_ID, or BHASHINI_INFERENCE_API_KEY
        if self.inference_api_key and self.inference_api_key.strip():
            return True
        if self.api_key and self.api_key.strip():
            return True
        return False

    def normalize_language(self, lang: Optional[str]) -> str:
        """
        Validates and maps language names/codes to standard Bhashini language codes.
        Supports 'en', 'hi', 'mr' (and English, Hindi, Marathi).
        """
        if not lang or not lang.strip():
            raise ValueError("Language parameter must not be empty.")
        clean_lang = lang.strip().lower()
        if clean_lang not in SUPPORTED_LANGUAGES:
            raise ValueError(
                f"Unsupported language: '{lang}'. Supported languages: "
                f"en (English), hi (Hindi), mr (Marathi)."
            )
        return SUPPORTED_LANGUAGES[clean_lang]

    def validate_audio(self, filename: Optional[str], content_type: Optional[str], audio_bytes: bytes) -> str:
        """
        Validates audio content and determines the audio format (wav, mp3, webm, etc.).
        """
        if not audio_bytes or len(audio_bytes) == 0:
            raise ValueError("Audio file must not be empty.")

        ext = ""
        if filename and "." in filename:
            ext = "." + filename.rsplit(".", 1)[-1].lower()

        # Validate MIME type or file extension
        is_mime_valid = bool(content_type and any(content_type.lower().startswith(p) for p in SUPPORTED_MIME_PREFIXES))
        is_ext_valid = ext in SUPPORTED_AUDIO_EXTENSIONS

        if not is_mime_valid and not is_ext_valid and ext not in ("", ".bin", ".octet-stream"):
            raise ValueError(
                f"Invalid audio format. Extension '{ext}' or content-type '{content_type}' "
                f"is not a recognized audio format. Supported: {sorted(list(SUPPORTED_AUDIO_EXTENSIONS))}."
            )

        # Determine format tag for Bhashini
        if ext in (".wav",):
            return "wav"
        elif ext in (".mp3",):
            return "mp3"
        elif ext in (".flac",):
            return "flac"
        elif ext in (".ogg",):
            return "ogg"
        elif ext in (".webm",) or (content_type and "webm" in content_type):
            return "webm"
        elif ext in (".m4a", ".aac"):
            return "m4a"
        else:
            return "wav"

    def get_status_info(self) -> Dict[str, Any]:
        """
        Returns public service status without exposing sensitive credentials.
        """
        configured = self.is_configured()
        return {
            "status": "configured" if configured else "not_configured",
            "provider": "Bhashini",
            "supported_languages": ["en", "hi", "mr"],
            "disclaimer": self.DISCLAIMER,
        }

    def transcribe(
        self,
        audio_bytes: bytes,
        language: str,
        filename: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Processes audio transcription via Bhashini ASR.
        If credentials are not configured, returns safe status: "not_configured".
        """
        lang_code = self.normalize_language(language)
        audio_format = self.validate_audio(filename, content_type, audio_bytes)

        if not self.is_configured():
            logger.info("Bhashini requested but credentials are not configured in environment.")
            return {
                "status": "not_configured",
                "provider": "Bhashini",
                "message": "Bhashini credentials are not configured.",
                "supported_languages": ["en", "hi", "mr"],
                "disclaimer": self.DISCLAIMER,
            }

        # Encode audio to base64
        base64_audio = base64.b64encode(audio_bytes).decode("utf-8")

        return self._call_bhashini_api(base64_audio, lang_code, audio_format)

    def _call_bhashini_api(self, base64_audio: str, lang_code: str, audio_format: str) -> Dict[str, Any]:
        """
        Executes HTTP request against official Bhashini ASR endpoint.
        Handles both direct inference endpoint and pipeline config resolution.
        """
        inference_url = self.api_url
        auth_header = self.inference_api_key or self.api_key

        # If user credentials exist without direct inference key, resolve pipeline via config URL
        if self.user_id and self.api_key and not self.inference_api_key:
            try:
                resolved_endpoint, resolved_auth = self._resolve_pipeline(lang_code)
                if resolved_endpoint:
                    inference_url = resolved_endpoint
                if resolved_auth:
                    auth_header = resolved_auth
            except Exception as e:
                logger.error("Failed to resolve Bhashini pipeline config: %s", str(e))
                # Fallback to direct inference URL if resolution fails

        payload = {
            "pipelineTasks": [
                {
                    "taskType": "asr",
                    "config": {
                        "language": {
                            "sourceLanguage": lang_code
                        },
                        "audioFormat": audio_format,
                        "samplingRate": 16000,
                    }
                }
            ],
            "inputData": {
                "audio": [
                    {
                        "audioContent": base64_audio
                    }
                ]
            }
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": str(auth_header),
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(inference_url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()

            # Parse Bhashini response structure
            transcript = self._extract_transcript(data)
            return {
                "status": "success",
                "provider": "Bhashini",
                "language": lang_code,
                "transcript": transcript,
                "disclaimer": self.DISCLAIMER,
            }

        except httpx.TimeoutException:
            logger.error("Bhashini ASR request timed out.")
            return {
                "status": "error",
                "provider": "Bhashini",
                "message": "Bhashini ASR request timed out.",
                "disclaimer": self.DISCLAIMER,
            }
        except httpx.HTTPStatusError as e:
            # Mask any internal sensitive details
            logger.error("Bhashini HTTP error status: %s", e.response.status_code)
            return {
                "status": "error",
                "provider": "Bhashini",
                "message": f"Bhashini service returned status code {e.response.status_code}.",
                "disclaimer": self.DISCLAIMER,
            }
        except Exception as e:
            logger.error("Unexpected error during Bhashini ASR: %s", str(e))
            return {
                "status": "error",
                "provider": "Bhashini",
                "message": "An error occurred while connecting to Bhashini ASR service.",
                "disclaimer": self.DISCLAIMER,
            }

    def _resolve_pipeline(self, lang_code: str) -> tuple[Optional[str], Optional[str]]:
        """
        Resolves model pipeline callback URL and authorization key via Bhashini Config API.
        """
        headers = {
            "Content-Type": "application/json",
            "userID": str(self.user_id),
            "ulcaApiKey": str(self.api_key),
        }
        payload = {
            "pipelineTasks": [
                {
                    "taskType": "asr",
                    "config": {
                        "language": {
                            "sourceLanguage": lang_code
                        }
                    }
                }
            ],
            "pipelineRequestConfig": {
                "pipelineId": self.pipeline_id
            }
        }

        with httpx.Client(timeout=15.0) as client:
            resp = client.post(self.config_url, json=payload, headers=headers)
            resp.raise_for_status()
            config_data = resp.json()

        callback_url = (
            config_data.get("pipelineInferenceAPIEndPoint", {}).get("callbackUrl")
        )
        api_key_val = (
            config_data.get("pipelineInferenceAPIEndPoint", {})
            .get("inferenceApiKey", {})
            .get("value")
        )
        return callback_url, api_key_val

    def _extract_transcript(self, data: Dict[str, Any]) -> str:
        """
        Extracts transcript text from standard Bhashini pipeline response.
        """
        # Standard ULCA/Dhruva structure: pipelineResponse[0].output[0].source
        pipeline_responses = data.get("pipelineResponse", [])
        for task_resp in pipeline_responses:
            if task_resp.get("taskType") == "asr":
                outputs = task_resp.get("output", [])
                if outputs and isinstance(outputs, list):
                    first_out = outputs[0]
                    if isinstance(first_out, dict):
                        return first_out.get("source", "").strip()
        # Fallback search if structure is flat:
        if "output" in data and isinstance(data["output"], list) and data["output"]:
            return data["output"][0].get("source", "").strip()
        return ""


# Singleton instance for application use
bhashini_service = BhashiniService()
