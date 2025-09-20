"""Knowledge base search tool for the tax assistant agent."""
from typing import Optional, List
from langchain_core.tools import tool
from knowledge_base.client import KnowledgeBaseClient
from knowledge_base.schemas import KnowledgeSearchRequest


# Initialize the knowledge base client
kb_client = KnowledgeBaseClient()


@tool
def search_tax_knowledge(
    query: str,
    category: Optional[str] = None,
    tax_year: Optional[str] = None,
    limit: int = 3
) -> str:
    """Search the Australian tax knowledge base for authoritative information.
    
    This tool searches through official ATO (Australian Taxation Office) information
    to provide accurate tax guidance with source attribution.
    
    Args:
        query: The tax question or topic to search for
        category: Optional filter - "deduction", "calculation", "concept", or "faq"
        tax_year: Optional filter - "2024-25", "2025-26", "general", etc.
        limit: Maximum number of results to return (default 3)
    
    Returns:
        Formatted response with tax information and ATO source links
    
    Examples:
        - "What are the tax rates for 2025-26?"
        - "How does working from home deduction work?"
        - "What is the medicare levy?"
    """
    try:
        # Create search request
        search_request = KnowledgeSearchRequest(
            query=query,
            limit=limit,
            min_score=0.5  # Only return relevant results
        )
        
        # Perform search
        results = kb_client.search(search_request)
        
        # If no results found
        if not results:
            return f"I couldn't find specific information about '{query}' in the knowledge base. " \
                   f"This might be a specialized topic that requires direct consultation with the ATO " \
                   f"or a tax professional. You can visit https://www.ato.gov.au for official guidance."
        
        # Filter by tax year if specified
        if tax_year:
            results = [r for r in results if r.entry.tax_year == tax_year or r.entry.tax_year == "general"]
        
        # Format response
        response_parts = []
        
        # Add main answer from best match
        best_result = results[0]
        response_parts.append(f"**{best_result.entry.title}**")
        response_parts.append(f"{best_result.entry.content}")
        response_parts.append(f"📋 **Source:** {best_result.entry.url}")
        
        # Add additional relevant information if multiple good matches
        if len(results) > 1 and results[1].score > 0.8:
            response_parts.append(f"\n**Related Information:**")
            for result in results[1:]:
                response_parts.append(f"• **{result.entry.title}**: {result.entry.content[:150]}...")
                response_parts.append(f"  📋 Source: {result.entry.url}")
        
        # Add confidence indicator
        confidence = "High" if best_result.score > 0.9 else "Medium" if best_result.score > 0.8 else "Moderate"
        response_parts.append(f"\n*Confidence: {confidence} (Score: {best_result.score:.2f})*")
        
        return "\n".join(response_parts)
        
    except Exception as e:
        return f"I encountered an error searching the knowledge base: {str(e)}. " \
               f"Please try rephrasing your question or visit https://www.ato.gov.au for official information."


@tool 
def get_tax_concept_explanation(concept: str) -> str:
    """Get detailed explanation of a specific tax concept.
    
    This tool provides comprehensive explanations of Australian tax concepts
    with examples and official ATO references.
    
    Args:
        concept: The tax concept to explain (e.g., "progressive tax system", 
                "marginal tax rate", "tax-free threshold")
    
    Returns:
        Detailed explanation with examples and ATO sources
    """
    try:
        # Search specifically in concepts category
        search_request = KnowledgeSearchRequest(
            query=concept,
            category="concept",
            limit=2,
            min_score=0.7
        )
        
        results = kb_client.search(search_request)
        
        if not results:
            # Fallback to general search if no concept match
            return search_tax_knowledge(f"explain {concept}", category=None, limit=2)
        
        response_parts = []
        
        # Use the best concept match
        best_result = results[0]
        response_parts.append(f"**{best_result.entry.title}**")
        response_parts.append(f"{best_result.entry.content}")
        response_parts.append(f"📋 **Official ATO Reference:** {best_result.entry.url}")
        
        # Add related concept if available
        if len(results) > 1:
            related = results[1]
            response_parts.append(f"\n**Related Concept: {related.entry.title}**")
            response_parts.append(f"{related.entry.content}")
            response_parts.append(f"📋 Source: {related.entry.url}")
        
        return "\n".join(response_parts)
        
    except Exception as e:
        return f"Error retrieving concept explanation: {str(e)}. " \
               f"Visit https://www.ato.gov.au for official tax information."


