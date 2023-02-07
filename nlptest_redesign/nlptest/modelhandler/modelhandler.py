from abc import ABC, abstractmethod
from typing import List

import spacy
from transformers import pipeline

from ..utils.custom_types import NEROutput


class _ModelHandler(ABC):
    """Abstract base class for handling different models.

    Implementations should inherit from this class and override load_model() and predict() methods.
    """

    @classmethod
    @abstractmethod
    def load_model(cls, path):
        """Load the model.
        """
        return NotImplementedError()

    @abstractmethod
    def predict(self, text: str, *args, **kwargs):
        """Perform predictions on input text.
        """
        return NotImplementedError()


class ModelFactory:
    """
    A factory class for instantiating models.
    """
    SUPPORTED_TASKS = ["ner"]

    def __init__(
            self,
            model,
            task: str,
    ):
        """Initializes the ModelFactory object.
        Args:
            model: SparkNLP, HuggingFace or Spacy model to test.
            task (str): task to perform

        Raises:
            ValueError: If the task specified is not supported.
        """
        assert task in self.SUPPORTED_TASKS, \
            ValueError(f"Task '{task}' not supported. Please choose one of {', '.join(self.SUPPORTED_TASKS)}")

        self.model_class = model
        self.task = task

    @classmethod
    def load_model(cls, task, backend, path) -> 'ModelFactory':
        """Load the model.

        Args:
            path (str): path to model to use
            task (str): task to perform
            backend (optional, str): model backend to load custom model from the path
        """

        class_map = {
            cls.__name__.replace("PretrainedModel", "").lower(): cls for cls in _ModelHandler.__subclasses__()
        }
        model_class_name = task + backend
        model_class = class_map[model_class_name].load_model(path)
        return cls(
            model_class,
            task
        )

    def predict(self, text: str, **kwargs) -> List[NEROutput]:
        """Perform predictions on input text.

        Args:
            text (str): Input text to perform predictions on.

        Returns:
            List[NEROutput]:
                List of NEROutput objects representing the entities and their corresponding labels.
        """
        return self.model_class(text=text, **kwargs)

    def __call__(self, text: str, *args, **kwargs) -> List[NEROutput]:
        """Alias of the 'predict' method"""
        return self.model_class(text=text, **kwargs)


class NERHuggingFacePretrainedModel(_ModelHandler):
    """
    Args:
        model (transformers.pipeline.Pipeline): Pretrained HuggingFace NER pipeline for predictions.
    """

    def __init__(
            self,
            model
    ):
        """
        Attributes:
            model (transformers.pipeline.Pipeline):
                Loaded NER pipeline for predictions.
        """
        self.model = model

    @classmethod
    def load_model(cls, path) -> 'NERHuggingFacePretrainedModel':
        """Load the NER model into the `model` attribute.
        """
        return cls(
            model=pipeline(model=path, task="ner", ignore_labels=[])
        )

    def predict(self, text: str, **kwargs) -> List[NEROutput]:
        """Perform predictions on the input text.

        Args:
            text (str): Input text to perform NER on.
            kwargs: Additional keyword arguments.

        Keyword Args:
            group_entities (bool): Option to group entities.

        Returns:
            List[NEROutput]: A list of named entities recognized in the input text.

        Raises:
            OSError: If the `model` attribute is None, meaning the model has not been loaded yet.
        """
        prediction = self.model(text, **kwargs)

        if kwargs.get("group_entities"):
            prediction = [group for group in self.model.group_entities(prediction) if group["entity_group"] != "O"]

        return [NEROutput(**pred) for pred in prediction]

    def __call__(self, text: str, *args, **kwargs) -> List[NEROutput]:
        """Alias of the 'predict' method"""
        return self.predict(text=text, **kwargs)


class NERSpaCyPretrainedModel(_ModelHandler):
    """
    Args:
        model: Pretrained spacy model.
    """

    def __init__(
            self,
            model
    ):
        self.model = model

    @classmethod
    def load_model(cls, path) -> 'NERSpaCyPretrainedModel':
        """"""
        return cls(
            model=spacy.load(path)
        )

    def predict(self, text: str, *args, **kwargs) -> List[NEROutput]:
        """"""
        doc = self.model(text)

        if kwargs.get("group_entities"):
            return [
                NEROutput(
                    entity=ent.label_,
                    word=ent.text,
                    start=ent.start_char,
                    end=ent.end_char
                ) for ent in doc.ents
            ]

        return [
            NEROutput(
                entity=f"{token.ent_iob_}-{token.ent_type_}" if token.ent_type_ else token.ent_iob_,
                word=token.text,
                start=token.idx,
                end=token.idx + len(token)
            ) for token in doc
        ]

    def __call__(self, text: str, *args, **kwargs) -> List[NEROutput]:
        """Alias of the 'predict' method"""
        return self.predict(text=text)

