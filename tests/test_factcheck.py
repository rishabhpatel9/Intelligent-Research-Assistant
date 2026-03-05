from src.tools import factcheck

query = "Is it true that coffee causes dehydration?"
result = factcheck.run(query)
print(result)