#---------------------------------------------------------------------------
# Various extensions to use with WTForms
#---------------------------------------------------------------------------

#---------------------------------------------------------------------------
# Disabled/ablable versions of the fields
#---------------------------------------------------------------------------
from wtforms import Form
from wtforms import fields

def DisabledFieldFactory(Base):
    def my_init(self, *args, **kwargs):
        self.disabled = kwargs.pop('disabled', True)
        Base.__init__(self, *args, **kwargs)
    def my_call(self, *args, **kwargs):
        if self.disabled:
            kwargs.setdefault("disabled", True)
        return Base.__call__(self, *args, **kwargs)
    def my_populate_obj(self, *args, **kwargs):
        if not self.disabled:
            Base.populate_obj(self, *args, **kwargs)
    def my_process_formdata(self, *args, **kwargs):
        if not self.disabled:
            Base.process_formdata(self, *args, **kwargs)
    def my_Option(self, *args, **kwargs):
        DisabledOption = DisabledFieldFactory(fields.SelectFieldBase._Option)
        kwargs["disabled"] = self.disabled
        return DisabledOption(*args, **kwargs)
    Field = type("Disablable" + Base.__name__, (Base,),
                 {'__init__':         my_init,
                  '__call__':         my_call,
                  'process_formdata': my_process_formdata,
                  'populate_obj':     my_populate_obj})
    if issubclass(Base, fields.SelectFieldBase):
        Field._Option = my_Option
    return Field

DisabledBooleanField         = DisabledFieldFactory(fields.BooleanField)
DisabledDecimalField         = DisabledFieldFactory(fields.DecimalField)
DisabledDateField            = DisabledFieldFactory(fields.DateField)
DisabledDateTimeField        = DisabledFieldFactory(fields.DateTimeField)
DisabledFieldList            = DisabledFieldFactory(fields.FieldList)
DisabledFloatField           = DisabledFieldFactory(fields.FloatField)
DisabledFormField            = DisabledFieldFactory(fields.FormField)
DisabledIntegerField         = DisabledFieldFactory(fields.IntegerField)
DisabledRadioField           = DisabledFieldFactory(fields.RadioField)
DisabledSelectField          = DisabledFieldFactory(fields.SelectField)
DisabledSelectMultipleField  = DisabledFieldFactory(fields.SelectMultipleField)
DisabledStringField          = DisabledFieldFactory(fields.StringField)
DisabledTextAreaField        = DisabledFieldFactory(fields.TextAreaField)
DisabledPasswordField        = DisabledFieldFactory(fields.PasswordField)
DisabledFileField            = DisabledFieldFactory(fields.FileField)
DisabledHiddenField          = DisabledFieldFactory(fields.HiddenField)
DisabledSubmitField          = DisabledFieldFactory(fields.SubmitField)
DisabledTextField            = DisabledFieldFactory(fields.TextField)

#---------------------------------------------------------------------------
# Standard Submit Buttons
#---------------------------------------------------------------------------
from wtforms.fields  import HiddenField
from wtforms.fields  import SubmitField

class SubmitBtns(Form):
    rowid       = HiddenField()
    csrfToken   = HiddenField()
    hiddenBtn   = SubmitField("  ")
    loginBtn    = DisabledSubmitField(u"LOGIN",           disabled=False)
    addBtn      = DisabledSubmitField(u"Add",             disabled=False)
    delBtn      = DisabledSubmitField(u"Delete",          disabled=False)
    modBtn      = DisabledSubmitField(u"Modify",          disabled=False)
    pwdBtn      = DisabledSubmitField(u"Change Password", disabled=False)
    cancelBtn   = DisabledSubmitField(u"Cancel",          disabled=False)
    okBtn       = DisabledSubmitField(u"OK",              disabled=False)
    anotherBtn  = DisabledSubmitField("OK+Another",       disabled=False)
    misc1Btn    = DisabledSubmitField(u"Miscellany",      disabled=False)

