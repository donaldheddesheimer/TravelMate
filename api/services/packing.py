# api/services/packing.py

import json
import logging
import re  # Import regular expressions for advanced cleaning
from django.conf import settings
# Ensure you have the correct imports for your OpenAI library version
# (typically `openai` >= 1.0)
try:
    from openai import OpenAI, OpenAIError, APIError # Include APIError for more specific network/API issues
except ImportError:
    # Handle potential older versions or inform the user
    raise ImportError("Please ensure the 'openai' library (version 1.0 or later) is installed: pip install --upgrade openai")

logger = logging.getLogger(__name__)

class PackingListGenerator:
    @staticmethod
    def generate_packing_list(trip, weather_summary):
        """
        Generates a packing list using an OpenAI compatible API (like OpenRouter)
        based on trip details and weather, attempting to force JSON output.

        Args:
            trip: The Trip object (assuming it has attributes like id, destination,
                  date_leaving, date_returning, activities).
            weather_summary (str): A concise string describing the weather forecast.

        Returns:
            str: A JSON string representing the packing list if successful,
                 otherwise a JSON string containing an error message.
        """
        if not hasattr(settings, 'OPENROUTER_API_KEY') or not settings.OPENROUTER_API_KEY:
            logger.error("OPENROUTER_API_KEY not configured in Django settings.")
            # Return a valid JSON string indicating the error
            return json.dumps({"error": "Configuration error: AI service API key not configured."})

        # --- Initialize OpenAI Client for OpenRouter ---
        try:
            client = OpenAI(
              base_url=getattr(settings, 'OPENROUTER_BASE_URL', "https://openrouter.ai/api/v1"), # Allow overriding base URL via settings
              api_key=settings.OPENROUTER_API_KEY,
              # Consider adding timeouts if needed:
              # timeout=30.0, # Timeout for establishing connection
              # max_retries=2 # Number of retries on transient errors
            )

            # Optional OpenRouter Headers (get from Django settings)
            # Replace 'YOUR_SITE_URL_SETTING' and 'YOUR_SITE_NAME_SETTING' below
            # with the actual names of your Django settings variables if you use them.
            site_url = getattr(settings, 'YOUR_SITE_URL_SETTING', None)
            site_name = getattr(settings, 'YOUR_SITE_NAME_SETTING', None)
            extra_headers = {}
            if site_url:
                extra_headers["HTTP-Referer"] = site_url
            if site_name:
                extra_headers["X-Title"] = site_name
            # Add any other custom headers required by OpenRouter or your setup
            # extra_headers["Your-Custom-Header"] = "Value"

        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client for OpenRouter: {e}", exc_info=True)
            return json.dumps({"error": f"Configuration error: Failed to initialize AI client: {e}"})
        # ----------------------------------------------------

        # --- Define Model and Prompt ---
        # Use the model specified in settings, default to Gemini Flash
        model_name = getattr(settings, 'OPENROUTER_MODEL', "google/gemini-flash-1.5")
        logger.info(f"Using OpenRouter model: {model_name} for trip {trip.id}")

        # Improved, stricter prompt
        prompt = f"""Generate a detailed packing list strictly in JSON format for a trip to {trip.destination} from {trip.date_leaving.strftime('%Y-%m-%d')} to {trip.date_returning.strftime('%Y-%m-%d')}.

Consider these details:
Destination: {trip.destination}
Dates: {trip.date_leaving.strftime('%b %d, %Y')} to {trip.date_returning.strftime('%b %d, %Y')} ({ (trip.date_returning - trip.date_leaving).days + 1 } days)
Planned Activities: {trip.activities or 'General tourism and leisure'}
Weather Forecast Summary: {weather_summary}

**IMPORTANT INSTRUCTIONS:**
1.  Your *entire* response MUST be **ONLY** a valid JSON object.
2.  The JSON object must contain a single top-level key: "categories".
3.  The "categories" value must be a list of category objects.
4.  Each category object must have "name" (string) and "items" (list) keys.
5.  Each item object must have "name" (string, required) and can optionally have "quantity" (integer, default 1), "essential" (boolean, default false), "notes" (string), "for_day" (string 'YYYY-MM-DD'). Mark essentials like passports/visas/meds as true.
6.  **DO NOT** include *any* introductory text, concluding text, explanations, apologies, code comments (like // ...), or markdown formatting (like ```json ... ```) in your response.
7.  The response **must** start directly with `{{` and end directly with `}}`. Your output should be parsable by Python's `json.loads()`.

Example structure:
{{
    "categories": [
        {{
            "name": "Documents & Money",
            "items": [
                {{"name": "Passport", "quantity": 1, "essential": true}},
                {{"name": "Visa (if required)", "quantity": 1, "essential": true, "notes": "Check requirements for nationality"}},
                {{"name": "Local Currency", "quantity": 1, "essential": true, "notes": "Some cash recommended"}}
            ]
        }},
        {{
            "name": "Clothing",
            "items": [
                {{"name": "T-shirts", "quantity": 4, "essential": false, "notes": "Breathable fabric"}},
                {{"name": "Comfortable Walking Shoes", "quantity": 1, "essential": true}}
            ]
        }},
        {{
            "name": "Toiletries",
            "items": [
                {{"name": "Toothbrush", "quantity": 1, "essential": true}},
                {{"name": "Sunscreen", "quantity": 1, "essential": false}}
            ]
        }}
        // Add other relevant categories like Electronics, Medications, Gear etc. based on trip details.
    ]
}}

Generate the JSON packing list now based *only* on the trip details provided. Ensure the output is ONLY the JSON object.
"""
        # -------------------------------------

        try:
            logger.info(f"Sending packing list request to OpenRouter ({model_name}) for trip {trip.id} to {trip.destination}")

            # --- Prepare API Call Parameters ---
            completion_params = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": "You are an expert travel assistant. Your sole task is to generate a packing list in a specific JSON format based on user-provided trip details, activities, and weather. Your output MUST be a single, valid JSON object conforming exactly to the structure requested by the user. Do not include any text outside of the JSON structure itself."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.5, # Lower temperature for more deterministic JSON
                "max_tokens": 2500, # Generous limit, adjust based on typical list size
                "extra_headers": extra_headers # Pass optional headers
            }

            # Attempt to use JSON Mode (check model compatibility/OpenRouter support)
            # Common OpenAI models (GPT-3.5/4) and Gemini models generally support this.
            # Add other model families if known to support it via OpenRouter.
            if any(m in model_name.lower() for m in ["gpt", "gemini"]):
                 try:
                     logger.info(f"Attempting to use JSON response format for model {model_name}")
                     completion_params["response_format"] = {"type": "json_object"}
                 except Exception as rf_err:
                     # Log if setting the format itself fails (e.g., library version issue)
                     logger.warning(f"Could not set response_format parameter for {model_name}, proceeding without it. Check library compatibility or model support. Error: {rf_err}")
                     # Ensure the parameter is removed if it caused an error during setup
                     if "response_format" in completion_params:
                         del completion_params["response_format"]
            else:
                logger.info(f"Model {model_name} not in known list for JSON mode, relying on prompt instructions.")
            # ---------------------------------

            # --- Make the API Call ---
            completion = client.chat.completions.create(**completion_params)
            # -------------------------

            # --- Process the Response ---
            if not completion.choices:
                 logger.error(f"No choices returned from OpenRouter ({model_name}) for trip {trip.id}.")
                 return json.dumps({"error": "AI service returned an empty response."})

            raw_content = completion.choices[0].message.content
            if not raw_content:
                logger.error(f"Empty content received from OpenRouter ({model_name}) choice for trip {trip.id}.")
                return json.dumps({"error": "AI service returned empty content."})

            raw_content = raw_content.strip()
            logger.debug(f"Raw response received from OpenRouter for trip {trip.id} (len={len(raw_content)}): {repr(raw_content)}")

            # --- JSON Cleaning/Extraction ---
            cleaned_content = raw_content
            original_content_for_log = raw_content # Keep a copy for error logging

            # 1. Regex to find JSON within optional markdown fences (```json ... ``` or ``` ... ```)
            # Handles potential leading/trailing whitespace within the fences. DOTALL allows '.' to match newlines.
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned_content, re.DOTALL | re.IGNORECASE)
            if match:
                cleaned_content = match.group(1).strip()
                logger.info(f"Extracted JSON using regex from markdown fences for trip {trip.id}")
            else:
                # 2. If no fences, look for the first '{' and the last '}'
                # This assumes the primary content is the JSON, possibly with leading/trailing text.
                json_start = cleaned_content.find('{')
                json_end = cleaned_content.rfind('}')

                if json_start != -1 and json_end != -1 and json_start < json_end:
                    potential_json = cleaned_content[json_start : json_end + 1]
                    # Basic check: does it look like JSON? (Starts/ends with braces)
                    if potential_json.startswith('{') and potential_json.endswith('}'):
                         cleaned_content = potential_json
                         # Log only if we actually extracted a substring
                         if len(cleaned_content) < len(raw_content):
                              logger.info(f"Extracted potential JSON block using brace finding for trip {trip.id}")
                         # else: it was already just the JSON block
                    else:
                         # If the extraction looks wrong (e.g., found braces inside text but not valid JSON)
                         logger.warning(f"Brace finding yielded non-JSON-like block for trip {trip.id}. Proceeding with original (cleaned) content.")
                         # Revert to the stripped raw content if extraction failed sanity check
                         cleaned_content = raw_content
                else:
                    # If we couldn't find any braces, it's very unlikely to be JSON.
                    # Log a warning but proceed; parsing will likely fail, triggering error handling.
                    logger.warning(f"Response for trip {trip.id} doesn't appear to contain JSON braces. Content starts: {cleaned_content[:200]}...")
                    # Keep cleaned_content as is (it's the stripped raw content)
            # -----------------------------

            # --- Attempt to Parse the Cleaned JSON ---
            logger.debug(f"Attempting to parse cleaned content for trip {trip.id} (len={len(cleaned_content)}): {repr(cleaned_content)}")
            try:
                # Load the JSON to validate its structure
                parsed_json = json.loads(cleaned_content)

                # Optional: Add a basic structure check if needed
                if not isinstance(parsed_json, dict) or "categories" not in parsed_json or not isinstance(parsed_json["categories"], list):
                    logger.error(f"Parsed JSON for trip {trip.id} lacks expected root structure ('categories' list).")
                    # Log the problematic structure
                    logger.error(f"--- Problematic Parsed Structure --- Trip {trip.id} ---\n{json.dumps(parsed_json, indent=2)}\n--- End Structure ---")
                    return json.dumps({"error": "AI response was valid JSON but lacked the expected structure (missing 'categories' list)."})

                logger.info(f"Successfully parsed and validated JSON response from OpenRouter for trip {trip.id}")
                # Return the validated, cleaned JSON string
                return cleaned_content

            except json.JSONDecodeError as json_err:
                logger.error(f"Failed to decode JSON response from AI ({model_name}) for trip {trip.id}: {json_err}", exc_info=False) # Keep traceback minimal here

                # Provide context from the content being parsed
                error_context = ""
                try:
                    # Use json_err attributes to pinpoint the error location
                    line_start_index = max(0, json_err.pos - 40) # Show context before error
                    line_end_index = min(len(cleaned_content), json_err.pos + 40) # Show context after error
                    error_snippet = cleaned_content[line_start_index:line_end_index]
                    pointer = " " * (json_err.pos - line_start_index) + "^" # Point to the error char
                    error_context = f"Error near character {json_err.pos} (line ~{json_err.lineno}, col ~{json_err.colno}). Context:\n...\n{error_snippet}\n{pointer}\n..."
                except Exception as context_err:
                    logger.warning(f"Could not extract error context snippet: {context_err}")
                    error_context = f"Error at char {json_err.pos} (line ~{json_err.lineno}, col ~{json_err.colno})."

                # Log the content that failed parsing and the original raw response
                logger.error(f"--- Problematic Content (Cleaned) --- Trip {trip.id} ---\n{repr(cleaned_content)}\n--- End Problematic Content ---")
                logger.error(f"--- Original Raw Content --- Trip {trip.id} ---\n{repr(original_content_for_log)}\n--- End Original Raw Content ---")

                return json.dumps({"error": f"AI response could not be parsed as valid JSON. {error_context}. Details: {json_err.msg}"})
            # -----------------------------------------

        # --- Handle API and Other Errors ---
        except APIError as e: # Catch broader API errors (network, rate limits, etc.)
             logger.error(f"OpenRouter API error ({model_name}) for trip {trip.id}: {e.status_code} - {e.message}", exc_info=True)
             # Try to extract a meaningful message from the response body if available
             error_message = e.message or str(e)
             if e.body and isinstance(e.body, dict) and 'error' in e.body:
                 api_err_details = e.body['error']
                 if isinstance(api_err_details, dict) and 'message' in api_err_details:
                     error_message = api_err_details['message']
                 elif isinstance(api_err_details, str): # Sometimes error is just a string
                     error_message = api_err_details

             return json.dumps({"error": f"AI service API error ({e.status_code}): {error_message}"})
        except OpenAIError as e: # Catch specific OpenAI library errors not covered by APIError
            logger.error(f"OpenRouter OpenAI library error ({model_name}) for trip {trip.id}: {e}", exc_info=True)
            error_message = str(e)
             # Check common attributes for error details
            if hasattr(e, 'message') and e.message:
                error_message = e.message
            elif hasattr(e, 'body') and isinstance(e.body, dict):
                 if 'message' in e.body:
                     error_message = e.body['message']
                 elif 'error' in e.body and isinstance(e.body['error'], dict) and 'message' in e.body['error']:
                     error_message = e.body['error']['message']

            return json.dumps({"error": f"AI service communication error: {error_message}"})
        except Exception as e:
            # Catch any other unexpected errors during the process
            logger.error(f"Unexpected error during OpenRouter call or processing ({model_name}) for trip {trip.id}: {e}", exc_info=True)
            return json.dumps({"error": f"An unexpected internal error occurred during AI generation: {e}"})