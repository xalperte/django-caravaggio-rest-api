# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
# All rights reserved.
import logging

from collections import OrderedDict

from django.contrib.gis.measure import Distance

from caravaggio_rest_api.utils import get_primary_keys_values

try:
    from dse.cqlengine.columns import UUID, TimeUUID
except ImportError:
    from cassandra.cqlengine.columns import UUID, TimeUUID

from django.conf import settings

from drf_haystack.viewsets import HaystackViewSet
from haystack.exceptions import SpatialError

from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

LOGGER = logging.getLogger(__name__)


class CustomPageNumberPagination(PageNumberPagination):
    page_size_query_param = "limit"

    def get_paginated_response(self, data):

        if data and len(data):
            has_distance = False
            loaded_objects = []
            for instance in data.serializer.instance:
                model = instance.model

                try:
                    distance = getattr(instance, "distance", None)
                    if not has_distance and isinstance(distance, Distance):
                        has_distance = True
                except SpatialError as ex:
                    pass

                loaded_objects.append(
                    model.objects.all().
                    filter(**get_primary_keys_values(
                                instance, instance.model)).
                    first())

            # Get the results serializer from the original View that originated
            # the current response
            results_serializer = \
                data.serializer.context['view'].results_serializer_class

            serializer = results_serializer(loaded_objects, many=True)
            detail_data = serializer.data

            # Copy the relevance score into the model object
            for i_obj, obj in enumerate(detail_data):
                obj["score"] = data[i_obj].get("score", None)

            # Copy the distance field if it exists in the results
            if has_distance:
                for i_obj, obj in enumerate(detail_data):
                    obj["distance"] = data[i_obj].get("distance", None)

            data = detail_data

        return Response(OrderedDict([
            ('total', self.page.paginator.count),
            ('page', len(data)),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))


class CustomModelViewSet(viewsets.ModelViewSet):
    throttle_scope = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for operation in settings.THROTTLE_OPERATIONS.keys():
            scope = "{0}.{1}".format(self.__class__.__name__, operation)
            if scope not in settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]:
                settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"][scope] = \
                    settings.THROTTLE_OPERATIONS[operation]

    def add_throttle(self, operation, rate):
        scope = "{}.{}".format(self.__class__.__name__, operation)
        settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"][scope] = rate

    def get_throttles(self):
        # Only if the scope is not already set
        # we can do that overwriting the method in a subclass
        if not self.throttle_scope:
            if self.action:
                self.throttle_scope = "{0}.{1}". \
                    format(self.__class__.__name__, self.action)
            else:
                # If there is no action we use the DESTROY by default)
                # It can happen if we define a detail_route in the ViewSet
                # and the method (POST, DELETE, etc) used is not the one
                # associated to the detail method.
                self.throttle_scope = "{0}.{1}". \
                    format(self.__class__.__name__, "destroy")

            LOGGER.debug("Throttling Scope: {}".format(self.throttle_scope))
        return super().get_throttles()


class CustomHaystackViewSet(HaystackViewSet):
    throttle_scope = ""
    pagination_class = CustomPageNumberPagination

    document_uid_field = "id"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for operation in settings.THROTTLE_OPERATIONS.keys():
            scope = "{0}.{1}".format(self.__class__.__name__, operation)
            if scope not in settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]:
                settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"][scope] = \
                    settings.THROTTLE_OPERATIONS[operation]

    def add_throttle(self, operation, rate):
        scope = "{}.{}".format(self.__class__.__name__, operation)
        settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"][scope] = rate

    def get_throttles(self):
        if self.action:
            self.throttle_scope = "{0}.{1}". \
                format(self.__class__.__name__, self.action)
        else:
            # If there is no action we use the DESTROY by default)
            # It can happen if we define a detail_route in the ViewSet
            # and the method (POST, DELETE, etc) used is not the one
            # associated to the detail method.
            self.throttle_scope = "{0}.{1}". \
                format(self.__class__.__name__, settings.DELETE_THROTTLE_RATE)

        LOGGER.debug("Throttling Scope: {}".format(self.throttle_scope))
        return super().get_throttles()
