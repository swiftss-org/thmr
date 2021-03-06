from datetime import date

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField, \
    HiddenField, IntegerField, DateField
from wtforms.validators import DataRequired, Optional

from app import base_data
from app.models import Cepod, Side, Occurrence, InguinalHerniaType, Complexity, AnestheticType, Pain
from app.util.form_utils import choice_for_bool, coerce_for_bool, choice_for_enum, coerce_for_enum
from app.validators import validate_pain_comments, validate_aware_of_mesh, validate_infection, validate_seroma, \
    validate_numbness, validate_perioperative_complication, validate_post_operative_antibiotics, \
    validate_antibiotics_iv_days, validate_antibiotics_oral_days


def _readonly_render_kw(readonly):
    if readonly:
        return {'readonly': True}
    else:
        return {}


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class UserForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    center_id = SelectField('Center')


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


class PatientEditForm(FlaskForm):
    id = StringField('Patient Id', render_kw={'readonly': True})
    name = StringField('Name', validators=[DataRequired()])
    national_id = StringField('National Id')
    hospital_number = StringField('Hospital Number')
    birth_year = IntegerField('Year of Birth')
    age = IntegerField('Age')
    center_id = SelectField('Center', validators=[DataRequired()])
    gender = SelectField('Gender', choices=[('M', 'Male'), ('F', 'Female')], validators=[DataRequired()])
    phone_1 = StringField('Phone #1 No.')
    phone_1_comments = StringField('Phone #1 Comments')
    phone_2 = StringField('Phone #2 No.')
    phone_2_comments = StringField('Phone #2 Comments')
    address = TextAreaField('Address (e.g. Village, District)')
    next_action = HiddenField('NextAction')
    created_by = HiddenField('Created By')
    created_at = HiddenField('Created At')
    updated_by = HiddenField('Updated By')
    updated_at = HiddenField('Updated At')
    submit = SubmitField('Save Changes')


class PatientSearchForm(FlaskForm):
    id = StringField('Patient Id', validators=[Optional()])
    name = StringField('Name', validators=[Optional()])
    national_id = StringField('National Id', validators=[Optional()])
    hospital_number = StringField('Hospital Number', validators=[Optional()])
    birth_year = IntegerField('Year of Birth', validators=[Optional()])
    age = IntegerField('Age', validators=[Optional()])
    center_id = SelectField('Center', validators=[Optional()])
    gender = SelectField('Gender', choices=[('', 'Any'), ('M', 'Male'), ('F', 'Female')], validators=[Optional()])
    phone = StringField('Phone #', validators=[Optional()])
    address = TextAreaField('Address (e.g. Village, District)', validators=[Optional()])
    next_action = HiddenField('NextAction')
    created_by = HiddenField('Created By')
    created_at = HiddenField('Created At')
    updated_by = HiddenField('Updated By')
    updated_at = HiddenField('Updated At')
    submit = SubmitField('Search')


class EventForm(FlaskForm):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if 'inline' in kwargs:
            self.inline = True
        else:
            self.inline = False

    id = HiddenField('id')
    version = HiddenField('version')

    type = StringField('Type', render_kw={'readonly': True})
    date = DateField('Date', default=date.today)

    patient_id = SelectField('Patient', render_kw={'readonly': True})
    center_id = SelectField('Center')
    comments = TextAreaField('Comments')

    created_by = HiddenField('Created By')
    created_at = HiddenField('Created At')
    updated_by = HiddenField('Updated By')
    updated_at = HiddenField('Updated At')

    submit = SubmitField('Save Changes')


class DischargeForm(EventForm):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    perioperative_complication = HiddenField('Perioperative Complication?')
    perioperative_complication_comments = StringField('Perioperative Complication Description',
                                                      validators=[validate_perioperative_complication])

    post_operative_antibiotics = HiddenField('Post-Operative Antibiotics?')
    post_operative_antibiotics_comments = StringField('Post-Operative Antibiotics Description',
                                                      validators=[validate_post_operative_antibiotics])
    post_operative_antibiotics_iv_days = IntegerField('IV antibiotics for # days',
                                                      validators=[Optional(), validate_antibiotics_iv_days])
    post_operative_antibiotics_oral_days = IntegerField('Oral antibiotics for # days',
                                                        validators=[Optional(), validate_antibiotics_oral_days])


class FollowupForm(EventForm):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    attendee_id = SelectField('Attendee', validators=[DataRequired()])

    pain = SelectField('Pain',
                       choices=choice_for_enum(Pain, include_blank=False),
                       coerce=coerce_for_enum(Pain),
                       validators=[DataRequired()])
    pain_comments = StringField('Pain Description', validators=[validate_pain_comments])

    mesh_awareness = HiddenField('Aware of Mesh?')
    mesh_awareness_comments = StringField('Mesh Awareness Description', validators=[validate_aware_of_mesh])

    infection = HiddenField('Infection?')
    infection_comments = StringField('Infection Description', validators=[validate_infection])

    seroma = HiddenField('Seroma?')
    seroma_comments = StringField('Seroma Description', validators=[validate_seroma])

    numbness = HiddenField('Numbness?')
    numbness_comments = StringField('Numbness Description', validators=[validate_numbness])


class InguinalMeshHerniaRepairForm(EventForm):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    cepod = SelectField('CEPOD',
                        choices=choice_for_enum(Cepod, include_blank=False),
                        coerce=coerce_for_enum(Cepod),
                        validators=[DataRequired()])
    side = SelectField('Side',
                       choices=choice_for_enum(Side, include_blank=False),
                       coerce=coerce_for_enum(Side),
                       validators=[DataRequired()])
    occurrence = SelectField('Occurrence',
                             choices=choice_for_enum(Occurrence, include_blank=False),
                             coerce=coerce_for_enum(Occurrence),
                             validators=[DataRequired()])
    hernia_type = SelectField('Hernia Type',
                              choices=choice_for_enum(InguinalHerniaType, include_blank=False),
                              coerce=coerce_for_enum(InguinalHerniaType),
                              validators=[DataRequired()])
    complexity = SelectField('Complexity',
                             choices=choice_for_enum(Complexity, include_blank=False),
                             coerce=coerce_for_enum(Complexity),
                             validators=[DataRequired()])

    mesh_type_id = SelectField('Mesh Type', validators=[DataRequired()])

    anaesthetic_type = SelectField('Anaesthetic Type',
                                   choices=choice_for_enum(AnestheticType, include_blank=False),
                                   coerce=coerce_for_enum(AnestheticType),
                                   validators=[DataRequired()])
    anaesthetic_other = StringField('Anaesthetic Other', validators=[Optional()])
    diathermy_used = HiddenField('Diathermy Used?', validators=[Optional()])
    discharge_date = DateField('Discharge Date', validators=[Optional()], default=date.today)

    primary_surgeon_id = SelectField('Primary Surgeon', validators=[Optional()])
    secondary_surgeon_id = SelectField('Secondary Surgeon', validators=[Optional()])
    tertiary_surgeon_id = SelectField('Tertiary Surgeon', validators=[Optional()])

    additional_procedure = TextAreaField('Additional Procedure', validators=[Optional()])
    complications = TextAreaField('Complications', validators=[Optional()])
