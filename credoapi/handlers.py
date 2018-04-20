from credoapi.helpers import OutputFrame, OutputHeader, Body
from credoapi.serializers import OutputFrameSerializer
from credoapi.models import User, Team, Device, Detection
from credoapi.exceptions import RegisterException, LoginException

from django.db.utils import IntegrityError
from django.core.mail import send_mail
from django.contrib.auth import authenticate

import string
from random import choice

import logging

logger = logging.getLogger(__name__)

CHARS = string.ascii_letters


def generate_key():
    return ''.join(choice(CHARS) for x in range(8))


def handle_register_frame(frame):
    # throw proper exception on duplicated user
    user_info = frame['body']['user_info']
    # device_info = frame['body']['device_info']

    # create or get team
    team_name = user_info['team']
    team, _ = Team.objects.get_or_create(name=team_name)

    # create user
    user_email = user_info['email']
    user_name = user_info['name']

    key = generate_key()
    while User.objects.filter(key=key).exists():
        key = generate_key()

    try:
        user = User.objects.create(
            team=team,
            display_name=user_name,
            key=key,
            username=user_name,
            email=user_email
        )
        user.set_password(key)
        user.save()
    except IntegrityError as e:
        if 'UNIQUE' in e.message:
            logger.info("Already registered user tried to register! {%s, %s}" % (user_name, user_email))
            raise RegisterException("Username or e-mail address is already registered!")
        else:
            raise e

    # send email with key
    send_mail(
        "Credo API registration information",
        "Hello!\n\nThank you for registering in Credo API Portal, your generated access token is: %s please use it for login operation in the mobile app. \n\nbest regards,\nCredo Team" % key,
        'credoapi@credo.science',
        [user_email],
        fail_silently=False
    )

    logger.info("Registered new user {%s, %s}" % (user_name, user_email))

    return


def handle_login_frame(frame):
    key = frame['body']['key_info']['key']

    user = authenticate(token=key)

    if user == None:
        logger.info("Unsuccessful login attempt." % user.display_name)
        raise LoginException("Wrong username or password!")

    logger.info("User %s logged in." % user.display_name)

    user_info = UserInfoSerializer(user)
    body = Body(user_info=user_info)
    output_header = OutputHeader('server', 'login', '1.3')
    output_frame = OutputFrame(output_header, body)
    output_frame_serializer = OutputFrameSerializer(output_frame)
    return output_frame_serializer.data


def handle_ping_frame(frame):
    pass


def handle_detection_frame(frame):
    pass
