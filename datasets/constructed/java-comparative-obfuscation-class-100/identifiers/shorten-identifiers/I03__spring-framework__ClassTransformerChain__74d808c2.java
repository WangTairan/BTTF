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
        return cv.visitMethod(acc, nam, des, sig, exc);
    }

    @Override
	public String to() {
		StringBuilder sb = new StringBuilder();
        sb.append("ClassTransformerChain{");
        for (int i = 0; i < chain.length; i++) {
            if (i > 0) {
                sb.append(", ");
            }
            sb.append(chain[i].toString());
        }
        sb.append("}");
        return sb.toString();
    }
}
