import os
from dotenv import load_dotenv
load_dotenv()

import google.genai as genai
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from typing import List, Dict, Optional

VECTOR_DB_DIR = "vector_store/chroma"

# Configure Gemini with the new google.genai package
api_key = os.getenv("GOOGLE_API_KEY")
# Using a newer supported model
MODEL_NAME = "gemini-2.0-flash"

# Conversation history for multi-turn support
conversation_history: List[Dict[str, str]] = []

def ask(question: str, maintain_context: bool = True):
    """
    Ask a question using RAG with multi-turn conversation support.
    
    Args:
        question: The user's question
        maintain_context: Whether to use conversation history for context
    
    Returns:
        The LLM response
    """
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    db = Chroma(
        persist_directory=VECTOR_DB_DIR,
        embedding_function=embeddings
    )

    docs = db.similarity_search(question, k=4)
    context = "\n\n".join([d.page_content for d in docs])

    # Build conversation history string
    history_text = ""
    if maintain_context and conversation_history:
        history_text = "Previous conversation:\n"
        for exchange in conversation_history[-3:]:  # Keep last 3 exchanges for context
            history_text += f"User: {exchange['question']}\nAssistant: {exchange['answer']}\n\n"

    prompt = f"""
You are an academic assistant with access to specific documents.
Answer ONLY using the context below and previous conversation if provided.
If the answer is not present, say "Not found in documents".
Be conversational and maintain context from previous exchanges.

{history_text}

Context from documents:
{context}

Question:
{question}
"""

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        # Handle response from google.genai
        if hasattr(response, "text") and response.text:
            answer = response.text
        else:
            # Try nested structure for genai responses
            try:
                answer = response.candidates[0].content.parts[0].text
            except (AttributeError, IndexError, TypeError):
                answer = str(response)
        
        # Store in conversation history
        if maintain_context:
            conversation_history.append({
                "question": question,
                "answer": answer
            })
        
        return answer
    except Exception as e:
        # Provide clear error info and a safe extractive fallback using the
        # retrieved documents so the script doesn't crash when the model is
        # unavailable (e.g. model not found / deprecated package).
        err_summary = f"{e.__class__.__name__}: {e}"
        # Smarter extractive fallback: return sentences from context that match
        # important words from the question, filtering out headers/structure
        try:
            sentences = [s.strip() for s in context.replace('\n', ' ').split('.') if s.strip()]
            q_words = {w.lower() for w in question.split() if len(w) > 3}
            
            # Common imperative verbs that indicate headers/instructions
            imperative_verbs = {'write', 'explain', 'define', 'describe', 'discuss', 'list', 'state', 'mention', 'give', 'what', 'how', 'when', 'where', 'why'}
            
            # Filter: keep sentences with keywords, exclude headers and very short ones
            matches = [
                s for s in sentences 
                if any(w in s.lower() for w in q_words) 
                and len(s) > 20  # Avoid headers
                and s.lower() != question.lower()  # Don't repeat exact question
                and not any(s.lower().startswith(verb) for verb in imperative_verbs)  # Exclude imperative headers
            ]
            if matches:
                # Remove duplicates while preserving order
                seen = set()
                unique_matches = []
                for m in matches:
                    if m not in seen:
                        seen.add(m)
                        unique_matches.append(m)
                answer = "Fallback (extracted from documents): " + " ".join(unique_matches[:3])
                if maintain_context:
                    conversation_history.append({
                        "question": question,
                        "answer": answer
                    })
                return answer
        except Exception:
            pass
        
        fallback_answer = f"LLM error ({err_summary}). Fallback: Not found in documents."
        if maintain_context:
            conversation_history.append({
                "question": question,
                "answer": fallback_answer
            })
        return fallback_answer


def clear_history():
    """Clear conversation history"""
    global conversation_history
    conversation_history = []


def get_history() -> List[Dict[str, str]]:
    """Get current conversation history"""
    return conversation_history.copy()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("RAG Query Assistant - Multi-turn Conversation Mode")
    print("="*60)
    print("Type 'exit' to quit, 'clear' to clear history, 'history' to see conversation\n")
    
    while True:
        q = input("\nYou: ")
        if q.lower() == "exit":
            print("Goodbye!")
            break
        elif q.lower() == "clear":
            clear_history()
            print("Conversation history cleared.")
            continue
        elif q.lower() == "history":
            if conversation_history:
                print("\n--- Conversation History ---")
                for i, exchange in enumerate(conversation_history, 1):
                    print(f"\n[{i}] User: {exchange['question']}")
                    print(f"    Assistant: {exchange['answer'][:100]}...")
            else:
                print("No conversation history yet.")
            continue
        
        print("\nAssistant:")
        answer = ask(q, maintain_context=True)
        print(answer)
