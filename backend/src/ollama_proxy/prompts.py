# Description: This file contains the prompt templates for the different tasks.
# The prompts are used to instruct the instruct model on how to perform.
# Feel free to modify the prompts to suit your needs.

SUMMARIZE_SYSTEM_PROMPT = (
    "You are tasked with generating a concise summary of the provided "
    "document chunks that captures the document's main purpose, key arguments, "
    "and significant points. Only include essential information as presented "
    "in the text, and ensure the summary flows naturally. Do not add "
    "introductory phrases, commentary, or extra wording—only shorten and "
    "combine the content accurately. The summary should be limited to "
    "the document's actual information and reflect its content directly."
)

SUMMARIZE_PROMPT_TEMPLATE = (
    "Please read the following text and generate a concise summary. "
    "The summary should focus on the key arguments, findings, or conclusions, "
    "written in a clear and factual manner without referencing the text "
    "or context directly.\n\n"
    "Text: {context_str}\n\n"
    "Summary:"
)

QA_SYSTEM_PROMPT = (
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

DOCUMENT_RERANK_SYSTEM_PROMPT = (
    "You are an assistant that evaluates the relevance of documents based "
    "on a given user query. Your task is to analyze the text chunk provided "
    "and determine if it directly addresses or is useful for answering "
    "the query. If the text chunk is relevant, respond with "
    "{{\"relevant\": \"yes\"}}, and if it is not relevant, "
    "respond with {{\"relevant\": \"no\"}}. Provide only the "
    "JSON output without any additional commentary."
)

DOCUMENT_RERANK_PROMPT_TEMPLATE = (
    "Given the following text chunk and user query, classify "
    "whether the document is relevant to the query.\n"
    "\n"
    "Document Summary:\n"
    "{document_summary}\n"
    "\n"
    "User Query:\n"
    "\n"
    "{user_query}\n"
    "\n"
    "Provide your answer in JSON format as "
    "{{\"relevant\": \"yes\"}} or {{\"relevant\": \"no\"}}."
)