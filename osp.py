import asyncio
import os

# This example uses aiofile for asynchronous file reads.
# It's not a dependency of the project but can be installed
# with `pip install aiofile`.
import aiofile

import requests
import urllib.parse

from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import TranscriptEvent

api_url = ""
api_resource = ""

"""
Here's an example of a custom event handler you can extend to
process the returned transcription results as needed. This
handler will simply print the text out to your interpreter.
"""


def move(y, x):
    print("\033[%d;%dH" % (y, x))


class MyEventHandler(TranscriptResultStreamHandler):
    async def handle_transcript_event(self, transcript_event: TranscriptEvent):
        # This handler can be implemented to handle transcriptions as needed.
        # Here's an example to get started.
        results = transcript_event.transcript.results
        for result in results:
            for alt in result.alternatives:
                r = get_req(alt.transcript)
                f = get_face(r)
                k = get_key_phrases(r)
                os.system('clear')
                print(f + alt.transcript + '\n')
                print(k)

def get_req(text: str) -> list:
    arg = urllib.parse.quote(text)
    url = api_url + api_resource + '?' + 'content=' + arg
    req = requests.get(url).json()
    return req

def get_face(req: list) -> str:
    sentiment = req.get('sentiment')
    max_value = max(sentiment.get('Neutral'), sentiment.get(
        'Mixed'), sentiment.get('Negative'), sentiment.get('Positive'))
    if max_value > 0.5:
        if max_value == sentiment.get('Neutral'):
            face = '😑'
        elif max_value == sentiment.get('Mixed'):
            face = '🤔'
        elif max_value == sentiment.get('Negative'):
            face = '😡'
        elif max_value == sentiment.get('Positive'):
            face = '😍'
    else:
        face = '😑'
    return face


def get_key_phrases(req: list) -> str:
    kp = '|'
    key_phrases = req.get('key_phrases')
    for k in key_phrases:
        kp += k + '|'
    return kp

async def basic_transcribe():
    # Setup up our client with our chosen AWS region
    client = TranscribeStreamingClient(region="ap-northeast-1")

    # Start transcription to generate our async stream
    stream = await client.start_stream_transcription(
        language_code="ja-JP",
        media_sample_rate_hz=22050,
        media_encoding="pcm",
    )

    async def write_chunks():
        # An example file can be found at tests/integration/assets/test.wav
        # NOTE: For pre-recorded files longer than 5 minutes, the sent audio
        # chunks should be rate limited to match the realtime bitrate of the
        # audio stream to avoid signing issues.
        async with aiofile.AIOFile('kushikawa.wav', 'rb') as afp:
            reader = aiofile.Reader(afp, chunk_size=1024 * 16)
            async for chunk in reader:
                await stream.input_stream.send_audio_event(audio_chunk=chunk)
        await stream.input_stream.end_stream()

    # Instantiate our handler and start processing events
    handler = MyEventHandler(stream.output_stream)
    await asyncio.gather(write_chunks(), handler.handle_events())

loop = asyncio.get_event_loop()
loop.run_until_complete(basic_transcribe())
loop.close()
