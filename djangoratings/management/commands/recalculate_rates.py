from django.core.management.base import NoArgsCommand, CommandError
from django.contrib.contenttypes.models import *
from djangoratings.models import *
from django.db import connection

class Command(NoArgsCommand):
    
    def handle_noargs(self, **options):
        """
        Recalculate the djangoratings_score and related content type table using djangoratings_vote.
        
        I created this management command because for some reason my djangoratings_score and
        the object being rated upon became out of sync with the djangoratings_vote
        (which, upon testing was correct).
        
        NOTE: Assumes field name 'rating' on rated model!!!!
        
        @author: Alex Hayes <alex@alution.com>
        """
        sums = {}
        votes = Vote.objects.all()
        for vote in votes:
            if not vote.content_type_id in sums:
                sums[ vote.content_type_id ] = {}
            if not vote.object_id in sums[ vote.content_type_id ]:
                sums[ vote.content_type_id ][ vote.object_id ] = {
                    'score': 0,
                    'votes': 0
                }
            sums[ vote.content_type_id ][ vote.object_id ]['votes'] += 1
            sums[ vote.content_type_id ][ vote.object_id ]['score'] += vote.score
        
        for content_type_id in sums:
            content_type = ContentType.objects.get(id=content_type_id)
            model = content_type.model_class()
            for object_id in sums[content_type_id]:
                # Update the Score
                score = Score.objects.get(content_type=content_type, object_id=object_id)
                score.votes = sums[content_type_id][object_id]['votes']
                score.score = sums[content_type_id][object_id]['score']
                score.save()
                
                # Update the actual object that was rated
                inst = model.objects.get(id=object_id)
                inst.rating_votes = sums[content_type_id][object_id]['votes']
                inst.rating_score = sums[content_type_id][object_id]['score']
                inst.save()