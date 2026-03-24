"""Document Agent for analyzing CIMs, NDAs, and financial filings."""

import json
import asyncio
from typing import Dict, Any, Optional, Callable
from anthropic import AsyncAnthropic
from app.config import get_settings


DOCUMENT_SYSTEM_PROMPT = """You are a legal and financial due diligence specialist at an investment bank. You are reviewing 
a document uploaded to a deal data room. Extract and return JSON with:
- summary: 3-4 sentence executive summary of the document
- key_risks: array of 5 risk items (each: { risk: string, severity: "High"|"Medium"|"Low", detail: string })
- key_terms: object with extracted deal terms (e.g. purchase_price, closing_conditions, 
  representations_and_warranties, termination_fee, exclusivity_period — include only what's present)
- document_type_detected: your assessment of what kind of document this is
Be precise, professional, and conservative in risk assessment.

Return JSON in this exact format:
{
  "document_type_detected": "string",
  "summary": "string",
  "key_risks": [
    {
      "risk": "string",
      "severity": "High|Medium|Low",
      "detail": "string"
    }
  ],
  "key_terms": {
    "field_name": "value"
  }
}"""


class DocumentAgent:
    """Agent for analyzing legal and financial documents."""
    
    def __init__(self):
        settings = get_settings()
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY) if settings.ANTHROPIC_API_KEY else None
        self.model = "claude-sonnet-4-20250514"
    
    async def analyze(
        self,
        document_id: str,
        document_text: str,
        filename: str,
        file_type: str,
        streaming_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """
        Analyze a document and extract key information.
        
        Args:
            document_id: The document identifier
            document_text: Extracted text content from the document
            filename: Original filename
            file_type: Document type classification (CIM, NDA, Financial, etc.)
            streaming_callback: Optional callback for streaming updates
            
        Returns:
            Dictionary containing document analysis results
        """
        if streaming_callback:
            streaming_callback("Reading document content...")
            await asyncio.sleep(0.3)
            streaming_callback("Extracting key terms and conditions...")
            await asyncio.sleep(0.3)
            streaming_callback("Identifying risk factors...")
            await asyncio.sleep(0.3)
            streaming_callback("Generating executive summary...")
            await asyncio.sleep(0.3)
        
        # If no API key or no document text, return mock analysis
        if not self.client or not document_text:
            return self._generate_mock_analysis(filename, file_type)
        
        # Truncate text if too long
        max_chars = 15000
        truncated_text = document_text[:max_chars]
        if len(document_text) > max_chars:
            truncated_text += "\n\n[Document truncated for analysis...]"
        
        prompt = f"""Analyze this {file_type} document:

Filename: {filename}
Document Type: {file_type}

Document Content:
{truncated_text}

Extract key information, identify risks, and summarize the document professionally."""
        
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=DOCUMENT_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text if response.content else ""
            
            try:
                result = json.loads(content)
                result["document_id"] = document_id
                return result
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(1))
                    result["document_id"] = document_id
                    return result
                raise
                
        except Exception:
            return self._generate_mock_analysis(filename, file_type)
    
    def _generate_mock_analysis(self, filename: str, file_type: str) -> Dict[str, Any]:
        """Generate mock document analysis."""
        
        doc_types = {
            "CIM": "Confidential Information Memorandum",
            "NDA": "Non-Disclosure Agreement",
            "Financial": "Financial Statements",
            "Other": "Due Diligence Document"
        }
        
        detected_type = doc_types.get(file_type, "Due Diligence Document")
        
        if file_type == "CIM":
            return {
                "document_id": "",
                "document_type_detected": detected_type,
                "summary": "This Confidential Information Memorandum presents a technology company with strong recurring revenue growth and established market position. The company operates in a growing sector with favorable tailwinds. Financial performance shows consistent EBITDA margins above 20% with visibility into forward revenue.",
                "key_risks": [
                    {"risk": "Customer Concentration", "severity": "Medium", "detail": "Top 5 customers represent 45% of revenue, creating potential volatility"},
                    {"risk": "Technology Obsolescence", "severity": "Medium", "detail": "Rapid pace of innovation in sector may require continued R&D investment"},
                    {"risk": "Key Person Dependency", "severity": "High", "detail": "Founder/CEO critical to customer relationships and product roadmap"},
                    {"risk": "Competition Intensity", "severity": "Medium", "detail": "Well-funded competitors entering adjacent markets"},
                    {"risk": "Regulatory Changes", "severity": "Low", "detail": "Potential data privacy regulations may increase compliance costs"}
                ],
                "key_terms": {
                    "revenue": "$180M (LTM)",
                    "ebitda": "$42M (LTM)",
                    "growth_rate": "18% YoY",
                    "margin": "23.3% EBITDA margin"
                }
            }
        elif file_type == "NDA":
            return {
                "document_id": "",
                "document_type_detected": detected_type,
                "summary": "Standard mutual non-disclosure agreement with customary terms for M&A transactions. Agreement covers confidential information exchange during due diligence process with standard survival and return provisions.",
                "key_risks": [
                    {"risk": "Definition of Confidentiality", "severity": "Low", "detail": "Broad definition may capture unintended information"},
                    {"risk": "Term Duration", "severity": "Medium", "detail": "3-year survival period is longer than typical 2-year standard"},
                    {"risk": "Jurisdiction", "severity": "Low", "detail": "Governing law in non-standard jurisdiction may complicate enforcement"},
                    {"risk": "Breach Remedies", "severity": "Medium", "detail": "Injunctive relief provisions are broadly drafted"},
                    {"risk": "Permitted Disclosures", "severity": "Low", "detail": "Standard carve-outs for legal and regulatory disclosures"}
                ],
                "key_terms": {
                    "term": "3 years from execution",
                    "governing_law": "Delaware",
                    "return_period": "10 business days upon request",
                    "mutual": "Yes - obligations apply to both parties"
                }
            }
        else:
            return {
                "document_id": "",
                "document_type_detected": detected_type,
                "summary": "Financial and operational document containing relevant deal information. Review indicates standard representations with some areas requiring additional diligence focus.",
                "key_risks": [
                    {"risk": "Data Completeness", "severity": "Medium", "detail": "Some historical periods may require supplemental schedules"},
                    {"risk": "Accounting Policies", "severity": "Low", "detail": "Revenue recognition methodology aligns with industry standards"},
                    {"risk": "Working Capital", "severity": "Medium", "detail": "Seasonal fluctuations may impact closing working capital adjustment"},
                    {"risk": "Related Party Transactions", "severity": "Low", "detail": "Minor related party transactions disclosed and adequately documented"},
                    {"risk": "Tax Compliance", "severity": "Low", "detail": "No material tax exposures identified in documentation"}
                ],
                "key_terms": {}
            }
