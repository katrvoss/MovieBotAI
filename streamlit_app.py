import streamlit as st
from random import choice
import time

# -----------------------------
# Simple "AI" movie database
# -----------------------------
MOVIES = {
    "action": [
        "Mad Max: Fury Road",
        "John Wick",
        "The Dark Knight",
    ],
    "comedy": [
        "Superbad",
        "The Lego Movie",
        "Ghostbusters",
    ],
    "drama": [
        "The Shawshank Redemption",
        "Forrest Gump",
        "The Green Mile",
    ],
    "scifi": [
        "Inception",
        "Interstellar",
        "The Matrix",
    ],
    "horror": [
        "Get Out",
        "A Quiet Place",
        "The Conjuring",
    ],
}

# -----------------------------
# Session state initialization
# -----------------------------
if "stage" not in st.session_state:
    st.session_state.stage = "user"       # which part of the UI to show
    st.session_state.history = []         # full chat history
    st.session_state.pending = None       # pending assistant answer text
    st.session_state.validation = {}      # used in the validation stage

st.title("AI Movie Buddy 🎬")
st.caption("A simple AI-style movie recommendation chatbot (no API key required).")


# -----------------------------
# AI logic: generate a response
# -----------------------------
def get_genre_from_text(text: str) -> str | None:
    """
    Very simple 'AI' logic:
    - Look for known genre keywords in the user's text.
    - Return the matched genre key or None if nothing is found.
    """
    text = text.lower()
    for genre in MOVIES.keys():
        if genre in text:
            return genre
    # also map some mood words to genres
    if "funny" in text or "laugh" in text:
        return "comedy"
    if "scary" in text or "spooky" in text or "horror" in text:
        return "horror"
    if "sad" in text or "emotional" in text:
        return "drama"
    if "space" in text or "future" in text:
        return "scifi"
    if "fight" in text or "explosion" in text or "fast" in text:
        return "action"
    return None


def generate_movie_recommendation(prompt: str) -> str:
    """
    Given user input, pick a genre and recommend a movie.
    If no genre is found, ask the user to clarify.
    No external APIs or keys are used.
    """
    text = prompt.strip().lower()

    # handle 'exit' or 'quit'
    if text in ["exit", "quit"]:
        return "Okay, ending the chat. Thanks for using AI Movie Buddy! 👋"

    genre = get_genre_from_text(prompt)

    # invalid / unclear input
    if genre is None:
        return (
            "I'm not sure what kind of movie you want yet. "
            "Try mentioning a genre like action, comedy, drama, sci-fi, or horror, "
            "or describe your mood."
        )

    # choose a random movie from the detected genre
    movie = choice(MOVIES[genre])
    return (
        f"You seem in the mood for a(n) {genre} movie. "
        f"How about: {movie}? 🎥\n\n"
        "You can ask again for another suggestion or type 'exit' to end the chat."
    )


# -----------------------------
# Validation helpers
# -----------------------------
def validate(response: str):
    """
    Fake 'validation' logic:
    - Split the answer into sentences.
    - Mark sentences valid if they have more than 4 spaces
      (i.e., more than 5 words).
    """
    response_sentences = response.split(". ")
    response_sentences = [
        sentence.strip(". ") + "."
        for sentence in response_sentences
        if sentence.strip(". ") != ""
    ]
    validation_list = [
        True if sentence.count(" ") > 4 else False for sentence in response_sentences
    ]
    return response_sentences, validation_list


def add_highlights(response_sentences, validation_list, bg="red", text="red"):
    """
    Wrap sentences that failed validation in a colored highlight.
    """
    return [
        f":{text}[:{bg}-background[" + sentence + "]]" if not is_valid else sentence
        for sentence, is_valid in zip(response_sentences, validation_list)
    ]


# -----------------------------
# Display chat history
# -----------------------------
for message in st.session_state.history:
    with st.chat_message(message["role"]):
        st.write(message["content"])


