from server.services.llm import call_llm

def main():
    prompt = "Explain how Gemini (Google) works in a few words."
    try:
        # Adjust model, temperature, and max_tokens if you want
        result = call_llm(prompt, model="gemini-2.5-flash-lite", temperature=0.2, max_tokens=200)
        print("LLM response:\n", result)
    except Exception as e:
        print("Error calling LLM:", type(e).__name__, e)

if __name__ == "__main__":
    main()
