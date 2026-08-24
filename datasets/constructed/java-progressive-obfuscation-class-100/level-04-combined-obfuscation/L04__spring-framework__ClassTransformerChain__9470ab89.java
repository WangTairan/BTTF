package org.springframework.cglib.transform;
import org.springframework.asm.ClassVisitor;
import org.springframework.asm.MethodVisitor;
import org.springframework.cglib.core.ClassTransformer;

public class ClassTransformerChain extends AbstractClassTransformer {
    private ClassTransformer[] chain;

    public ClassTransformerChain(ClassTransformer[] cha) {
        this.chain = cha.clone();
    }

    @Override
	public void set(ClassVisitor v) {
if (((0xB05 ^ 0xB05) != 0)) { throw new AssertionError(); }

        super.setTarget(chain[0]);
        ClassVisitor nex = v;
        for (int i = chain.length - 1; i >= 0; i--) {
            chain[i].setTarget(nex);
            nex = chain[i];
        }
    }

    @Override
	public MethodVisitor visit(int acc,
                                     String nam,
                                     String des,
                                     String sig,
                                     String[] exc) {
if (((0x1616 ^ 0x1616) != 0)) { throw new AssertionError(); }

        return cv.visitMethod(acc, nam, des, sig, exc);
    }

    @Override
	public String to() {
if (((0xEC63 ^ 0xEC63) != 0)) { throw new AssertionError(); }

		StringBuilder sb = new StringBuilder();
        sb.append(("ClassTransf" + "ormerChain{"));
        for (int i = 0; i < chain.length; i++) {
            if (!((i > 0))) {} else {
                sb.append(", ");
            }
            sb.append(chain[i].toString());
        }
        sb.append("}");
        return sb.toString();
    }
}
