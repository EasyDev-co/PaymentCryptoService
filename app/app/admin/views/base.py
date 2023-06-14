from flask_admin.contrib.sqla import ModelView


class CustomModelView(ModelView):
    def is_accessible(self):
        return True
        # return current_user.is_authenticated
