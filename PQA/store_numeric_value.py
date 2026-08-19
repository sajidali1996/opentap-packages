from enum import Enum
from System import Double, String
import OpenTap
from OpenTap import Input
from opentap import TestStep, attribute, property


class NumericValueSource(Enum):
    Manual = ("Manual Value", "Store a number entered in this step.")
    PreviousStep = (
        "Previous Step Output",
        "Store a numeric output produced by an earlier step."
    )

    def __str__(self):
        return self.value[0]

    def describe(self):
        return self.value[1]


@attribute(
    OpenTap.Display(
        "Store Numeric Value",
        "Capture a numeric value for use by following test steps.",
        "Variables"
    )
)
class StoreNumericValue(TestStep):

    VariableName = property(String, "StoredValue").add_attribute(
        OpenTap.Display(
            "Variable Name",
            "Descriptive name used in logs and results.",
            "Variable"
        )
    )

    Source = property(
        NumericValueSource,
        NumericValueSource.PreviousStep
    ).add_attribute(
        OpenTap.Display(
            "Source",
            "Choose a manual value or an earlier step output.",
            "Variable"
        )
    )

    ManualValue = property(Double, 0.0).add_attribute(
        OpenTap.Display(
            "Manual Value",
            "Value used when Source is Manual Value.",
            "Variable"
        )
    )

    InputValue = property(Input[Double], None).add_attribute(
        OpenTap.Display(
            "Input Value",
            "Numeric output from an earlier step.",
            "Variable"
        )
    )

    StoredValue = property(Double, 0.0).add_attribute(
        OpenTap.Display(
            "Stored Value",
            "Captured value available to following steps.",
            "Output"
        )
    ).add_attribute(OpenTap.Output())

    def __init__(self):
        super().__init__()
        self.InputValue = Input[Double]()

    def Run(self):
        if self.Source == NumericValueSource.Manual:
            self.StoredValue = float(self.ManualValue)
            source_description = "manual value"

        elif self.Source == NumericValueSource.PreviousStep:
            try:
                self.StoredValue = float(self.InputValue.Value)
            except Exception:
                self.log.Error(
                    "Input Value is not connected to an earlier step output."
                )
                self.UpgradeVerdict(OpenTap.Verdict.Error)
                return

            source_description = "previous step output"

        else:
            raise ValueError("Unsupported numeric value source")

        self.log.Info(
            "Stored variable '{0}' = {1} from {2}",
            self.VariableName,
            self.StoredValue,
            source_description
        )

        self.PublishResult(
            "Stored Numeric Variable",
            ["Variable", "Value", "Source"],
            [
                self.VariableName,
                self.StoredValue,
                source_description
            ]
        )

        self.UpgradeVerdict(OpenTap.Verdict.Pass)
        