from .models import User, Login
from passlib.pwd import genword
from passlib.hash import pbkdf2_sha512


def user_login(user, password):
    user = User.objects.filter(userName=user)
    if user.count() == 0:
        return None

    user = user.get()

    if pbkdf2_sha512.verify(user.devID + password, user.password):
        Login.objects.filter(userID=user).delete()
        token = genword(entropy=52, length=64)
        new_login = Login(userID=user.userName, token=token).save()
        return token
    else:
        return None


def user_register(user, password, device):
    if User.objects.filter(userName=user).count() != 0 or User.objects.filter(devID=device).count() != 0:
        return False

    passwd = pbkdf2_sha512.hash(device + password)
    new_user = User(userName=user, password=passwd, devID=device).save()
    return True


def get_user(token):
    res = Login.objects.filter(token=token)
    if res.count() != 0:
        return res.get().userID
    else:
        return False
