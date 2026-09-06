from pathlib import Path
import unittest
from unittest.mock import patch
import yaml
from scripts import pull_news, validate_draft_data

ROOT = Path(__file__).resolve().parents[1]

class CommissionerReviewTests(unittest.TestCase):
    def test_brand_and_home_field_contract(self):
        layout=(ROOT/'_layouts/default.html').read_text(encoding='utf-8')
        self.assertIn('include league-mark.html',layout)
        self.assertIn('league-brand.css',layout)
        for path in ['_includes/franchise-card.html','_includes/franchise-gallery.html','retired/quahog-stripes.md']:
            text=(ROOT/path).read_text(encoding='utf-8')
            self.assertIn('Home Field:',text)
            self.assertNotIn('>Field:',text)

    def test_news_does_not_ingest_bodies_or_unsafe_links(self):
        xml=b'<rss><channel><item><title>Good</title><link>https://example.com/a</link><description>PRIVATE ARTICLE BODY</description></item><item><title>Bad</title><link>javascript:alert(1)</link></item></channel></rss>'
        payload,_=pull_news.build_news_payload([('Fixture',pull_news.parse_feed(xml,'Fixture'))])
        self.assertEqual(len(payload['items']),1)
        self.assertNotIn('PRIVATE ARTICLE BODY',str(payload))
        self.assertEqual(set(payload['items'][0]),{'source','title','link','published_at','category'})

    def test_failed_source_keeps_previous_items_with_fresh_other_source(self):
        old={'source':'RotoWire NFL','title':'Earlier','link':'https://example.com/old','published_at':'2026-09-05T12:00:00Z','category':'fantasy'}
        fresh={'source':'CBS Sports NFL','title':'New','link':'https://example.com/new','published_at':'Sun, 06 Sep 2026 12:00:00 GMT'}
        payload,_=pull_news.build_news_payload([('RotoWire NFL',[]),('CBS Sports NFL',[fresh,fresh])],existing={'items':[old]})
        self.assertEqual([i['title'] for i in payload['items']],['New','Earlier'])
        self.assertEqual(payload['items'][0]['published_at'],'2026-09-06T12:00:00Z')

    def test_failure_scrubs_unknown_fields_in_existing_data(self):
        old={'source':'Test','title':'Good','link':'https://example.com/a','body':'DO NOT PUBLISH'}
        payload,_=pull_news.build_news_payload([],existing={'items':[old]})
        self.assertNotIn('body',payload['items'][0])

    def test_wire_escapes_and_exposes_pause_control(self):
        text=(ROOT/'_includes/news-wire.html').read_text(encoding='utf-8')
        self.assertIn('item.title | escape',text)
        self.assertIn('item.link | escape',text)
        self.assertIn('data-wire-toggle',text)
        self.assertIn('noopener noreferrer',text)
        self.assertNotIn('item.description',text)

    def test_malformed_news_url_is_rejected_without_crashing(self):
        self.assertEqual(pull_news.valid_items({'items':[{'title':'Bad','link':'https://['}]}),[])

    def test_newest_items_are_chosen_before_source_limit(self):
        items=[{'source':'Test','title':str(i),'link':f'https://example.com/{i}','published_at':f'2026-09-{i:02d}T12:00:00Z'} for i in range(1,11)]
        payload,_=pull_news.build_news_payload([('Test',items)])
        self.assertEqual(len(payload['items']),8)
        self.assertEqual(payload['items'][0]['title'],'10')
        self.assertNotIn('1',[i['title'] for i in payload['items']])

    def test_cup_gallery_is_local_and_complete(self):
        data=yaml.safe_load((ROOT/'_data/cup_gallery.yml').read_text(encoding='utf-8'))
        self.assertEqual(len(data['images']),12)
        self.assertEqual(len({i['file'] for i in data['images']}),12)
        for photo in data['images']:
            self.assertTrue((ROOT/'assets/img/cup'/photo['file']).is_file())
            self.assertTrue(photo['alt'])

    def test_every_historical_order_image_exists(self):
        drafts=validate_draft_data.load('drafts.yml')['drafts']
        for draft in drafts:
            if draft['year'] < 2026:
                self.assertTrue(validate_draft_data.local_asset(draft['order_asset']['path'],draft['year']))

    def test_2026_is_completed_not_an_invented_board(self):
        draft=next(d for d in validate_draft_data.load('drafts.yml')['drafts'] if d['year']==2026)
        self.assertEqual(draft['draft_date'],'2026-09-02 21:00:00 -0400')
        self.assertEqual(draft['time_label'],'9:00 PM ET')
        self.assertEqual(draft['draft_order'],[])
        self.assertIsNone(draft['pick_count'])
        self.assertTrue((ROOT/'_drafts/2026.md').is_file())

    def test_2026_unknown_values_cannot_be_zero(self):
        data={name:validate_draft_data.load(name) for name in ('drafts.yml','franchises.yml','seasons.yml')}
        next(d for d in data['drafts.yml']['drafts'] if d['year']==2026)['pick_count']=0
        with patch.object(validate_draft_data,'load',side_effect=data.__getitem__):
            with self.assertRaisesRegex(SystemExit,'unresolved draft data'):
                validate_draft_data.main()
