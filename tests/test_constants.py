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
import sys
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from neon_diana_utils.constants import *


class TestConstants(unittest.TestCase):
    def test_orchestrators(self):
        self.assertIsInstance(Orchestrator.DOCKER.value, int)
        self.assertIsInstance(Orchestrator.KUBERNETES.value, int)
        self.assertIsInstance(Orchestrator.OPENSHIFT.value, int)

    def test_service_classes(self):
        self.assertEqual(ServiceClass.MQ.value, "mq-backend")
        self.assertEqual(ServiceClass.HTTP.value, "http-backend")
        self.assertEqual(ServiceClass.CORE.value, "neon-core")

    def test_get_services_by_class(self):
        from neon_diana_utils.constants import _get_services_by_class
        services_by_class = _get_services_by_class()
        self.assertIsInstance(services_by_class, dict)
        self.assertIsInstance(services_by_class[ServiceClass.MQ.value], list)
        self.assertIsInstance(services_by_class[ServiceClass.HTTP.value], list)
        # self.assertIsInstance(services_by_class[ServiceClass.CORE.value], list)
        self.assertFalse(set(services_by_class[ServiceClass.MQ.value])
                         .intersection(set(services_by_class
                                           [ServiceClass.HTTP.value])))

    def test_valid_mq_services(self):
        self.assertIsInstance(valid_mq_services(), set)

    def test_valid_http_services(self):
        self.assertIsInstance(valid_http_services(), set)

    def test_valid_default_mq_services(self):
        defaults = default_mq_services()
        self.assertIsInstance(defaults, set)
        self.assertTrue(all([svc in valid_mq_services() for svc in defaults]))


if __name__ == '__main__':
    unittest.main()
