from auth import app
from flask_mail import Mail
mail_settings = {
    "MAIL_SERVER": 'smtp.gmail.com',
    "MAIL_PORT": 465,
    "MAIL_USE_TLS": False,
    "MAIL_USE_SSL": True,
    "MAIL_USERNAME": '5genesismanagement@gmail.com',
    "MAIL_PASSWORD": 'TestAtos'
}
app.config.update(mail_settings)
mail = Mail(app)
