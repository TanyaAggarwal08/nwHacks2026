import os
from dotenv import load_dotenv
from openai import OpenAI
from tavily import TavilyClient
import datetime

load_dotenv(override=True)

# 1. Initialize Clients (One time only)
client = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=os.getenv("GITHUB_TOKEN"),
)
# Ensure TAVILY_API_KEY is in your .env
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

def get_agent_config(category: str) -> dict:
    current_date = datetime.datetime.now().strftime("%B %Y")
    
    # This prompt works for 2026, 2030, and beyond
    base_instructions = (
        f"You are a BC Legal Research Assistant. The current date is {current_date}.\n"
        "STRICT INSTRUCTIONS:\n"
        "1. PRIORITY: Your internal training data is OUTDATED. You must use ONLY use the current information from the sites\n"
        "2. NUMERIC DATA: Extract all numbers (hours, percentages, dollars) exactly as they appear in the context. Never use numbers from your memory.\n"
        "3. TEMPORAL AWARENESS: If the context mentions a 'new rule' or 'as of [date]', prioritize it as the current law.\n"
    )
    configs = {
        "rent": {
            "name": "RentExpert",
            "instructions": (base_instructions+
                "You are a BC Rental Law Expert. You must operate as a precision legal retrieval system.\n"
                "STRICT PROTOCOLS:\n"
                "1.Your internal training data is OUTDATED. You must use ONLY the current information from the sites mentioned below in DATA SOURCE.\n"
                "2. NUMERIC DATA: Extract all numbers (hours, percentages, dollars) exactly as they appear in the context. Never use numbers from your memory.\n"
                "3. TEMPORAL AWARENESS: If the context mentions a 'new rule' or 'as of [date]', prioritize it as the current law.\n"
                "4. DATA SOURCE: Use ONLY the provided context from gov.bc.ca or BC Statutes. If context is missing, say 'Information not found in official records.'\n"
                "5. FORMATTING: Use detailed bullet points. Use bold text for deadlines and percentages (e.g., **2.3%**, **10 days**).\n"
                "6. LEGAL SECTIONS: You MUST list the specific Section numbers from the Residential Tenancy Act (e.g., Section 47, Section 49).\n"
                "7. NO HALLUCINATION: Never provide 'general advice.' If the 2026 rent cap or a specific notice period isn't in the context, do not guess.\n"
                "8. CITATIONS: Every bullet point must end with a bracketed source link. Example: - Rule detail [gov.bc.ca/url]"
                "9. NO FLUFF: Start the response immediately with the answer. Use bolding for numbers."
            )
        },
        "immigration": {
            "name": "ImmigrationExpert",
            "instructions": (base_instructions+
                "You are a BC Immigration Specialist (BC PNP and IRCC context). You are an technical assistant, not a representative.\n"
                "STRICT PROTOCOLS:\n"
                  "1.Your internal training data is OUTDATED. You must use ONLY the current information from the sites mentioned below in DATA SOURCE.\n"
                "2. NUMERIC DATA: Extract all numbers (hours, percentages, dollars) exactly as they appear in the context. Never use numbers from your memory.\n"
                "3. TEMPORAL AWARENESS: If the context mentions a 'new rule' or 'as of [date]', prioritize it as the current law.\n"
           
                "4. CITATION: Cite specific program guides or IRCC policy manuals. Link every factual claim to the official .gc.ca or .gov.bc.ca URL.\n"
                "5. SPECIFICITY: Provide exact points requirements (SIRS), income thresholds, and processing times from the context.\n"
                "6. CAUTION: You must state: 'I am an AI, not a Regulated Canadian Immigration Consultant (RCIC).' if asked for a recommendation.\n"
                "7. ZERO GENERALIZATION: Do not explain 'how immigration works.' Only answer the specific visa or pathway question asked."
                "8. NO FLUFF: Start the response immediately with the answer. Use bolding for numbers."
            )
        },
        "work": {
            "name": "WorkLawExpert",
            "instructions": (base_instructions+
                "You are a BC Employment Standards Expert. You interpret the Employment Standards Act (ESA).\n"
                "STRICT PROTOCOLS:\n"
                  "1.Your internal training data is OUTDATED. You must use ONLY the current information from the sites mentioned below in DATA SOURCE.\n"
                "2. NUMERIC DATA: Extract all numbers (hours, percentages, dollars) exactly as they appear in the context. Never use numbers from your memory.\n"
                "3. TEMPORAL AWARENESS: If the context mentions a 'new rule' or 'as of [date]', prioritize it as the current law.\n"
           
                "4. ACT CITATION: Identify the specific Part or Section of the ESA (e.g., Part 4: Hours of Work and Overtime).\n"
                "5. NUMERIC PRECISION: State exact multipliers (e.g., 1.5x for overtime after 8hrs, 2x after 12hrs) and statutory holiday rules.\n"
                "6. JURISDICTION: Remind the user this applies ONLY to provincially regulated employees in BC.\n"
                "7. TERMINATION: Provide the exact 'Length of Service' vs 'Notice Period' table from the Act if asked about firing or quitting."
                "8. NO FLUFF: Start the response immediately with the answer. Use bolding for numbers."
            )
        }
    }
    return configs.get(category.lower(), configs["rent"])

