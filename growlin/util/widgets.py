from flask.ext.admin.model.fields import AjaxSelect2Widget
from wtforms.widgets.core import HTMLString

class AddModelSelect2Widget(AjaxSelect2Widget):
    def __init__(self, model_create_url, **kwargs):
        self.model_create_url = model_create_url
        return super(AddModelSelect2Widget, self).__init__(**kwargs)

    def __call__(self, field, **kwargs):
        model_create_url = self.model_create_url
        model_create_button = '<a class="icon" data-target="#fa_modal_window" title="Create New Record" href="%s?url=%%2Fapi%%2Fok&amp;modal=True" data-toggle="modal">Create new record</a>' % model_create_url

        result =  super(AddModelSelect2Widget, self).__call__(field, **kwargs)
        return HTMLString(result.__html__() + model_create_button)
