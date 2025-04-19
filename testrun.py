# from PIL import Image
# from transformers import AutoModelForCausalLM, AutoProcessor

# model_path = "moonshotai/Kimi-VL-A3B-Thinking"
# model = AutoModelForCausalLM.from_pretrained(
#     model_path,
#     torch_dtype="auto",
#     device_map="auto",
#     trust_remote_code=True,
# )
# processor = AutoProcessor.from_pretrained(model_path, trust_remote_code=True)

# image_paths = ["image1.png"]
# images = [Image.open(path) for path in image_paths]
# messages = [
#     {
#         "role": "user",
#         "content": [
#             {"type": "image", "image": image_path} for image_path in image_paths
#         ] + [{"type": "text", "text": "Explain this meme step by step. Break down the visual elements, cultural references, and implied meaning. Identify any notable characters, templates, or formats used. Describe why this might be considered funny or relatable to certain audiences."}],
#     },
# ]
# text = processor.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt")
# inputs = processor(images=images, text=text, return_tensors="pt", padding=True, truncation=True).to(model.device)
# generated_ids = model.generate(**inputs, max_new_tokens=2048)
# generated_ids_trimmed = [
#     out_ids[len(in_ids) :] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
# ]
# response = processor.batch_decode(
#     generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
# )[0]
# print(response)


# To run this test, make sure you have Ollama running locally and a model pulled (e.g., llama3 or llama3.1)
# Install dependencies with:
#   pip install -U langchain-ollama ollama

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage

messages = [
    HumanMessage(
        content=(
            "System: You are a Twitter content classifier focused on AI industry developments.\n"
            "Your task is to identify tweets about significant AI developments by returning only YES or NO.\n\n"
            "Include tweets about:\n"
            "- New AI model releases or major updates (e.g., GPT-4, Claude 3, Gemini)\n"
            "- Significant AI agent developments or breakthroughs\n"
            "- AI performance benchmarks and competition results\n"
            "- AI in finance, quantitative research, or algorithmic trading\n"
            "- Research paper announcements with notable findings\n\n"
            "Exclude tweets about:\n"
            "- Tutorials or educational content\n"
            "- General AI discussions\n"
            "- Personal opinions without news\n"
            "- Marketing or promotional content\n\n"
            "Human: Analyze this tweet and respond with YES if it contains significant AI news or NO if it doesn't:\n\n"
            "Best wrist exercise ever"
        ),
        additional_kwargs={},
        response_metadata={}
    )
]



# Instantiate the Ollama chat model
llm = ChatOllama(
    model="phi4-mini",  # Change to your local model name if needed
    temperature=0,
    base_url="http://127.0.0.1:11434"
)

# # Define the messages for translation
# messages = [
#     ("system", "You are a helpful assistant that translates English to French. Translate the user sentence."),
#     ("human", "I love programming."),
# ]

# Invoke the model
ai_msg = llm.invoke(messages)

# Print the response
print(ai_msg.content)
