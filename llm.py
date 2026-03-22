from groq import Groq

from config import GROQ_API_KEY


def get_groq_client() -> Groq:
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set.")
    return Groq(api_key=GROQ_API_KEY)


def generate_answer(query: str, context: str) -> str:
    """Answer using Groq (LLaMA 3.3 70B) and retrieved context only."""
    try:
        client = get_groq_client()
    except ValueError as e:
        return f"Configuration Error: {str(e)}"

    system_prompt = (
        "You are an expert AI Codebase Intelligence assistant. "
        "You answer developer questions using ONLY the provided codebase context. "
        "If the answer cannot be found in the context, explicitly state that you don't know based on the codebase. "
        "When explaining, reference the specific classes, functions, and file names provided in the context."
    )
    user_prompt = f"Context from the codebase:\n{context}\n\nQuestion: {query}\nAnswer:"
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=1024,
        )
        return completion.choices[0].message.content or ""
    except Exception as e:
        return f"Error connecting to LLM: {str(e)}"
