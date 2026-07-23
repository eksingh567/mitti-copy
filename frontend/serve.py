import http.server
import socketserver

class NoCacheHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

if __name__ == '__main__':
    PORT = 8000
    with socketserver.TCPServer(("", PORT), NoCacheHTTPRequestHandler) as httpd:
        print("Serving without cache at port", PORT)
        httpd.serve_forever()
