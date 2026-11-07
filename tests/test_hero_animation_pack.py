"""The installed pack must match its inventory and explicit action coverage."""
import hashlib,json,struct,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PACK=ROOT/'app/src/midlet/resources/hd/characters/hero'
class HeroPackTest(unittest.TestCase):
 def test_installed_asset_inventory(self):
  inventory=json.loads((PACK/'inventory.json').read_text())
  self.assertEqual(16,len(inventory['sheets']))
  self.assertEqual(52,sum(m['frames'] for m in inventory['sheets'].values()))
  for name,meta in inventory['sheets'].items():
   data=(PACK/name).read_bytes()
   self.assertEqual(hashlib.sha256(data).hexdigest(),meta['sha256'])
   self.assertEqual((meta['width'],meta['height']),struct.unpack_from('>II',data,16))
 def test_manifest_coverage_and_anchors(self):
  props=dict(line.split('=',1) for line in (PACK/'animation.properties').read_text().splitlines() if line and not line.startswith('#'))
  selectors=set()
  for key in props:
   if not key.endswith('.sheet'):continue
   prefix=key[:-6];get=lambda k:props[prefix+'.'+k]
   selector=(int(get('set')),int(get('slot')),int(get('layout')))
   self.assertNotIn(selector,selectors);selectors.add(selector)
   self.assertTrue((PACK/get('sheet')).is_file())
   self.assertEqual(('40','40','20','38'),tuple(get(k) for k in ('width','height','pivotX','pivotY')))
   self.assertEqual(('*','*'),(get('appearance9'),get('appearance10')))
  expected={(s,slot,0) for s in (0,3) for slot in range(12 if s==0 else 16)}
  self.assertEqual(expected,selectors)
