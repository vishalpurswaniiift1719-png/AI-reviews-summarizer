import asyncio
from src.tools.cluster_themes import cluster_themes
from src.tools.generate_pulse import generate_pulse

def test():
    print("Running cluster_themes...")
    res = cluster_themes.invoke({})
    print(res)
    print("Running generate_pulse...")
    res2 = generate_pulse.invoke({})
    print(res2)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    test()
