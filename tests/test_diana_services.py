# NEON AI (TM) SOFTWARE, Software Development Kit & Application Development System
# All trademark and other rights reserved by their respective owners
# Copyright 2008-2021 Neongecko.com Inc.
# BSD-3
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS  BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS;  OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE,  EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os
import subprocess
import unittest
import pytest
from time import time
from neon_mq_connector.utils.client_utils import send_mq_request
from neon_mq_connector.utils import wait_for_mq_startup


class TestDianaServices(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cached_config_path = os.environ.get("NEON_CONFIG_PATH")
        os.environ["NEON_CONFIG_PATH"] = os.path.join(os.path.dirname(__file__), "config")
        cls.docker_compose_path = os.path.join(os.path.dirname(__file__), "test_diana_services_config")
        subprocess.Popen(["/bin/bash", "-c", f"cd {cls.docker_compose_path} && docker-compose up"])
        wait_for_mq_startup("0.0.0.0", 5672)

    @classmethod
    def tearDownClass(cls) -> None:
        os.environ.pop("NEON_CONFIG_PATH")
        if cls.cached_config_path:
            os.environ["NEON_CONFIG_PATH"] = cls.cached_config_path
        subprocess.Popen(["/bin/bash", "-c", f"cd {cls.docker_compose_path} && docker-compose down"])

    @pytest.mark.skip
    def test_api_proxy(self):
        resp = send_mq_request("/neon_api", {"test": True,
                                             "service": "api_test_endpoint"}, "neon_api_input", "neon_api_output")
        self.assertIsInstance(resp, dict)
        self.assertEqual(resp['status_code'], 200)

        resp = send_mq_request("/neon_api", {"test": True,
                                             "service": "not_implemented"}, "neon_api_input", "neon_api_output")
        self.assertIsInstance(resp, dict)
        self.assertEqual(resp['status_code'], 401)

    @pytest.mark.skip
    def test_brands_service(self):
        brand_coupon_data = send_mq_request("/neon_coupons", {"brands": True,
                                                              "coupons": True}, "neon_coupons_input")
        self.assertTrue(brand_coupon_data["success"])

    @pytest.mark.skip
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

    @pytest.mark.skip
    def test_script_parser(self):
        with open(os.path.join(os.path.dirname(__file__), "ccl", "test.nct")) as f:
            text = f.read()
        resp = send_mq_request("/neon_script_parser", {"text": text,
                                                       "meta": {"test": "val"}}, "neon_script_parser_input", timeout=45)
        self.assertIsInstance(resp, dict)
        self.assertIsInstance(resp["parsed_file"], str)


if __name__ == '__main__':
    unittest.main()