#---------------------------------------------------------------------------
# Coerce functions - useful for SelectFields
#---------------------------------------------------------------------------
def toIdOf(cls):
    def toId(obj):
        if isinstance(obj, cls):
            return obj.id
        else:
            return obj
    return toId

def toIntIdOf(cls):
    def toId(obj):
        if isinstance(obj, cls):
            return int(obj.id)
        else:
            return int(obj)
    return toId

#---------------------------------------------------------------------------
# Pyramid Form with Buttons
#---------------------------------------------------------------------------
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPNotImplemented
from sqlalchemy import inspect as sqla_inspect
from .models import DBSession

class PyramidForm(Form):
    def __init__(self, obj=None, prefix='', **kwargs):
        Form.__init__(self, prefix=prefix, **kwargs)
        self.btns = SubmitBtns(prefix=prefix, **kwargs)
        self.obj  = obj
        self.okUrl      = \
        self.cancelUrl  = \
        self.anotherUrl = \
        self.addUrl     = \
        self.misc1Url   = \
        self.modUrl     = None
        self.extvtors = {}

        for field in self._fields.values():
            field.extattrs = {}

    def validate(self):
        extra = {}
        for name in self._fields:
            # This is quite awful, but we need to keep our dynamically
            # generated validators from being added and re-added to
            # the more static unbound field's validators
            extra[name] = self.extvtors.get(name, [])[:]
            inline = getattr(self.__class__, 'validate_%s' % name, None)
            if inline is not None:
                extra[name].append(inline)
        return super(Form, self).validate(extra)

    def addValidators(self):
        if self.obj is None:
            return
        ormMapper = sqla_inspect(self.obj.__class__, raiseerr=False)
        if ormMapper is None:
            return
        self._obj = self.obj # needed for Unique
        for name, field in self._fields.items():
            if not getattr(field, 'disabled', False):
                ormProp = ormMapper.attrs.get(name)
                extra = self.extvtors.setdefault(name, [])
                if len(getattr(ormProp, 'columns', [])) == 1:
                    addValidators(field, ormProp.columns[0], extra,
                                  DBSession, self.obj.__class__)

    def handle(self, request, info={}):
        retval = dict(info)
        retval['form'] = self
        retval['btns'] = self.btns
        self.btns.csrfToken.data = request.session.get_csrf_token()
        self.process(request.POST, self.obj)
        if request.method == 'POST':
            self.btns.process(request.POST)
            if self.btns.cancelBtn.data:
                self.checkCsrf(request)
                return self.handleCancel(request, retval)
            elif self.btns.okBtn.data or self.btns.anotherBtn.data:
                self.checkCsrf(request)
                if self.validate():
                    if self.btns.anotherBtn.data:
                        return self.handleAnother(request, retval)
                    else:
                        return self.handleOk(request, retval)
                else:
                    return retval
            elif self.btns.addBtn.data:
                self.checkCsrf(request)
                return self.handleAdd(request, retval)
            elif self.btns.delBtn.data:
                self.checkCsrf(request)
                return self.handleDel(request, retval)
            elif self.btns.modBtn.data:
                self.checkCsrf(request)
                return self.handleMod(request, retval)
            elif self.btns.misc1Btn.data:
                self.checkCsrf(request)
                return self.handleMisc1(request, retval)
            elif self.btns.hiddenBtn.data:
                pass # swallow this as default
            else:
                self.btns.csrfToken.data = request.session.get_csrf_token()
                return self.handleNotImplemented(retval)
        return retval

    def handleCancel(self, request, retval):
        return HTTPFound(location = self.cancelUrl or request.path_url)

    def handleOk(self, request, retval):
        if self.obj:
            self.populate_obj(self.obj)
            self.save()
        return HTTPFound(location = self.okUrl or request.path_url)

    def handleAnother(self, request, retval):
        retval = self.handleOk(request, retval)
        if isinstance(retval, HTTPFound):
            retval.location = self.anotherUrl or request.path_url
        return retval

    def handleAdd(self, request, retval):
        return self._redirectTo(self.addUrl, retval)

    def handleDel(self, request, retval):
        return self.handleNotImplemented(retval)

    def handleMod(self, request, retval):
        return self._redirectTo(self.modUrl, retval)

    def handleMisc1(self, request, retval):
        return self._redirectTo(self.misc1Url, retval)

    def _redirectTo(self, url, retval):
        if url:
            return HTTPFound(location = url)
        else:
            return self.handleNotImplemented(retval)

    def save(self):
        ormObj = sqla_inspect(self.obj, raiseerr=False)
        if ormObj and ormObj.transient:
            self.obj.insert()

    def checkCsrf(self, request):
        if self.btns.csrfToken.data != request.session.get_csrf_token():
            raise HTTPForbidden()

    def handleNotImplemented(self, retval):
        raise HTTPNotImplemented()

