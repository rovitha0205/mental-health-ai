from transformers import pipeline

emotion_classifier = pipeline(
    "text-classification",
    model="j-hartmann/emotion-english-distilroberta-base",
    return_all_scores=True
)

text = "I feel very lonely and sad today"
result = emotion_classifier(text)

print(result)
