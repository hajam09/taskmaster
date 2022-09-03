import os
import random
import string

from colorfield.fields import ColorField
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils import timezone


def getRandomAvatar():
    return "avatars/" + random.choice(os.listdir(os.path.join(settings.MEDIA_ROOT, "avatars/")))


def generateString():
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))


class BaseModelManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleteFl=False)


class BaseModel(models.Model):
    createdDttm = models.DateTimeField(default=timezone.now)
    modifiedDttm = models.DateTimeField(auto_now=True)
    reference = models.CharField(max_length=2048, blank=True, null=True)
    deleteFl = models.BooleanField(default=False)
    orderNo = models.IntegerField(default=1, blank=True, null=True)
    versionNo = models.IntegerField(default=1, blank=True, null=True)

    class Meta:
        abstract = True

    def _delete(self, using=None, keep_parents=False):
        # NOT IN USE
        self.deleteFl = True
        self.save()


class ComponentGroup(BaseModel):
    internalKey = models.CharField(max_length=2048, blank=True, null=True, unique=True)
    code = models.CharField(max_length=2048, blank=True, null=True)
    icon = models.CharField(max_length=2048, blank=True, null=True)
    colour = ColorField(default='#FF0000')

    class Meta:
        verbose_name = "ComponentGroup"
        verbose_name_plural = "ComponentGroups"

    def __str__(self):
        return self.internalKey

    def getRelatedComponentsByOrderNo(self):
        return self.components.all().order_by('orderNo')


class Component(BaseModel):
    componentGroup = models.ForeignKey(ComponentGroup, on_delete=models.CASCADE, related_name="components")
    internalKey = models.CharField(max_length=2048, blank=True, null=True)
    code = models.CharField(max_length=2048, blank=True, null=True)
    icon = models.CharField(max_length=2048, blank=True, null=True)
    colour = ColorField(default='#FF0000')

    class Meta:
        ordering = ['componentGroup', 'orderNo']
        verbose_name_plural = "Component"

    def __str__(self):
        return self.internalKey

    def serializeComponentVersion1(self):
        return {
            "id": self.id or None,
            "internalKey": self.internalKey,
            "code": self.code,
            "icon": self.icon,
            "colour": self.colour,
        }


class Team(BaseModel):
    internalKey = models.CharField(max_length=2048, blank=True, null=True, unique=True)
    url = models.SlugField(max_length=10, editable=settings.DEBUG, unique=True, default=generateString, db_index=True)
    description = models.TextField()
    admins = models.ManyToManyField(User, related_name='teamAdmins')
    members = models.ManyToManyField(User, related_name='teamMembers')
    isPrivate = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Team"
        verbose_name_plural = "Teams"
        index_together = [
            ("internalKey", "url"),
        ]

    def __str__(self):
        return self.internalKey

    def getUrl(self):
        return reverse('jira:team-page', kwargs={'url': self.url})

    def hasAccessPermission(self, user):
        if not self.isPrivate:
            return True
        return user in self.members.all() or user in self.admins.all()


class Profile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    url = models.SlugField(max_length=10, editable=settings.DEBUG, unique=True, default=generateString, db_index=True)
    publicName = models.CharField(max_length=2048, blank=True, null=True)
    jobTitle = models.CharField(max_length=2048, blank=True, null=True)
    department = models.CharField(max_length=2048, blank=True, null=True)
    profilePicture = models.ImageField(upload_to='profile-picture', blank=True, null=True, default=getRandomAvatar)

    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"


class TeamChatMessage(BaseModel):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='teamChatMessages')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()

    class Meta:
        verbose_name = "TeamChatMessage"
        verbose_name_plural = "TeamChatMessages"

    def getUserProfilePicture(self):
        profile = self.user.profile.profilePicture.url

        if profile is None:
            return getRandomAvatar()

        return profile.profilePicture.url

    def getChatTime(self):
        hour = self.createdDttm.hour
        minute = self.createdDttm.minute
        if len(str(minute)) == 1:
            minute = f'0{minute}'
        meridiem = "am" if hour < 12 else "pm"
        return f'{hour}:{minute} {meridiem}'
