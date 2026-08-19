from enum import Enum
from System import Double
import OpenTap
from OpenTap import Input
from opentap import TestStep, attribute, property


class ComparisonOperator(Enum):
    GreaterThan = (">", "Actual value must be greater than the threshold.")
    GreaterOrEqual = (">=", "Actual value must be greater than or equal to the threshold.")
    LessThan = ("<", "Actual value must be less than the threshold.")
    LessOrEqual = ("<=", "Actual value must be less than or equal to the threshold.")
    Equal = ("==", "Actual value must equal the threshold within tolerance.")
    NotEqual = ("!=", "Actual value must differ from the threshold by more than tolerance.")

    def __str__(self):
        return self.value[0]

    def describe(self):
        return self.value[1]


@attribute(
    OpenTap.Display(
        "Numeric Assert",
        "Compare any numeric step output against a threshold.",
        "Assertions"
    )
)
class NumericAssert(TestStep):

    Value = property(Input[Double], None).add_attribute(
        OpenTap.Display("Value", "Numeric output to evaluate.", "Assertion")
    )

    Operator = property(
        ComparisonOperator,
        ComparisonOperator.GreaterThan
    ).add_attribute(
        OpenTap.Display("Operator", "Comparison operator.", "Assertion")
    )

    Threshold = property(Double, 100.0).add_attribute(
        OpenTap.Display("Threshold", "Comparison threshold.", "Assertion")
    )

    Tolerance = property(Double, 0.001).add_attribute(
        OpenTap.Display(
            "Tolerance",
            "Allowed difference for equality comparisons.",
            "Assertion"
        )
    )

    def __init__(self):
        super().__init__()
        self.Value = Input[Double]()

    def Run(self):
        actual = float(self.Value.Value)
        threshold = float(self.Threshold)
        tolerance = abs(float(self.Tolerance))
        operator = self.Operator

        if operator == ComparisonOperator.GreaterThan:
            passed = actual > threshold

        elif operator == ComparisonOperator.GreaterOrEqual:
            passed = actual >= threshold

        elif operator == ComparisonOperator.LessThan:
            passed = actual < threshold

        elif operator == ComparisonOperator.LessOrEqual:
            passed = actual <= threshold

        elif operator == ComparisonOperator.Equal:
            passed = abs(actual - threshold) <= tolerance

        elif operator == ComparisonOperator.NotEqual:
            passed = abs(actual - threshold) > tolerance

        else:
            raise ValueError("Unsupported comparison operator")

        symbol = str(operator)

        self.PublishResult(
            "Numeric Assertion",
            ["Actual", "Operator", "Threshold", "Tolerance", "Passed"],
            [actual, symbol, threshold, tolerance, passed]
        )

        self.log.Info(
            "Assert: {0} {1} {2}; tolerance={3}; result={4}",
            actual,
            symbol,
            threshold,
            tolerance,
            "PASS" if passed else "FAIL"
        )

        if passed:
            self.UpgradeVerdict(OpenTap.Verdict.Pass)
        else:
            self.UpgradeVerdict(OpenTap.Verdict.Fail)