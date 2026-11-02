import json
import unittest
import urllib.error
import urllib.request

from tt_referee.scoring import ScoreEngine, ScoringRules
from tt_referee.ui.server import ScoreServer


class TestUIServer(unittest.TestCase):
    def setUp(self):
        self.engine = ScoreEngine(ScoringRules(best_of=5), log_events=False)

    def get(self, url):
        with urllib.request.urlopen(url, timeout=5) as response:
            return response.status, response.read()

    def post(self, url):
        request = urllib.request.Request(url, method="POST")
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, response.read()

    def test_state_and_static(self):
        server = ScoreServer(self.engine, port=0, allow_demo=True).start()
        try:
            status, body = self.get(server.url + "api/state")
            self.assertEqual(status, 200)
            data = json.loads(body)
            self.assertEqual(data["points"], {"A": 0, "B": 0})
            self.assertTrue(data["demo"])
            self.assertIn("side_of_a", data)
            status, html = self.get(server.url)
            self.assertEqual(status, 200)
            self.assertIn("选手 A", html.decode("utf-8"))
        finally:
            server.stop()

    def test_demo_mutations(self):
        server = ScoreServer(self.engine, port=0, allow_demo=True).start()
        try:
            self.post(server.url + "api/demo/award?side=A")
            _, body = self.get(server.url + "api/state")
            self.assertEqual(json.loads(body)["points"]["A"], 1)
            self.post(server.url + "api/demo/undo")
            _, body = self.get(server.url + "api/state")
            self.assertEqual(json.loads(body)["points"]["A"], 0)
            self.post(server.url + "api/demo/pending")
            _, body = self.get(server.url + "api/state")
            self.assertIsNotNone(json.loads(body)["pending"])
        finally:
            server.stop()

    def test_read_only_mode(self):
        server = ScoreServer(self.engine, port=0, allow_demo=False).start()
        try:
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                self.post(server.url + "api/demo/award?side=A")
            self.assertEqual(ctx.exception.code, 403)
        finally:
            server.stop()


if __name__ == "__main__":
    unittest.main()
