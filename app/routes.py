import logging
from datetime import datetime

from flask import current_app as application, send_file
from flask import jsonify, request, render_template, flash, redirect, url_for
from flask_login import current_user, login_user, logout_user, login_required
from sqlalchemy import and_
from werkzeug.urls import url_parse

from app import db, login, reporting, attendees_parser, initalise
from app.forms import LoginForm, PatientSearchForm, PatientEditForm, EpisodeEditForm, EpisodeSearchForm, SurgeryForm, \
    UserEditForm, AdminForm
from app.models import User, Patient, Episode, Hospital, Surgery, Procedure
from app.tests import constants
from app.util.filter import like_all


@application.before_first_request
def before_first_request():
    initalise.initalise(application)


@login.user_loader
def load_user(user_id):
    if not isinstance(user_id, int):
        user_id = int(user_id)

    u = db.session.query(User).filter(User.id == user_id).first()
    return u


@application.route('/', methods=['GET'])
def root():
    return redirect(url_for('index'))


@application.route('/not_implemented', methods=['GET'])
def not_implemented():
    return render_template('not_implemented.html', title='Ooops')


@application.route('/index', methods=['GET'])
@login_required
def index():
    return render_template('index.html', title='Index')


@application.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()

    if application.config.get('DEFAULT_TEST_ACCOUNT_LOGIN'):
        form.username.data = constants.TEST_ACCOUNT_EMAIL
        form.password.data = constants.TEST_ACCOUNT_PASSWORD

    if form.validate_on_submit():
        user = db.session.query(User).filter_by(email=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        login_msg = 'Login successful for {}'.format(form.username.data)
        logging.info(login_msg)
        flash(login_msg)

        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            return redirect(url_for('index'))
        return redirect(next_page)

    return render_template('login.html', title='Sign In', form=form)


@application.route('/user/self', methods=['GET', 'POST'])
@login_required
def user_self():
    return redirect(url_for('user', id=current_user.id))


@application.route('/user/<int:id>', methods=['GET', 'POST'])
@login_required
def user(id):
    user = db.session.query(User).filter(User.id == id).first()
    form = UserEditForm(obj=user)
    form.hospital_id.choices = _hospital_id_choices(include_empty=True)

    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Unable to save changes as current password is not correct!'.format(user.name))
            return redirect(url_for('user', id=user.id))

        user.name = form.name.data
        user.email = form.email.data
        user.active = form.active.data

        if len(form.new_password.data) > 0:
            if form.new_password.data != form.verify_password.data:
                flash('Unable to save changes as passwords for not match for {}!'.format(user.name))
                return render_template('user_edit.html', title='Register New User', form=form, edit_disabled=False)

            minimum_password_strength = application.config.get('MINIMUM_PASSWORD_STRENGTH', 0.3)
            if user.check_password_strength(form.new_password.data) < minimum_password_strength:
                flash('Unable to save changes as password is not strong enough for {}!'.format(user.name))
                return render_template('user_edit.html', title='Register New User', form=form, edit_disabled=False)

            user.set_password(form.new_password.data)

        db.session.commit()

        flash('User details for {} have been updated.'.format(user.name))
        return redirect(url_for('user', id=user.id))

    return render_template('user_edit.html', title='User Details', form=form, edit_disabled=False)


@application.route('/user/create', methods=['GET', 'POST'])
def user_create():
    user = User()
    form = UserEditForm(obj=user)
    form.hospital_id.choices = _hospital_id_choices(include_empty=True)

    if form.validate_on_submit():
        user.name = form.name.data
        user.email = form.email.data
        user.active = form.active.data

        if form.new_password.data != form.verify_password.data:
            flash('Unable to save changes as passwords for not match for {}!'.format(user.name))
            return render_template('user_create.html', title='Register New User', form=form, edit_disabled=False)

        minimum_password_strength = application.config.get('MINIMUM_PASSWORD_STRENGTH', 0.3)
        if user.check_password_strength(form.new_password.data) < minimum_password_strength:
            flash('Unable to save changes as password is not strong enough for {}!'.format(user.name))
            return render_template('user_create.html', title='Register New User', form=form, edit_disabled=False)

        user.set_password(form.new_password.data)

        db.session.add(user)
        db.session.commit()

        flash('User details for {} have been updated.'.format(user.name))
        return redirect(url_for('user', id=user.id))

    return render_template('user_create.html', title='Register New User', form=form, edit_disabled=False)


@application.route('/patient_search', methods=['GET', 'POST'])
@login_required
def patient_search():
    form = PatientSearchForm()
    form.hospital_id.choices = _hospital_id_choices(include_empty=True)

    if form.validate_on_submit():
        f = like_all({
            Patient.name: form.name.data,
            Patient.national_id: form.national_id.data,
            Patient.gender: form.gender.data,
            Patient.phone: form.phone.data,
            Patient.address: form.address.data,
        })

        if form.hospital_id.data != '':
            f.append(Patient.hospital_id == form.hospital_id.data)

        patients = db.session.query(Patient).filter(f).order_by(Patient.name).all()
        return render_template('patient_search.html', title='Patient Search', form=form, results=patients)

    return render_template('patient_search.html', title='Patient Search', form=form)


@application.route('/patient/create', methods=['GET', 'POST'])
@login_required
def patient_create():
    patient = Patient()
    episodes = []

    form = PatientEditForm(obj=patient)
    form.hospital_id.choices = _hospital_id_choices()

    if form.validate_on_submit():
        patient.name = form.name.data
        patient.national_id = form.national_id.data
        patient.hospital_id = form.hospital_id.data
        patient.gender = form.gender.data
        patient.phone1 = form.phone.data
        patient.address = form.address.data

        patient.created_by = current_user
        patient.updated_by = current_user

        db.session.add(patient)
        db.session.commit()
        flash('New patient details for {} have been registered.'.format(patient.name))

        if form.next_action.data == 'CreateEpisode':
            return redirect(url_for('episode_create', patient_id=patient.id))

        return redirect(url_for('patient', id=patient.id))

    return render_template('patient.html', title='Register New Patient', form=form, episodes=episodes)


@application.route('/patient/<int:id>', methods=['GET', 'POST'])
@login_required
def patient(id):
    patient = db.session.query(Patient).filter(Patient.id == id).first()
    episodes = db.session.query(Episode).filter(Episode.patient_id == patient.id).all()

    form = PatientEditForm(obj=patient)
    form.hospital_id.choices = _hospital_id_choices()

    if form.validate_on_submit():
        patient.name = form.name.data
        patient.national_id = form.national_id.data
        patient.hospital_id = form.hospital_id.data
        patient.gender = form.gender.data
        patient.phone1 = form.phone.data
        patient.address = form.address.data
        patient.updated_by = current_user

        db.session.commit()

        flash('Patient details have been updated.')

        if form.next_action.data == 'CreateEpisode':
            return redirect(url_for('episode_create', id=patient.id))

        return redirect(url_for('patient', id=patient.id))

    return render_template('patient.html', title='Patient Details', form=form, episodes=episodes)


@application.route('/episode/<int:id>', methods=['GET', 'POST'])
@login_required
def episode(id):
    episode = db.session.query(Episode).filter(Episode.id == id).first()

    form = EpisodeEditForm(obj=episode)
    form.patient_id.disabled = True
    form.hospital_id.choices = _hospital_id_choices()
    form.patient_id.choices = _patient_id_choices()
    form.attendee_id.choices = _attendee_id_choices()

    if form.validate_on_submit():
        episode.episode_type = form.episode_type.data
        episode.date = form.date.data
        episode.patient_id = form.patient_id.data
        episode.hospital_id = form.hospital_id.data
        episode.surgery_id = form.surgery_id.data
        episode.comments = form.comments.data

        episode.attendees = attendees_parser.from_json(form.attendees.data, episode.id)

        episode.updated_by = current_user

        db.session.commit()

        flash('Episode details have been updated.')

        if form.next_action.data == 'RecordSurgery':
            return redirect(url_for('surgery_create', episode_id=episode.id))

        return redirect(url_for('episode', id=episode.id))

    return render_template('episode.html', title='Episode Details', form=form, episode=episode, edit_disabled=False)


@application.route('/episode_search', methods=['GET', 'POST'])
@login_required
def episode_search():
    form = EpisodeSearchForm()
    form.patient_id.disabled = False
    form.hospital_id.choices = _hospital_id_choices(include_empty=True)
    form.patient_id.choices = _patient_id_choices(include_empty=True)
    form.attendee_id.choices = _attendee_id_choices()

    if form.is_submitted():
        filter = []
        if form.date.data:
            filter.append(Episode.date == form.date.data)
        if form.episode_type.data:
            filter.append(Episode.episode_type == form.episode_type.data)
        if form.hospital_id.data:
            filter.append(Episode.hospital_id == form.hospital_id.data)
        if form.patient_id.data:
            filter.append(Episode.patient_id == form.patient_id.data)

        episodes = db.session.query(Episode).filter(and_(*filter)).order_by(Episode.date).all()
        return render_template('episode_search.html',
                               title='Episode Search',
                               form=form,
                               results=episodes,
                               edit_disabled=False)

    return render_template('episode_search.html', title='Episode Search', form=form, edit_disabled=False)


@application.route('/episode_create', methods=['GET', 'POST'])
@application.route('/episode_create/<int:patient_id>', methods=['GET', 'POST'])
@login_required
def episode_create(patient_id=None):
    episode = Episode()
    form = EpisodeEditForm(obj=episode)
    form.hospital_id.choices = _hospital_id_choices()
    form.patient_id.choices = _patient_id_choices()
    form.attendee_id.choices = _attendee_id_choices()

    form.date.data = datetime.today()

    if patient_id:
        form.patient_id.data = str(patient_id)

    if form.validate_on_submit():
        episode.episode_type = form.episode_type.data
        episode.date = form.date.data
        episode.patient_id = form.patient_id.data
        episode.hospital_id = form.hospital_id.data
        episode.surgery_id = form.surgery_id.data
        episode.comments = form.comments.data

        episode.attendees = attendees_parser.from_json(form.attendees.data, episode.id)

        episode.created_by = current_user
        episode.updated_by = current_user

        db.session.add(episode)
        db.session.commit()

        flash('Episode details have been recorded.')

        if form.next_action.data == 'RecordSurgery':
            return redirect(url_for('surgery_create', episode_id=episode.id))

        return redirect(url_for('episode', id=episode.id))

    return render_template('episode.html', title='Record Episode Details',
                           form=form,
                           episode=episode,
                           edit_disabled=False)


@application.route('/surgery/<int:id>', methods=['GET', 'POST'])
@login_required
def surgery(id):
    surgery = db.session.query(Surgery).filter(Surgery.id == id).first()
    form = SurgeryForm(obj=surgery)
    form.procedure_id.choices = _procedure_id_choices()

    if form.validate_on_submit():
        surgery.cepod = form.cepod.data
        surgery.date_of_discharge = form.date_of_discharge.data
        surgery.side = form.side.data
        surgery.primary = form.primary.data
        surgery.type = form.type.data
        surgery.additional_procedure = form.additional_procedure.data
        surgery.antibiotics = form.antibiotics.data
        surgery.comments = form.comments.data
        surgery.opd_rv_date = form.opd_rv_date.data
        surgery.opd_pain = form.opd_pain.data
        surgery.opd_numbness = form.opd_numbness.data
        surgery.opd_infection = form.opd_infection.data
        surgery.opd_comments = form.opd_comments.data

        episode.updated_by = current_user

        db.session.commit()

        flash('Surgery details have been updated.')
        return redirect(url_for('surgery', id=surgery.id))

    return render_template('surgery.html', title='Surgery Details', form=form, surgery=surgery)


@application.route('/surgery_create/<int:episode_id>', methods=['GET', 'POST'])
@login_required
def surgery_create(episode_id):
    procedure_id_choices = _procedure_id_choices()

    surgery = Surgery()
    episode = db.session.query(Episode).filter(Episode.id == episode_id).first()

    if episode is None:
        raise ValueError('Unable to find an episode with id {}'.format(episode_id))

    surgery.episode = episode
    episode.surgery = surgery

    form = SurgeryForm(obj=surgery)
    form.procedure_id.choices = procedure_id_choices

    if form.validate_on_submit():
        surgery.procedure_id = form.procedure_id.data
        surgery.cepod = form.cepod.data
        surgery.date_of_discharge = form.date_of_discharge.data
        surgery.side = form.side.data
        surgery.primary = form.primary.data
        surgery.type = form.type.data
        surgery.additional_procedure = form.additional_procedure.data
        surgery.antibiotics = form.antibiotics.data
        surgery.comments = form.comments.data
        surgery.opd_rv_date = form.opd_rv_date.data
        surgery.opd_pain = form.opd_pain.data
        surgery.opd_numbness = form.opd_numbness.data
        surgery.opd_infection = form.opd_infection.data
        surgery.opd_comments = form.opd_comments.data

        surgery.created_by = current_user
        surgery.updated_by = current_user

        db.session.commit()

        flash('Surgery details have been updated.')
        return redirect(url_for('surgery', id=surgery.id))

    return render_template('surgery.html', title='Surgery Details', form=form, surgery=surgery)


@application.route('/typeahead/patients', methods=['GET'])
@login_required
def typeahead_patients():
    names = db.session.query(Patient.name).all()
    return jsonify(names)


@application.route('/report', methods=['GET'])
@login_required
def report_index():
    return render_template('report.html', title='Reporting')


@application.route('/report/<string:report_name>', methods=['GET', 'POST'])
@login_required
def report(report_name):
    path = reporting.to_excel(_run_report(report_name))
    return send_file(filename_or_fp=path,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     attachment_filename=report_name + '.xlsx',
                     as_attachment=True)


def _run_report(report_name):
    if report_name.lower() == 'patient':
        patients = db.session.query(Patient).order_by(Patient.name).all()
        d = reporting.patients_as_dict(patients)
    elif report_name.lower() == 'episode':
        episodes = db.session.query(Episode).order_by(Episode.date).all()
        d = reporting.episodes_as_dict(episodes)
    return d


@application.route('/logout')
def logout():
    logout_user()
    flash('Logout successful.')
    return redirect(url_for('index'))


@application.route('/health_check', methods=['GET'])
def health_check():
    try:
        if not application:
            raise ValueError('No application running!')

        if db.session.query(User).count() < 1:
            raise ValueError('No users defined!')

        logging.info('Health Check Passed')
        return '', 204
    except Exception as e:
        logging.error('Health Check Failed!')
        raise e


@application.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    form = AdminForm(obj=surgery)

    if form.validate_on_submit():
        command = form.command.data
        return render_template('admin.html', title='Admin Console', form=form, response=command)

    return render_template('admin.html', title='Admin Console', form=form, response='Waiting...')


# @application.route('/reset', methods=['GET'])
# def reset():
#     admin_command.execute(application, 'reset_db')
#     logging.info('Reset Successful')
#     return redirect(url_for('index'))


def _field_errors(form):
    errors = []
    for field in form:
        for error in field.errors:
            errors.append((field.name, error))

    return errors


def _patient_id_choices(include_empty=False):
    choices = [(str(h.id), h.name) for h in
               db.session.query(Patient).order_by(Patient.name).all()]

    if include_empty:
        choices = [('', '(Any)')] + choices

    return choices


def _hospital_id_choices(include_empty=False):
    choices = [(str(h.id), h.name) for h in
               db.session.query(Hospital).order_by(Hospital.name).all()]

    if include_empty:
        choices = [('', '(Any)')] + choices

    return choices


def _attendee_id_choices(include_empty=False):
    choices = [(str(h.id), h.name) for h in
               db.session.query(User).order_by(User.name).all()]

    if include_empty:
        choices = [('', '(Any)')] + choices

    return choices


def _procedure_id_choices(include_empty=False):
    choices = [(str(h.id), h.name) for h in
               db.session.query(Procedure).order_by(Procedure.name).all()]

    if include_empty:
        choices = [('', '(Any)')] + choices

    return choices
