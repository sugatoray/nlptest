import unittest

from nlptest import Harness
import pandas as pd
from johnsnowlabs import nlp

class AccuracyTestCase(unittest.TestCase):

    def setUp(self) -> None:
        nlp.start()

        self.h_spacy = Harness(
            task="ner",
            model="en_core_web_sm",
            data="nlptest/data/conll/sample.conll",
            hub="spacy"
            )
        self.h_spacy.configure(
            {'defaults': {
                'min_pass_rate': 0.65,
            },
             'tests': {
                 'accuracy': {
                     'min_f1_score': {
                        'min_score': 0.65
                    }
                 }
             }
            })
        self.report = self.h_spacy.generate().run().report()

    def test_report(self):
        self.assertIsInstance(self.report, pd.DataFrame)
