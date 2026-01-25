import pandas as pd
import json
import re
import os
from src.llm import client as llm_client
from src.parse import tei_parser

def assess_risk_of_bias(tei_path):
    """
    Assess Risk of Bias for a single article using its TEI XML.
    Returns the assessment as a dictionary.
    """
    llm = llm_client.LLMClient()
    
    full_text = tei_parser.extract_text_from_tei(tei_path)
    if not full_text:
        return None

    # Limit text length to avoid token limits (approx 10k chars)
    text_snippet = (full_text[:12000] + '...') if len(full_text) > 12000 else full_text

    system_prompt = """You are an expert in Cochrane Risk of Bias assessment tool (RoB 2) and ROBINS-I.
Analyze the provided research paper text and assess the risk of bias for the following domains:
1. Randomization (Selection Bias)
2. Deviations from intended interventions (Performance Bias)
3. Missing outcome data (Attrition Bias)
4. Measurement of the outcome (Detection Bias)
5. Selection of the reported result (Reporting Bias)

For each domain, determine the risk level: "Low", "High", or "Unclear/Some Concerns".
Provide a brief explanation for your judgment.

Output Format:
JSON object with keys as domain names (e.g., "Randomization") and values as an object {"level": "...", "explanation": "..."}.
Example:
{
  "Randomization": {"level": "Low", "explanation": "The study mentions computer-generated random numbers."},
  ...
}
"""
    user_prompt = f"""
Papers Text:
---
{text_snippet}
---

Assess the Risk of Bias. Return JSON.
"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    try:
        response = llm.get_completion(messages)
        if response:
             # Basic regex to catch json blocks or just the curlies
             match = re.search(r"({[\s\S]*})", response)
             if match:
                 return json.loads(match.group(1))
    except Exception as e:
        print(f"Error evaluating RoB: {e}")
    
    return None

def batch_assess_rob(tei_dir, output_csv_path):
    """
    Runs RoB assessment for all XML files in the TEI directory.
    Saves results to a CSV file.
    """
    print("\n--- Starting Automated Risk of Bias (RoB) Assessment ---")
    
    rob_results = []
    
    tei_files = [f for f in os.listdir(tei_dir) if f.endswith('.xml')]
    if not tei_files:
        print("No TEI files found for RoB assessment.")
        return

    for tei_file in tei_files:
        pmid = tei_file.replace('.xml', '')
        tei_path = os.path.join(tei_dir, tei_file)
        
        print(f"Assess RoB for PMID: {pmid}...", end="\r")
        
        assessment = assess_risk_of_bias(tei_path)
        
        if assessment:
            flat_result = {'pmid': pmid}
            for domain, details in assessment.items():
                if isinstance(details, dict):
                    flat_result[f"{domain}_Level"] = details.get('level', 'Unclear')
                    flat_result[f"{domain}_Explanation"] = details.get('explanation', '')
                else:
                    # Fallback if structure is flat or weird
                    flat_result[domain] = str(details)
            rob_results.append(flat_result)
        else:
            print(f"Failed to assess RoB for {pmid}")

    if rob_results:
        df = pd.DataFrame(rob_results)
        df.to_csv(output_csv_path, index=False, encoding='utf-8-sig')
        print(f"\nSaved RoB assessment results to {output_csv_path}")
        return df
    else:
        print("\nNo RoB results generated.")
        return None
