import unittest
import json
import os

from flask import current_app as app
from unittest.mock import patch
from unittest import mock
from app.test.base import BaseTestCase

class TestErrorLogBlueprint(BaseTestCase):
    @patch('app.main.lib.error_log.sentry_sdk.capture_exception')
    def test_error_log_called(self, mock_capture_exception):
        mock_exception = Exception('Model search failed when using test_key')
        ErrorLog.notify(mock_exception)
        mock_capture_exception.assert_called_once_with(mock_exception)

    @patch('app.main.lib.error_log.sentry_sdk.set_context')
    @patch('app.main.lib.error_log.sentry_sdk.capture_exception')
    def test_error_log_called_with_context(self, mock_capture_exception, mock_set_context):
        mock_exception = Exception('Model search failed when using test_key')
        mock_context = {"info": "some info"}
        ErrorLog.notify(mock_exception, mock_context)
        mock_set_context.assert_called_once_with("internal_context", mock_context)
        mock_capture_exception.assert_called_once_with(mock_exception)


if __name__ == '__main__':
    unittest.main()
