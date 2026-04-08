from post_search import Post
import streamlit as st
import torch

@st.cache_resource
def load_model():
    # model_name = "cointegrated/rubert-tiny2-cedr-emotion-detection"
    # return AutoTokenizer.from_pretrained(model_name), AutoModelForSequenceClassification.from_pretrained(model_name)
    # return pipeline("text-classification", model_name)
    model_file = "big_bert_trained.pt"
    with open(model_file, "rb") as f:
        pipe = torch.load(f, weights_only=False)
    return pipe

# tokenizer, model = load_model()
pipe = load_model()
emotions = ['no_emotion', 'joy', 'sadness', 'surprise', 'fear', 'anger']
BATCH_SIZE = 64

# def get_sentiment(posts: list[Post]):
#     all_texts = [post.text for post in posts]
#     result = []
#     for i in range(0, len(all_texts), BATCH_SIZE):
#         texts = all_texts[i*BATCH_SIZE:(i+1)*BATCH_SIZE]
#         inputs = tokenizer(texts, padding=True, truncation=True, max_len=512, return_tensors='pt')
#         print("Got tokens", inputs, flush=True)
#         output = model(**inputs)
#         print("Got output", flush=True)
#         probs = torch.softmax(output['logits'], dim=-1)
#         print("Got probs", flush=True)
#         result.extend([{emotion: probs[i, j].item() for j, emotion in enumerate(emotions)} for i in range(len(probs))])
#     return result

def get_sentiment(posts: list[Post]):
    all_texts = [post.text for post in posts]
    return pipe(all_texts, truncation=True, max_len=2048)