def get_context_from_db_or_api(query: str, category: str):
   # We add "2026" and "2025" and "update" to the query string
    enhanced_query = f"{query} current rules {datetime.datetime.now().year}"
    
    try:
        response = tavily.search(
            query=enhanced_query, 
            search_depth="advanced", # Use 'advanced' for legal queries
            max_results=3,           # Get 3 results to let the LLM compare dates
            include_domains=["canada.ca", "gov.bc.ca", "ircc.canada.ca"]
        )
        
        if response['results']:
            best_match = response['results'][0]
            # Returning both text and the URL
            return best_match['content'], best_match['url']
            
    except Exception as e:
        print(f"Tavily Error: {e}")
        
    return "No official records found.", "https://www.gov.bc.ca"


def classify_intent(user_input: str) -> str:
    """
    Analyzes the user's question and returns 'rent', 'work', or 'immigration'.
    """
    try:
        system_prompt = (
            "You are a classification assistant for a BC legal bot. "
            "Categorize the user's query into one of these three labels: 'rent', 'work', or 'immigration'.\n"
            "Rules:\n"
            "- 'rent': for anything related to housing, landlords, tenants, or evictions.\n"
            "- 'work': for anything related to jobs, wages, labor rights, or firing.\n"
            "- 'immigration': for visas, PNP, PR, or work permits.\n"
            "- Respond with ONLY the word (e.g., 'work')."
        )

        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Classify this query: {user_input}"}
            ],
            model=os.getenv("GITHUB_MODEL", "gpt-4o"),
            temperature=0 # Absolute precision
        )
        
        # Extract the label and clean it
        category = response.choices[0].message.content.strip().lower()
        
        # Safety check: default to 'rent' if the AI gives a weird answer
        valid_categories = ["rent", "work", "immigration"]
        return category if category in valid_categories else "rent"
    except Exception as e:
        print(f"Error in classify_intent: {str(e)}")
        return "rent"  # Default fallback


def legal_bot_response(user_input: str, category: str):
    """Generate legal bot response for a user query in a specific category"""
    try:
        config = get_agent_config(category)
        current_year = datetime.datetime.now().year
        
        # DYNAMIC SEARCH: Automatically append the year and 'official' to every query
        # This forces Tavily to find the 2.3% or 24hr rule without us knowing what they are.
        search_query = f"official BC {category} limit rate {current_year} {user_input}"
        
        context_text, source_url = get_context_from_db_or_api(search_query, category)
        
        prompt_content = f"""
    CONTEXT DATA:
    {context_text}
    
    USER QUESTION: {user_input}
    
    INSTRUCTION: 
    Extract the specific legal limit or value for the year {current_year} from the CONTEXT DATA. 
    If the context contains a specific number (like a percentage or hour limit) associated with {current_year}, 
    report it as the primary answer. Do not use any other numbers.
    """

        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": config["instructions"]},
                {"role": "user", "content": prompt_content}
            ],
            model=os.getenv("GITHUB_MODEL", "gpt-4o"),
            temperature=0.1 # Keep it low for legal reliability
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in legal_bot_response: {str(e)}")
        raise

