import logging
import os
import pickle
from collections import defaultdict
from typing import Optional, Union

import pandas as pd
import yaml
from pkg_resources import resource_filename

from .augmentation import AugmentRobustness
from .datahandler.datasource import DataFactory
from .modelhandler import ModelFactory
from .testrunner import BaseRunner
from .transform import TestFactory


class Harness:
    """ Harness is a testing class for NLP models.

    Harness class evaluates the performance of a given NLP model. Given test data is
    used to test the model. A report is generated with test results.
    """
    SUPPORTED_HUBS = ["spacy", "huggingface", "johnsnowlabs"]
    DEFAULTS_DATASET = {
        ("ner", "dslim/bert-base-NER", "huggingface"): "conll/sample.conll",
        ("ner", "en_core_web_sm", "spacy"): "conll/sample.conll",
        ("ner", "ner.dl", "johnsnowlabs"): "conll/sample.conll",
        ("ner", "ner_dl_bert", "johnsnowlabs"): "conll/sample.conll",
        ("text-classification", "mrm8488/distilroberta-finetuned-tweets-hate-speech", "huggingface"):
            "tweet/sample.csv",
        ("text-classification", "textcat_imdb", "spacy"): "imdb/sample.csv",
        ("text-classification", "en.sentiment.imdb.glove", "johnsnowlabs"): "imdb/sample.csv"
    }

    def __init__(
            self,
            model: Union[str],
            task: Optional[str] = "ner",
            hub: Optional[str] = None,
            data: Optional[str] = None,
            config: Optional[Union[str, dict]] = None
    ):
        """
        Initialize the Harness object.

        Args:
            task (str, optional): Task for which the model is to be evaluated.
            model (str | ModelFactory): ModelFactory object or path to the model to be evaluated.
            hub (str, optional): model hub to load from the path. Required if path is passed as 'model'.
            data (str, optional): Path to the data to be used for evaluation.
            config (str | dict, optional): Configuration for the tests to be performed.

        Raises:
            ValueError: Invalid arguments.
        """

        super().__init__()
        self.task = task

        if data is None and (task, model, hub) in self.DEFAULTS_DATASET.keys():
            data_path = os.path.join("data", self.DEFAULTS_DATASET[(task, model, hub)])
            data = resource_filename("nlptest", data_path)
            self.data = DataFactory(data, task=self.task).load()
            if model == "textcat_imdb":
                model = resource_filename("nlptest", "data/textcat_imdb")

            logging.info(f"Default dataset '{(task, model, hub)}' successfully loaded.")

        elif data is None and (task, model, hub) not in self.DEFAULTS_DATASET.keys():
            raise ValueError(f"You haven't specified any value for the parameter 'data' and the configuration you "
                             f"passed is not among the default ones. You need to either specify the parameter 'data' "
                             f"or use a default configuration.")
        elif isinstance(data, list):
            self.data = data
        else:
            self.data = DataFactory(data, task=self.task).load() if data is not None else None

        if isinstance(model, str):
            if hub is None:
                raise OSError(f"You need to pass the 'hub' parameter when passing a string as 'model'.")

            self.model = ModelFactory.load_model(path=model, task=task, hub=hub)
        else:
            self.model = ModelFactory(task=task, model=model)

        if config is not None:
            self._config = self.configure(config)
        else:
            logging.info(f"No configuration file was provided, loading default config.")
            self._config = self.configure(resource_filename("nlptest", "data/config.yml"))

        self._testcases = None
        self._generated_results = None
        self.accuracy_results = None
        self.min_pass_dict = None
        self.default_min_pass_dict = None
        self.df_report = None

    def __repr__(self) -> str:
        return ""
    def __str__(self) -> str:
        return object.__repr__(self)

    def configure(self, config: Union[str, dict]) -> dict:
        """
        Configure the Harness with a given configuration.

        Args:
            config (str | dict): Configuration file path or dictionary
                for the tests to be performed.

        Returns:
            dict: Loaded configuration.
        """
        if type(config) == dict:
            self._config = config
        else:
            with open(config, 'r') as yml:
                self._config = yaml.safe_load(yml)
        self._config_copy = self._config
        return self._config

    def generate(self) -> "Harness":
        """
        Generates the testcases to be used when evaluating the model. The generated testcases are stored in
        `_testcases` attribute.
        """
        if self._config is None:
            raise RuntimeError("Please call .configure() first.")

        tests = self._config['tests']
        self._testcases = TestFactory.transform(self.data, tests, self.model)
        return self

    def run(self) -> "Harness":
        """
        Run the tests on the model using the generated testcases.

        Returns:
            None: The evaluations are stored in `generated_results` attribute.
        """
        if self._testcases is None:
            raise RuntimeError("The test casess have not been generated yet. Please use the `.generate()` method before"
                               "calling the `.run()` method.")
        self._generated_results = BaseRunner(
            self._testcases,
            self.model,
            self.data
        ).evaluate()
        return self

    def report(self) -> pd.DataFrame:
        """
        Generate a report of the test results.

        Returns:
            pd.DataFrame:
                DataFrame containing the results of the tests.
        """
        if self._generated_results is None:
            raise RuntimeError("The tests have not been run yet. Please use the `.run()` method before"
                               "calling the `.report()` method.")

        if isinstance(self._config, dict):
            self.default_min_pass_dict = self._config['defaults'].get('min_pass_rate', 0.65)
            self.min_pass_dict = {
                j: k.get('min_pass_rate', self.default_min_pass_dict) for i, v in \
                self._config['tests'].items() for j, k in v.items()
            }

        summary = defaultdict(lambda: defaultdict(int))
        for sample in self._generated_results:
            summary[sample.test_type]['category'] = sample.category
            summary[sample.test_type][str(sample.is_pass()).lower()] += 1

        report = {}
        for test_type, value in summary.items():
            pass_rate = summary[test_type]["true"] / (summary[test_type]["true"] + summary[test_type]["false"])
            min_pass_rate = self.min_pass_dict.get(test_type, self.default_min_pass_dict)

            if summary[test_type]['category'] == "Accuracy":
                min_pass_rate = 1

            report[test_type] = {
                "category": summary[test_type]['category'],
                "fail_count": summary[test_type]["false"],
                "pass_count": summary[test_type]["true"],
                "pass_rate": pass_rate,
                "minimum_pass_rate": min_pass_rate,
                "pass": pass_rate >= min_pass_rate
            }

        df_report = pd.DataFrame.from_dict(report, orient="index")
        df_report = df_report.reset_index().rename(columns={'index': 'test_type'})

        df_report['pass_rate'] = df_report['pass_rate'].apply(lambda x: "{:.0f}%".format(x * 100))
        df_report['minimum_pass_rate'] = df_report['minimum_pass_rate'].apply(lambda x: "{:.0f}%".format(x * 100))

        col_to_move = 'category'
        first_column = df_report.pop('category')
        df_report.insert(0, col_to_move, first_column)
        df_report = df_report.reset_index(drop=True)

        self.df_report = df_report.fillna("-")

        return self.df_report

    def generated_results(self) -> Optional[pd.DataFrame]:
        """
        Generates an overall report with every textcase and labelwise metrics.

        Returns:
            pd.DataFrame: Generated dataframe.
        """
        if self._generated_results is None:
            logging.warning("Please run `Harness.run()` before calling `.generated_results()`.")
            return
        generated_results_df = pd.DataFrame.from_dict([x.to_dict() for x in self._generated_results])

        return generated_results_df

    def augment(self, input_path: str, output_path: str, inplace: bool = False) -> "Harness":

        """
        Augments the data in the input file located at `input_path` and saves the result to `output_path`.

        Args:
            input_path (str): Path to the input file.
            output_path (str): Path to save the augmented data.
            inplace (bool, optional): Whether to modify the input file directly. Defaults to False.

        Returns:
            Harness: The instance of the class calling this method.

        Raises:
            ValueError: If the `pass_rate` or `minimum_pass_rate` columns have an unexpected data type.

        Note:
            This method uses an instance of `AugmentRobustness` to perform the augmentation.

        Example:
            >>> harness = Harness(...)
            >>> harness.augment("train.conll", "augmented_train.conll")
        """

        dtypes = list(map(
            lambda x: str(x),
            self.df_report[['pass_rate', 'minimum_pass_rate']].dtypes.values.tolist()))
        if dtypes not in [['int64'] * 2, ['int32'] * 2]:
            self.df_report['pass_rate'] = self.df_report['pass_rate'].str.replace("%", "").astype(int)
            self.df_report['minimum_pass_rate'] = self.df_report['minimum_pass_rate'].str.replace("%", "").astype(int)
        _ = AugmentRobustness(
            task=self.task,
            config=self._config,
            h_report=self.df_report,
            model=self.model
        ).fix(
            input_path=input_path,
            output_path=output_path,
            inplace=inplace
        )

        return self

    def testcases(self) -> pd.DataFrame:
        """
        Testcases after .generate() is called

        Returns:
            pd.DataFrame:
                testcases formatted into a pd.DataFrame
        """
        final_df = pd.DataFrame([x.to_dict() for x in self._testcases]).drop(["pass", "actual_result"], errors="ignore",
                                                                             axis=1)
        final_df = final_df.reset_index(drop=True)
        return final_df

    def save(self, save_dir: str) -> None:
        """
        Save the configuration, generated testcases and the `DataFactory` to be reused later.

        Args:
            save_dir (str): path to folder to save the different files
        Returns:

        """
        if self._config is None:
            raise RuntimeError("The current Harness has not been configured yet. Please use the `.configure` method "
                               "before calling the `.save` method.")

        if self._testcases is None:
            raise RuntimeError("The test cases have not been generated yet. Please use the `.generate` method before"
                               "calling the `.save` method.")

        if not os.path.isdir(save_dir):
            os.mkdir(save_dir)

        with open(os.path.join(save_dir, "config.yaml"), 'w') as yml:
            yml.write(yaml.safe_dump(self._config_copy))

        with open(os.path.join(save_dir, "test_cases.pkl"), "wb") as writer:
            pickle.dump(self._testcases, writer)

        with open(os.path.join(save_dir, "data.pkl"), "wb") as writer:
            pickle.dump(self.data, writer)

    @classmethod
    def load(cls, save_dir: str, model: Union[str, 'ModelFactory'], task: Optional[str] = "ner",
             hub: Optional[str] = None) -> 'Harness':
        """
        Loads a previously saved `Harness` from a given configuration and dataset

        Args:
            save_dir (str):
                path to folder containing all the needed files to load an saved `Harness`
            task (str):
                task for which the model is to be evaluated.
            model (str | ModelFactory):
                ModelFactory object or path to the model to be evaluated.
            hub (str, optional):
                model hub to load from the path. Required if path is passed as 'model'.
        Returns:
            Harness:
                `Harness` loaded from from a previous configuration along with the new model to evaluate
        """
        for filename in ["config.yaml", "test_cases.pkl", "data.pkl"]:
            if not os.path.exists(os.path.join(save_dir, filename)):
                raise OSError(f"File '{filename}' is missing to load a previously saved `Harness`.")

        with open(os.path.join(save_dir, "data.pkl"), "rb") as reader:
            data = pickle.load(reader)

        harness = Harness(task=task, model=model, data=data, hub=hub, config=os.path.join(save_dir, "config.yaml"))
        harness.generate()

        return harness
