"""Mutation checks for the independent native two-page Options oracle."""
import copy
import unittest
from native_ui_oracles import validate_page_navigation


def sample():
    names=['normal-entry','normal-draft','difficulty-entry','difficulty-draft',
           'normal-retained','confirmed','cancel-drafts','cancelled','restored']
    points=[];before=0x5144;expected=(before|1)^0x20
    for i,name in enumerate(names):
        field=name in ('confirmed','cancelled','restored')
        row=dict(name=name,frame=100+i*40,state=0 if field else 0x02004000,
                 options_owner=0x02003000,field=True,nav_live=int(not field),
                 mode=int(name.startswith('difficulty')),word=before if i<5 or name=='restored' else expected)
        if not field:
            row.update(choices=[0 if i==0 else 2 if name=='cancel-drafts' else 1,0,0,0,0,0,0],
                       counts=[3,2,2,2,4,20,2],nav='008000020101150c030d7a0280900002')
        points.append(row)
    return dict(points=points,inputs=[{'key':k} for k in ('L','R','RIGHT')]+
                [{'touch':[x,180]} for x in (89,18,149,200)])


class NativePageTests(unittest.TestCase):
    def test_valid_retained_drafts_and_shared_exit(self):
        validate_page_navigation(sample())

    def test_rejects_lost_draft_partial_commit_wrong_owner_and_window(self):
        for index,field,value in [(4,'choices',[0]*7),(5,'word',0x5145),
                                  (7,'word',0x5144),(8,'word',0x5165),
                                  (2,'mode',0),(3,'options_owner',0x02003002),
                                  (2,'counts',[0]*7),(5,'nav_live',1),
                                  (2,'nav','00'*16),(3,'word',0x5164)]:
            with self.subTest(index=index,field=field):
                run=copy.deepcopy(sample());run['points'][index][field]=value
                with self.assertRaises(AssertionError):validate_page_navigation(run)

    def test_rejects_missing_navigation_and_outcome_write(self):
        for change in ('missing-point','missing-touch','outcome-write'):
            run=sample()
            if change=='missing-point':run['points'].pop(4)
            elif change=='missing-touch':run['inputs']=[{'key':k} for k in ('L','R','RIGHT')]
            else:run['inputs'].append({'write':0x02003000})
            with self.subTest(change=change),self.assertRaises(AssertionError):validate_page_navigation(run)
