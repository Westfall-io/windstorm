package a {
    import ScalarValues::*;
    import SI::*;

    part def B {
        attribute c : Real = 1;
        attribute d : Real = 2;
        attribute e : MassValue = 3 [kg];
    }

    part def A {
        part b : B;
    }

    part a : A;
}
