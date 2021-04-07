from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.utils.deconstruct import deconstructible
from django.template.defaultfilters import filesizeformat
from imghdr import what
from hashlib import md5


def content_file_name(instance, filename):
    filename = filename.split('.')[0]
    print(filename)
    return '/'.join(
        [md5(str(instance.author).encode('utf-8')).hexdigest(),
         str(md5((filename + str(timezone.now())).encode('utf-8')).hexdigest())])


@deconstructible
class FileValidator(object):
    error_messages = {
        'max_size': ("Ensure this file size is not greater than %(max_size)s."
                     " Your file size is %(size)s."),
        'min_size': ("Ensure this file size is not less than %(min_size)s. "
                     "Your file size is %(size)s."),
        'content_type': "Files of type %(content_type)s are not supported.",
    }

    def __init__(self, max_size=None, min_size=None, types=()):
        self.max_size = max_size
        self.min_size = min_size
        self.types = types

    def __call__(self, data):
        if self.max_size is not None and data.size > self.max_size:
            params = {
                'max_size': filesizeformat(self.max_size),
                'size': filesizeformat(data.size),
            }
            raise ValidationError(self.error_messages['max_size'],
                                  'max_size', params)

        if self.min_size is not None and data.size < self.min_size:
            params = {
                'min_size': filesizeformat(self.mix_size),
                'size': filesizeformat(data.size)
            }
            raise ValidationError(self.error_messages['min_size'],
                                  'min_size', params)

        if self.types:
            guess = what(data)
            if guess not in self.types:
                params = {'type': guess}
                raise ValidationError(self.error_messages['content_type'],
                                      'content_type', params)

    def __eq__(self, other):
        return isinstance(other, FileValidator)


class Post(models.Model):
    validate_file = FileValidator(max_size=512 * 512,
                                  types=('png', 'jpeg', 'gif', 'jpg'))
    author = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    title = models.CharField(max_length=35)
    text = models.TextField()
    rating = models.IntegerField(default=0)
    postType = models.IntegerField(default=1)
    picture = models.ImageField(upload_to=content_file_name, blank=True, validators=[validate_file])

    published_date = models.DateTimeField(
        blank=True, null=True)

    def get_absolute_url(self):
        return "/%i/" % self.id

    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def __str__(self):
        return self.title


class LikeDislike(models.Model):
    LIKE = 1
    DISLIKE = -1

    VOTES = (
        (DISLIKE, 'Не нравится'),
        (LIKE, 'Нравится')
    )

    vote = models.SmallIntegerField(verbose_name="Голос", choices=VOTES)
    user = models.ForeignKey('auth.User', verbose_name="Пользователь", on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)


class Comments(models.Model):
    validate_file = FileValidator(max_size=512 * 512,
                                  types=('png', 'jpeg', 'gif', 'jpg'))
    author = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    published_date = models.DateTimeField(
        blank=True, null=True)
    text = models.TextField()
    picture = models.ImageField(upload_to=content_file_name, blank=True, validators=[validate_file])

    def __str__(self):
        return self.text[:20]
