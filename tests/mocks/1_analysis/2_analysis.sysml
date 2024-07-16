package Analysis {
    import a::*;
    import AnalysisTooling::*;

    // Run Matrix
    // No Action, Action, Two Actions
    // No Meta, Meta, Two Metas
    // Single Input, Multiple Input
    // 18 Cases

    // Invalid Case - No action, no meta, single input
    analysis def case1 {
        subject A;

        in engine_weight = a.b.c;
    }

    // Invalid Case - Action, no meta, single input
    analysis def case2 {
        subject A;
        action runSim {
            in engine_weight = a.b.c;
        }
    }

    // Valid Case - No action, meta, string direct input
    analysis def case3 {
        subject A;

        metadata ToolExecution {
            toolName = "Windstorm";
        }

        in engine_weight = "No" {@ToolVariable {name = "deltaT";}}
    }

    // Valid Case - No action, meta, two level input (Rational)
    analysis def case4 {
        subject A;

        metadata ToolExecution {
            toolName = "Windstorm";
        }

        in engine_weight = a.f {@ToolVariable {name = "deltaT";}}
    }

    // Valid Case - No action, meta, three level input (Integer)
    analysis def case5 {
        subject A;

        metadata ToolExecution {
            toolName = "Windstorm";
        }

        in engine_weight = a.b.c {@ToolVariable {name = "deltaT";}}
    }

    // Valid Case - No action, meta, three level input (Units)
    analysis def case6 {
        subject A;

        metadata ToolExecution {
            toolName = "Windstorm";
        }

        in engine_weight = a.b.e {@ToolVariable {name = "deltaT";}}
    }

}