#---------------------------------------------------------------------------
# Custom Validators
#---------------------------------------------------------------------------
from wtforms import validators
from wtforms.validators import ValidationError
from cgi import FieldStorage

class DataRequiredIf(validators.DataRequired):
    # a validator which makes a field required if
    # another field is set and has a truthy value
    # from http://stackoverflow.com/questions/8463209
    def __init__(self, other_field_name, *args, **kwargs):
        self.other_field_name = other_field_name
        super(DataRequiredIf, self).__init__(*args, **kwargs)

    def __call__(self, form, field):
        other_field = form._fields.get(self.other_field_name)
        if other_field is None:
            raise Exception('no field named "%s" in form' % self.other_field_name)
        if bool(other_field.data):
            super(DataRequiredIf, self).__call__(form, field)


class FileIsPdf(object):
    """
    Checks that the file being uploaded is a PDF
    """
    def __call__(self, form, field):
        if (not hasattr(field.data, "filename") or
            not hasattr(field.data, "file")):
            raise ValidationError("Is not a file field")
        if field.data.filename[-4:].lower() != ".pdf":
            raise ValidationError("Upload .PDF files only")
        fp = field.data.file
        fp.seek(0)
        header = fp.read(5)
        if header != b"%PDF-":
            # 99% of PDFs start with %PDF-1, but it may be further in
            fp.seek(0)
            header = fp.read(1024)
            if b"%PDF-" not in header:
                raise ValidationError("Corrupt file or not a PDF file")
        fp.seek(-10, 2)
        trailer = fp.read(10)
        if b"%%EOF" not in trailer:
            raise ValidationError("Corrupt file or not a PDF file")
        if fp.tell() > 16777215:
            raise ValidationError("File is too large (16MB is the max file size)")
        fp.seek(0)

#---------------------------------------------------------------------------
# Add validators to a field based on a SQLAlchemy column, my own version
# like wtforms.ext.sqlalchemy.orm.ModelConverter or 
# wtforms_alchemy.generator.FormGenerator (but much simpler)
#---------------------------------------------------------------------------
from wtforms.validators import Optional, InputRequired, Length, NumberRange
from wtforms.ext.sqlalchemy.validators import Unique
from sqlalchemy import types
def addValidators(field, column, validators=None, getDBSes=None, model=None):
    if validators is None:
        validators = field.validators
    if not hasattr(field, 'extattrs'):
        field.extattrs = {}
    extattrs = field.extattrs
    if column.nullable:
        validators.append(Optional())
    elif not isinstance(column.type, types.Boolean):
        validators.append(InputRequired())
        field.label = RequiredLabel(field.label.field_id, field.label.text)
    if column.unique and getDBSes is not None and model is not None:
        validators.append(Unique(getDBSes, model, column))
    if isinstance(column.type, types.String) and column.type.length:
        validators.append(Length(max = column.type.length))
        extattrs['maxlength'] = column.type.length
    elif isinstance(column.type, (types.Integer,
                                  types.SmallInteger,
                                  types.BigInteger,
                                  types.Float,
                                  types.Numeric)):
        extattrs['maxlength'] = 15
        if not any(isinstance(v, NumberRange) for v in validators):
            # arbitary decision to forbid negatives unless otherwise allowed
            # TODO support HTML5 input[number] max and min?
            validators.append(NumberRange(min = 0))
    for vtor in validators:
        flags = getattr(vtor, 'field_flags', ())
        for flag in flags:
            setattr(field.flags, flag, True)


