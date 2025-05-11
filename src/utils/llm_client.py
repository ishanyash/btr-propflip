import os
import requests
import json
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('btr_utils.llm_client')

class LLMClient:
    """Client for interacting with OpenAI or Grok APIs to curate property valuations"""
    
    def __init__(self):
        # Determine which API to use based on available keys
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.grok_api_key = os.getenv('GROK_API_KEY')
        
        if self.openai_api_key:
            self.api_type = 'openai'
            logger.info("Using OpenAI API")
        elif self.grok_api_key:
            self.api_type = 'grok'
            logger.info("Using Grok API")
        else:
            self.api_type = None
            logger.warning("No API keys found. LLM curation will be disabled.")
    
    def curate_property_valuation(self, address, estimated_value, property_type_name):
        """
        Curate property valuation by cross-checking with internet data via LLMs
        
        Args:
            address: Property address
            estimated_value: Current estimated value from our data
            property_type_name: Property type (Detached, Semi-detached, etc.)
            
        Returns:
            dict: Curated property information
        """
        if not self.api_type:
            logger.warning("LLM curation disabled due to missing API keys")
            return {
                'curated_value': estimated_value,
                'confidence': 'low',
                'curated': False,
                'explanation': "Automated valuation based on local property data"
            }
        
        try:
            # Construct prompt for the LLM
            prompt = f"""
            You are a property valuation expert in the UK. I have an estimated value of £{estimated_value:,.0f} 
            for a {property_type_name} at "{address}". Using your knowledge of the UK property market:
            
            1. Is this valuation reasonable based on current market data?
            2. If not, what would be a more accurate valuation?
            3. What factors might affect this valuation?
            
            Respond with a JSON object with the following fields:
            - curated_value: Your estimate of the property value in GBP (no currency symbol, just the number)
            - confidence: "high", "medium", or "low"
            - explanation: A brief explanation of your valuation
            """
            
            # Call appropriate API
            if self.api_type == 'openai':
                response = self._call_openai(prompt)
            else:  # grok
                response = self._call_grok(prompt)
            
            if response:
                # Ensure curated value is numeric
                if 'curated_value' in response:
                    try:
                        response['curated_value'] = float(response['curated_value'])
                    except (ValueError, TypeError):
                        # If conversion fails, use original estimate
                        response['curated_value'] = estimated_value
                else:
                    response['curated_value'] = estimated_value
                
                # Add curated flag
                response['curated'] = True
                
                # Ensure other required fields exist
                if 'confidence' not in response:
                    response['confidence'] = 'medium'
                if 'explanation' not in response:
                    response['explanation'] = "Valuation based on current market data"
                
                return response
            else:
                # Return default response if API call failed
                return {
                    'curated_value': estimated_value,
                    'confidence': 'low',
                    'curated': False,
                    'explanation': "Automated valuation based on local property data"
                }
        
        except Exception as e:
            logger.error(f"Error in property valuation curation: {e}")
            return {
                'curated_value': estimated_value,
                'confidence': 'low',
                'curated': False,
                'explanation': f"Automated valuation based on local property data"
            }
    
    def _call_openai(self, prompt):
        """Call OpenAI API"""
        try:
            import openai
            openai.api_key = self.openai_api_key
            
            response = openai.ChatCompletion.create(
                model="gpt-4", 
                messages=[
                    {"role": "system", "content": "You are a UK property valuation expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            
            # Extract JSON from response
            content = response.choices[0].message.content
            
            # Try to parse JSON
            try:
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = content[start_idx:end_idx]
                    return json.loads(json_str)
                else:
                    logger.warning("No JSON found in OpenAI response")
                    return None
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON from OpenAI response")
                return None
        
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            return None
    
    def _call_grok(self, prompt):
        """Call Grok API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.grok_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "messages": [
                    {"role": "system", "content": "You are a UK property valuation expert."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2
            }
            
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=data
            )
            
            response_data = response.json()
            
            # Extract JSON from response
            if 'choices' in response_data and len(response_data['choices']) > 0:
                content = response_data['choices'][0]['message']['content']
                
                # Try to parse JSON
                try:
                    start_idx = content.find('{')
                    end_idx = content.rfind('}') + 1
                    if start_idx >= 0 and end_idx > start_idx:
                        json_str = content[start_idx:end_idx]
                        return json.loads(json_str)
                    else:
                        logger.warning("No JSON found in Grok response")
                        return None
                except json.JSONDecodeError:
                    logger.warning("Failed to parse JSON from Grok response")
                    return None
            else:
                logger.warning("Invalid response format from Grok API")
                return None
                
        except Exception as e:
            logger.error(f"Grok API call failed: {e}")
            return None