@tool
def find_deduction_information(deduction_type: str, tax_year: str = "2024-25") -> str:
    """Find specific information about tax deductions.
    
    This tool searches for detailed deduction rules, eligibility criteria,
    calculation methods, and record-keeping requirements.
    
    Args:
        deduction_type: Type of deduction (e.g., "working from home", "car expenses", 
                       "clothing", "phone", "tools")
        tax_year: Tax year for deduction rules (default "2024-25")
    
    Returns:
        Comprehensive deduction information with ATO source
    """
    try:
        # Search in deductions category for specific year
        search_request = KnowledgeSearchRequest(
            query=deduction_type,
            category="deduction",
            limit=3,
            min_score=0.7
        )
        
        results = kb_client.search(search_request)
        
        # Filter by tax year
        year_filtered = [r for r in results if r.entry.tax_year == tax_year]
        if not year_filtered:
            # If no specific year match, use any available
            year_filtered = results
        
        if not year_filtered:
            return f"I couldn't find specific deduction information for '{deduction_type}' " \
                   f"in {tax_year}. Please check the ATO website at " \
                   f"https://www.ato.gov.au/individuals-and-families/income-deductions-and-offsets " \
                   f"for the most current deduction rules."
        
        response_parts = []
        
        # Primary deduction information
        best_match = year_filtered[0]
        response_parts.append(f"**{best_match.entry.title}**")
        response_parts.append(f"{best_match.entry.content}")
        response_parts.append(f"📋 **Official ATO Guide:** {best_match.entry.url}")
        
        # Add year context
        response_parts.append(f"💡 **Tax Year:** {best_match.entry.tax_year}")
        
        # Add related deduction info if available
        if len(year_filtered) > 1:
            response_parts.append(f"\n**Additional Information:**")
            for result in year_filtered[1:]:
                if result.score > 0.75:  # Only high relevance
                    response_parts.append(f"• {result.entry.content[:200]}...")
                    break
        
        return "\n".join(response_parts)
        
    except Exception as e:
        return f"Error finding deduction information: {str(e)}. " \
               f"Please consult https://www.ato.gov.au for official deduction rules."


@tool
def get_calculation_help(calculation_topic: str, tax_year: str = "2024-25") -> str:
    """Get help with tax calculations and how they work.
    
    This tool provides detailed explanations of tax calculations including
    tax brackets, Medicare levy, offsets, and worked examples.
    
    Args:
        calculation_topic: What calculation you need help with (e.g., "tax brackets",
                          "medicare levy", "LITO", "progressive tax")
        tax_year: Relevant tax year (default "2024-25")
    
    Returns:
        Detailed calculation explanation with examples and ATO references
    """
    try:
        # Search in calculations category
        search_request = KnowledgeSearchRequest(
            query=calculation_topic,
            category="calculation", 
            limit=3,
            min_score=0.7
        )
        
        results = kb_client.search(search_request)
        
        # Prefer specific tax year results
        year_results = [r for r in results if r.entry.tax_year == tax_year]
        if not year_results:
            year_results = results  # Fall back to any year
        
        if not year_results:
            return f"I couldn't find calculation information for '{calculation_topic}'. " \
                   f"Please use the tax calculation tool or visit " \
                   f"https://www.ato.gov.au/calculators-and-tools for official ATO calculators."
        
        response_parts = []
        
        # Main calculation explanation
        primary = year_results[0]
        response_parts.append(f"**{primary.entry.title}**")
        response_parts.append(f"{primary.entry.content}")
        response_parts.append(f"📋 **ATO Reference:** {primary.entry.url}")
        
        # Add calculation context
        response_parts.append(f"💡 **Tax Year:** {primary.entry.tax_year}")
        
        # Include related calculation info
        for result in year_results[1:]:
            if result.score > 0.8:  # High relevance only
                response_parts.append(f"\n**Related: {result.entry.title}**")
                response_parts.append(f"{result.entry.content}")
                break
        
        # Suggest using calculation tool
        response_parts.append(f"\n💻 **Tip:** Use the `calculate_tax` tool for precise calculations with your specific income and circumstances.")
        
        return "\n".join(response_parts)
        
    except Exception as e:
        return f"Error retrieving calculation help: {str(e)}. " \
               f"Please use the ATO calculators at https://www.ato.gov.au/calculators-and-tools"