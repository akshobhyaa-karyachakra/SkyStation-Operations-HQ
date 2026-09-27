import unittest
from backend.delivery import build_delivery_projection


def record(stage, status, key, state='current', issues=None, delivery=None):
    return {'stage':stage,'status':status,'activity_repository_relations':[{'monday_item_id':key}], 'scheduled_date':'2026-09-21' if stage=='flight' else None, 'data_state':state, 'validation_issues':issues or [], 'delivery_status':delivery}

class DeliveryProjectionTests(unittest.TestCase):
    def test_complete_chain(self):
        out=build_delivery_projection({'records':[record('flight','Done','a')]},{'records':[record('processing_qa','Done','a')]},{'records':[record('report_submission','Done','a',delivery='Done')]})
        self.assertEqual(out['totals'], {'planned':1,'flown':1,'processed':1,'submitted':1,'customer_ready':1})
        self.assertEqual(out['quality']['needs_review'],0)

    def test_missing_stages_are_review_not_success(self):
        out=build_delivery_projection({'records':[record('flight','Done','a')]},{'records':[]},{'records':[]})
        self.assertEqual(out['totals'], {'planned':1,'flown':1,'processed':0,'submitted':0,'customer_ready':0})
        self.assertEqual(out['quality']['needs_review'],1)

    def test_invalid_done_report_is_not_submitted(self):
        out=build_delivery_projection({'records':[record('flight','Done','a')]},{'records':[record('processing_qa','Done','a')]},{'records':[record('report_submission','Done','a','needs_review',['done_without_report_link'],'Done')]})
        self.assertEqual(out['totals']['submitted'],0)
        self.assertEqual(out['totals']['customer_ready'],0)

    def test_duplicate_stage_is_review(self):
        out=build_delivery_projection({'records':[record('flight','Done','a'),record('flight','Done','a')]},{'records':[]},{'records':[]})
        self.assertEqual(out['quality']['needs_review'],1)
        self.assertEqual(out['totals']['flown'],1)

if __name__=='__main__': unittest.main()
