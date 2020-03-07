from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField, \
    HiddenField
from wtforms.ext.dateutil.fields import DateField
from wtforms.validators import DataRequired, Optional

from app import strtobool
from app.models import EpisodeType, Cepod, Side, Type


def choice_for_enum(enum, include_blank=False):
    l = [(e, e.name) for e in enum]
    if include_blank:
        l.insert(0, ('', '(Any)'))
    return l


def coerce_for_enum(enum):
    def coerce(name):
        if name is None or str(name) == '':
            return None

        if isinstance(name, enum):
            return name

        try:
            id = int(name)
            try:
                return enum(id)
            except KeyError:
                raise ValueError(name)
        except ValueError:
            try:
                if '.' in name:
                    name = name[name.find('.') + 1:]
                return enum[name]
            except KeyError:
                raise ValueError(name)

    return coerce


def coerce_for_bool():
    def coerce(name):
        if isinstance(name, bool):
            return name

        return strtobool(name)

    return coerce


def choice_for_bool():
    return [(True, 'True'), (False, 'False')]


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class UserForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    hospital_id = SelectField('Hospital')


class UserCreateForm(UserForm):
    new_password = PasswordField('New Password')
    verify_password = PasswordField('Verify Password')
    submit = SubmitField('Register User')


class UserEditForm(UserForm):
    current_password = PasswordField('Current Password')
    new_password = PasswordField('New Password')
    verify_password = PasswordField('Verify Password')
    active = SelectField('Active',
                         default=True,
                         choices=choice_for_bool(),
                         coerce=coerce_for_bool())
    submit = SubmitField('Save Changes')


class PatientForm(FlaskForm):
    name = StringField('Name')
    national_id = StringField('National Id')
    hospital_id = SelectField('Hospital')
    gender = SelectField('Gender', choices=[('', 'Any'), ('M', 'Male'), ('F', 'Female')])
    phone = StringField('Phone #')
    address = TextAreaField('Address')
    next_action = HiddenField('NextAction')
    created_by = HiddenField('Created By')
    created_at = HiddenField('Created At')
    updated_by = HiddenField('Updated By')
    updated_at = HiddenField('Updated At')


class PatientSearchForm(PatientForm):
    submit = SubmitField('Search')


class PatientEditForm(PatientForm):
    submit = SubmitField('Save Changes')


class EpisodeForm(FlaskForm):
    patient_id = SelectField('Patient')
    hospital_id = SelectField('Hospital')
    surgery_id = HiddenField('Surgery')
    comments = TextAreaField('Comments')
    created_by = HiddenField('Created By')
    created_at = HiddenField('Created At')
    updated_by = HiddenField('Updated By')
    updated_at = HiddenField('Updated At')

    attendee_id = SelectField('Attendee')
    attendees = HiddenField('Attendees')

    next_action = HiddenField('NextAction')


class EpisodeEditForm(EpisodeForm):
    date = DateField('Date', default=datetime.now())
    episode_type = SelectField('Episode Type',
                               choices=choice_for_enum(EpisodeType, include_blank=False),
                               coerce=coerce_for_enum(EpisodeType))
    submit = SubmitField('Save Changes')


class EpisodeSearchForm(EpisodeForm):
    date = DateField('Date')
    episode_type = SelectField('Episode Type',
                               choices=choice_for_enum(EpisodeType, include_blank=True),
                               coerce=coerce_for_enum(EpisodeType))
    submit = SubmitField('Search')


class SurgeryForm(FlaskForm):
    procedure_id = SelectField('Procedure')
    cepod = SelectField('CEPOD',
                        choices=choice_for_enum(Cepod, include_blank=False),
                        coerce=coerce_for_enum(Cepod))

    date_of_discharge = DateField('Date of Discharge', default=None, validators=(Optional(),))
    side = SelectField('Side',
                       choices=choice_for_enum(Side, include_blank=False),
                       coerce=coerce_for_enum(Side))
    primary = SelectField('Primary',
                          choices=choice_for_bool(),
                          coerce=coerce_for_bool())
    type = SelectField('Type',
                       choices=choice_for_enum(Type, include_blank=False),
                       coerce=coerce_for_enum(Type))

    additional_procedure = TextAreaField('Additional Procedure')
    antibiotics = TextAreaField('Antibiotics')
    comments = TextAreaField('Comments')

    opd_rv_date = DateField('RV Date', default=None, validators=(Optional(),))
    opd_pain = StringField('Pain')
    opd_numbness = StringField('Numbness')
    opd_infection = StringField('Infection')
    opd_comments = TextAreaField('Comments')

    created_by = HiddenField('Created By')
    created_at = HiddenField('Created At')
    updated_by = HiddenField('Updated By')
    updated_at = HiddenField('Updated At')

    submit = SubmitField('Save Changes')


class AdminForm(FlaskForm):
    command = StringField('Command')
    execute = SubmitField('Execute')
