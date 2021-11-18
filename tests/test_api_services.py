import os
import unittest
from time import time
from neon_utils.mq_utils import send_mq_request


class TestNeonServices(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ["NEON_CONFIG_PATH"] = os.path.join(os.path.dirname(__file__), "config")

    def test_api_proxy(self):
        resp = send_mq_request("/neon_api", {"test": True,
                                             "service": "api_test_endpoint"}, "neon_api_input", "neon_api_output")
        self.assertIsInstance(resp, dict)
        self.assertEqual(resp['status_code'], 200)

        resp = send_mq_request("/neon_api", {"test": True,
                                             "service": "not_implemented"}, "neon_api_input", "neon_api_output")
        self.assertIsInstance(resp, dict)
        self.assertEqual(resp['status_code'], 401)

    def test_brands_service(self):
        brand_coupon_data = send_mq_request("/neon_coupons", {"brands": True,
                                                              "coupons": True}, "neon_coupons_input")
        self.assertTrue(brand_coupon_data["success"])

    def test_email_proxy(self):
        request_data = {"recipient": "test@neongecko.com",
                        "subject": "Test Message",
                        "body": "This is a test\ncalled from neon_skill_tests.py in neon-utils",
                        "attachments": None}
        data = send_mq_request("/neon_emails", request_data, "neon_emails_input")
        self.assertTrue(data.get("success"))

    def test_metrics_service(self):
        t = time()
        send_mq_request("/neon_metrics", {"name": "test",
                                          "time": t}, "neon_metrics_input", expect_response=False)
        # TODO: Check metrics dir for this entry

    def test_script_parser(self):
        TEST_PATH = os.path.join(os.path.dirname(__file__), "ccl")
        with open(os.path.join(TEST_PATH, "test.nct")) as f:
            text = f.read()
        resp = send_mq_request("/neon_script_parser", {"text": text,
                                                       "meta": {"test": "val"}}, "neon_script_parser_input", timeout=45)
        self.assertIsInstance(resp, dict)
        self.assertIsInstance(resp["parsed_file"], str)


if __name__ == '__main__':
    unittest.main()
