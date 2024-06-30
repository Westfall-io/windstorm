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

    // Invalid Case - No action, no meta, two inputs
    analysis def case2 {
        subject A;

        in engine_weight = a.b.c;
        in engine = a.b.d;
    }

    // Valid Case - No action, meta, one input
    analysis def case3 {
        subject A;

        metadata ToolExecution {
            toolName = "Windstorm";
        }

        in engine_weight = a.b.c {@ToolVariable {name = "deltaT";}}
    }

    // Valid Case - No action, meta, two input
    analysis def case4 {
        subject A;

        metadata ToolExecution {
            toolName = "Windstorm";
        }

        in engine_weight = a.b.c {@ToolVariable {name = "deltaT";}}
        in engine = a.b.d {@ToolVariable {name = "deltaE";}}
    }

    // Valid Case - No action, two metas, one input
    analysis def case5 {
        subject A;

        metadata ToolExecution {
            toolName = "Windstorm";
        }

        metadata ToolExecution {
            toolName = "ModelCenter";
        }

        in engine_weight = a.b.c {@ToolVariable {name = "deltaT";}}
    }

    // Valid Case - No action, two metas, two input
    analysis def case6 {
        subject A;

        metadata ToolExecution {
            toolName = "Windstorm";
        }

        metadata ToolExecution {
            toolName = "ModelCenter";
        }

        in engine_weight = a.b.c {@ToolVariable {name = "deltaT";}}
        in engine = a.b.d {@ToolVariable {name = "deltaE";}}
    }

    // Invalid Case - Action, no meta, single input
    analysis def case7 {
        subject A;
        action runSim {
            in engine_weight = a.b.c;
        }
    }

    // Invalid Case - Action, no meta, two inputs
    analysis def case8 {
        subject A;

        action runSim {
            in engine_weight = a.b.c;
            in engine = a.b.d;
        }
    }

    // Valid Case - Action, meta, one input
    analysis def case9 {
        subject A;

        action runSim {
            metadata ToolExecution {
                toolName = "Windstorm";
            }

            in engine_weight = a.b.c {@ToolVariable {name = "deltaT";}}
        }
    }

    // Invalid Case - Action, meta-wrong place, one input
    analysis def scase9 {
        subject A;

        metadata ToolExecution {
            toolName = "Windstorm";
        }

        action runSim {
            in engine_weight = a.b.c {@ToolVariable {name = "deltaT";}}
        }
    }

    // Valid Case - Action, meta, two input
    analysis def case10 {
        subject A;

        action runSim {
            metadata ToolExecution {
                toolName = "Windstorm";
            }

            in engine_weight = a.b.c {@ToolVariable {name = "deltaT";}}
            in engine = a.b.d {@ToolVariable {name = "deltaE";}}
        }
    }

    // Valid Case - Action, meta, two input
    analysis def scase10 {
        subject A;

        action runSim {
            metadata ToolExecution {
                toolName = "Windstorm";
            }

            in engine_weight = a.b.c {@ToolVariable {name = "deltaT";}}
            in engine = a.b.e {@ToolVariable {name = "deltaE";}}
        }
    }

    // Valid Case - Action, two metas, one input
    analysis def case11 {
        subject A;

        action runSim {
            metadata ToolExecution {
                toolName = "Windstorm";
            }

            metadata ToolExecution {
                toolName = "ModelCenter";
            }

            in engine_weight = a.b.c {@ToolVariable {name = "deltaT";}}
        }
    }

    // Valid Case - Action, two metas, two input
    analysis def case12 {
        subject A;

        action runSim {
            metadata ToolExecution {
                toolName = "Windstorm";
            }

            metadata ToolExecution {
                toolName = "ModelCenter";
            }

            in engine_weight = a.b.c {@ToolVariable {name = "deltaT";}}
            in engine = a.b.d {@ToolVariable {name = "deltaE";}}
        }
    }

    // Invalid Case - Two action, no meta, single input
    analysis def case13 {
        subject A;
        action runSim {
            in engine_weight = a.b.c;
        }
        action postProcess {
            in engine_weight = a.b.c;
        }
    }

    // Invalid Case - Two action, no meta, two inputs
    analysis def case14 {
        subject A;

        action runSim {
            in engine_weight = a.b.c;
            in engine = a.b.d;
        }

        action postProcess {
            in engine_weight = a.b.c;
        }
    }

    // Valid Case - Two action, meta, one input
    analysis def case15 {
        subject A;

        action runSim {
            metadata ToolExecution {
                toolName = "Windstorm";
            }

            in engine_weight = a.b.c {@ToolVariable {name = "deltaT";}}
        }

        action postProcess {
            in engine_weight = a.b.c;
        }
    }

    // Valid Case - Two action, meta, one input
    analysis def scase15 {
        subject A;

        action preProcess {
            in engine_weight = a.b.c;
        }

        action runSim {
            metadata ToolExecution {
                toolName = "Windstorm";
            }

            in engine_weight = a.b.c {@ToolVariable {name = "deltaT";}}
        }

    }

    // Valid Case - Two action, meta, two input
    analysis def case16 {
        subject A;

        action runSim {
            metadata ToolExecution {
                toolName = "Windstorm";
            }

            in engine_weight = a.b.c {@ToolVariable {name = "deltaT";}}
            in engine = a.b.d {@ToolVariable {name = "deltaE";}}
        }
    }

    // Valid Case - Two action, two metas, one input
    analysis def case17 {
        subject A;

        action runSim {
            metadata ToolExecution {
                toolName = "Windstorm";
            }

            metadata ToolExecution {
                toolName = "ModelCenter";
            }

            in engine_weight = a.b.c {@ToolVariable {name = "deltaT";}}
        }

        action postProcess {
            in engine_weight = a.b.c;
        }
    }

    // Valid Case - Two action, two metas, two input
    analysis def case18 {
        subject A;

        action runSim {
            metadata ToolExecution {
                toolName = "Windstorm";
            }

            metadata ToolExecution {
                toolName = "ModelCenter";
            }

            in engine_weight = a.b.c {@ToolVariable {name = "deltaT";}}
            in engine = a.b.d {@ToolVariable {name = "deltaE";}}
        }

        action postProcess {
            in engine_weight = a.b.c;
        }
    }

}
