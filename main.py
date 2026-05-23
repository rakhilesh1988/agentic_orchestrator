import asyncio

from agentic.agent import Agent

if __name__ == "__main__":
    # Test query
    agent = Agent()

    # query = "Fetch https://en.wikipedia.org/wiki/Claude_Shannon and tell me his birth date, death date, and three key contributions to information theory."
    # query = "Find 3 family-friendly things to do in Tokyo this weekend. Check Saturday's weather forecast there and tell me which one is most appropriate."
    # query = "My mom's birthday is 15 May 2026. Remember that and give me a calendar reminder for two weeks before and on the day."
    # query = "When is mom's birthday?"
    query = "Search for 'Python asyncio best practices', read the top 3 results, and give me a short numbered list of the advice they agree on."
    res = asyncio.run(agent.run(query))
    print(f"\n[FINAL RESPONSE]\n{res}")
