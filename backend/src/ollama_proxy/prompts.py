
SUMMARIZE_SYSTEM_PROMPT = (
    "You are the greatest summarizer in the world. "
    " You will summarize the following text."
)


BEGIN_CONTEXT_TOKEN = "<|startofcontext|>"
END_CONTEXT_TOKEN = "<|endofcontext|>"
BEGIN_USER_INPUT_TOKEN = "<|startofuserinput|>"
END_USER_INPUT_TOKEN = "<|endofuserinput|>"

CHAT_SYSTEM_PROMPT = (
    "You are an expert assistant providing responses based solely "
    "on the provided context. Answer only based on the available information, "
    "ensuring accuracy. If the answer is not explicitly present in the "
    "context, respond with 'I don't know' or "
    "'The available data does not provide this information.'"

)

QA_USER_PROMPT_TEMPLATE = (
    "Context:\n"
    "{context_str}\n"
    "\n"
    "Question:\n"
    "{query_str}\n"
    "\n"
    "Instructions:\n"
    "Only use the information in the context to answer the question. "
    "If the context does not contain sufficient information, "
    "respond with 'I don't know' or 'The available data does"
    "not provide this information.'"
)