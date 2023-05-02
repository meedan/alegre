from flask import current_app as app
import sentry_sdk


class ErrorLog:
    @classmethod
    def notify(err, context={}):
        app.extensions['pybrake'].notify(err)
        if context:
            with sentry_sdk.configure_scope() as scope:
                for key, value in context.items():
                    scope.set_extra(key, value)
                sentry_sdk.capture_exception(err)
        else:
            sentry_sdk.capture_exception(err)
        