#---------------------------------------------------------------------------
# Extra fields and widgets
#---------------------------------------------------------------------------
from io import StringIO
from wtforms.fields  import SelectField
from wtforms.fields  import SelectMultipleField
from wtforms.fields  import Label
from wtforms.widgets import CheckboxInput
from wtforms.widgets import RadioInput
from wtforms.widgets import html_params, HTMLString
from datetime import datetime
from .utils import getTradingMonth
from calendar import month_name


class RequiredLabel(Label):
    def __call__(self, text=None, **kwargs):
        kwargs['class_'] = kwargs.get('class_', "")+" is-required"
        return super(RequiredLabel, self).__call__(text, **kwargs)

class MonthField(SelectField):
    """
    Field to select a month
    """
    def __init__(self, label=None, validators=None, **kwargs):
        super(MonthField, self).__init__(label, validators, **kwargs)
        self.month = getTradingMonth(datetime.utcnow()).month

    def iter_choices(self):
        months = [(month, name, month==self.month)
                  for month, name in enumerate(month_name)]
        return months

    def pre_validate(self, form):
        pass

class YearField(SelectField):
    """
    Field to select a year
    """
    def __init__(self, toYear=2014, label=None, validators=None, **kwargs):
        super(YearField, self).__init__(label, validators, **kwargs)
        self.year   = getTradingMonth(datetime.utcnow()).year
        self.toYear = toYear

    def iter_choices(self):
        years = [(0, "", False), (self.year, str(self.year), True)]
        years.extend([(year, str(year), False)
                      for year in range(self.year - 1, self.toYear - 1, -1)])
        return years

    def pre_validate(self, form):
        pass

class MultiCheckboxWidget(object):
    def __init__(self):
        pass

    @staticmethod
    def javascript():
        retval = """\
<script type="text/javascript" charset="utf8">
     $(function () {
        $(".multi-checkboxes ul").selectable({
            'stop': function() {
                $(".ui-selected input", this).each(function() {
                    this.checked = !this.checked;
                });
            }
        });
        $("a.tick-all").click(function() {
            var ourCbs = $(this).closest(".multi-checkboxes");
            ourCbs.find("ul li input", this).prop("checked", true);
        });
        $("a.tick-none").click(function() {
            var ourCbs = $(this).closest(".multi-checkboxes");
            ourCbs.find("ul li input").prop("checked", false);
        });
    });
</script>"""
        return retval

    def __call__(self, field, **kwargs):
        kwargs.setdefault("id", field.id)
        kwargs['class_'] = kwargs.get('class_', "")+" multi-checkboxes"
        body = StringIO()
        body.write('<div {}>'.format(html_params(**kwargs)))
        body.write('<div class="tick-checkboxes">')
        body.write('<b>tick:</b> ')
        body.write('<a href="javascript:void(0);" class="tick-all">all</a> ')
        body.write('<a href="javascript:void(0);" class="tick-none">none</a>')
        body.write('</div>')
        body.write('<ul>')
        for subfield in field:
            body.write(self.itemTag(subfield))
        body.write('</ul>')
        body.write('</div>')
        return HTMLString(body.getvalue())

    def itemTag(self, subfield):
        return '<li>{} {}</li>'.format(subfield(), subfield.label)

class MultiCheckboxField(SelectMultipleField):
    widget        = MultiCheckboxWidget()
    option_widget = CheckboxInput()

class MultiCountryWidget(MultiCheckboxWidget):
    def itemTag(self, subfield):
        code = subfield._value()
        flag = "famfamfam-flag-{}".format(code.lower())
        label = subfield.label('<i title="{}" class="{}"></i>{}'
                               .format(code, flag, subfield.label.text))
        return '<li>{} {}</li>'.format(subfield(), label)

class MultiCountryField(MultiCheckboxField):
    widget = MultiCountryWidget()

