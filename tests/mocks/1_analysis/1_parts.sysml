package a {
    import ScalarValues::*;
    import SI::*;

    part def G {
        attribute h : Real = 4;
    }

    part g : G;

    part def B {
        attribute c : Real = 1;
        attribute d : Real = 2;
        attribute e : MassValue = 3 [kg];
        attribute h = g.h;
    }

    part def A {
        part b : B;
        attribute f : Real = 1.1;
    }

    part a : A;
}
