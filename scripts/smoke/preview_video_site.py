"""Local static preview with byte-range support so MP4 timeline seeking works."""

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
import re


class RangeHandler(SimpleHTTPRequestHandler):
    def send_head(self):
        self.remaining = None
        path = self.translate_path(self.path)
        request_range = self.headers.get("Range")
        if not request_range or not os.path.isfile(path):
            return super().send_head()
        size = os.path.getsize(path)
        match = re.fullmatch(r"bytes=(\d*)-(\d*)", request_range.strip())
        if not match or not any(match.groups()):
            self.send_error(416, "Unsupported byte range")
            return None
        begin, end = match.groups()
        if not begin:
            start, stop = max(0, size - int(end)), size - 1
        else:
            start, stop = int(begin), min(int(end) if end else size - 1, size - 1)
        if start >= size or stop < start:
            self.send_response(416)
            self.send_header("Content-Range", f"bytes */{size}")
            self.end_headers()
            return None
        file = open(path, "rb")
        file.seek(start)
        self.remaining = stop - start + 1
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Content-Length", str(self.remaining))
        self.send_header("Content-Range", f"bytes {start}-{stop}/{size}")
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        return file

    def end_headers(self):
        self.send_header("Accept-Ranges", "bytes")
        super().end_headers()

    def copyfile(self, source, outputfile):
        if self.remaining is None:
            return super().copyfile(source, outputfile)
        while self.remaining > 0:
            chunk = source.read(min(self.remaining, 64 * 1024))
            if not chunk:
                break
            outputfile.write(chunk)
            self.remaining -= len(chunk)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True)
    parser.add_argument("--port", type=int, default=8767)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), partial(RangeHandler, directory=args.directory))
    print(f"Video preview: http://127.0.0.1:{args.port}", flush=True)
    server.serve_forever()