class SingleSelectionWidget(object):
    def __init__(self):
        pass

    @staticmethod
    def javascript():
        retval = """\
<script type="text/javascript" charset="utf8">
    $(function () {
        $(".single-selection .drop-down").selectable({
            'selecting': function (event, ui) {
                $(event.target).children('.ui-selecting').not(':first').removeClass('ui-selecting');
            },
            'selected': function(event, ui) {
                var radio = $(ui.selected).find("input[type=radio]");
                radio.prop("checked", true);
                onItemSelected(radio);
                $(this).hide();
            }
        });
        $(".single-selection .drop-down input[type=radio]").click(function() {
            onItemSelected($(this));
        });
        $(".single-selection .selection").click(function() {
            $(".single-selection .drop-down").toggle();
            return false;
        });
        $("#content").click(function() {
            $(".single-selection .drop-down").hide();
        });
    });
    function onItemSelected(item) {
        var ourSelection = item.closest(".single-selection").find(".selection");
        var ourLabel     = item.next("label");
        var newFlag      = ourLabel.find("i").clone();
        var newLabel     = $("<label>");
        newLabel.append(newFlag);
        newLabel.append( ourLabel.text());
        ourSelection.find("label").replaceWith(newLabel);
    }
</script>"""
        return retval

    def __call__(self, field, **kwargs):
        kwargs.setdefault("id", field.id)
        kwargs['class_'] = kwargs.get('class_', "")+" single-selection"
        body = StringIO()
        body.write('<div {}>'.format(html_params(**kwargs)))
        if field.coerce(field.data) == field.coerce(None):
            selected = next(iter(field))
        else:
            label = next((ch[1] for ch in field.choices
                                if ch[0] == field.data), "")
            selected = field._Option(label=label, _name=field.name, _form=None)
            selected.process(None, field.data)
            selected.checked = True
        body.write(self.selection(selected))
        body.write(self.dropDown(field))
        body.write('</div>')
        return HTMLString(body.getvalue())

    def selection(self, field):
        retval = StringIO()
        retval.write('<div class="selection">')
        retval.write(field)
        retval.write('</div>')
        return HTMLString(retval.getvalue())

    def dropDown(self, field):
        retval = StringIO()
        retval.write('<div class="drop-holder">')
        retval.write('<ul class="drop-down">')
        for subfield in field:
            retval.write(self.itemTag(subfield))
        retval.write('</ul>')
        retval.write('</div>')
        return HTMLString(retval.getvalue())

    def itemTag(self, subfield):
        return '<li>{}</li>'.format(subfield.label.text)

class SingleSelectionField(SelectField):
    widget = SingleSelectionWidget()
    option_widget = RadioInput()

    def iter_choices(self):
        choiceIter = iter(self.choices)
        try:
            value, label = next(choiceIter)
            if self.coerce(self.data) == self.coerce(None):
                yield (value, label, True)
            else:
                yield (value, label, self.coerce(value) == self.data)
        except StopIteration:
            pass
        for value, label in choiceIter:
            if self.coerce(self.data) == self.coerce(None):
                selected = False
            else:
                selected = self.coerce(value) == self.data
            yield (value, label, selected)

class CountryWidget(SingleSelectionWidget):
    def selection(self, subfield):
        retval = StringIO()
        retval.write('<div class="selection">')
        code = subfield._value()
        flag = "famfamfam-flag-{}".format(code.lower())
        retval.write(subfield.label('<i title="{}" class="{}"></i>{}'
                                    .format(code, flag, subfield.label.text)))
        retval.write('<img class="expand-selection" width="21" height=21" '
                     'alt="+" src="/static/selection-expand-arrow.png" />')
        retval.write('</div>')
        return HTMLString(retval.getvalue())

    def itemTag(self, subfield):
        code = subfield._value()
        flag = "famfamfam-flag-{}".format(code.lower())
        label = subfield.label('<i title="{}" class="{}"></i>{}'
                               .format(code, flag, subfield.label.text))
        return '<li>{} {}</li>'.format(subfield, label)

class CountryField(SingleSelectionField):
    widget = CountryWidget()
