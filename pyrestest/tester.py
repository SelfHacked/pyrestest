"""API Tester."""
import abc
import typing
import uuid

import pytest
from django.urls import reverse
from rest_framework.response import Response


class Endpoint:
    """API Endpoint."""

    def __init__(self, basename: str):
        """
        Initialize  endpoint.

        :param basename:
            Base URI of the endpoint. Must end with a trailing slash.
        """
        from rest_framework.test import APIClient

        self._basename = basename
        self._client = APIClient()

    def list_url(self):
        """List url."""
        return reverse(f'{self._basename}-list')

    def detail_url(self, pk: typing.Any):
        """Detail url."""
        return reverse(f'{self._basename}-detail', kwargs={'pk': pk})

    def set_user(self, user):
        """Set user for authentication."""
        if user:
            self._client.force_authenticate(user)

    def get(self, pk: typing.Any) -> Response:
        """Make get request."""
        return self._client.get(self.detail_url(pk=pk))

    def get_items(self) -> Response:
        """Make list request."""
        return self._client.get(self.list_url())

    def post(self, payload: dict) -> Response:
        """Make post request."""
        return self._client.post(self.list_url(), payload)

    def put(self, pk: typing.Any, payload: dict) -> Response:
        """Make put request."""
        return self._client.put(self.detail_url(pk=pk), payload)

    def delete(self, pk: typing.Any):
        """Make delete request."""
        return self._client.delete(self.detail_url(pk=pk))


class RestTester(abc.ABC):
    """Test REST API."""

    MODEL = None
    AUTH_USER_MODEL = None
    BASENAME = None
    READONLY_FIELDS = []

    def setup_method(self, method):
        """Setup test."""
        self._endpoint = Endpoint(basename=self.BASENAME)

    def teardown_method(self, method):
        """Teardown test."""
        self._endpoint = None

    def auth_user(
            self,
            user_id=None,
            email='foo@example.com',
            subscription={},  # noqa: B006
    ) -> typing.Any:
        """
        Create a regular user.

        Args:
            user_id: User id
            email: Email address
            subscription: type of subscription

        :returns Auth User object.
        """
        return self.AUTH_USER_MODEL(
            uuid=str(user_id or uuid.uuid4()),
            email=email,
            groups=[],
            is_active=True,
            is_staff=False,
            subscription=subscription,
        )

    @staticmethod
    def assert_equal_item(item: typing.Any, data: dict):
        """Assert that item equal to the data."""
        for key in data.keys():
            assert str(getattr(item, key)) == str(data[key])

    @abc.abstractmethod
    def get_create_payload(self, user_id=None) -> dict:
        """
        Get item payload for create.

        Subclass should override this method to return the payload used for
        create.
        :param user_id: User identifier.

        :returns Payload used for create
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_update_payload(self, payload: dict, readonly=False) -> dict:
        """
        Get item payload for update.

        Subclass should override this method to return the payload used for
        update.
        :param payload: Payload used to create.
        :param readonly: Specify whether to update readonly fields.

        :returns Payload used for update.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def test_create(self):
        """Test create."""
        raise NotImplementedError()

    @abc.abstractmethod
    def test_list_by_owner(self):
        """Test list items belong to the owner."""
        raise NotImplementedError()

    @pytest.mark.django_db
    def test_get_by_owner(self):
        """Test owner can get item belong to the user."""
        user_id = uuid.uuid4()
        item = self.MODEL.objects.create(**self.get_create_payload(user_id))

        self._endpoint.set_user(user=self.auth_user(user_id))
        response = self._endpoint.get(pk=item.id)

        # check status
        assert response.status_code == 200

        # assert that data is stored correctly
        self.assert_equal_item(item, response.data)

    @pytest.mark.django_db
    def test_anonymous_user_not_allowed(self):
        """Test user get."""
        item = self.MODEL.objects.create(**self.get_create_payload())
        response = self._endpoint.get(pk=item.id)

        assert response.status_code == 401

    @pytest.mark.django_db
    def test_get_non_owner_not_allowed(self):
        """Test that regular users can only get self."""
        user_id = uuid.uuid4()
        item = self.MODEL.objects.create(**self.get_create_payload(user_id=user_id))

        self._endpoint.set_user(user=self.auth_user(uuid.uuid4()))
        response = self._endpoint.get(pk=item.id)

        assert response.status_code == 403

    def _update(
            self,
            owner: typing.Any,
            auth_user: typing.Optional[typing.Any],
            readonly=False,
    ):
        payload = self.get_create_payload(owner.id)
        item = self.MODEL.objects.create(**payload)

        payload = self.get_update_payload(payload, readonly)
        self._endpoint.set_user(auth_user)
        response = self._endpoint.put(pk=item.id, payload=payload)

        return item.id, payload, response

    @pytest.mark.django_db
    def test_put_owner(self):
        """Test regular users can update profiles."""
        owner = self.auth_user()
        item_id, payload, response = self._update(
            owner=owner,
            auth_user=owner,
        )

        # check status
        assert response.status_code == 200

        # assert that data is stored correctly
        item = self.MODEL.objects.get(pk=item_id)
        self.assert_equal_item(item, payload)

    @pytest.mark.django_db
    def test_anonymous_not_allowed(self):
        """Test profile puth."""
        _, _, response = self._update(
            owner=self.auth_user(),
            auth_user=None,
        )

        # check status
        assert response.status_code == 401

    @pytest.mark.django_db
    def test_readonly_fields(self):
        """Test that user_id and id are not editable."""
        owner = self.auth_user()
        item_id, payload, response = self._update(
            owner=owner,
            auth_user=owner,
            readonly=True,
        )

        assert response.status_code == 200

        # readonly fields are not changed.
        item = self.MODEL.objects.get(pk=item_id)

        for key in self.READONLY_FIELDS:
            assert getattr(item, key) != payload[key]

        # new profile is not created.
        assert len(self.MODEL.objects.all()) == 1

    @pytest.mark.django_db
    def test_delete(self):
        """Test delete."""
        raise NotImplementedError()
