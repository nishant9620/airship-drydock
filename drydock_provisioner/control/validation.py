# Copyright 2017 AT&T Intellectual Property.  All other rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import falcon
import json

from drydock_provisioner import policy
from drydock_provisioner.control.base import StatefulResource
import drydock_provisioner.error as errors


class ValidationResource(StatefulResource):
    """
    Drydock validation endpoint
    """

    def __init__(self, orchestrator=None, **kwargs):
        """Object initializer.

        :param orchestrator: instance of orchestrator.Orchestrator
        """
        super().__init__(**kwargs)
        self.orchestrator = orchestrator

    @policy.ApiEnforcer('physical_provisioner:validate_site_design')
    def on_post(self, req, resp):

        # create resp message
        resp_message = {
            'kind': 'Status',
            'apiVersion': 'v1',
            'metaData': {},
            'status': '',
            'message': '',
            'reason': 'Validation',
            'details': {
                'errorCount': 0,
                'messageList': []
            },
            'code': '',
        }

        try:
            json_data = self.req_json(req)

            if json_data is None:
                resp.status = falcon.HTTP_400
                err_message = 'Request body must not be empty for validation.'
                self.error(req.context, err_message)
                return self.return_error(resp, falcon.HTTP_400, err_message)

            design_ref = json_data.get('href', None)

            if not design_ref:
                resp.status = falcon.HTTP_400
                err_message = 'The "href" key must be provided in the request body.'
                self.error(req.context, err_message)
                return self.return_error(resp, falcon.HTTP_400, err_message)

            message, design_data = self.orchestrator.get_effective_site(
                design_ref)

            resp_message['details']['errorCount'] = message.error_count
            resp_message['details']['messageList'] = [
                m.to_dict() for m in message.message_list
            ]

            if message.error_count == 0:
                resp_message['status'] = 'Valid'
                resp_message['message'] = 'Drydock Validations succeeded'
                resp_message['code'] = 200
                resp.status = falcon.HTTP_200
                resp.body = json.dumps(resp_message)
            else:
                resp_message['status'] = 'Invalid'
                resp_message['message'] = 'Drydock Validations failed'
                resp_message['code'] = 400
                resp.status = falcon.HTTP_400
                resp.body = json.dumps(resp_message)

        except errors.InvalidFormat as e:
            err_message = str(e)
            resp.status = falcon.HTTP_400
            self.error(req.context, err_message)
            self.return_error(resp, falcon.HTTP_400, err_message)
