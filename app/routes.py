from flask import flash, redirect, url_for, request, make_response, jsonify, abort, session
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from app.models import User, Journey, Photo
from app import app, db
from app.email import send_password_reset_email
from datetime import datetime
from app import s3_client, s3_resource
import traceback

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

# some proxy data
user = {
    "email": "john@example.com",
    "name": "John Tan",
    "journeys": ["journey1-id", "journey2-id"]
}

journey = {
    "id": "example-id",
    "members": [
        {
            "email": "john@example.com",
            "password": "example-password",
            "name": "John Tan"
        },
        {
            "email": "mary@example.com",
            "password": "example-password",
            "name": "Mary Mee"
        }
    ]
}

photo = {
    "id" : "photo-id",
    "url" : "example@url.com",
    "longitude" : 1.234,
    "latitude" : 5.678,
    "taken_on" : datetime.now().isoformat()
}

error_already_logged_in = {
    "error" : "User is already logged in"
}

error_incorrect_password = {
    "error" : "Incorrect password"
}

error_invalid_email = {
    "error" : "Account does not exist"
}

error_not_authenticated = {
    "error" : "User is not logged in"
}

error_missing_parameters = {
    "error" : "Missing parameters required"
}

success_logout = {
    "success" : "User logged out"
}

@app.route('/login', methods=['POST'])
def login():

    credentials = request.json
    
    try:
        email = credentials['email']
        password = credentials['password']
    except Exception:
        print('missing parameters')
        return jsonify(error_missing_parameters), 401

    user = User.query.filter_by(email=email).first()

    if current_user.is_authenticated:
        print("current user: \n{}".format(current_user.get_as_dict()))
        return make_response(user.get_as_dict(), 200)

    if user is None:
        print('user is none')
        return make_response(jsonify(error_invalid_email), 404)
    elif not user.check_password(password):
        print('incorrect password')
        return make_response(jsonify(error_incorrect_password), 401)

    login_user(user)
    session['user'] = user.get_as_dict()
    print("current user: \n{}".format(current_user.get_as_dict()))
    return make_response(user.get_as_dict(), 200)

@app.route('/logout')
@login_required
def logout():  
    if not current_user.is_authenticated:
        return make_response('You are not logged in', 403)
    logout_user()
    return make_response(jsonify(success_logout), 200)

@app.route('/signup', methods=['POST'])
def signup():

    if current_user.is_authenticated:
        return make_response(user.get_as_dict(), 200)

    try: 
        name = request.json['name']
        email = request.json['email']
        password = request.json['password']
    except Exception:
        print('missing parameters')
        return jsonify(error_missing_parameters), 401

    user = User(name=name, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return make_response(user.get_as_dict(), 200)

@app.route('/journeys/<id>')
def get_journey(id):
    journey = Journey.query.filter_by(id=id).first()
    if journey is None:
        abort(404)
    return journey.get_as_dict()


@app.route('/journeys', methods=['POST'])
@login_required
def post_journey():
    try:
        id = request.json['id']
    except Exception:
        print('missing journey id')
        return make_reponse(error_missing_parameters, 401)
    journey = Journey(id=id)
    journey.add_user(current_user)
    db.session.add(journey)
    db.session.commit()
    return journey.get_as_dict()

@app.route('/journeys/<id>/join')
@login_required
def join_journey(id):
    try:
        journey = Journey.query.filter_by(id=id).first()
        print("journey: \n{}".format(journey.get_as_dict()))
        print("current user: \n{}".format(current_user.get_as_dict()))
        if journey in current_user.journeys:
            return make_response("User is already part of this journey", 403)
        journey.add_user(current_user)
        db.session.commit()
        return make_response({
            "success" : "Current user added to journey"
        }, 200)
    except Exception:
        print('invalid journey id')
        return make_response(error_missing_parameters, 401)

@app.route('/journeys/<id>/leave')
@login_required
def leave_journey(id):
    try:
        journey = Journey.query.filter_by(id=id).first()
        print("journey: \n{}".format(journey.get_as_dict()))
        print("current user: \n{}".format(current_user.get_as_dict()))
        if journey not in current_user.journeys:
            return make_response("User is not part of this journey", 403)
        journey.remove_user(current_user)
        db.session.commit()
        return make_response({
            "success" : "Current user removed from journey"
        }, 200)
    except Exception:
        print('invalid journey id')
        return make_response(error_missing_parameters, 401)
    

#TODO: add security measures for current_user authentication
@app.route('/journeys/<id>/photos', methods = ['GET', 'POST'])
def journey_photos(id):
    journey = Journey.query.filter_by(id=id).first()
    if journey is None:
        abort(404)

    if request.method == 'GET':
        journey = Journey.query.filter_by(id=id).first()
        if journey is None:
            abort(404)
        try:
            photos = {
                "urls" : [i.get_as_dict() for i in journey.photos]
            }
            return make_response(photos, 200)
        except:
            return make_response('Error while getting photo IDs')
        
    try:
        photo_blob = request.files['photo']
        longitude = request.form.get('longitude')
        latitude = request.form.get('latitude')
    except Exception:
        return make_response(error_missing_parameters, 401)
    photo = Photo(longitude=longitude, latitude=latitude, journey__id=id)
    db.session.add(photo)
    db.session.commit()
    photo.set_url()
    db.session.commit()
    s3_client.upload_fileobj(photo_blob, app.config["BUCKET_NAME"], "{}.jpg".format(photo.id))
    
    return make_response(photo.get_as_dict(), 200)
    
# @app.route('/reset_password_request', methods=['GET', 'POST'])
# def reset_password_request():
#     if current_user.is_authenticated:
#         return redirect(url_for('index'))
#     form = ResetPasswordRequestForm()
#     if form.validate_on_submit():
#         user = User.query.filter_by(email=form.email.data).first()
#         if user:
#             send_password_reset_email(user)
#         flash('Instructions to reset your password have been sent to your email.')
#         return redirect(url_for('login'))
#     return render_template('reset_password_request.html', title="Reset Password", form=form)


# @app.route('/reset_password/<token>', methods=['GET', 'POST'])
# def reset_password(token):
#     if current_user.is_authenticated:
#         return redirect(url_for('index'))
#     user = User.verify_reset_password_token(token)
#     if not user:
#         return redirect(url_for('index'))
#     form = ResetPasswordForm()
#     if form.validate_on_submit():
#         user.set_password(form.password.data)
#         db.session.commit()
#         flash('Your password has been reset successfully')
#         return redirect(url_for('login'))
#     return render_template('reset_password.html', form=form)


# spare code fragments
       # ret = {}
        # print(photos)
        # for photo in photos:
        # # try:
        #     obj = s3_resource.Object(app.config["BUCKET_NAME"], "{}.jpg".format(photo['id']))
        #     try:
        #         print(obj)
        #         print(obj.get())
        #     except:
        #         continue
        #     body = obj.get()['Body'].read()
        #     print(type(body))
        #     ret[photo['id']] = body.decode(errors="ignore")
        #     # except:
        #     #     return make_response('Something else went wrong', 400)
        # print(type(ret.get('3')))
        # # print(ret)
        # response = make_response(ret, 200)