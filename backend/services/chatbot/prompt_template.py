SYSTEM_PROMPT = """You are a Data Intelligence Assistant. Answer queries strictly based on the provided dataset context."""

def format_prompt(query: str, context: str):
    return f"{SYSTEM_PROMPT}\nContext:\n{context}\nUser Question: {query}"
