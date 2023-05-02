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
            with sentry_sdk.configure_scope() as scope:
                for key, value in context.items():
                    scope.set_extra(key, value)
                sentry_sdk.capture_exception(err)
        else:
            sentry_sdk.capture_exception(err)
