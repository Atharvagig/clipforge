import json
import urllib.request
import urllib.error
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GeminiClient")

class GeminiClient:
    def __init__(self, api_key=None, model="gemini-1.5-flash"):
        self.api_key = api_key
        self.model = model

    def _call_api(self, prompt, system_instruction=None, json_mode=False):
        """Sends a request to the Gemini API via HTTP POST."""
        if not self.api_key:
            logger.error("Gemini API key is not configured.")
            return {"error": "API key missing. Please configure it in Settings."}

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        
        contents = {
            "parts": [
                {"text": prompt}
            ]
        }
        
        data = {
            "contents": [contents]
        }
        
        if system_instruction:
            data["systemInstruction"] = {
                "parts": [
                    {"text": system_instruction}
                ]
            }

        if json_mode:
            data["generationConfig"] = {
                "responseMimeType": "application/json"
            }

        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                
                # Parse response
                candidates = res_data.get("candidates", [])
                if not candidates:
                    return {"error": "Empty response from Gemini API"}
                
                text_content = candidates[0]["content"]["parts"][0]["text"]
                if json_mode:
                    try:
                        # Clean markdown json formatting if LLM returned it anyway
                        cleaned = text_content.strip()
                        if cleaned.startswith("```json"):
                            cleaned = cleaned[7:]
                        if cleaned.endswith("```"):
                            cleaned = cleaned[:-3]
                        return json.loads(cleaned.strip())
                    except json.JSONDecodeError as je:
                        logger.error(f"Failed to parse JSON response from Gemini: {text_content}. Error: {je}")
                        return {"error": "Failed to parse JSON content from Gemini", "raw": text_content}
                
                return {"text": text_content}

        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8")
            logger.error(f"Gemini API HTTP Error {e.code}: {err_msg}")
            return {"error": f"API HTTP Error {e.code}: {err_msg}"}
        except Exception as e:
            logger.error(f"Gemini API connection error: {e}")
            return {"error": f"Connection error: {str(e)}"}

    def detect_highlights(self, transcript_segments):
        """
        Sends transcript segments to Gemini and asks it to identify viral, educational, or funny moments.
        Returns a list of clips with start_time, end_time, title, viral_score (0-100), and rationale.
        """
        system_instruction = (
            "You are a viral video editor agent. Your job is to read transcript segments of a long-form video "
            "and detect short clips (15 to 60 seconds) that would make engaging vertical TikToks, YouTube Shorts, or Reels. "
            "You must return a valid JSON array of objects. Each object should have: "
            "'title' (short clip headline), 'start_time' (float, in seconds), 'end_time' (float, in seconds), "
            "'viral_score' (integer 0-100), and 'rationale' (reason why this is a good clip)."
        )
        
        prompt = (
            f"Review the transcript segments below. Identify the top 3-5 engaging, funny, educational, or motivational "
            f"moments. Return them in raw JSON matching the system instruction.\n\n"
            f"Transcript Data:\n{json.dumps(transcript_segments, indent=2)}"
        )
        
        result = self._call_api(prompt, system_instruction=system_instruction, json_mode=True)
        if isinstance(result, list):
            return result
        elif isinstance(result, dict) and "error" not in result:
            # Check if result is wrapped in an outer key e.g. {"clips": [...]}
            for key in ["clips", "highlights", "segments"]:
                if key in result and isinstance(result[key], list):
                    return result[key]
            return [result]
        else:
            logger.warning(f"Unexpected response format or error from highlight detector: {result}")
            # Return empty list on failure so the app doesn't crash
            return []

    def generate_marketing_copy(self, clip_title, clip_transcript):
        """
        Generates copywriting elements for a clip: Hook, SEO Description, Short Title, and Hashtags.
        """
        system_instruction = (
            "You are an expert social media manager. Provide high-converting marketing copywriting for short video clips. "
            "You must return a JSON object with keys: 'hook' (strong 1-sentence opening text overlay), "
            "'title' (optimized YouTube Shorts/TikTok title under 60 chars), "
            "'description' (SEO friendly description with summary), and 'hashtags' (comma-separated list of popular tags)."
        )
        
        prompt = (
            f"Generate copy for a clip titled '{clip_title}' with the following transcript segment:\n\n"
            f"Transcript:\n{clip_transcript}"
        )
        
        result = self._call_api(prompt, system_instruction=system_instruction, json_mode=True)
        if isinstance(result, dict):
            return {
                "hook": result.get("hook", "Check this out!"),
                "title": result.get("title", clip_title),
                "description": result.get("description", "A clip from our long-form video."),
                "hashtags": result.get("hashtags", "#shorts, #viral")
            }
        return {
            "hook": "Check this out!",
            "title": clip_title,
            "description": "A clip from our long-form video.",
            "hashtags": "#shorts, #viral"
        }

    def summarize_analytics(self, analytics_records):
        """
        Generates a summary of performance metrics and suggests growth opportunities.
        """
        prompt = (
            f"You are an AI Analytics Advisor for creators. Review the following social media performance statistics "
            f"representing watch time, views, CTR, and retention rates across various clips and platforms. "
            f"Provide a brief (2-3 paragraphs) summary highlighting the top performing platform/clip, key trends, "
            f"and actionable tips to improve CTR and retention next week.\n\n"
            f"Analytics Data:\n{json.dumps(analytics_records, indent=2)}"
        )
        
        res = self._call_api(prompt)
        return res.get("text", "Unable to generate analytics summary at this time.")
