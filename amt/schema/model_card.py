from __future__ import annotations

from datetime import datetime

from pydantic import Field

from amt.schema.shared import BaseModel


class Provenance(BaseModel):
    git_commit_hash: str | None = Field(
        None,
        description="Git commit hash of the commit which contains the transformation file used to create this card",
    )
    timestamp: datetime | None = Field(
        None,
        description="A timestamp of the date, time and timezone of generation of this Model Card in ISO 8601 format",
    )
    uri: str | None = Field(None, description="URI to the tool that was used to perform the transformations")
    author: str | None = Field(None, description="Name of person that initiated the transformations")


class License(BaseModel):
    license_name: str = Field(..., description="Any license from the open source license list")
    license_link: str | None = Field(
        None,
        description="A link to a file of that name inside the repo,"
        "or a URL to a remote file containing the license contents",
    )


class Owner(BaseModel):
    oin: str | None = Field(None, description="If applicable the Organisatie-identificatienummer (OIN)")
    organization: str | None = Field(
        None,
        description="Name of the organization that owns the model. If ion is NOT provided this field is REQUIRED",
    )
    name: str | None = Field(None, description="Name of a contact person within the organization")
    email: str | None = Field(None, description="Email address of the contact person or organization")
    role: str | None = Field(
        None,
        description="Role of the contact person. This field should only be set when the name field is set",
    )


class Artifact(BaseModel):
    uri: str | None = Field(None, description="The URI of the model artifact")
    content_type: str | None = Field(
        None,
        alias="content-type",  # pyright: ignore [reportGeneralTypeIssues]
        description="The content type of the model artifact.Recognized values are 'application/onnx',"
        "to refer to an ONNX representation of the model",
    )
    md5_checksum: str | None = Field(
        None,
        alias="md5-checksum",  # pyright: ignore [reportGeneralTypeIssues]
        description="Optional checksum for the content of the file",
    )


class Label(BaseModel):
    name: str = Field(..., description="The name of the label.")
    dtype: str = Field(..., description="The data type of the label.")
    value: str = Field(..., description="The value of the label.")


class Parameter(BaseModel):
    name: str = Field(..., description="The name of the parameter.")
    dtype: str | None = Field(None, description="The data type of the parameter.")
    value: str | None = Field(None, description="The value of the parameter.")
    labels: list[Label] | None = None


class TaskItem(BaseModel):
    type: str = Field(..., description="The task of the model")
    name: str | None = Field(None, description="The (pretty) name for the model tasks")


class Dataset(BaseModel):
    type: str = Field(..., description="The type of the dataset")
    name: str = Field(..., description="The name of the dataset")
    split: str | None = Field(None, description="The dataset split (e.g., train, test, validation).")
    features: list[str] | None = None
    revision: str | None = Field(None, description="Version of the dataset")


class Label1(BaseModel):
    name: str | None = Field(None, description="The name of the feature")
    type: str | None = Field(None, description="The type of the label")
    dtype: str | None = Field(None, description="The data type of the feature")
    value: str | None = Field(None, description="The value of the feature.")


class Metric(BaseModel):
    type: str = Field(..., description="Metric-id from Hugging Face Metrics")
    name: str = Field(..., description="A descriptive name of the metric.")
    dtype: str = Field(..., description="The data type of the metric")
    value: str | int | float = Field(..., description="The value of the metric")
    labels: list[Label1] | None = Field(None, description="This field allows to store meta information about a metric")


class Result1(BaseModel):
    name: str = Field(..., description="The name of the bar")
    value: float = Field(..., description="The value of the corresponding bar")


class BarPlot(BaseModel):
    type: str = Field(..., description="The type of the bar plot")
    name: str | None = Field(None, description="A (pretty) name for the plot")
    results: list[Result1]


class Datum(BaseModel):
    x_value: float = Field(..., description="The x-value of the graph")
    y_value: float = Field(..., description="The y-value of the graph")


class Result2(BaseModel):
    class_: str | int | float | bool | None = Field(
        None,
        alias="class",
        description="The output class name that the graph corresponds to",
    )
    feature: str = Field(..., description="The feature the graph corresponds to")
    data: list[Datum]


class GraphPlot(BaseModel):
    type: str = Field(..., description="The type of the graph plot")
    name: str | None = Field(None, description="A (pretty) name of the graph")
    results: list[Result2]


class Measurements(BaseModel):
    bar_plots: list[BarPlot] | None = None
    graph_plots: list[GraphPlot] | None = None


class Result(BaseModel):
    task: list[TaskItem]
    datasets: list[Dataset]
    metrics: list[Metric]
    measurements: Measurements


class ModelIndexItem(BaseModel):
    name: str | None = Field(None, description="The name of the model")
    model: str | None = Field(None, description="A URI pointing to a repository containing the model file")
    artifacts: list[Artifact] | None = None
    parameters: list[Parameter] | None = None
    results: list[Result]


class ModelCardSchema(BaseModel):
    provenance: Provenance | None = None
    name: str | None = Field(None, description="Name of the model")
    language: list[str] | None = Field(None, description="The natural languages the model supports in ISO 639")
    license: License
    tags: list[str] | None = Field(None, description="Tags with keywords to describe the project")
    owners: list[Owner] | None = None
    model_index: list[ModelIndexItem] = Field(alias="model-index")  # pyright: ignore [reportGeneralTypeIssues]
