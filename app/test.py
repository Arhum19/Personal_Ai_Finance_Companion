# test_whisper_record.py
import os
import tempfile
import numpy as np
import sounddevice as sd
import soundfile as sf
import whisper
from pynput import keyboard
import re
from word2number import w2n
import dateparser
from datetime import datetime
import json

# Choose model: "tiny", "small", "base" -> tiny fastest on CPU
MODEL_NAME = "tiny"   # change to "tiny" for faster tests on CPU

print("Loading Whisper model (this may take a moment)...")
model = whisper.load_model(MODEL_NAME)
print(f"Model '{MODEL_NAME}' loaded.")

CATEGORIES = {
    'food': ['lunch', 'dinner', 'breakfast', 'coffee', 'meal', 'food', 'eat', 'brunch', 'restaurant'],
    'transport': ['transport', 'taxi', 'uber', 'bus', 'train', 'petrol', 'gas', 'fuel', 'ride', 'metro', 'uber'],
    'shopping': ['shopping', 'clothes', 'shoes', 'grocery', 'groceries', 'market', 'store', 'mall'],
    'entertainment': ['movie', 'cinema', 'netflix', 'game', 'gaming', 'concert', 'club'],
    'bills': ['bill', 'electricity', 'water', 'internet', 'phone', 'rent'],
    'health': ['doctor', 'medicine', 'pharmacy', 'gym', 'hospital'],
    'other': ['gift', 'donation', 'misc', 'other']
}

recording = False
audio_chunks = []

SAMPLE_RATE = 16000
CHANNELS = 1

def categorize(text):
    t = text.lower()
    for category, keywords in CATEGORIES.items():
        for kw in keywords:
            if kw in t:
                return category
    return 'other'

# helper: find numeric digits first, otherwise detect number-words in sequence
NUMBER_WORDS = set("""
zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen
twenty thirty forty fifty sixty seventy eighty ninety hundred thousand lakh million crore
""".split())

def extract_amount(text):
    # 1) digits like "500" or "500.50"
    m = re.search(r'(\d+(?:\.\d+)?)', text.replace(',', ''))
    if m:
        try:
            return float(m.group(1))
        except:
            pass
    # 2) words -> find contiguous tokens that are number words
    tokens = re.findall(r"[a-zA-Z]+", text.lower())
    current = []
    candidates = []
    for tok in tokens:
        if tok in NUMBER_WORDS:
            current.append(tok)
        else:
            if current:
                candidates.append(" ".join(current))
                current = []
    if current:
        candidates.append(" ".join(current))
    for cand in candidates:
        try:
            num = w2n.word_to_num(cand)
            return float(num)
        except Exception:
            continue
    return None

DATE_KEYWORDS = r'\b(today|yesterday|tomorrow|\d{1,2}(?:st|nd|rd|th)?\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*(?:\s+\d{2,4})?|last\s+\w+|\d+\s+days?\s+ago)\b'

def parse_date(text):
    # First try to extract date-related phrases
    match = re.search(DATE_KEYWORDS, text.lower())
    if match:
        date_phrase = match.group(0)
        dt = dateparser.parse(date_phrase, settings={'PREFER_DATES_FROM': 'past'})
        if dt:
            return dt.isoformat()
    
    # Fallback: try parsing entire text
    dt = dateparser.parse(text, settings={'PREFER_DATES_FROM': 'past'})
    if dt:
        return dt.isoformat()
    
    return datetime.now().isoformat()

def process_and_parse(wav_path):
    # transcribe using whisper
    print("Transcribing audio with Whisper...")
    result = model.transcribe(wav_path, language='en')
    transcribed = result.get("text", "").strip()
    print("Transcribed:", transcribed)

    amount = extract_amount(transcribed)
    category = categorize(transcribed)
    date_iso = parse_date(transcribed)

    expense = {
        "date": date_iso,
        "amount": amount,
        "category": category,
        "description": transcribed
    }
    print("Parsed expense:", json.dumps(expense, indent=2))
    return expense

# sounddevice callback: append frames
def callback(indata, frames, time, status):
    if recording:
        audio_chunks.append(indata.copy())

def on_press(key):
    global recording, audio_chunks
    try:
        if key == keyboard.Key.space and not recording:
            print("🎙️ Recording... hold SPACE and speak. Release to stop.")
            audio_chunks = []
            recording = True
    except AttributeError:
        pass

def on_release(key):
    global recording
    if key == keyboard.Key.esc:
        # Stop listener and exit
        return False
    if key == keyboard.Key.space and recording:
        print("⏹️ Stopped recording. Processing...")
        recording = False
        # concatenate
        data = np.concatenate(audio_chunks, axis=0)
        # write wav to temp file with correct samplerate and channels
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
            temp_wav = tf.name
        # soundfile expects shape (frames, channels)
        sf.write(temp_wav, data, SAMPLE_RATE)
        # process
        try:
            process_and_parse(temp_wav)
        finally:
            # remove temp file
            os.remove(temp_wav)

# main: create input stream and keyboard listener
if __name__ == "__main__":
    stream = sd.InputStream(callback=callback, channels=CHANNELS, samplerate=SAMPLE_RATE)
    stream.start()
    print("Ready. Hold SPACE to record and release to process.")
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        try:
            listener.join()
        except KeyboardInterrupt:
            print("Exiting...")
        finally:
            stream.stop()
