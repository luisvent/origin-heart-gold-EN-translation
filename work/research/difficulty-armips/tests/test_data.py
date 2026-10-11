"""Independent numeric facts from ROM archives and current site data.
No generated docs cache and no raw official text written into source tests.
"""
import hashlib
from itertools import accumulate
import json
import struct
import unittest
from ndspy.narc import NARC
from support import ROOT, SOURCE, load_rom, arm9_main

class ROMDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=load_rom()
        cls.schedule=json.loads((SOURCE/'research/gym_schedule.json').read_text())
        cls.parties=NARC(cls.rom.getFileByName('a/0/5/6')).files
        cls.trainers=NARC(cls.rom.getFileByName('a/0/5/5')).files
        cls.scripts=NARC(cls.rom.getFileByName('a/0/1/2')).files
        cls.site={t['id']:t for t in json.loads((ROOT/'site/src/data/trainers.json').read_text())}

    def test_all_schedule_and_story_maxima_vs_rom_and_site(self):
        for row in self.schedule['gym_facts']+self.schedule['story_facts']:
            maxima=[]
            for opponent in row['opponents']:
                tid=opponent['trainer_id'];raw=self.parties[tid]
                with self.subTest(trainer=tid):
                    self.assertEqual(hashlib.sha256(raw).hexdigest(),opponent['party_member_sha256'])
                    count=self.trainers[tid][3]
                    levels=[struct.unpack_from('<H',raw,i*28+6)[0] for i in range(count)]
                    self.assertEqual(levels,[m['level'] for m in self.site[tid]['team']])
                    self.assertEqual(max(levels),opponent['maximum']);maxima.append(max(levels))
            if 'rank' in row:self.assertEqual(max(maxima),row['maximum'])

    def test_guide_order_table_and_two_exceptions(self):
        gyms=self.schedule['gym_facts']
        self.assertEqual([g['rank'] for g in gyms],list(range(1,17)))
        self.assertEqual([g['maximum'] for g in gyms],[12,20,25,38,55,65,80,100,80,80,88,80,80,80,85,85])
        self.assertEqual([g['badge_id'] for g in gyms],[0,1,2,3,5,6,4,7,8,9,10,11,13,12,14,15])
        guide=json.loads((ROOT/'site/src/data/trainer_guide.json').read_text())
        entries=[e for section in guide if section['title'] in ('Kanto Gym challenges','Johto Gym challenges') for e in section['entries']]
        self.assertEqual(len(entries),16)
        for gym,entry in zip(gyms,entries):self.assertTrue({o['trainer_id'] for o in gym['opponents']}&set(entry['ids']))
        self.assertEqual(gyms[3]['completion']['candidate_predicate']['any'],[{'badge':3},{'flag':1220}])
        self.assertEqual(gyms[-1]['completion']['candidate_predicate']['any'],[{'badge':15},{'flag':209}])

    def test_effective_caps_are_running_maxima_not_changed_gym_facts(self):
        policy=self.schedule['proposal']
        actual=[g['maximum'] for g in self.schedule['gym_facts']]
        expected=[12,20,25,38,55,65,80]+[100]*9
        self.assertEqual(policy['caps'],expected)
        self.assertEqual(policy['caps'],list(accumulate(actual,max)))
        self.assertEqual(policy['completed_all_gyms_cap'],100)
        self.assertEqual((actual[8],actual[10],actual[11],actual[15]),(80,88,80,85))
        self.assertTrue(self.schedule['user_approved'] and policy['approved'])
        self.assertEqual(policy['interpretation_authority'],'user')
        self.assertEqual(policy['selection'],'first_unfinished_gym_in_guide_order')
        contract=json.loads((SOURCE/'native/integration_contract.json').read_text())['cap_contract']
        self.assertEqual(contract['decision'],policy['decision'])
        self.assertEqual(contract['selection'],policy['selection'])
        self.assertEqual(contract['completed_all_gyms_cap'],policy['completed_all_gyms_cap'])
        self.assertTrue(self.schedule['resolver_abi']['no_story_cap_stages'])

    def test_all_recorded_script_instructions_and_member_hashes(self):
        commands=json.loads((ROOT/'work/tools/docs/script_cmds.json').read_text())
        def records(node):
            if isinstance(node,dict):
                if all(k in node for k in ('script','offset','command','args')):yield node
                for v in node.values():yield from records(v)
            elif isinstance(node,list):
                for v in node:yield from records(v)
        count=0
        for record in records(self.schedule):
            data=self.scripts[record['script']];off=record['offset'];op=struct.unpack_from('<H',data,off)[0]
            name,sizes=commands[str(op)]
            with self.subTest(script=record['script'],offset=off):
                self.assertEqual(name,record['command']);values=[];off+=2
                for size in sizes:
                    values.append(int.from_bytes(data[off:off+size],'little'));off+=size
                self.assertEqual(values,record['args']);count+=1
        self.assertGreater(count,50)
        for member in self.schedule['script_members']:
            self.assertEqual(hashlib.sha256(self.scripts[member['id']]).hexdigest(),member['sha256'])
        c=self.schedule['constructor'];arm=arm9_main(self.rom);off=c['arm9_address']-0x02000000
        self.assertEqual(hashlib.sha256(arm[off:off+c['region_length']]).hexdigest(),c['sha256'])

    def test_all_twenty_item_additions_have_native_effect_dispatch(self):
        archive=self.rom.getFileByName('a/0/1/7');rows=NARC(archive).files
        self.assertEqual(hashlib.sha256(archive).hexdigest(),'e28535d77ab2c5fdb7914279b2338a354122303a864c65ed524b79f7c0648637')
        self.assertEqual(len(rows),791);self.assertTrue(all(len(row)==34 for row in rows))
        ids=[18,19,20,21,22,23,24,25,27,28,29,34,35,37,38,39,40,41,42,54]
        self.assertEqual(len(set(ids)),20)
        for i in ids:
            with self.subTest(item=i):
                self.assertEqual(int.from_bytes(rows[i][8:10],'little')>>11,0)
                self.assertEqual((rows[i][11],rows[i][12]),(2,1))
