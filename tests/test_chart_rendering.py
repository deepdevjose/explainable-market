"""Visual data semantics: observed direction, forecast separation and provenance."""
import unittest
from unittest.mock import patch
from xml.etree import ElementTree

import charts
from market_explained.intelligence.visualization import prediction_chart


def svg(markup):
    start = markup.index('<svg')
    return ElementTree.fromstring(markup[start:markup.index('</svg>')+6])


class ChartRenderingTests(unittest.TestCase):
    def test_every_observed_move_uses_its_own_direction_in_both_chart_sizes(self):
        for markup in (charts.sparkline([100,102,101,101]),
                       charts.price_chart(['2026-11-01','2026-11-02','2026-11-03','2026-11-04'],[100,102,101,101])):
            segments = svg(markup).findall(".//line[@data-direction]")
            self.assertEqual([s.attrib['data-direction'] for s in segments],['up','down','flat'])
            self.assertLess(float(segments[0].attrib['y2']),float(segments[0].attrib['y1']))
            self.assertGreater(float(segments[1].attrib['y2']),float(segments[1].attrib['y1']))

    def test_forecast_starts_at_last_observed_close_and_has_a_separate_horizon(self):
        markup = charts.price_chart(['2026-11-01','2026-11-02','2026-11-03'],[100,102,101],
            forecast=dict(predicted_value='103',lower_value='99',upper_value='107'))
        root = svg(markup)
        last = root.findall(".//line[@data-direction]")[-1]
        future = root.find(".//line[@stroke-dasharray='7 5']")
        self.assertEqual(future.attrib['x1'],last.attrib['x2'])
        self.assertEqual(future.attrib['y1'],last.attrib['y2'])
        self.assertGreater(float(future.attrib['x2']),float(future.attrib['x1']))
        self.assertLess(float(future.attrib['y2']),float(future.attrib['y1']))
        self.assertIsNotNone(root.find(".//polygon[@class='forecast-band']"))
        self.assertIn('Predicción (estimación)',markup)
        historical = charts.price_chart(['2026-11-01','2026-11-02'],[100,101])
        self.assertNotIn('forecast-line',historical)

    def test_forecast_never_attaches_to_newer_data_another_source_or_revised_reference(self):
        rows = [dict(date='2026-11-01',cutoff='2026-11-01T23:59:59+00:00',price='100'),
                dict(date='2026-11-02',cutoff='2026-11-02T23:59:59+00:00',price='101'),
                dict(date='2026-11-03',cutoff='2026-11-03T23:59:59+00:00',price='999')]
        prediction = dict(provider='test-source',data_cutoff_timestamp=rows[1]['cutoff'],reference_price='101',
            predicted_value='102',uncertainty_interval=dict(lower_value='99',upper_value='105'))
        with patch('market_explained.intelligence.visualization.series',return_value=('test-source',rows)):
            chart = prediction_chart({},prediction)
            self.assertIn('forecast-line',chart)
            self.assertNotIn('999',chart)
            self.assertIsNone(prediction_chart({},dict(prediction,reference_price='101.01')))
            self.assertIsNone(prediction_chart({},dict(prediction,provider='other-source')))
            self.assertIsNone(prediction_chart({},dict(prediction,data_cutoff_timestamp='2026-11-04T23:59:59+00:00')))

    def test_invalid_forecast_values_are_rejected_and_axis_text_is_escaped(self):
        dates=['2026-<bad>','2026-11-02']
        self.assertNotIn('<bad>',charts.price_chart(dates,[100,101]))
        for bounds in (dict(predicted_value='NaN',lower_value='99',upper_value='105'),
                       dict(predicted_value='110',lower_value='99',upper_value='105')):
            with self.assertRaises(ValueError):
                charts.price_chart(dates,[100,101],forecast=bounds)

    def test_forecast_legend_and_axis_follow_the_page_language(self):
        import app as web
        from flask import g
        with web.app.test_request_context('/'):
            for language,legend,axis in (('en','Prediction (estimate)','Next close'),
                                         ('zh-Hans','预测（估计）','下一收盘')):
                g.language=language
                markup=charts.price_chart(['2026-11-01','2026-11-02'],[100,101],
                    forecast=dict(predicted_value='102',lower_value='99',upper_value='105'))
                self.assertIn(legend,markup)
                self.assertIn(axis,markup)
