from src.tools import summarize

# Case 1: Rich text input
long_text = """
Artificial intelligence in healthcare is rapidly evolving.
It is being used for diagnostics, patient monitoring, workflow automation,
and predictive analytics. Several studies highlight its potential to reduce
errors and improve efficiency.
"""

print("=== Case 1: Rich text ===")
print(summarize.run(long_text))
print()

# Case 2: Limited context (headlines + URLs)
search_results = """- Advancements in AI based healthcare techniques
https://www.sciencedirect.com/article/...
- 10 Top AI Tools in Healthcare for 2025
https://www.techtarget.com/..."""
print("=== Case 2: Headlines only ===")
print(summarize.run(search_results))
print()

# Case 3: Empty / minimal input
minimal = "AI in healthcare"
print("=== Case 3: Minimal input ===")
print(summarize.run(minimal))