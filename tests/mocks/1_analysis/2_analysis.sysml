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

    // Valid Case - String direct input
    analysis def case3 {
        subject A;

        metadata ToolExecution {
            toolName = "Windstorm";
        }

        in engine_weight = "No" {@ToolVariable {name = "deltaT";}}
    }

    // Valid Case - Two level input (Rational)
    analysis def case4 {
        subject A;

        metadata ToolExecution {
            toolName = "Windstorm";
        }

        in engine_weight = a.f {@ToolVariable {name = "deltaT";}}
    }

    // Valid Case - Three level input (Integer)
    analysis def case5 {
        subject A;

        metadata ToolExecution {
            toolName = "Windstorm";
        }

        in engine_weight = a.b.c {@ToolVariable {name = "deltaT";}}
    }

    // Valid Case - Three level input (Units)
    analysis def case6 {
        subject A;

        metadata ToolExecution {
            toolName = "Windstorm";
        }

        in engine_weight = a.b.e {@ToolVariable {name = "deltaT";}}
    }

    // Invalid Case - No parameters
    analysis def case7 {
        subject A;

        metadata ToolExecution {
            toolName = "Windstorm";
        }

        in engine_weight = a.b.e;
    }

    // Valid Case - Reference to reference
    analysis def case8 {
        subject A;

        metadata ToolExecution {
            toolName = "Windstorm";
        }

        in engine_weight = a.b.h {@ToolVariable {name = "deltaT";}}
    }

    // Valid Case - List of objects
    analysis def case9 {
        subject A;

        metadata ToolExecution {
            toolName = "Windstorm";
        }

        in engine_weight = a.b.i {@ToolVariable {name = "deltaT";}}
    }

    // Valid Case - Boolean
    analysis def case10 {
        subject A;

        metadata ToolExecution {
            toolName = "Windstorm";
        }

        in engine_weight = a.b.j {@ToolVariable {name = "deltaT";}}
    }

    // Valid Case - Five variables
    analysis def case11 {
        subject A;

        metadata ToolExecution {
            toolName = "Windstorm";
        }

        in engine_weight = a.b.j {@ToolVariable {name = "deltaT";}}
        in engine = a.b.c {@ToolVariable {name = "deltaE";}}
        in engine_num = a.f {@ToolVariable {name = "deltaF";}}
        in engine_test = "ABC" {@ToolVariable {name = "deltaC";}}
        in engine_temp = a.b.h {@ToolVariable {name = "deltaG";}}
    }


}
