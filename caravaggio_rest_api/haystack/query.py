# -*- coding: utf-8 -*
# Copyright (c) 2018-2019 PreSeries Tech, SL
# All rights reserved.
from haystack.query import SearchQuerySet, \
    ValuesSearchQuerySet, ValuesListSearchQuerySet


class CaravaggioSearchQuerySet(SearchQuerySet):

    def terms_json_facet(self, facet_name, field, facets, **kwargs):
        """Adds a terms json facet to a query for the provided field."""
        clone = self._clone()
        if not getattr(clone.query, "add_json_query_facet"):
            raise TypeError(
                "'{}.{}' is not valid SearchQuerySet class. "
                "It has not support for json facets.",
                clone.query.__module__,
                clone.query.__name__)
        clone.query.add_json_terms_facet(facet_name, field, facets, **kwargs)
        return clone

    def query_json_facet(self, facet_name, q, facets, **kwargs):
        """Adds a query json facet to a query for the provided field."""
        clone = self._clone()
        if not getattr(clone.query, "add_json_query_facet"):
            raise TypeError(
                "'{}.{}' is not valid SearchQuerySet class. "
                "It has not support for json facets.",
                clone.query.__module__,
                clone.query.__name__)
        clone.query.add_json_query_facet(facet_name, q, facets, **kwargs)
        return clone

    def values(self, *fields):
        """
        Returns a list of dictionaries, each containing the key/value pairs for
        the result, exactly like Django's ``ValuesQuerySet``.
        """
        qs = self._clone(klass=CaravaggioValuesSearchQuerySet)
        qs._fields.extend(fields)
        return qs

    def values_list(self, *fields, **kwargs):
        """
        Returns a list of field values as tuples, exactly like Django's
        ``QuerySet.values``.

        Optionally accepts a ``flat=True`` kwarg, which in the case of a
        single field being provided, will return a flat list of that field
        rather than a list of tuples.
        """
        flat = kwargs.pop("flat", False)

        if flat and len(fields) > 1:
            raise TypeError(
                "'flat' is not valid when values_list is"
                " called with more than one field.")

        qs = self._clone(klass=CaravaggioValuesListSearchQuerySet)
        qs._fields.extend(fields)
        qs._flat = flat
        return qs


class CaravaggioValuesListSearchQuerySet(ValuesListSearchQuerySet):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._internal_fields = ['score']


class CaravaggioValuesSearchQuerySet(ValuesSearchQuerySet):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._internal_fields = ['score']
