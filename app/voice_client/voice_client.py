"""
Voice Client for Finance Companion
Records voice input, transcribes with Whisper, parses, and sends to API.

Usage:
    cd D:\Finance_companion
    python -m app.voice_client.voice_client

Controls:
    - Hold SPACE to record, release to process
    - Press 'L' to login
    - Press 'B' to check balance
    - Press 'C' to list categories
    - Press ESC to exit
"""
import os
import sys
import tempfile
import numpy as np
import sounddevice as sd
import soundfile as sf
import whisper
from pynput import keyboard

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.voice_client.config import WHISPER_MODEL, SAMPLE_RATE, CHANNELS
from app.voice_client.nlp_parser import parse_text, format_parsed_data
from app.voice_client.api_client import get_client


class VoiceClient:
    """
    Voice-to-Finance client.
    Records audio, transcribes with Whisper, parses, and sends to API.
    """
    
    def __init__(self):
        self.recording = False
        self.audio_chunks = []
        self.model = None
        self.api_client = get_client()
        self.stream = None
        self.confirm_mode = True  # Ask for confirmation before sending
    
    def load_whisper_model(self):
        """Load Whisper model."""
        print(f"🔄 Loading Whisper model '{WHISPER_MODEL}'... (this may take a moment)")
        self.model = whisper.load_model(WHISPER_MODEL)
        print(f"✅ Model '{WHISPER_MODEL}' loaded successfully!")
    
    def audio_callback(self, indata, frames, time, status):
        """Callback for audio stream."""
        if self.recording:
            self.audio_chunks.append(indata.copy())
    
    def start_recording(self):
        """Start recording audio."""
        if not self.recording:
            print("\n🎙️ Recording... (hold SPACE and speak, release to stop)")
            self.audio_chunks = []
            self.recording = True
    
    def stop_recording(self):
        """Stop recording and process audio."""
        if self.recording:
            print("⏹️ Processing...")
            self.recording = False
            
            if not self.audio_chunks:
                print("⚠️ No audio recorded")
                return
            
            # Concatenate audio chunks
            audio_data = np.concatenate(self.audio_chunks, axis=0)
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
                temp_path = tf.name
            sf.write(temp_path, audio_data, SAMPLE_RATE)
            
            try:
                self.process_audio(temp_path)
            finally:
                os.remove(temp_path)
    
    def process_audio(self, audio_path: str):
        """Process audio file: transcribe, parse, and optionally send to API."""
        # Transcribe with Whisper
        print("🔊 Transcribing with Whisper...")
        result = self.model.transcribe(audio_path, language='en')
        transcribed = result.get("text", "").strip()
        
        if not transcribed:
            print("⚠️ Could not transcribe audio. Please try again.")
            return
        
        print(f"\n📝 Transcribed: \"{transcribed}\"")
        
        # Parse text
        parsed = parse_text(transcribed)
        
        if parsed.get("error"):
            print(f"❌ Parse error: {parsed['error']}")
            return
        
        if not parsed.get("amount"):
            print("⚠️ Could not detect amount. Please mention the amount clearly.")
            print(format_parsed_data(parsed))
            return
        
        # Display parsed data
        print("\n" + format_parsed_data(parsed))
        
        # Confirm before sending (if enabled)
        if self.confirm_mode:
            print("\n❓ Send to API? (y/n/e to edit): ", end="", flush=True)
            confirm = input().strip().lower()
            
            if confirm == 'n':
                print("❌ Cancelled")
                return
            elif confirm == 'e':
                parsed = self.edit_parsed_data(parsed)
                if not parsed:
                    return
        
        # Send to API
        self.send_to_api(parsed)
    
    def edit_parsed_data(self, parsed: dict) -> dict:
        """Allow user to edit parsed data."""
        print("\n📝 Edit mode (press Enter to keep current value):")
        
        if parsed["type"] == "expense":
            new_title = input(f"   Title [{parsed['title']}]: ").strip()
            new_amount = input(f"   Amount [{parsed['amount']}]: ").strip()
            new_category = input(f"   Category [{parsed['category']}]: ").strip()
            
            if new_title:
                parsed['title'] = new_title
            if new_amount:
                try:
                    parsed['amount'] = float(new_amount)
                except ValueError:
                    print("⚠️ Invalid amount, keeping original")
            if new_category:
                parsed['category'] = new_category.lower()
        else:
            new_amount = input(f"   Amount [{parsed['amount']}]: ").strip()
            new_source = input(f"   Source [{parsed['source']}]: ").strip()
            
            if new_amount:
                try:
                    parsed['amount'] = float(new_amount)
                except ValueError:
                    print("⚠️ Invalid amount, keeping original")
            if new_source:
                parsed['source'] = new_source
        
        print("\n📋 Updated:")
        print(format_parsed_data(parsed))
        
        confirm = input("\n❓ Send now? (y/n): ").strip().lower()
        if confirm != 'y':
            print("❌ Cancelled")
            return None
        
        return parsed
    
    def send_to_api(self, parsed: dict):
        """Send parsed data to API."""
        if parsed["type"] == "income":
            result = self.api_client.post_income({
                "amount": parsed["amount"],
                "source": parsed["source"],
                "date": parsed["date"]
            })
        else:
            result = self.api_client.post_expense({
                "title": parsed["title"],
                "amount": parsed["amount"],
                "category": parsed["category"],
                "description": parsed["description"],
                "date": parsed["date"]
            })
        
        if not result.get("error"):
            print(f"\n✅ {parsed['type'].capitalize()} saved! ID: {result.get('id')}")
    
    def show_balance(self):
        """Show current balance."""
        print("\n💰 Fetching balance...")
        balance = self.api_client.get_balance()
        
        if balance.get("error"):
            print(f"❌ {balance['error']}")
        else:
            print(f"\n📊 Balance Summary:")
            print(f"   Total Income:  ₹{float(balance['total_income']):,.2f}")
            print(f"   Total Expense: ₹{float(balance['total_expense']):,.2f}")
            print(f"   Balance:       ₹{float(balance['remaining_balance']):,.2f}")
    
    def show_categories(self):
        """Show available categories."""
        print("\n📂 Fetching categories...")
        categories = self.api_client.fetch_categories()
        
        if categories:
            print(f"\n📂 Your Categories ({len(categories)}):")
            for name, cat_id in categories.items():
                print(f"   • {name.capitalize()} (ID: {cat_id})")
        else:
            print("❌ No categories found or not authenticated")
    
    def on_press(self, key):
        """Handle key press events."""
        try:
            # SPACE to record
            if key == keyboard.Key.space:
                self.start_recording()
            
            # Character keys
            elif hasattr(key, 'char'):
                if key.char == 'l':
                    print("\n🔐 Login")
                    self.api_client.login()
                    self.api_client.fetch_categories()
                
                elif key.char == 'b':
                    self.show_balance()
                
                elif key.char == 'c':
                    self.show_categories()
                
                elif key.char == 'q':
                    print("\n👋 Goodbye!")
                    return False
                    
        except AttributeError:
            pass
    
    def on_release(self, key):
        """Handle key release events."""
        # ESC to exit
        if key == keyboard.Key.esc:
            print("\n👋 Goodbye!")
            return False
        
        # SPACE released = stop recording
        if key == keyboard.Key.space:
            self.stop_recording()
    
    def run(self):
        """Main run loop."""
        print("\n" + "=" * 60)
        print("🎤 Finance Companion - Voice Client")
        print("=" * 60)
        
        # Load Whisper model
        self.load_whisper_model()
        
        # Ensure authenticated
        if not self.api_client.ensure_authenticated():
            print("❌ Authentication required to continue")
            return
        
        # Load categories
        self.api_client.fetch_categories()
        
        # Show controls
        print("\n" + "-" * 60)
        print("🎮 Controls:")
        print("   SPACE (hold) = Record voice")
        print("   L = Login")
        print("   B = Check balance")
        print("   C = List categories")
        print("   Q or ESC = Exit")
        print("-" * 60)
        print("\n✅ Ready! Hold SPACE and speak your expense or income.")
        
        # Start audio stream
        self.stream = sd.InputStream(
            callback=self.audio_callback,
            channels=CHANNELS,
            samplerate=SAMPLE_RATE
        )
        self.stream.start()
        
        # Start keyboard listener
        with keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        ) as listener:
            try:
                listener.join()
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
            finally:
                self.stream.stop()


def main():
    """Entry point."""
    client = VoiceClient()
    client.run()


if __name__ == "__main__":
    main()
