import io
import json
import urllib.error
import unittest
from unittest.mock import patch
from mcp_geruest.__main__ import ticket_eskalieren, bearbeite


class McpEskalierenTest(unittest.TestCase):
    def test_agent_und_403(self):
        body = {"code": "eskalation_verboten", "meldung": "Nur mensch", "korrelation": "test"}
        error = urllib.error.HTTPError("http://localhost", 403, "Forbidden", {},
                                       io.BytesIO(json.dumps(body).encode()))
        with patch("mcp_geruest.__main__.urllib.request.urlopen", side_effect=error) as call:
            fehl, text = ticket_eskalieren({"id": 433})
        self.assertTrue(fehl)
        self.assertIn("HTTP 403", text)
        self.assertIn("eskalation_verboten", text)
        req = call.call_args.args[0]
        self.assertEqual(req.method, "POST")
        self.assertTrue(req.full_url.endswith("/api/tickets/433/eskalieren"))
        self.assertEqual(dict(req.header_items())["X-aufrufer"], "agent")

    def test_parameter_nicht_als_rollenwechsel_nutzbar(self):
        with patch("mcp_geruest.__main__.urllib.request.urlopen") as call:
            for args in [{}, {"id": True}, {"id": "433"}, {"id": 433, "aufrufer": "mensch"}, []]:
                self.assertTrue(ticket_eskalieren(args)[0])
            call.assert_not_called()

    def test_tool_liste(self):
        with patch("sys.stdout", new_callable=io.StringIO) as output:
            bearbeite({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        tools = json.loads(output.getvalue())["result"]["tools"]
        self.assertEqual({t["name"] for t in tools}, {"ticket_lesen", "ticket_eskalieren"})
