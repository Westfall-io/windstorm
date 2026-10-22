package Verify {
    public import AnalysisTooling::*;

    verification def verify_case1 {
        subject A;

        metadata ToolExecution {
            toolName = "Windstorm";
        }

        in engine_weight = 5.0 {@ToolVariable {name = "deltaT";}}
        in engine = 4.0 {@ToolVariable {name = "deltaE";}}
    }
}