# -----------------------------
# Main chat stages
# -----------------------------
if st.session_state.stage == "user":
    # User can type a prompt for a movie recommendation
    user_input = st.chat_input(
        "Tell me what kind of movie you want (or type 'exit' to quit):"
    )
    if user_input:
        # Save and show user message
        st.session_state.history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        # Generate AI-style movie recommendation
        with st.chat_message("assistant"):
            # Simulate thinking delay
            with st.spinner("Thinking of a movie for you..."):
                time.sleep(0.5)
            response = generate_movie_recommendation(user_input)
            st.write(response)

        # Store pending response and move to validation stage
        st.session_state.pending = response
        st.session_state.stage = "validate"
        st.rerun()

elif st.session_state.stage == "validate":
    # User temporarily cannot type; must accept/correct/rewrite first
    st.chat_input("Accept, correct, or rewrite the answer above.", disabled=True)

    response_sentences, validation_list = validate(st.session_state.pending)
    highlighted_sentences = add_highlights(response_sentences, validation_list)

    with st.chat_message("assistant"):
        st.markdown(" ".join(highlighted_sentences))
        st.divider()
        cols = st.columns(3)

        # Button: Correct errors
        if cols[0].button(
            "Correct errors", type="primary", disabled=all(validation_list)
        ):
            st.session_state.validation = {
                "sentences": response_sentences,
                "valid": validation_list,
            }
            st.session_state.stage = "correct"
            st.rerun()

        # Button: Accept as-is
        if cols[1].button("Accept"):
            st.session_state.history.append(
                {"role": "assistant", "content": st.session_state.pending}
            )
            st.session_state.pending = None
            st.session_state.validation = {}
            st.session_state.stage = "user"
            st.rerun()

        # Button: Rewrite entire answer
        if cols[2].button("Rewrite answer", type="tertiary"):
            st.session_state.stage = "rewrite"
            st.rerun()

elif st.session_state.stage == "correct":
    st.chat_input("Accept, correct, or rewrite the answer above.", disabled=True)

    response_sentences = st.session_state.validation["sentences"]
    validation_list = st.session_state.validation["valid"]
    highlighted_sentences = add_highlights(
        response_sentences, validation_list, "gray", "gray"
    )

    # Focus on the first invalid sentence, if any
    if not all(validation_list):
        focus = validation_list.index(False)
        highlighted_sentences[focus] = ":red[:red" + highlighted_sentences[focus][11:]
    else:
        focus = None

    with st.chat_message("assistant"):
        st.markdown(" ".join(highlighted_sentences))
        st.divider()

        if focus is not None:
            # Let user replace or remove the invalid sentence
            new_sentence = st.text_input(
                "Replacement text:", value=response_sentences[focus]
            )
            cols = st.columns(2)
            if cols[0].button(
                "Update", type="primary", disabled=len(new_sentence.strip()) < 1
            ):
                st.session_state.validation["sentences"][focus] = (
                    new_sentence.strip(". ") + "."
                )
                st.session_state.validation["valid"][focus] = True
                st.session_state.pending = " ".join(
                    st.session_state.validation["sentences"]
                )
                st.rerun()
            if cols[1].button("Remove"):
                st.session_state.validation["sentences"].pop(focus)
                st.session_state.validation["valid"].pop(focus)
                st.session_state.pending = " ".join(
                    st.session_state.validation["sentences"]
                )
                st.rerun()
        else:
            # All sentences valid; accept or re-validate
            cols = st.columns(2)
            if cols[0].button("Accept", type="primary"):
                st.session_state.history.append(
                    {"role": "assistant", "content": st.session_state.pending}
                )
                st.session_state.pending = None
                st.session_state.validation = {}
                st.session_state.stage = "user"
                st.rerun()
            if cols[1].button("Re-validate"):
                st.session_state.validation = {}
                st.session_state.stage = "validate"
                st.rerun()

elif st.session_state.stage == "rewrite":
    st.chat_input("Accept, correct, or rewrite the answer above.", disabled=True)
    with st.chat_message("assistant"):
        new = st.text_area("Rewrite the answer", value=st.session_state.pending)
        if st.button(
            "Update", type="primary", disabled=new is None or new.strip(". ") == ""
        ):
            st.session_state.history.append({"role": "assistant", "content": new})
            st.session_state.pending = None
            st.session_state.validation = {}
            st.session_state.stage = "user"
            st.rerun()
