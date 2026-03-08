from src.tools.search import run

def test_search():
    res = run("Python programming language", source="wikipedia")
    print(res)
    assert res is not None
    assert "Wikipedia" in res

if __name__ == "__main__":
    test_search()
    print("Search test passed")
