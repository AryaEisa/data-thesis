import pandas as pd
import emoji
import re
import openai
import time


openai.api_key = ""


def remove_emojis(text):
    return emoji.replace_emoji(text, replace='')


def correct_spelling_gpt(text):
    try:
        prompt = f"Korrigera endast stavfel i följande svenska text. Ändra inte meningsstruktur, ordval eller innehållets betydelse. Behåll originalets ton, grammatik och stil så långt det går. Lägg inte till eller ta bort information. Texten är:\n\n{text}"
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Du är en textkorrigerare som rättar stavfel i svenska texter."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=1024
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Fel vid GPT-anrop: {e}")
        return text


df = pd.read_csv()

df['text'] = df['text'].astype(str).apply(remove_emojis)


df = df.drop_duplicates(subset='text')


corrected_texts = []
for i, row in df.iterrows():
    print(f"Bearbetar rad {i+1} av {len(df)}...")
    corrected_text = correct_spelling_gpt(row['text'])
    corrected_texts.append(corrected_text)
    time.sleep(1.5) 

df['corrected_text'] = corrected_texts

# 💾 Spara resultat
df.to_csv("rensad_och_korrigerad.csv", index=False)
print("✅ Fil sparad som 'rensad_och_korrigerad.csv'")
