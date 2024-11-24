import streamlit as st
from exa_py import Exa
from autogen import AssistantAgent
from dotenv import load_dotenv
import os
import json
import re
import markdown

# Load environment variables
load_dotenv()

# Configuration for Market Research Agent
class MarketResearchAgent:
    def __init__(self, api_key):
        self.exa = Exa(api_key=api_key)
        self.llm_config = {
            "config_list": [{
                "model": "gpt-4o-mini",
                "api_key": os.getenv("OPENAI_API_KEY")
                # "model": "llama3-8b-8192",
                # "api_key":os.getenv("GROQ_API_KEY"),

            }]
        }

    def research_industry(self, industry, company_name):
        """Conduct comprehensive industry and company research"""
        search_queries = [
            f"{industry} industry overview and trends",
            f"{company_name} strategic focus and market position",
            f"{industry} technological innovations and future outlook"
        ]
        
        research_results = {}
        for query in search_queries:
            try:
                results = self.exa.search(query, num_results=3, type="neural")
                research_results[query] = [
                    {"title": res.title, "url": res.url, "snippet": res.summary} 
                    for res in results.results
                ]
            except Exception as e:
                st.error(f"Research error for query '{query}': {e}")
        
        return research_results

    def generate_use_cases(self, industry, research_insights):
        """Generate AI/ML use cases based on industry research"""
        use_case_prompt = f"""
        Based on the {industry} industry insights, generate innovative AI/ML use cases:
        1. Analyze the research insights: {json.dumps(research_insights)}
        2. Propose use cases focusing on:
           - Operational efficiency
           - Customer experience enhancement
           - Technological innovation
        3. Provide specific, actionable recommendations
        """
        
        assistant = AssistantAgent("use_case_generator", llm_config=self.llm_config)
        use_cases = assistant.generate_reply(messages=[{"content": use_case_prompt, "role": "user"}])
        
        # Process and clean use cases
        return [case.strip() for case in re.split(r'\d+\.', str(use_cases)) if case.strip()]

    def collect_resource_assets(self, use_cases):
        """Collect dataset resources for each use case"""
        resource_map = {}
        platforms = [
            "kaggle.com/datasets", 
            "huggingface.co/datasets", 
            "github.com/datasets"
        ]
        
        for use_case in use_cases:
            resources = []
            for platform in platforms:
                query = f'"{use_case}" dataset site:{platform}'
                try:
                    results = self.exa.search(query, num_results=3)
                    platform_resources = [
                        {"url": res.url, "title": res.title}
                        for res in results.results
                        if platform in res.url and any(keyword in res.url.lower() for keyword in ['dataset', 'data'])
                    ]
                    resources.extend(platform_resources)
                except Exception as e:
                    st.warning(f"Resource collection error for '{use_case}': {e}")
            
            resource_map[use_case] = resources[:3]
        
        return resource_map

    def generate_final_proposal(self, use_cases, resource_map, research_insights):
        """Create comprehensive markdown proposal"""
        proposal = "# AI Use Cases & Strategic Insights Proposal\n\n"
        
        # Add research context
        proposal += "## Industry Research Context\n"
        for query, insights in research_insights.items():
            proposal += f"### {query}\n"
            for insight in insights:
                proposal += f"- **{insight['title']}**: [Source]({insight['url']})\n  *{insight['snippet']}*\n\n"
        
        # Add use cases and resources
        proposal += "## Recommended AI/ML Use Cases\n\n"
        for idx, use_case in enumerate(use_cases, 1):
            proposal += f"### Use Case {idx}: {use_case}\n\n"
            
            # Add resources if available
            if use_case in resource_map and resource_map[use_case]:
                proposal += "#### Recommended Datasets:\n"
                for resource in resource_map[use_case]:
                    proposal += f"- [{resource['title']}]({resource['url']})\n"
            
            proposal += "\n"
        
        return proposal

def main():
    st.set_page_config(page_title="AI Strategy Research Agent", page_icon="🚀")
    
    # Initialize Research Agent
    research_agent = MarketResearchAgent(api_key=os.getenv("EXA_API_KEY"))
    
    st.title("🌐 AI Strategy & Use Case Research Agent")
    st.markdown("Generate strategic AI/ML use cases for your industry")

    # User Inputs
    col1, col2 = st.columns(2)
    with col1:
        industry = st.text_input("Industry Focus", placeholder="Healthcare, Finance, etc.")
    with col2:
        company_name = st.text_input("Company Name", placeholder="Optional")

    if st.button("Generate Strategic Insights", type="primary"):
        if industry:
            with st.spinner("Generating comprehensive insights..."):
                # Conduct Research
                research_insights = research_agent.research_industry(industry, company_name)
                
                # Generate Use Cases
                use_cases = research_agent.generate_use_cases(industry, research_insights)
                
                # Collect Resource Assets
                resource_map = research_agent.collect_resource_assets(use_cases)
                
                # Create Tabs for Presentation
                tab1, tab2, tab3, tab4 = st.tabs(
                    ["Industry Insights", "AI Use Cases", "Resource Assets", "Final Proposal"]
                )
                
                # Display Results
                with tab1:
                    st.subheader("Industry Research Insights")
                    for query, insights in research_insights.items():
                        st.markdown(f"### {query}")
                        for insight in insights:
                            st.markdown(f"- **{insight['title']}**\n  [Source]({insight['url']})")
                
                with tab2:
                    st.subheader("AI Use Cases")
                    for case in use_cases:
                        st.markdown(f"- {case}")
                
                with tab3:
                    st.subheader("Recommended Datasets")
                    for use_case, resources in resource_map.items():
                        st.markdown(f"#### {use_case}")
                        for resource in resources:
                            st.markdown(f"- [{resource['title']}]({resource['url']})")
                
                with tab4:
                    # Generate Final Proposal
                    final_proposal = research_agent.generate_final_proposal(
                        use_cases, resource_map, research_insights
                    )
                    st.markdown(final_proposal)

                    # Save Proposal as Markdown file
                    with open("ai_strategy_proposal.md", "w") as file:
                        file.write(final_proposal)

                    # Provide download link for Markdown file
                    with open("ai_strategy_proposal.md", 'rb') as md_file:
                        btn = st.download_button(
                            label="Download Markdown Proposal",
                            data=md_file,
                            file_name="ai_strategy_proposal.md",
                            mime='text/markdown'
                        )

                    
        else:
            st.warning("Please enter an industry")

if __name__ == "__main__":
    main()
