"""Times one TTS service: py tools/bench.py http://127.0.0.1:9160 [--token T] [--voice V] [--runs 3] [--save DIR]

Sends the same sentences to /v1/speak and prints, per sentence, the wait, the audio length and how many times faster
than real time it was. Run it against TTSPiperModel and TTSParadeeModel with the same sentences to compare them.
Uses only the standard library."""
import argparse
import json
import pathlib
import time
import urllib.request

SENTENCES = [
    "Hello there.",
    "In the wild, parakeets fly in loud, colorful flocks across the open grasslands of Australia.",
    "The quick brown fox jumps over the lazy dog. She sells seashells by the seashore. Tomatoes and avocados were on the schedule.",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--token", default="")
    parser.add_argument("--voice", default=None)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--save", default="")
    args = parser.parse_args()
    for number, text in enumerate(SENTENCES, 1):
        body = {"text": text, **({"voice": args.voice} if args.voice else {})}
        for run in range(1, args.runs + 1):
            request = urllib.request.Request(args.url.rstrip("/") + "/v1/speak", json.dumps(body).encode(),
                                             {"Content-Type": "application/json", "X-Internal-Token": args.token})
            started = time.perf_counter()
            with urllib.request.urlopen(request, timeout=300) as reply:
                audio, headers = reply.read(), reply.headers
            wait = time.perf_counter() - started
            seconds = float(headers["X-Audio-Seconds"])
            print(f"sentence {number} run {run}: wait {wait:.3f}s  audio {seconds:.2f}s  {seconds / wait:5.1f}x real time  voice {headers['X-Voice']}")
            if args.save and run == 1:
                folder = pathlib.Path(args.save)
                folder.mkdir(parents=True, exist_ok=True)
                (folder / f"{number}-{headers['X-Voice']}.wav").write_bytes(audio)


if __name__ == "__main__":
    main()
