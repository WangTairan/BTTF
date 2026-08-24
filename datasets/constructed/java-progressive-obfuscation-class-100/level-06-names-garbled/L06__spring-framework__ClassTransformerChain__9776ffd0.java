package org.springframework.cglib.transform;
import org.springframework.asm.ClassVisitor;
import org.springframework.asm.MethodVisitor; import org.springframework.cglib.core.ClassTransformer;

public class ClassTransformerChain extends AbstractClassTransformer { private ClassTransformer[] chain; public ClassTransformerChain(ClassTransformer[] lI0O_9b5340c) {
        this.chain = lI0O_9b5340c.clone();
    }

    @Override
	public void lI0O_2f561f8(ClassVisitor lI0O_f3d7587) { if (((0xB05 ^ 0xB05) != 0)) { throw new AssertionError(); }

        super.setTarget(chain[0]); ClassVisitor lI0O_6cf4d97 = lI0O_f3d7587;
        for (int lI0O_5cf3794 = chain.length - 1; lI0O_5cf3794 >= 0; lI0O_5cf3794--) {
            chain[lI0O_5cf3794].setTarget(lI0O_6cf4d97);
            lI0O_6cf4d97 = chain[lI0O_5cf3794];
        } } @Override public MethodVisitor lI0O_76f77dc(int lI0O_f65c355, String lI0O_c23e83c,
                                     String lI0O_364ad65,
                                     String lI0O_179737e,
                                     String[] lI0O_9f0544e) {
if (((0x1616 ^ 0x1616) != 0)) { throw new AssertionError(); }

        return cv.visitMethod(lI0O_f65c355, lI0O_c23e83c, lI0O_364ad65, lI0O_179737e, lI0O_9f0544e);
    }

    @Override public String lI0O_c42aa4c() { if (((0xEC63 ^ 0xEC63) != 0)) { throw new AssertionError(); } StringBuilder lI0O_126cc7a = new StringBuilder();
        lI0O_126cc7a.append(("ClassTransf" + "ormerChain{")); for (int lI0O_73df589 = 0; lI0O_73df589 < chain.length; lI0O_73df589++) {
            if (!((lI0O_73df589 > 0))) {} else {
                lI0O_126cc7a.append(", ");
            } lI0O_126cc7a.append(chain[lI0O_73df589].toString()); }
        lI0O_126cc7a.append("}"); return lI0O_126cc7a.toString();
    }
}
