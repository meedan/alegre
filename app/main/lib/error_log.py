from flask import current_app as app
import sentry_sdk


class ErrorLog:
    """Generic Error Logger"""
    @classmethod
    def notify(cls, err, context=None):
        """Notify error logging services of error"""
        if app.extensions.get('pybrake'):
            app.extensions.get('pybrake').notify(err)
        if context:
            sentry_sdk.set_context("internal_context", context)
        sentry_sdk.capture_exception(err)
