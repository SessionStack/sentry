from __future__ import absolute_import

from builtins import filter
from builtins import map
import functools32

from rest_framework.response import Response

from sentry.api.bases.group import GroupEndpoint
from sentry.api.serializers import serialize
from sentry.models import Group
from sentry.similarity import features
from sentry.utils.functional import apply_values


class GroupSimilarIssuesEndpoint(GroupEndpoint):
    def get(self, request, group):
        limit = request.GET.get('limit', None)
        if limit is not None:
            limit = int(limit) + 1  # the target group will always be included

        results = [group_id__scores for group_id__scores in features.compare(group, limit=limit) if group_id__scores[0] != group.id]

        serialized_groups = apply_values(
            functools32.partial(serialize, user=request.user),
            Group.objects.in_bulk([group_id for group_id, scores in results])
        )

        # TODO(tkaemming): This should log when we filter out a group that is
        # unable to be retrieved from the database. (This will soon be
        # unexpected behavior, but still possible.)
        return Response(
            list(filter(
                lambda group_id__scores: group_id__scores[0] is not None,
                list(map(
                    lambda group_id__scores: (serialized_groups.get(group_id__scores[0]), group_id__scores[1], ),
                    results,
                )),
            )),
        )
