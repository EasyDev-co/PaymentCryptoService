from flask import Flask
from flask_admin import Admin
from uuid import uuid4

from app.db.session import SyncSession, scope
from app.core.config import settings

from app.models.users import Users
from app.models.wallets import Wallet, CryptocurrencyWallet
from app.models.webhook_erc20 import WebhookErc20Alchemy
from app.models.settings import Settings
from app.models.transactions import CryptoTransaction

from app.admin.views.base import CustomModelView


session = SyncSession(settings.SYNC_SQLALCHEMY_DATABASE_URI)

secureApp = Flask(__name__)

secureApp.config['SECRET_KEY'] = 'secretkey'


class middleware():
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        scope.set(str(uuid4()))
        try:
            return self.app(environ, start_response)
        except:
            session.session.rollback()
        finally:
            session.session.expunge_all()
            session.scoped_session.remove()


secureApp.wsgi_app = middleware(secureApp.wsgi_app)


admin = Admin(secureApp, name='Admin', base_template='my_master.html', template_mode='bootstrap4')

admin.add_view(CustomModelView(Users, session.session))
admin.add_view(CustomModelView(Wallet, session.session))
admin.add_view(CustomModelView(CryptocurrencyWallet, session.session))
admin.add_view(CustomModelView(WebhookErc20Alchemy, session.session))
admin.add_view(CustomModelView(Settings, session.session))
admin.add_view(CustomModelView(CryptoTransaction, session.session))
